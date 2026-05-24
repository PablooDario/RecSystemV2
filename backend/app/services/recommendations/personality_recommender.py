import numpy as np
import pandas as pd

from app.services.recommendations.model_loader import _get_pmlp_model

# Synthetic user_id for stateless inference (the model uses an internal lookup
# keyed by user_id; we inject a single ad-hoc user before recommending).
_INFERENCE_UID = -1

TRAIT_COLS = [
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
]


def personality_recommend(
    traits: dict[str, float], exclude: set[int], top_k: int = 10
) -> list[int]:
    """
    Generate top-K recommendations from Big Five personality traits.

    Parameters
    ----------
    traits : dict with keys 'openness', 'conscientiousness', 'extraversion',
        'agreeableness', 'neuroticism' in 1-5 scale.
    exclude : set of movie indices to exclude (already-seen, etc.).
    top_k : number of recommendations to return.
    """
    model = _get_pmlp_model()

    # Inject the request's traits as a synthetic user, then ask the model
    # to recommend. set_personalities() handles feature mode (raw / quantile)
    # and updates genre affinity for coherent re-rank.
    pers_df = pd.DataFrame([{
        "user_id": _INFERENCE_UID,
        **{c: float(traits[c]) for c in TRAIT_COLS},
    }])
    model.set_personalities(pers_df)

    return model.recommend(_INFERENCE_UID, n=top_k, exclude=exclude)