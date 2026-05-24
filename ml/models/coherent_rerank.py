"""
Coherent Genre-Aware Re-ranking for personality-based recommendations.

Rationale
---------
MMR diversifies *within* a list using item embeddings, which inherits the
popularity bias of LightGCN. The result is incoherent lists (e.g., Gladiator
next to Toy Story) because MMR rewards dissimilarity.

This module implements an alternative re-ranker that uses **genre affinity**
derived from the Nave matrix to:

1. Compute each user's preferred genres from their Big Five traits (independent
   of the rating-based item embeddings, so it does not inherit popularity bias).
2. Select recommendations by quota: most slots come from the user's *primary*
   genre, plus a small number of wildcards from secondary genres.
3. Within each genre, select by raw score from the model.

This addresses three failure modes of the previous setup:
- Intra-list incoherence (mixing unrelated genres in the same top-K).
- Inter-user homogeneity (different users get same recommendations).
- Catalog coverage (different users activate different genre buckets, so
  the union of recommended items spans more of the catalog).
"""

from __future__ import annotations

import ast
from typing import Iterable

import numpy as np
import pandas as pd

# Big Five trait values per genre, from Nave et al. (2017).
# Columns: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
NAVE_MATRIX = {
    "Action":          [3.87, 3.45, 3.57, 3.58, 2.72],
    "Adventure":       [3.91, 3.56, 3.54, 3.68, 2.61],
    "Animation":       [4.04, 3.22, 3.26, 3.35, 3.02],
    "Comedy":          [3.88, 3.44, 3.58, 3.60, 2.75],
    "Drama":           [3.99, 3.43, 3.66, 3.60, 2.86],
    "Horror":          [3.90, 3.38, 3.52, 3.47, 2.91],
    "Romance":         [3.88, 3.44, 3.62, 3.62, 2.71],
    "Science Fiction": [3.99, 3.55, 3.53, 3.57, 2.73],
    "War":             [3.82, 3.51, 3.49, 3.50, 2.71],
}

# Mapping from catalog genres not in Nave to the nearest Nave genre.
# Justification per pair lives in the comments of the design doc.
GENRE_MAPPING_TO_NAVE = {
    "Thriller":    "Action",
    "Crime":       "Action",
    "Family":      "Animation",
    "Fantasy":     "Adventure",
    "Mystery":     "Drama",
    "History":     "Drama",
    "Documentary": "Drama",
    "Music":       "Drama",
    "TV Movie":    "Drama",
    "Western":     "Action",
}


def _safe_parse_genres(s) -> list[str]:
    if not isinstance(s, str):
        return []
    try:
        return list(ast.literal_eval(s))
    except (ValueError, SyntaxError):
        return []


def build_extended_nave() -> dict[str, list[float]]:
    """
    Return the Nave matrix extended to all 19 catalog genres.

    For genres not present in Nave (e.g., Thriller, Crime, Family) we
    use the values of the closest Nave genre per ``GENRE_MAPPING_TO_NAVE``.
    """
    extended = dict(NAVE_MATRIX)
    for catalog_genre, nave_genre in GENRE_MAPPING_TO_NAVE.items():
        extended[catalog_genre] = NAVE_MATRIX[nave_genre]
    return extended


def build_item_genres(movies_df: pd.DataFrame, n_items: int) -> tuple[np.ndarray, list[str]]:
    """
    Build a binary item × genre matrix.

    Returns
    -------
    genres_matrix : (n_items, n_genres) float32 array
        1 if item belongs to genre, 0 otherwise.
    genre_names : list of genre names in column order.
    """
    extended_nave = build_extended_nave()
    genre_names = sorted(extended_nave.keys())
    g_idx = {g: i for i, g in enumerate(genre_names)}

    matrix = np.zeros((n_items, len(genre_names)), dtype=np.float32)
    for row in movies_df.itertuples(index=False):
        idx = int(row.movie_id)
        if idx >= n_items:
            continue
        for g in _safe_parse_genres(row.genres):
            if g in g_idx:
                matrix[idx, g_idx[g]] = 1.0
    return matrix, genre_names


