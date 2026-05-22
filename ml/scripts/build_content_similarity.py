"""
Build the content-based cosine similarity matrix for the benchmark catalog.

For each of the 3,830 benchmark movies we encode six text fields independently
with ``all-mpnet-base-v2`` (768-dim sentence embeddings), compute a cosine
similarity matrix per field, and combine them with feature weights:

    Title       0.05
    Director    0.15
    Genres      0.20
    Cast        0.10
    Keywords    0.20
    Description 0.30   (overview + tagline)

The resulting matrix is saved as ``cosine_sim_benchmark.npy`` (float32) into
``ml/data/benchmark/``.

Usage
-----
    python -m ml.scripts.build_content_similarity
    # or
    python ml/scripts/build_content_similarity.py
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import logging

logging.set_verbosity_error()
warnings.filterwarnings("ignore")

_ML_DIR = Path(__file__).resolve().parent.parent
_MOVIES_PATH = _ML_DIR / "data" / "benchmark" / "movies_benchmark.csv"
_OUTPUT_PATH = _ML_DIR / "data" / "benchmark" / "cosine_sim_benchmark.npy"

_FIELDS = ("title", "genres", "director", "description", "cast", "keywords")
_FIELD_PREFIX = {
    "title": "Title: ",
    "genres": "Genres: ",
    "director": "Director: ",
    "description": "Movie Overview: ",
    "cast": "Cast: ",
    "keywords": "Keywords: ",
}
_WEIGHTS = np.array([0.05, 0.20, 0.15, 0.30, 0.10, 0.20])
_EMBED_DIM = 768
_BATCH_SIZE = 64


def _load_dataframe() -> pd.DataFrame:
    """Load and prepare the movie text fields used for embedding."""
    cols = [
        "movie_id", "tmdb_id", "title", "genres", "overview",
        "tagline", "cast", "director", "keywords",
    ]
    df = pd.read_csv(_MOVIES_PATH, usecols=cols).copy()
    df = df.sort_values("movie_id").reset_index(drop=True)
    df["tagline"] = df["tagline"].fillna("")
    df["description"] = df["overview"].fillna("") + " " + df["tagline"]
    for field, prefix in _FIELD_PREFIX.items():
        df[field] = df[field].fillna("").astype(str).map(lambda v, p=prefix: p + v)
    return df


def _encode_fields(model: SentenceTransformer, df: pd.DataFrame) -> np.ndarray:
    """Encode every field separately. Shape: (n_fields, n_movies, embed_dim)."""
    n_items = len(df)
    out = np.empty((len(_FIELDS), n_items, _EMBED_DIM), dtype=np.float32)
    for i, field in enumerate(_FIELDS):
        print(f"  encoding {field} ({n_items} items)...")
        emb = model.encode(
            df[field].tolist(),
            batch_size=_BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        out[i] = emb.astype(np.float32)
    return out


def _weighted_cosine(embeddings: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Weighted sum of per-field cosine similarity matrices."""
    n_fields, n_items, _ = embeddings.shape
    combined = np.zeros((n_items, n_items), dtype=np.float32)
    for i in range(n_fields):
        sim = cosine_similarity(embeddings[i]).astype(np.float32)
        combined += sim * float(weights[i])
    return combined


def main() -> None:
    print(f"[build_content_similarity] reading {_MOVIES_PATH}")
    df = _load_dataframe()
    print(f"  {len(df):,} movies loaded")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  device={device}")
    model = SentenceTransformer("all-mpnet-base-v2", device=device)

    embeddings = _encode_fields(model, df)
    cosine_sim = _weighted_cosine(embeddings, _WEIGHTS)
    print(f"  similarity matrix shape={cosine_sim.shape} dtype={cosine_sim.dtype}")

    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(_OUTPUT_PATH, cosine_sim)
    print(f"  saved → {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
