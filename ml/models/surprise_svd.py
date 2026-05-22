"""
Surprise-backed SVD / SVD++ recommenders.

Wraps scikit-surprise's Cython implementations behind the BaseRecommender
interface so they can be used by the evaluation runner.
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from surprise import Dataset, Reader, SVD, SVDpp

from .base import BaseRecommender


def _save_pickle(obj, path: str | Path) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def _load_pickle(path: str | Path):
    with open(path, "rb") as f:
        return pickle.load(f)


class SurpriseSVD(BaseRecommender):
    """FunkSVD via scikit-surprise."""

    def __init__(self, n_factors=150, n_epochs=50, lr_all=0.002, reg_all=0.001):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all

    def fit(self, ratings: pd.DataFrame) -> "SurpriseSVD":
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(
            ratings[["user_id", "movie_idx", "rating"]], reader
        )
        self._trainset = data.build_full_trainset()

        self._algo = SVD(
            n_factors=self.n_factors,
            n_epochs=self.n_epochs,
            lr_all=self.lr_all,
            reg_all=self.reg_all,
            verbose=False,
            random_state=42,
        )
        self._algo.fit(self._trainset)

        # Cache global catalog size once for score_all (avoids recomputing)
        self._n_items_global = max(
            int(self._trainset.to_raw_iid(i)) for i in range(self._trainset.n_items)
        ) + 1

        # Cache seen items per user (raw IDs)
        self._seen: dict[int, set[int]] = {}
        for inner_uid in range(self._trainset.n_users):
            raw_uid = self._trainset.to_raw_uid(inner_uid)
            items = {
                self._trainset.to_raw_iid(iid)
                for iid, _ in self._trainset.ur[inner_uid]
            }
            self._seen[raw_uid] = items

        return self

    def recommend(self, user_id: int, n: int = 10, exclude=None) -> list[int]:
        try:
            inner_uid = self._trainset.to_inner_uid(user_id)
        except ValueError:
            return []

        algo = self._algo
        mu = self._trainset.global_mean
        scores = (
            mu
            + algo.bu[inner_uid]
            + algo.bi
            + algo.pu[inner_uid] @ algo.qi.T
        )

        seen = self._seen.get(user_id, set())
        if exclude:
            seen = seen | exclude
        for raw_iid in seen:
            try:
                inner_iid = self._trainset.to_inner_iid(raw_iid)
                scores[inner_iid] = -np.inf
            except ValueError:
                pass

        top_inner = np.argsort(scores)[::-1][:n]
        return [int(self._trainset.to_raw_iid(int(iid))) for iid in top_inner]

    def score_all(self, user_id: int) -> np.ndarray | None:
        """Predicted rating for every movie in the catalog (raw matrix index)."""
        try:
            inner_uid = self._trainset.to_inner_uid(user_id)
        except ValueError:
            return None
        algo = self._algo
        mu = self._trainset.global_mean
        inner_scores = (
            mu + algo.bu[inner_uid] + algo.bi + algo.pu[inner_uid] @ algo.qi.T
        )
        return _inner_to_raw_scores(self._trainset, inner_scores, self._n_items_global)

    def save(self, path: str | Path) -> None:
        _save_pickle(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "SurpriseSVD":
        return _load_pickle(path)


def _inner_to_raw_scores(trainset, inner_scores: np.ndarray, n_items_global: int) -> np.ndarray:
    """
    Surprise re-numbers items by inner id; remap scores back to the matrix
    index space (raw_iid). Items the trainset never saw stay at -inf.
    """
    out = np.full(n_items_global, -np.inf, dtype=np.float32)
    for inner_iid in range(trainset.n_items):
        raw = int(trainset.to_raw_iid(inner_iid))
        out[raw] = inner_scores[inner_iid]
    return out


class SurpriseSVDpp(BaseRecommender):
    """SVD++ via scikit-surprise."""

    def __init__(self, n_factors=100, n_epochs=50, lr_all=0.002, reg_all=0.001):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all

    def fit(self, ratings: pd.DataFrame) -> "SurpriseSVDpp":
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(
            ratings[["user_id", "movie_idx", "rating"]], reader
        )
        self._trainset = data.build_full_trainset()

        self._algo = SVDpp(
            n_factors=self.n_factors,
            n_epochs=self.n_epochs,
            lr_all=self.lr_all,
            reg_all=self.reg_all,
            verbose=False,
            random_state=42,
        )
        self._algo.fit(self._trainset)

        # Cache global catalog size once for score_all (avoids recomputing)
        self._n_items_global = max(
            int(self._trainset.to_raw_iid(i)) for i in range(self._trainset.n_items)
        ) + 1

        # Cache seen items per user (raw IDs)
        self._seen: dict[int, set[int]] = {}
        for inner_uid in range(self._trainset.n_users):
            raw_uid = self._trainset.to_raw_uid(inner_uid)
            items = {
                self._trainset.to_raw_iid(iid)
                for iid, _ in self._trainset.ur[inner_uid]
            }
            self._seen[raw_uid] = items

        # Cache user vectors (pu + implicit feedback term) once — used by
        # recommend() and score_all(). Avoids O(|N(u)|) per inference call.
        self._u_vecs = np.empty(
            (self._trainset.n_users, self.n_factors), dtype=np.float32
        )
        for inner_uid in range(self._trainset.n_users):
            self._u_vecs[inner_uid] = self._user_vector(inner_uid)

        return self

    def _user_vector(self, inner_uid):
        algo = self._algo
        items_u = [iid for iid, _ in self._trainset.ur[inner_uid]]
        vec = algo.pu[inner_uid].copy()
        if items_u:
            vec += algo.yj[items_u].sum(0) / np.sqrt(len(items_u))
        return vec

    def recommend(self, user_id: int, n: int = 10, exclude=None) -> list[int]:
        try:
            inner_uid = self._trainset.to_inner_uid(user_id)
        except ValueError:
            return []

        algo = self._algo
        mu = self._trainset.global_mean
        u_vec = self._u_vecs[inner_uid]
        scores = mu + algo.bu[inner_uid] + algo.bi + u_vec @ algo.qi.T

        seen = self._seen.get(user_id, set())
        if exclude:
            seen = seen | exclude
        for raw_iid in seen:
            try:
                inner_iid = self._trainset.to_inner_iid(raw_iid)
                scores[inner_iid] = -np.inf
            except ValueError:
                pass

        top_inner = np.argsort(scores)[::-1][:n]
        return [int(self._trainset.to_raw_iid(int(iid))) for iid in top_inner]

    def score_all(self, user_id: int) -> np.ndarray | None:
        try:
            inner_uid = self._trainset.to_inner_uid(user_id)
        except ValueError:
            return None
        algo = self._algo
        mu = self._trainset.global_mean
        u_vec = self._u_vecs[inner_uid]
        inner_scores = mu + algo.bu[inner_uid] + algo.bi + u_vec @ algo.qi.T
        return _inner_to_raw_scores(self._trainset, inner_scores, self._n_items_global)

    def save(self, path: str | Path) -> None:
        _save_pickle(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "SurpriseSVDpp":
        return _load_pickle(path)
