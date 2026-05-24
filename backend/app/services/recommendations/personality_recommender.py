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
    print(f"  [PERS] personality_recommend called, traits={traits}, exclude={len(exclude)}, top_k={top_k}", flush=True)

    model = _get_pmlp_model()
    print(f"  [PERS]   model class: {type(model).__name__}", flush=True)
    print(f"  [PERS]   model module: {type(model).__module__}", flush=True)
    print(f"  [PERS]   has _head: {hasattr(model, '_head')}", flush=True)
    print(f"  [PERS]   has _mlp: {hasattr(model, '_mlp')}", flush=True)
    print(f"  [PERS]   coherent: {getattr(model, '_coherent', 'MISSING')}", flush=True)
    print(f"  [PERS]   feature_mode: {getattr(model, '_feature_mode', 'MISSING')}", flush=True)
    print(f"  [PERS]   model_type: {getattr(model, '_model_type', 'MISSING')}", flush=True)

    # Inject the request's traits as a synthetic user, then ask the model
    # to recommend. set_personalities() handles feature mode (raw / quantile)
    # and updates genre affinity for coherent re-rank.
    pers_df = pd.DataFrame([{
        "user_id": _INFERENCE_UID,
        **{c: float(traits[c]) for c in TRAIT_COLS},
    }])

    print(f"  [PERS]   calling model.set_personalities()...", flush=True)
    try:
        model.set_personalities(pers_df)
        print(f"  [PERS]   set_personalities OK", flush=True)
    except Exception as e:
        print(f"  [PERS]   ❌ set_personalities FAILED: {type(e).__name__}: {e}", flush=True)
        import traceback; traceback.print_exc()
        raise

    print(f"  [PERS]   calling model.recommend()...", flush=True)
    try:
        recs = model.recommend(_INFERENCE_UID, n=top_k, exclude=exclude)
        print(f"  [PERS]   recommend returned {len(recs)} items: {recs[:5]}...", flush=True)
        return recs
    except Exception as e:
        print(f"  [PERS]   ❌ recommend FAILED: {type(e).__name__}: {e}", flush=True)
        import traceback; traceback.print_exc()
        raise