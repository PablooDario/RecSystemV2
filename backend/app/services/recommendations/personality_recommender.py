import numpy as np

from app.services.recommendations.model_loader import (
    _get_cosine_sim,
    _get_pmlp_model,
    get_n_items,
)

MMR_LAMBDA = 0.5
MMR_POOL = 50


def _mmr_rerank(
    pool: list[int], scores: np.ndarray, cosine_sim: np.ndarray, n: int
) -> list[int]:
    selected: list[int] = []
    remaining = list(pool)
    while remaining and len(selected) < n:
        if not selected:
            best = max(remaining, key=lambda i: scores[i])
        else:
            best = max(
                remaining,
                key=lambda i: (
                    MMR_LAMBDA * scores[i]
                    - (1 - MMR_LAMBDA) * float(np.max(cosine_sim[i, selected]))
                ),
            )
        selected.append(best)
        remaining.remove(best)
    return selected


def personality_recommend(
    traits: dict[str, float], exclude: set[int], top_k: int = 10
) -> list[int]:
    model = _get_pmlp_model()
    cosine_sim = _get_cosine_sim()
    n_items = get_n_items()

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

    for idx in exclude:
        if 0 <= idx < n_items:
            scores[idx] = -np.inf

    pool = np.argsort(-scores)[:max(top_k, MMR_POOL)].tolist()
    return _mmr_rerank(pool, scores, cosine_sim, top_k)
