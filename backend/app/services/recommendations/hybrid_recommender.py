import numpy as np

from app.services.recommendations.model_loader import (
    _get_cosine_sim,
    _get_hybrid_weights,
    _get_item_embeddings,
    _get_popularity,
    _get_pmlp_model,
    get_n_items,
)

POSITIVE_THRESHOLD_CB = 3.5
POSITIVE_THRESHOLD_CF = 4.0
TOP_SEED_MOVIES = 10
POPULARITY_ALPHA = 0.10


def _content_scores(user_ratings: dict[int, float]) -> np.ndarray:
    cosine_sim = _get_cosine_sim()
    pop = _get_popularity()
    n_items = get_n_items()

    seeds = sorted(
        [(idx, r) for idx, r in user_ratings.items() if r > POSITIVE_THRESHOLD_CB],
        key=lambda x: x[1],
        reverse=True,
    )[:TOP_SEED_MOVIES]

    if not seeds:
        return np.full(n_items, -np.inf, dtype=np.float32)

    indices = [idx for idx, _ in seeds]
    ratings = np.array([r for _, r in seeds])
    weights = ratings - POSITIVE_THRESHOLD_CB
    weights = weights / weights.max()
    seed_sims = cosine_sim[indices]
    content = np.max(seed_sims * weights[:, np.newaxis], axis=0)
    return (1 - POPULARITY_ALPHA) * content + POPULARITY_ALPHA * pop


def _cf_scores(user_ratings: dict[int, float]) -> np.ndarray:
    Ei = _get_item_embeddings()
    n_items = get_n_items()

    positive_indices = [
        idx for idx, r in user_ratings.items()
        if r >= POSITIVE_THRESHOLD_CF and 0 <= idx < Ei.shape[0]
    ]

    if not positive_indices:
        return np.full(n_items, -np.inf, dtype=np.float32)

    user_emb = Ei[positive_indices].mean(axis=0)
    norm = np.linalg.norm(user_emb)
    if norm > 1e-8:
        user_emb = user_emb / norm
    return (user_emb @ Ei.T).astype(np.float32)


def _personality_scores(traits: dict[str, float]) -> np.ndarray:
    model = _get_pmlp_model()

    trait_vec = np.array([
        traits["openness"],
        traits["conscientiousness"],
        traits["extraversion"],
        traits["agreeableness"],
        traits["neuroticism"],
    ], dtype=np.float32)

    normed = (trait_vec - model._trait_mean) / model._trait_std
    u, _ = model._mlp.forward(normed[None, :], dropout=0.0)
    scores = (u @ model._Ei.T).ravel() + model._item_bias

    if model._popularity_penalty > 0.0 and model._item_popularity is not None:
        std = scores.std()
        if std > 1e-8:
            scores = scores - model._popularity_penalty * std * model._item_popularity

    return scores


def _popularity_scores() -> np.ndarray:
    return _get_popularity()


def _normalize(arr: np.ndarray) -> np.ndarray:
    valid = arr[arr > -np.inf]
    if len(valid) == 0:
        return np.zeros_like(arr)
    lo, hi = float(valid.min()), float(valid.max())
    if hi - lo < 1e-12:
        return np.where(arr > -np.inf, 0.5, -np.inf)
    out = (arr - lo) / (hi - lo)
    out[arr == -np.inf] = -np.inf
    return out


def hybrid_recommend(
    user_ratings: dict[int, float],
    traits: dict[str, float],
    exclude: set[int],
    top_k: int = 10,
) -> list[int]:
    meta = _get_hybrid_weights()
    weights = meta.get("weights", {})
    w_pop = weights.get("Popularity", 0.0)
    w_cb = weights.get("Content-Based", 0.15)
    w_cf = weights.get("LightGCN", 0.7)
    w_pers = weights.get("PMLP", 0.15)

    n_items = get_n_items()

    pop_s = _normalize(_popularity_scores())
    cb_s = _normalize(_content_scores(user_ratings))
    cf_s = _normalize(_cf_scores(user_ratings))
    pers_s = _normalize(_personality_scores(traits))

    combined = w_pop * pop_s + w_cb * cb_s + w_cf * cf_s + w_pers * pers_s

    for idx in exclude:
        if 0 <= idx < n_items:
            combined[idx] = -np.inf

    return np.argsort(-combined)[:top_k].tolist()
