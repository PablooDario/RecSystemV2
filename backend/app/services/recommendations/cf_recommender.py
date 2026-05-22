import numpy as np

from app.services.recommendations.model_loader import _get_item_embeddings, get_n_items

POSITIVE_THRESHOLD = 4.0


def cf_recommend(
    user_ratings: dict[int, float], exclude: set[int], top_k: int = 10
) -> list[int]:
    Ei = _get_item_embeddings()
    n_items = get_n_items()

    positive_indices = [
        idx for idx, rating in user_ratings.items()
        if rating >= POSITIVE_THRESHOLD and 0 <= idx < Ei.shape[0]
    ]

    if not positive_indices:
        return []

    user_emb = Ei[positive_indices].mean(axis=0)
    norm = np.linalg.norm(user_emb)
    if norm > 1e-8:
        user_emb = user_emb / norm

    scores = (user_emb @ Ei.T).astype(np.float32)

    for idx in exclude:
        if 0 <= idx < n_items:
            scores[idx] = -np.inf

    return np.argsort(-scores)[:top_k].tolist()
