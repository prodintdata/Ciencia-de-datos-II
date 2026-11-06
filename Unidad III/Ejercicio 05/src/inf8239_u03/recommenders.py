from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def weighted_popularity(ratings: pd.DataFrame, movies: pd.DataFrame, quantile: float = 0.80) -> pd.DataFrame:
    stats = ratings.groupby("movieId")["rating"].agg(["mean", "count"])
    global_mean = float(ratings["rating"].mean())
    minimum = float(stats["count"].quantile(quantile))
    stats["weighted_score"] = (
        stats["count"] / (stats["count"] + minimum) * stats["mean"]
        + minimum / (stats["count"] + minimum) * global_mean
    )
    return stats.query("count >= @minimum").join(movies.set_index("movieId")).sort_values("weighted_score", ascending=False)


class ContentRecommender:
    def fit(self, movies: pd.DataFrame) -> ContentRecommender:
        self.movies = movies.reset_index(drop=True).copy()
        self.movies["genres_text"] = self.movies["genres"].str.replace("|", " ", regex=False)
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(self.movies["genres_text"])
        return self

    def recommend(self, title: str, k: int = 10) -> pd.DataFrame:
        matches = self.movies.index[self.movies["title"].eq(title)]
        if len(matches) == 0:
            raise KeyError(f"Título no encontrado: {title}")
        index = int(matches[0])
        scores = cosine_similarity(self.matrix[index], self.matrix).ravel()
        order = [value for value in scores.argsort()[::-1] if value != index][:k]
        result = self.movies.loc[order, ["movieId", "title", "genres"]].copy()
        result["content_score"] = scores[order]
        return result.reset_index(drop=True)


class MatrixFactorization:
    def __init__(self, factors: int = 20, learning_rate: float = 0.01, regularization: float = 0.05, seed: int = 42):
        self.factors = factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.seed = seed

    def fit(self, ratings: pd.DataFrame, epochs: int = 12) -> MatrixFactorization:
        self.users = sorted(ratings["userId"].unique())
        self.items = sorted(ratings["movieId"].unique())
        self.user_index = {value: index for index, value in enumerate(self.users)}
        self.item_index = {value: index for index, value in enumerate(self.items)}
        rng = np.random.default_rng(self.seed)
        self.user_factors = rng.normal(0, 0.1, (len(self.users), self.factors))
        self.item_factors = rng.normal(0, 0.1, (len(self.items), self.factors))
        self.global_mean = float(ratings["rating"].mean())
        observations = [(self.user_index[r.userId], self.item_index[r.movieId], float(r.rating)) for r in ratings.itertuples()]
        for _ in range(epochs):
            rng.shuffle(observations)
            for user, item, rating in observations:
                error = rating - self.predict_indices(user, item)
                previous_user = self.user_factors[user].copy()
                self.user_factors[user] += self.learning_rate * (error * self.item_factors[item] - self.regularization * self.user_factors[user])
                self.item_factors[item] += self.learning_rate * (error * previous_user - self.regularization * self.item_factors[item])
        return self

    def predict_indices(self, user_index: int, item_index: int) -> float:
        return float(self.global_mean + self.user_factors[user_index] @ self.item_factors[item_index])

    def predict(self, user_id: int, movie_id: int) -> float:
        return self.predict_indices(self.user_index[user_id], self.item_index[movie_id])

    def top_n(self, user_id: int, seen: set[int], k: int = 10) -> pd.DataFrame:
        if user_id not in self.user_index:
            return pd.DataFrame(columns=["movieId", "collaborative_score"])
        # Vectorizado: mismo resultado que predict() ítem por ítem, sin el bucle en Python.
        mask = np.array([item not in seen for item in self.items])
        candidates = np.asarray(self.items)[mask]
        scores = self.global_mean + self.item_factors[mask] @ self.user_factors[self.user_index[user_id]]
        order = scores.argsort()[::-1][:k]
        return pd.DataFrame({"movieId": candidates[order], "collaborative_score": scores[order]})

    @property
    def size_bytes(self) -> int:
        return int(self.user_factors.nbytes + self.item_factors.nbytes)


def popularity_ranking(ratings: pd.DataFrame) -> list[int]:
    """Fallback documentado para usuarios fríos: cantidad de valoraciones y luego media. No es personalizado."""
    stats = ratings.groupby("movieId")["rating"].agg(["mean", "count"])
    return stats.sort_values(["count", "mean"], ascending=False).index.astype(int).tolist()


def popularity_top_n(ranking: list[int], seen: set[int], k: int = 10) -> list[int]:
    return [item for item in ranking if item not in seen][:k]


def _min_max(values: np.ndarray) -> np.ndarray:
    return (values - values.min()) / max(values.max() - values.min(), 1e-9)


class GenreProfile:
    """Perfil de contenido del usuario: promedio TF-IDF de géneros ponderado por (rating - 2.5)."""

    def fit(self, movies: pd.DataFrame) -> GenreProfile:
        table = movies.reset_index(drop=True)
        self.matrix = TfidfVectorizer().fit_transform(table["genres"].str.replace("|", " ", regex=False))
        self.movie_row = {int(movie_id): index for index, movie_id in enumerate(table["movieId"])}
        return self

    def profile(self, history: pd.DataFrame) -> np.ndarray:
        history = history[history["movieId"].isin(self.movie_row)]
        rows = [self.movie_row[int(item)] for item in history["movieId"]]
        weights = np.clip(history["rating"].to_numpy() - 2.5, 0.1, None)
        # .sum(axis=0) de una matriz dispersa devuelve np.matrix; cosine_similarity exige ndarray.
        return np.asarray(self.matrix[rows].multiply(weights[:, None]).sum(axis=0)) / weights.sum()

    def scores(self, profile: np.ndarray, movie_ids) -> np.ndarray:
        rows = [self.movie_row[int(item)] for item in movie_ids]
        return cosine_similarity(profile, self.matrix[rows]).ravel()


def hybrid_rerank(collaborative: pd.DataFrame, content_scores: np.ndarray, alpha: float, k: int = 10) -> pd.DataFrame:
    """alpha pondera la señal colaborativa y (1 - alpha) la de contenido, ambas normalizadas min-max en el pool."""
    result = collaborative.copy()
    result["normalized"] = _min_max(result["collaborative_score"].to_numpy())
    result["content_score"] = _min_max(content_scores)
    result["hybrid_score"] = alpha * result["normalized"] + (1 - alpha) * result["content_score"]
    return result.nlargest(k, "hybrid_score").reset_index(drop=True)


def temporal_leave_one_out(ratings: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = ratings.sort_values(["userId", "timestamp"])
    test = ordered.groupby("userId", sort=False).tail(1)
    train = ordered.drop(test.index)
    return train.reset_index(drop=True), test.reset_index(drop=True)
