"""
Shared evaluation helpers used by the recommender notebooks (9 → 12).

Evaluation protocols
--------------------

- **MovieLens** (temporal 80/20 split, full-catalog ranking):
  Precision@K, Normalized Recall@K, NDCG@K, Diversity@K, Novelty@K, Coverage.
  Threshold for relevance: rating >= 4.0.

- **Survey** (leave-one-out with 1 random positive per user, sampled
  evaluation with 1 positive + 99 negatives):
  HR@K, NDCG@K. Threshold for relevance: rating >= 4.0.
"""

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from ..models.base import BaseRecommender
from .metrics import (
    coverage,
    diversity_at_k,
    hit_rate_at_k,
    ndcg_at_k,
    normalized_recall_at_k,
    novelty_at_k,
    precision_at_k,
)


def normalized_composite_score(
    *metrics_arrays: np.ndarray,
    weights: list[float] | None = None,
) -> np.ndarray:
    """
    Composite score for hyperparameter selection: min-max normalize each
    metric array to [0, 1] and combine with the given weights.

    If weights is None, uses equal weights.  Edge cases (single value, all
    equal values) return 0.5 per metric (midpoint of the normalised range).
    """
    arrays = [np.asarray(a, dtype=np.float64) for a in metrics_arrays]
    n = len(arrays)
    if weights is None:
        weights = [1.0 / n] * n
    assert len(weights) == n, "weights length must match number of metric arrays"

    def _minmax(arr: np.ndarray) -> np.ndarray:
        lo, hi = float(arr.min()), float(arr.max())
        if hi - lo < 1e-12:
            return np.full_like(arr, 0.5)
        return (arr - lo) / (hi - lo)

    return sum(w * _minmax(a) for w, a in zip(weights, arrays))


_ML_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = _ML_DIR.parent / "backend" / "app" / "artifacts" / "cosine_sim.npy"
MOVIES_PATH = _ML_DIR / "data" / "processed" / "movies_final.csv"
RATINGS_ML_PATH = _ML_DIR / "data" / "processed" / "ratings_final.parquet"
RATINGS_SURVEY_PATH = _ML_DIR / "data" / "DataNewUsers" / "ratings.csv"
SAVED_MODELS_DIR = _ML_DIR / "models" / "saved"
RESULTS_DIR = _ML_DIR / "results"


# ── Catalog helpers ─────────────────────────────────────────────────────────


def load_cosine_sim() -> np.ndarray:
    return np.load(ARTIFACT_PATH)


def load_popularity() -> np.ndarray:
    """Min-max normalised popularity (TMDb weighted score), indexed by movie_id."""
    movies = pd.read_csv(MOVIES_PATH, usecols=["movie_id", "score"])
    movies = movies.sort_values("movie_id")
    scores = movies["score"].to_numpy(dtype=np.float64)
    lo, hi = float(scores.min()), float(scores.max())
    return (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)


def catalog_size() -> int:
    """Return catalog size from the movies CSV — avoids loading 98 MB cosine_sim.npy."""
    movies = pd.read_csv(MOVIES_PATH, usecols=["movie_id"])
    return int(movies["movie_id"].max()) + 1


def load_movies_df() -> pd.DataFrame:
    return pd.read_csv(MOVIES_PATH)


# ── MovieLens: full-catalog evaluation ──────────────────────────────────────


def evaluate_movielens(
    model: BaseRecommender,
    train: pd.DataFrame,
    test: pd.DataFrame,
    k: int,
    cosine_sim: np.ndarray,
    popularity: np.ndarray,
    n_items: int,
) -> dict[str, float]:
    """
    Full-catalog evaluation for MovieLens.

    Fits the model on train, generates a real top-K recommendation list
    from the full catalog for each test user, and computes:

      - Precision@K                                      (accuracy)
      - Normalized Recall@K = hits / min(K, |relevant|)  (coverage, fair)
      - NDCG@K                                           (ranking quality)
      - Diversity@K                                      (intra-list dissimilarity)
      - Novelty@K                                        (1 − popularity)
      - Coverage                                         (catalog usage)
    """
    model.fit(train)

    relevant_per_user: dict[int, set[int]] = (
        test.groupby("user_id")["movie_idx"].apply(set).to_dict()
    )

    prec, rec, ndcg, div, nov = [], [], [], [], []
    all_recs: list[list[int]] = []
    skipped = 0

    for user_id, relevant in relevant_per_user.items():
        recs = model.recommend(int(user_id), n=k)
        if not recs:
            skipped += 1
            continue
        all_recs.append(recs)
        prec.append(precision_at_k(recs, relevant, k))
        rec.append(normalized_recall_at_k(recs, relevant, k))
        ndcg.append(ndcg_at_k(recs, relevant, k))
        div.append(diversity_at_k(recs, cosine_sim, k))
        nov.append(novelty_at_k(recs, popularity, k))

    return {
        "precision": float(np.mean(prec)) if prec else 0.0,
        "recall": float(np.mean(rec)) if rec else 0.0,
        "ndcg": float(np.mean(ndcg)) if ndcg else 0.0,
        "diversity": float(np.mean(div)) if div else 0.0,
        "novelty": float(np.mean(nov)) if nov else 0.0,
        "coverage": coverage(all_recs, n_items),
        "n_evaluated": len(all_recs),
        "n_skipped": skipped,
    }