def compute_user_genre_affinity(
    traits: np.ndarray,
    genre_names: list[str],
) -> np.ndarray:
    """
    Compute genre affinity per user from Big Five traits using Nave.

    Parameters
    ----------
    traits : (n_users, 5) array of un-normalized Big Five traits in 1-5 scale.
    genre_names : list of genre names matching ``build_item_genres`` columns.

    Returns
    -------
    affinity : (n_users, n_genres) array. Higher = user more likely to enjoy genre.
        Computed as cosine similarity between user traits and Nave row, then
        z-scored per user (so the *relative* preference between genres is
        emphasized over absolute level).
    """
    extended = build_extended_nave()
    nave = np.array([extended[g] for g in genre_names], dtype=np.float32)  # (G, 5)

    # Cosine similarity user vs each Nave row
    u_norm = traits / np.linalg.norm(traits, axis=1, keepdims=True).clip(1e-8)
    n_norm = nave / np.linalg.norm(nave, axis=1, keepdims=True).clip(1e-8)
    cos = u_norm @ n_norm.T  # (U, G)

    # Per-user z-score so genre *relative* preferences dominate
    mean = cos.mean(axis=1, keepdims=True)
    std = cos.std(axis=1, keepdims=True).clip(1e-8)
    return (cos - mean) / std


def coherent_rerank(
    scores: np.ndarray,
    item_genres: np.ndarray,
    user_genre_affinity: np.ndarray,
    n: int = 10,
    primary_slots: int = 7,
    wildcard_slots: int = 2,
    free_slots: int = 1,
    pool_size: int = 200,
    primary_top_k: int = 1,
    wildcard_top_k: int = 3,
    excluded: set[int] | None = None,
) -> list[int]:
    """
    Re-rank items so the output list is coherent with the user's top genres.

    Strategy
    --------
    1. Take the top ``pool_size`` items by raw score.
    2. Select top ``primary_top_k`` genres by user affinity → "primary" pool.
    3. Select next ``wildcard_top_k`` genres → "wildcard" pool.
    4. Fill ``primary_slots`` slots from items whose genres include any primary
       genre, ordered by score (coherence).
    5. Fill ``wildcard_slots`` slots from items whose genres include any
       wildcard genre, ordered by score (controlled variety).
    6. Fill ``free_slots`` from the highest-scoring items remaining,
       regardless of genre — preserves the model's strong individual signals
       even when they fall outside the user's "statistical" genre profile.
    7. Backfill any remaining slots with the next best scores from the pool.

    Parameters
    ----------
    scores : (n_items,) float array of model scores. -inf for excluded items.
    item_genres : (n_items, n_genres) binary matrix.
    user_genre_affinity : (n_genres,) z-scored affinity vector for this user.
    n : list size.
    primary_slots, wildcard_slots, free_slots : slot quotas.
    pool_size : how many top-scored items to consider.
    primary_top_k : number of top-affinity genres treated as primary.
    wildcard_top_k : number of next-affinity genres treated as wildcards.
    excluded : items to exclude from output (already-seen, etc.).
    """
    excluded = excluded or set()

    # Top genres by affinity for this user
    genre_order = np.argsort(-user_genre_affinity)
    primary_genres = set(genre_order[:primary_top_k].tolist())
    wildcard_genres = set(genre_order[primary_top_k: primary_top_k + wildcard_top_k].tolist())

    # Pool: top-scored items
    pool = np.argsort(-scores)[:pool_size]
    pool = [int(i) for i in pool if int(i) not in excluded and not np.isneginf(scores[int(i)])]

    # Helper: does item i belong to any genre in `gset`?
    def _in_genres(i: int, gset: set[int]) -> bool:
        if not gset:
            return False
        item_g = item_genres[i]
        return any(item_g[g] > 0 for g in gset)

    primary_candidates = [i for i in pool if _in_genres(i, primary_genres)]
    wildcard_candidates = [i for i in pool
                           if _in_genres(i, wildcard_genres) and not _in_genres(i, primary_genres)]

    selected: list[int] = []
    seen: set[int] = set()

    # Slots from primary genre
    for i in primary_candidates:
        if len(selected) >= primary_slots:
            break
        if i in seen:
            continue
        selected.append(i)
        seen.add(i)

    # Wildcard slots
    wildcard_taken = 0
    for i in wildcard_candidates:
        if wildcard_taken >= wildcard_slots:
            break
        if i in seen:
            continue
        selected.append(i)
        seen.add(i)
        wildcard_taken += 1

    # Free slots: top model scores regardless of genre — preserves the model's
    # learned individual preferences when they don't fit the statistical genre profile
    free_taken = 0
    for i in pool:
        if free_taken >= free_slots:
            break
        if i in seen:
            continue
        selected.append(i)
        seen.add(i)
        free_taken += 1

    # Backfill: if we couldn't fill the list (rare), pad with top scores
    if len(selected) < n:
        for i in pool:
            if len(selected) >= n:
                break
            if i not in seen:
                selected.append(i)
                seen.add(i)

    return selected[:n]
