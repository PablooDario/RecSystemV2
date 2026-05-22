"""
Dataset split utilities.

MovieLens  → temporal 80/20 split per user (sorted by timestamp).
Survey     → leave-one-out cross-validation over all positive items per user.

Both base functions return DataFrames with columns:
    user_id     int
    movie_idx   int   (0-based index into the cosine similarity matrix)
    rating      float

The ``*_sampled`` variants wrap the base functions and attach, for each
held-out positive item, a candidate set of ``{positive} ∪ 99 random negatives``
drawn from the catalog of movies the user has not interacted with. This
enables the sampled-evaluation protocol (He et al. 2017, NeuMF; Rendle 2019)
where ranking metrics are computed over a 100-item universe per user
instead of the full catalog.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def _load_movie_matrix_map(movies_path: str | Path) -> dict[int, int]:
    """
    Build a mapping from the movie's catalog ID to its matrix index.

    movies_final.csv columns used:
        movieId  — 0-based matrix index (position in cosine_sim.npy)
        id       — TMDb ID (used by the survey dataset)
    """
    movies = pd.read_csv(movies_path, usecols=["tmdb_id", "movie_id"])
    return dict(zip(movies["tmdb_id"].astype(int), movies["movie_id"].astype(int)))


def _catalog_size(movies_path: str | Path) -> int:
    """Return the number of movies in the catalog (max movieId + 1)."""
    movies = pd.read_csv(movies_path, usecols=["movie_id"])
    return int(movies["movie_id"].max()) + 1


def movielens_split(
    ratings_path: str | Path,
    train_ratio: float = 0.8,
    positive_threshold: float = 4.0,
    split_strategy: str = "random",
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    80/20 split per user for the MovieLens dataset.

    ratings_final.parquet already uses the 0-based matrix index as movieId.

    Test set is filtered to positive ratings only (>= positive_threshold)
    because we only want to evaluate whether the model surfaces items the
    user genuinely liked. The default threshold is 4.0, aligned with the
    stricter relevance definition used by the evaluation pipeline.

    Parameters
    ----------
    split_strategy : {"random", "temporal"}
        - ``"random"`` (default): shuffle per user with a fixed seed.
          Metrics tend to be higher than temporal because the model can
          see temporally-adjacent interactions during training.
        - ``"temporal"``: sort by timestamp and take the last 20% per user
          (simulates real-world scenario, no future-leakage).

    Returns:
        train, test  — DataFrames with [user_id, movie_idx, rating].
    """
    ratings = pd.read_parquet(ratings_path)
    # Bug fix: drop duplicates introduced by NB5's genre-explode step
    ratings = ratings.drop_duplicates(subset=["user_id", "movie_id"])
    ratings = ratings.rename(
        columns={"movie_id": "movie_idx"}
    )[["user_id", "movie_idx", "rating", "timestamp"]]

    # Re-index user IDs to consecutive 0-based integers
    unique_users = sorted(ratings["user_id"].unique())
    user_map = {old: new for new, old in enumerate(unique_users)}
    ratings["user_id"] = ratings["user_id"].map(user_map)

    if split_strategy == "temporal":
        ratings = ratings.sort_values(["user_id", "timestamp"], kind="stable")
    elif split_strategy == "random":
        rng = np.random.default_rng(seed)
        ratings = ratings.sample(frac=1.0, random_state=seed).sort_values(
            "user_id", kind="stable"
        )
    else:
        raise ValueError(
            f"split_strategy must be 'temporal' or 'random', got {split_strategy!r}"
        )

    train_parts, test_parts = [], []
    for _, group in ratings.groupby("user_id", sort=False):
        cut = max(1, int(len(group) * train_ratio))
        train_parts.append(group.iloc[:cut])
        test_parts.append(group.iloc[cut:])

    train = (
        pd.concat(train_parts)
        .drop(columns="timestamp")
        .reset_index(drop=True)
    )
    test = (
        pd.concat(test_parts)
        .drop(columns="timestamp")
        .reset_index(drop=True)
    )

    # Only evaluate on items the user actually liked
    test = test[test["rating"] >= positive_threshold].reset_index(drop=True)

    return train, test


