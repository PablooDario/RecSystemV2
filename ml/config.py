"""
ml - benchmark configuration and path constants.
"""

import sys
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _ML_DIR.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

DATA_DIR = _ML_DIR / "data" / "benchmark"
RATINGS_PATH = DATA_DIR / "ratings_benchmark.parquet"
MOVIES_PATH = DATA_DIR / "movies_benchmark.csv"
COSINE_SIM_PATH = DATA_DIR / "cosine_sim_benchmark.npy"
MODELS_DIR = _ML_DIR / "models" / "saved"

ML_RAW_RATINGS = _ML_DIR / "data" / "raw" / "ratings.parquet"
ML_MOVIES = _ML_DIR / "data" / "processed" / "movies_final.csv"

from ml.evaluation.metrics import precision_at_k, normalized_recall_at_k, ndcg_at_k
from ml.evaluation.splits import movielens_split

import numpy as np
import pandas as pd


def load_cosine_sim():
    return np.load(COSINE_SIM_PATH)


def catalog_size():
    movies = pd.read_csv(MOVIES_PATH, usecols=["movie_id"])
    return int(movies["movie_id"].max()) + 1


def load_popularity():
    movies = pd.read_csv(MOVIES_PATH, usecols=["movie_id", "score"])
    movies = movies.sort_values("movie_id")
    scores = movies["score"].to_numpy(dtype=np.float64)
    lo, hi = float(scores.min()), float(scores.max())
    return (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)


# ── Nave et al. genre × Big Five loadings (same as notebook 6) ────────
NAVE_GENRE_PERSONALITY = {
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
TRAIT_COLS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def _softmax_rows(df: pd.DataFrame) -> pd.DataFrame:
    exp_df = np.exp(df.sub(df.max(axis=1), axis=0))
    return exp_df.div(exp_df.sum(axis=1), axis=0)


def derive_personalities(ratings: pd.DataFrame, movies: pd.DataFrame) -> pd.DataFrame:
    """
    Derive Big Five personality traits per user from their ratings
    using Nave et al. (2020) genre loadings.
    """
    import ast

    supported = set(NAVE_GENRE_PERSONALITY.keys())
    m = movies[["movie_id", "genres"]].copy()
    m["genres"] = m["genres"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )
    m["genres"] = m["genres"].apply(
        lambda g: [x for x in g if x in supported] if isinstance(g, list) else []
    )
    m = m[m["genres"].map(len) > 0]

    df = ratings.merge(m, on="movie_id")[["user_id", "genres", "rating"]]
    df = df.explode("genres")

    df = df.groupby(["user_id", "genres"]).aggregate("mean").reset_index()
    ug = df.pivot(index="user_id", columns="genres", values="rating").fillna(0.0)

    for g in supported:
        if g not in ug.columns:
            ug[g] = 0.0
    ug = ug[list(NAVE_GENRE_PERSONALITY.keys())]

    ug_softmax = _softmax_rows(ug)
    personality_matrix = pd.DataFrame.from_dict(
        NAVE_GENRE_PERSONALITY, orient="index",
        columns=["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"],
    )
    res = ug_softmax @ personality_matrix

    z = (res - res.mean()) / res.std()
    scaled = (3.0 + 0.7 * z).clip(1.0, 5.0)
    scaled.columns = TRAIT_COLS

    out = scaled.reset_index()
    out["user_id"] = out["user_id"].astype(int)
    return out
