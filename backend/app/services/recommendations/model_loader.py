import sys
from pathlib import Path

import numpy as np
import pandas as pd

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
_ML_DIR = _BASE_DIR / "ml"
_MODELS_DIR = _ML_DIR / "models" / "saved"
_DATA_DIR = _ML_DIR / "data" / "benchmark"

_COSINE_SIM_PATH = _DATA_DIR / "cosine_sim_benchmark.npy"
_MOVIES_CSV_PATH = _DATA_DIR / "movies_benchmark.csv"
_LIGHTGCN_PATH = _MODELS_DIR / "lightgcn_items.npy"
_PMLP_PATH = _MODELS_DIR / "pmlp_b.pkl"
_HYBRID_META_PATH = _MODELS_DIR / "hybrid_meta.json"

# Lazy-loaded singletons
_cosine_sim: np.ndarray | None = None
_popularity: np.ndarray | None = None
_item_embeddings: np.ndarray | None = None
_pmlp_model = None
_hybrid_weights: dict | None = None


def _get_cosine_sim() -> np.ndarray:
    global _cosine_sim
    if _cosine_sim is None:
        if not _COSINE_SIM_PATH.exists():
            raise FileNotFoundError(f"Cosine similarity matrix not found: {_COSINE_SIM_PATH}")
        _cosine_sim = np.load(_COSINE_SIM_PATH)
    return _cosine_sim


def _get_popularity() -> np.ndarray:
    global _popularity
    if _popularity is None:
        movies = pd.read_csv(_MOVIES_CSV_PATH, usecols=["movie_id", "score"])
        movies = movies.sort_values("movie_id")
        scores = movies["score"].to_numpy(dtype=np.float64)
        lo, hi = float(scores.min()), float(scores.max())
        _popularity = (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)
    return _popularity


def _get_item_embeddings() -> np.ndarray:
    global _item_embeddings
    if _item_embeddings is None:
        if not _LIGHTGCN_PATH.exists():
            raise FileNotFoundError(f"LightGCN embeddings not found: {_LIGHTGCN_PATH}")
        _item_embeddings = np.load(_LIGHTGCN_PATH).astype(np.float32)
    return _item_embeddings


def _get_pmlp_model():
    """
    Load PMLP_B (personality recommender trained on Benchmark with coherent re-rank).
    Restores cosine_sim reference (stripped at save time) so the model is
    fully functional after unpickling.
    """
    global _pmlp_model
    if _pmlp_model is None:
        print(f"[LOADER] _get_pmlp_model: first call, loading from disk", flush=True)
        print(f"[LOADER]   _BASE_DIR={_BASE_DIR}", flush=True)
        print(f"[LOADER]   _PMLP_PATH={_PMLP_PATH}", flush=True)
        print(f"[LOADER]   _PMLP_PATH.exists()={_PMLP_PATH.exists()}", flush=True)
        if not _PMLP_PATH.exists():
            raise FileNotFoundError(f"Personality model not found: {_PMLP_PATH}")
        if str(_BASE_DIR) not in sys.path:
            print(f"[LOADER]   adding {_BASE_DIR} to sys.path", flush=True)
            sys.path.insert(0, str(_BASE_DIR))

        # Inspect what 'ml.models.personality' resolves to BEFORE unpickling
        try:
            import ml.models.personality as pers_mod
            print(f"[LOADER]   ml.models.personality module file: {pers_mod.__file__}", flush=True)
            cls = pers_mod.PersonalityMLPRecommender
            print(f"[LOADER]   class loaded from: {cls.__module__}", flush=True)
            # Check what attributes the class declares
            test_attrs = [a for a in dir(cls) if not a.startswith('__')]
            print(f"[LOADER]   class methods/attrs (first 10): {test_attrs[:10]}", flush=True)
        except Exception as e:
            print(f"[LOADER] ⚠️ failed to inspect ml.models.personality: {e}", flush=True)

        import pickle
        with open(_PMLP_PATH, "rb") as f:
            _pmlp_model = pickle.load(f)

        print(f"[LOADER]   pickle loaded. type={type(_pmlp_model).__name__}", flush=True)
        print(f"[LOADER]   instance __class__.__module__: {_pmlp_model.__class__.__module__}", flush=True)
        print(f"[LOADER]   has _head: {hasattr(_pmlp_model, '_head')}", flush=True)
        print(f"[LOADER]   has _mlp: {hasattr(_pmlp_model, '_mlp')}", flush=True)
        print(f"[LOADER]   instance __dict__ keys (sample): {list(_pmlp_model.__dict__.keys())[:15]}", flush=True)

        # Restore references stripped before serialization
        _pmlp_model._cosine_sim = _get_cosine_sim()
        print(f"[LOADER]   _cosine_sim restored", flush=True)
    return _pmlp_model


def _get_hybrid_weights() -> dict:
    global _hybrid_weights
    if _hybrid_weights is None:
        if not _HYBRID_META_PATH.exists():
            raise FileNotFoundError(f"Hybrid meta not found: {_HYBRID_META_PATH}")
        import json
        with open(_HYBRID_META_PATH) as f:
            _hybrid_weights = json.load(f)
    return _hybrid_weights


def get_n_items() -> int:
    return _get_cosine_sim().shape[0]


def load_all_models() -> None:
    _get_cosine_sim()
    _get_popularity()
    _get_item_embeddings()
    _get_pmlp_model()
    _get_hybrid_weights()