# ── Survey: sampled LOO evaluation (1 random positive per user) ─────────────


def _padded_scores(model: BaseRecommender, user_id: int, n_items: int):
    """Get the full per-item score vector for a user, padded with -inf."""
    scores = model.score_all(user_id)
    if scores is None:
        return None
    if scores.shape[0] >= n_items:
        return scores[:n_items]
    out = np.full(n_items, -np.inf, dtype=np.float32)
    out[: scores.shape[0]] = scores
    return out


def evaluate_survey(
    model_factory: Callable[[], BaseRecommender],
    folds: list,
    k: int,
    n_items: int,
) -> dict[str, float]:
    """
    Sampled leave-one-out evaluation for Survey (HR@K, NDCG@K).

    One fold per user (the survey_split_sampled output).  For each fold,
    the model is refit on the fold's train set, and the held-out positive
    is ranked against 99 sampled negatives.
    """
    hr_list, ndcg_list = [], []
    skipped = 0

    for train, test, candidates in folds:
        model = model_factory()
        model.fit(train)
        uid = int(test["user_id"].iloc[0])
        positive = int(test["movie_idx"].iloc[0])
        relevant = {positive}

        scores = _padded_scores(model, uid, n_items)
        if scores is None:
            skipped += 1
            continue

        cand_scores = scores[candidates]
        ranked = candidates[np.argsort(-cand_scores)].tolist()
        hr_list.append(hit_rate_at_k(ranked, relevant, k))
        ndcg_list.append(ndcg_at_k(ranked, relevant, k))

    return {
        "hr": float(np.mean(hr_list)) if hr_list else 0.0,
        "ndcg": float(np.mean(ndcg_list)) if ndcg_list else 0.0,
        "n_evaluated": len(hr_list),
        "n_skipped": skipped,
    }


# ── Metrics display ─────────────────────────────────────────────────────────


_MOVIELENS_METRIC_KEYS = ["precision", "recall", "ndcg", "diversity", "novelty", "coverage"]
_SURVEY_METRIC_KEYS = ["hr", "ndcg"]
_BOOK_KEYS = ["n_evaluated", "n_skipped"]


def print_metrics(results: dict, decimals: int = 3) -> None:
    """
    Pretty-print a results dict.  Detects dataset by which metric keys are
    present: ``precision`` → MovieLens, ``hr`` → Survey.
    """
    from tabulate import tabulate

    if "precision" in results:
        metric_keys = _MOVIELENS_METRIC_KEYS
    elif "hr" in results:
        metric_keys = _SURVEY_METRIC_KEYS
    else:
        metric_keys = list(results.keys())

    rows = []
    for k in metric_keys:
        if k in results:
            rows.append([k, f"{results[k]:.{decimals}f}"])
    for k in _BOOK_KEYS:
        if k in results:
            rows.append([k, f"{int(results[k]):,}"])

    print(tabulate(rows, headers=["Métrica", "Valor"], tablefmt="fancy_grid"))


# ── Plotting ────────────────────────────────────────────────────────────────


def _bar_chart(ax, labels: list[str], values: list[float], title: str, color: str = "#4C72B0") -> None:
    import matplotlib.pyplot as plt  # noqa: F401

    x = np.arange(len(labels))
    ax.bar(x, values, 0.55, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ymax = max(values, default=0) * 1.25 + 0.01
    ax.set_ylim(0, ymax)
    ax.set_title(title)
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)


def plot_movielens_metrics(results: dict, title_prefix: str = "") -> None:
    """Two-panel plot for MovieLens: ranking (3 bars) + beyond-accuracy (3 bars)."""
    import matplotlib.pyplot as plt

    rank_labels = ["Precision@K", "Recall@K", "NDCG@K"]
    rank_values = [results["precision"], results["recall"], results["ndcg"]]
    beyond_labels = ["Diversity@K", "Novelty@K", "Coverage"]
    beyond_values = [results["diversity"], results["novelty"], results["coverage"]]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    _bar_chart(axes[0], rank_labels, rank_values, f"{title_prefix}MovieLens · Ranking".strip())
    _bar_chart(axes[1], beyond_labels, beyond_values, f"{title_prefix}MovieLens · Beyond-accuracy".strip(), color="#DD8452")
    plt.tight_layout()
    plt.show()


def plot_survey_metrics(results: dict, title_prefix: str = "") -> None:
    """Single-panel plot for Survey: HR@K and NDCG@K."""
    import matplotlib.pyplot as plt

    labels = ["HR@K", "NDCG@K"]
    values = [results["hr"], results["ndcg"]]

    fig, ax = plt.subplots(1, 1, figsize=(6, 4.2))
    _bar_chart(ax, labels, values, f"{title_prefix}Survey · Sampled (1+99)".strip(), color="#55A868")
    plt.tight_layout()
    plt.show()


