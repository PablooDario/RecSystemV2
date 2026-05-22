"""
Ranking metrics for Top-N recommendation evaluation.

All functions take:
- recommended: ordered list of movie matrix indices (best first)
- relevant:    set of ground-truth movie matrix indices
- k:           cutoff
"""

import numpy as np


def precision_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Fraction of the top-k recommendations that are relevant.

    Divides by ``len(rec_k)`` rather than ``k`` so that a model returning
    fewer than ``k`` items is not unfairly penalised.
    """
    rec_k = recommended[:k]
    if not rec_k:
        return 0.0
    hits = sum(1 for r in rec_k if r in relevant)
    return hits / len(rec_k)


def hit_rate_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Binary hit: 1.0 if any relevant item appears in the top-k, else 0.0.

    Standard ranking metric for sampled evaluation (1 positive + N negatives),
    used in NeuMF, BPR and LightGCN literature.
    """
    return 1.0 if any(r in relevant for r in recommended[:k]) else 0.0


def recall_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Fraction of all relevant items that appear in the top-k."""
    if not relevant:
        return 0.0
    hits = sum(1 for r in recommended[:k] if r in relevant)
    return hits / len(relevant)


def normalized_recall_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """
    Normalized recall: hits / min(k, |relevant|).

    Fixes the structural ceiling of plain recall when a user has more
    relevant items than the top-k can possibly fit.  Max value is always
    1.0, making comparisons across users fair regardless of how many
    positives each user has.
    """
    if not relevant:
        return 0.0
    hits = sum(1 for r in recommended[:k] if r in relevant)
    denom = min(k, len(relevant))
    return hits / denom if denom > 0 else 0.0


def ndcg_at_k(recommended: list[int], relevant: set[int], k: int) -> float:
    """Normalized Discounted Cumulative Gain at k (binary relevance)."""
    dcg = sum(
        1.0 / np.log2(i + 2)
        for i, r in enumerate(recommended[:k])
        if r in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def diversity_at_k(
    recommended: list[int], cosine_sim: np.ndarray, k: int
) -> float:
    """
    Intra-list diversity: mean pairwise dissimilarity (1 - cosine_sim)
    among the top-k recommendations.

    The cosine similarity matrix for this project was verified to be
    strictly non-negative (min ≈ 0.31), so ``1 - sim`` already yields a
    valid dissimilarity in [0, 1]; no extra normalisation is required.
    """
    rec_k = recommended[:k]
    if len(rec_k) < 2:
        return 0.0
    total, pairs = 0.0, 0
    for i in range(len(rec_k)):
        for j in range(i + 1, len(rec_k)):
            total += 1.0 - float(cosine_sim[rec_k[i], rec_k[j]])
            pairs += 1
    return total / pairs if pairs > 0 else 0.0


def novelty_at_k(
    recommended: list[int], popularity: np.ndarray, k: int
) -> float:
    """
    Average novelty of recommended items, normalised to [0, 1].

    popularity[i] is expected to be min-max normalised (0 = least popular,
    1 = most popular).  Novelty for a single item is simply 1 − popularity,
    so recommending obscure items yields values close to 1 and recommending
    blockbusters yields values close to 0.

    The metric is the mean over the top-k list.
    """
    rec_k = recommended[:k]
    if not rec_k:
        return 0.0
    return float(np.mean([1.0 - popularity[idx] for idx in rec_k]))


def coverage(all_recommended: list[list[int]], catalog_size: int) -> float:
    """Fraction of the catalog ever recommended across all users."""
    if catalog_size <= 0:
        return 0.0
    unique = {idx for recs in all_recommended for idx in recs}
    return len(unique) / catalog_size