def survey_split(
    ratings_path: str | Path,
    movies_path: str | Path,
    positive_threshold: float = 4.0,
    min_positive: int = 2,
    seed: int = 42,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Leave-one-out split with a single random positive item per user.

    For each user with at least ``min_positive`` positively-rated movies
    (rating >= positive_threshold), **one random positive movie** is chosen
    as the held-out test item.  This produces exactly one fold per user,
    avoiding the activity-bias of the per-positive LOO variant.

    The training set of each fold contains **all** ratings from **all**
    valid users (positive AND non-positive), excluding only the single
    held-out item.  This is critical for collaborative filtering, which
    needs the full user×item interaction matrix to learn embeddings.

    Survey ratings use TMDb IDs which are mapped to matrix indices via
    movies_final.csv.

    Returns:
        List of (train, test) DataFrames, one per user.
        Each test DataFrame contains a single row (the held-out item).
        Each train DataFrame contains all ratings from all valid users,
        minus the held-out item.
    """
    ratings = pd.read_csv(ratings_path)
    ratings = ratings.rename(columns={"userid": "user_id"})

    # The survey CSV now has movie_id (0-based benchmark index) directly.
    # Use it as movie_idx if available; otherwise fall back to tmdb_id mapping.
    if "movie_id" in ratings.columns:
        ratings["movie_idx"] = ratings["movie_id"].astype(int)
        ratings = ratings[["user_id", "movie_idx", "rating"]].reset_index(drop=True)
    else:
        if "movieid" in ratings.columns:
            ratings = ratings.rename(columns={"movieid": "tmdb_id"})
        tmdb_to_idx = _load_movie_matrix_map(movies_path)
        ratings = ratings.loc[ratings["tmdb_id"].isin(tmdb_to_idx)].copy()
        ratings.loc[:, "movie_idx"] = ratings["tmdb_id"].map(tmdb_to_idx)
        ratings = ratings[["user_id", "movie_idx", "rating"]].reset_index(drop=True)

    # Identify positive ratings (these define test items)
    positive_counts = (
        ratings[ratings["rating"] >= positive_threshold]
        .groupby("user_id")
        .size()
    )
    valid_users = positive_counts[positive_counts >= min_positive].index

    # Keep only valid users (but ALL their ratings, not just positives)
    ratings = ratings[ratings["user_id"].isin(valid_users)].reset_index(drop=True)

    rng = np.random.default_rng(seed)
    folds: list[tuple[pd.DataFrame, pd.DataFrame]] = []
    for user_id, user_group in ratings.groupby("user_id"):
        user_positives = user_group[user_group["rating"] >= positive_threshold]
        held_out_idx = int(rng.choice(user_positives.index.to_numpy()))
        test = user_group.loc[[held_out_idx]].reset_index(drop=True)
        train = ratings.drop(index=held_out_idx).reset_index(drop=True)
        folds.append((train, test))

    return folds


# ── Sampled-evaluation helpers ────────────────────────────────────────────


def _sample_negatives(
    rng: np.random.Generator,
    seen: set[int],
    positive: int,
    n_movies: int,
    n_negatives: int,
) -> list[int]:
    """
    Draw ``n_negatives`` movie indices from the catalog, excluding any index
    in ``seen`` and the ``positive`` item itself.

    Uses rejection sampling over a batched ``rng.choice``; the unseen pool is
    typically >90% of the catalog so the first batch almost always suffices.
    """
    target = n_negatives
    # Over-sample to absorb collisions with seen items
    batch = min(n_movies, max(target * 2, target + len(seen) + 1))
    picks = rng.choice(n_movies, size=batch, replace=False)
    negs: list[int] = []
    for p in picks:
        v = int(p)
        if v == positive or v in seen:
            continue
        negs.append(v)
        if len(negs) >= target:
            return negs
    # Fallback (extremely rare): deterministic scan to fill the rest
    for v in range(n_movies):
        if len(negs) >= target:
            break
        if v == positive or v in seen or v in negs:
            continue
        negs.append(v)
    return negs


def movielens_split_sampled(
    ratings_path: str | Path,
    movies_path: str | Path,
    n_negatives: int = 99,
    seed: int = 42,
    train_ratio: float = 0.8,
    positive_threshold: float = 4.0,
    split_strategy: str = "random",
) -> tuple[pd.DataFrame, pd.DataFrame, list[tuple[int, int, np.ndarray]]]:
    """
    80/20 split with sampled-evaluation candidates for each test item.

    For every positive item in the test set, builds a candidate set of
    ``{positive} ∪ n_negatives`` random unseen movies. Negatives are drawn
    uniformly from the catalog complement of the user's interactions (train
    ∪ test).

    Parameters
    ----------
    split_strategy : {"temporal", "random"}
        See :func:`movielens_split`.

    Returns:
        train              — DataFrame [user_id, movie_idx, rating]
        test               — DataFrame with the positive items (for reference)
        sampled_test       — list of (user_id, positive_idx, candidates_array)
                             where candidates_array has shape (1 + n_negatives,)
                             and candidates_array[0] is always the positive.
    """
    train, test = movielens_split(
        ratings_path, train_ratio, positive_threshold, split_strategy, seed
    )
    n_movies = _catalog_size(movies_path)
    rng = np.random.default_rng(seed)

    # Build per-user "seen" set from the full rating history (train ∪ test)
    user_seen: dict[int, set[int]] = {}
    for uid, mid in zip(train["user_id"].values, train["movie_idx"].values):
        user_seen.setdefault(int(uid), set()).add(int(mid))
    for uid, mid in zip(test["user_id"].values, test["movie_idx"].values):
        user_seen.setdefault(int(uid), set()).add(int(mid))

    sampled_test: list[tuple[int, int, np.ndarray]] = []
    for uid, mid in zip(test["user_id"].values, test["movie_idx"].values):
        uid_i, mid_i = int(uid), int(mid)
        negs = _sample_negatives(
            rng, user_seen[uid_i], mid_i, n_movies, n_negatives
        )
        candidates = np.array([mid_i] + negs, dtype=np.int32)
        sampled_test.append((uid_i, mid_i, candidates))

    return train, test, sampled_test


def survey_split_sampled(
    ratings_path: str | Path,
    movies_path: str | Path,
    n_negatives: int = 99,
    seed: int = 42,
    positive_threshold: float = 4.0,
    min_positive: int = 2,
) -> list[tuple[pd.DataFrame, pd.DataFrame, np.ndarray]]:
    """
    Leave-one-out with sampled-evaluation candidates (1 random positive per user).

    Wraps ``survey_split`` and attaches a candidate set of
    ``{held_out_positive} ∪ n_negatives`` random unseen movies to each fold.
    Threshold defaults to 4.0 (>=), aligned with the evaluation pipeline.

    Returns:
        List of (train, test, candidates) tuples, one per user. ``candidates``
        is a (1 + n_negatives,) int32 array with the positive at index 0.
    """
    folds = survey_split(
        ratings_path, movies_path, positive_threshold, min_positive, seed=seed
    )
    n_movies = _catalog_size(movies_path)
    rng = np.random.default_rng(seed)

    sampled: list[tuple[pd.DataFrame, pd.DataFrame, np.ndarray]] = []
    for train, test in folds:
        uid = int(test["user_id"].iloc[0])
        pos = int(test["movie_idx"].iloc[0])
        # User's seen items: their positive history in train + the held-out
        user_train = train[train["user_id"] == uid]
        seen = set(user_train["movie_idx"].astype(int).tolist()) | {pos}

        negs = _sample_negatives(rng, seen, pos, n_movies, n_negatives)
        candidates = np.array([pos] + negs, dtype=np.int32)
        sampled.append((train, test, candidates))

    return sampled