def plot_dataset_metrics(
    movielens: dict | None = None,
    survey: dict | None = None,
    title_prefix: str = "",
) -> None:
    """Render separate panels per dataset.  Pass either or both results dicts."""
    if movielens is not None:
        plot_movielens_metrics(movielens, title_prefix=title_prefix)
    if survey is not None:
        plot_survey_metrics(survey, title_prefix=title_prefix)


# ── User examples ───────────────────────────────────────────────────────────


def _movie_lookup(movies_df: pd.DataFrame) -> dict[int, tuple[str, str]]:
    """movie_id → (title, year_string). Year is extracted from release_date."""
    df = movies_df.copy()

    if "release_date" in df.columns:
        years = pd.to_datetime(df["release_date"], errors="coerce").dt.year
        df["year"] = years.fillna(0).astype(int).astype(str).replace("0", "—")
    else:
        df["year"] = "—"

    return {
        int(row.movie_id): (str(row.title), str(row.year))
        for row in df[["movie_id", "title", "year"]].itertuples(index=False)
    }


def show_user_examples(
    model: BaseRecommender,
    train: pd.DataFrame,
    movies_df: pd.DataFrame,
    n_users: int = 3,
    k: int = 10,
    seed: int = 42,
    min_ratings: int = 5,
    score_label: str = "Score",
    score_kind: str = "raw",
    show_filtered: bool = False,
    popularity_ranking: list[int] | None = None,
) -> None:
    """
    Render recommendation examples for ``n_users`` random users from train.

    For each user prints a markdown header and two tabulate tables:
      1. Top-5 favourite movies of the user (in train)
      2. Top-K recommendations from the model

    See original notebook documentation for all kwargs.
    """
    from IPython.display import Markdown, display
    from tabulate import tabulate

    rng = np.random.default_rng(seed)
    counts = train.groupby("user_id").size()
    eligible = counts[counts >= min_ratings].index.tolist()
    if len(eligible) == 0:
        print("No eligible users.")
        return
    picks = rng.choice(eligible, size=min(n_users, len(eligible)), replace=False)

    lookup = _movie_lookup(movies_df)
    tmdb_scores = None
    if score_kind == "tmdb":
        tmdb_scores = (
            movies_df.set_index("movie_id")["score"].astype(float).to_dict()
        )

    def _fmt_title(idx: int) -> tuple[str, str]:
        return lookup.get(int(idx), (f"<idx {idx}>", "—"))

    for user_id in picks:
        user_id = int(user_id)
        user_rows = train[train["user_id"] == user_id]

        top5 = (
            user_rows.sort_values("rating", ascending=False)
            .head(5)[["movie_idx", "rating"]]
            .values.tolist()
        )
        fav_rows = []
        for rank, (idx, rating) in enumerate(top5, start=1):
            title, year = _fmt_title(int(idx))
            fav_rows.append([rank, title, year, f"{float(rating):.1f}"])

        recs = model.recommend(user_id, n=k)
        scores_vec = None
        if score_kind in {"raw", "cosine", "predicted"}:
            scores_vec = model.score_all(user_id)

        rec_rows = []
        for rank, idx in enumerate(recs, start=1):
            title, year = _fmt_title(int(idx))
            if score_kind == "tmdb" and tmdb_scores is not None:
                s = tmdb_scores.get(int(idx), float("nan"))
                score_str = f"{s:.2f}"
            elif scores_vec is not None and 0 <= int(idx) < len(scores_vec):
                s = float(scores_vec[int(idx)])
                score_str = f"{s:.3f}" if score_kind == "cosine" else f"{s:.2f}"
            else:
                score_str = "—"
            rec_rows.append([rank, title, year, score_str])

        display(Markdown(f"## Usuario {user_id}"))
        display(Markdown("**Top-5 películas favoritas (en train):**"))
        print(tabulate(fav_rows, headers=["#", "Título", "Año", "Rating"], tablefmt="fancy_grid"))
        display(Markdown(f"**Top-{k} recomendaciones del modelo:**"))
        print(tabulate(rec_rows, headers=["#", "Título", "Año", score_label], tablefmt="fancy_grid"))

        if show_filtered and popularity_ranking is not None:
            seen = set(user_rows["movie_idx"].astype(int).tolist())
            filtered = [idx for idx in popularity_ranking if idx in seen][:k]
            if filtered:
                filt_rows = []
                for idx in filtered:
                    title, year = _fmt_title(int(idx))
                    filt_rows.append([title, year])
                display(Markdown("**Películas del top global omitidas porque el usuario ya las vio:**"))
                print(tabulate(filt_rows, headers=["Título", "Año"], tablefmt="fancy_grid"))
            else:
                display(Markdown("_El usuario no había visto ninguna del top global, así que la lista mostrada coincide con el ranking._"))
