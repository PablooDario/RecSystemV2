import sys
from pathlib import Path

import numpy as np
import pandas as pd

_BASE_DIR = Path(__file__).resolve().parents[4]
_ML_DIR = _BASE_DIR / "ml"
_MODELS_DIR = _ML_DIR / "models" / "saved"
_DATA_DIR = _ML_DIR / "data" / "benchmark"

_COSINE_SIM_PATH = _DATA_DIR / "cosine_sim_benchmark.npy"
_MOVIES_CSV_PATH = _DATA_DIR / "movies_benchmark.csv"
_LIGHTGCN_PATH = _MODELS_DIR / "lightgcn_benchmark.npz"
_PMLP_SV_PATH = _MODELS_DIR / "pmlp_sv.pkl"
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
            raise FileNotFoundError(f"LightGCN model not found: {_LIGHTGCN_PATH}")
        data = np.load(_LIGHTGCN_PATH)
        _item_embeddings = data["Ei_final"].astype(np.float32)
    return _item_embeddings


def _get_pmlp_model():
    global _pmlp_model
    if _pmlp_model is None:
        if not _PMLP_SV_PATH.exists():
            raise FileNotFoundError(f"Personality model not found: {_PMLP_SV_PATH}")
        if str(_BASE_DIR) not in sys.path:
            sys.path.insert(0, str(_BASE_DIR))
        import pickle
        with open(_PMLP_SV_PATH, "rb") as f:
            _pmlp_model = pickle.load(f)
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
