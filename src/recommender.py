from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


FEATURE_COLUMNS = [
    "nature",
    "history",
    "culture",
    "adventure",
    "photography",
    "shopping",
    "religious",
    "family",
]

BASE_WEIGHTS = {
    "structured": 0.25,
    "tfidf": 0.25,
    "semantic": 0.30,
    "rating": 0.10,
    "popularity": 0.10,
}


class TravelRecommender:
    """
    Shared city-aware personalized hybrid travel recommender.

    Render memory-safe version:
    - Does NOT import or load SentenceTransformer/PyTorch.
    - Uses TF-IDF + TruncatedSVD as a lightweight semantic proxy.
    - Keeps the personalized hybrid-ranking logic.
    - Existing precomputed SentenceTransformer embeddings are accepted
      for API compatibility but are intentionally not loaded/used.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        place_embeddings=None,
        model_name=None,
    ):
        self.df = df.copy()

        required = {
            "city",
            "name",
            "category",
            "travel_tags",
            "rating",
            "reviews",
        }

        missing = sorted(required - set(self.df.columns))
        if missing:
            raise ValueError(
                f"Missing recommender columns: {missing}"
            )

        for column in [
            "city",
            "name",
            "category",
            "travel_tags",
        ]:
            self.df[column] = (
                self.df[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        for feature in FEATURE_COLUMNS:
            if feature not in self.df.columns:
                self.df[feature] = 0

        self.df["rating_score"] = self._minmax(self.df["rating"])

        review_values = (
            pd.to_numeric(
                self.df["reviews"],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
        )

        self.df["popularity_score"] = self._minmax(
            np.log1p(review_values)
        )

        self.structured_matrix = (
            self.df[FEATURE_COLUMNS]
            .fillna(0)
            .astype(float)
            .to_numpy(dtype=np.float32)
        )

        self.df["recommendation_text"] = (
            self.df["name"]
            + ". "
            + self.df["city"]
            + ". "
            + self.df["category"]
            + ". "
            + self.df["travel_tags"]
        ).str.lower()

        # Lightweight text model.
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
            dtype=np.float32,
        )

        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
            self.df["recommendation_text"]
        )

        # Lightweight semantic proxy.
        # For a small catalogue, 32 components is enough and uses very little RAM.
        n_features = self.tfidf_matrix.shape[1]
        max_components = max(1, min(32, n_features - 1))

        if self.tfidf_matrix.shape[0] <= 2 or max_components < 1:
            self.svd_model = None
            self.semantic_matrix = self.tfidf_matrix
        else:
            self.svd_model = TruncatedSVD(
                n_components=max_components,
                random_state=42,
            )
            self.semantic_matrix = self.svd_model.fit_transform(
                self.tfidf_matrix
            ).astype(np.float32)

        # Kept for backward compatibility with the existing API.
        # Do not retain the large numpy embedding array in production memory.
        self.place_embeddings = np.empty(
            (0, 0),
            dtype=np.float32,
        )
        self.model_name = model_name

    @staticmethod
    def _minmax(series):
        values = (
            pd.to_numeric(
                series,
                errors="coerce",
            )
            .fillna(0.0)
        )

        low = values.min()
        high = values.max()

        if low == high:
            return pd.Series(
                np.ones(len(values), dtype=np.float32),
                index=values.index,
            )

        return (values - low) / (high - low)

    @staticmethod
    def get_personalized_weights(
        preferences,
        emphasis=0.15,
    ):
        values = {
            feature: float(
                preferences.get(feature, 0.0)
            )
            for feature in FEATURE_COLUMNS
        }

        total = sum(
            max(value, 0.0)
            for value in values.values()
        )

        if total <= 0:
            return BASE_WEIGHTS.copy()

        structured_boost = (
            emphasis
            * min(
                total / len(FEATURE_COLUMNS),
                1.0,
            )
        )

        weights = BASE_WEIGHTS.copy()
        weights["structured"] += structured_boost
        weights["semantic"] -= structured_boost / 2
        weights["tfidf"] -= structured_boost / 2

        return weights

    def _personalized_structured_score(
        self,
        result,
        preferences,
    ):
        matrix = (
            result[FEATURE_COLUMNS]
            .fillna(0)
            .astype(float)
            .to_numpy(dtype=np.float32)
        )

        preference_vector = np.array(
            [
                float(
                    preferences.get(feature, 0.0)
                )
                for feature in FEATURE_COLUMNS
            ],
            dtype=np.float32,
        )

        numerator = matrix @ preference_vector

        denominator = (
            np.linalg.norm(matrix, axis=1)
            * np.linalg.norm(preference_vector)
        )

        result_scores = np.zeros(
            len(matrix),
            dtype=np.float32,
        )

        valid = denominator > 0
        result_scores[valid] = (
            numerator[valid] / denominator[valid]
        )

        return result_scores

    def recommend(
        self,
        destination,
        query,
        user_preferences,
        top_n=5,
    ):
        missing_preferences = [
            feature
            for feature in FEATURE_COLUMNS
            if feature not in user_preferences
        ]

        if missing_preferences:
            raise ValueError(
                "Missing preference fields: "
                f"{missing_preferences}"
            )

        preference_values = [
            float(user_preferences[feature])
            for feature in FEATURE_COLUMNS
        ]

        if any(
            value < 0 or value > 1
            for value in preference_values
        ):
            raise ValueError(
                "Preference values must be between 0 and 1."
            )

        requested_city = (
            str(destination)
            .strip()
            .lower()
        )

        positions = np.flatnonzero(
            self.df["city"]
            .str.lower()
            .eq(requested_city)
            .to_numpy()
        )

        if len(positions) == 0:
            available = sorted(
                self.df["city"]
                .unique()
                .tolist()
            )
            raise ValueError(
                f"Destination '{destination}' not found. "
                f"Available: {available}"
            )

        result = (
            self.df.iloc[positions]
            .copy()
            .reset_index(drop=True)
        )

        preference_vector = np.array(
            preference_values,
            dtype=np.float32,
        ).reshape(1, -1)

        result["structured_score"] = (
            cosine_similarity(
                preference_vector,
                self.structured_matrix[positions],
            )
            .flatten()
        )

        query_text = (
            f"{destination}. {query}"
        ).lower()

        query_tfidf = self.tfidf_vectorizer.transform(
            [query_text]
        )

        result["tfidf_score"] = (
            cosine_similarity(
                query_tfidf,
                self.tfidf_matrix[positions],
            )
            .flatten()
        )

        # Lightweight semantic score using the same TF-IDF -> SVD space.
        if self.svd_model is None:
            query_semantic = query_tfidf
        else:
            query_semantic = (
                self.svd_model.transform(
                    query_tfidf
                )
            ).astype(np.float32)

        result["semantic_score"] = (
            cosine_similarity(
                query_semantic,
                self.semantic_matrix[positions],
            )
            .flatten()
        )

        weights = self.get_personalized_weights(
            user_preferences
        )

        result["personalized_structured_score"] = (
            self._personalized_structured_score(
                result,
                user_preferences,
            )
        )

        result["final_score"] = (
            weights["structured"]
            * result["personalized_structured_score"]
            + weights["tfidf"]
            * result["tfidf_score"]
            + weights["semantic"]
            * result["semantic_score"]
            + weights["rating"]
            * result["rating_score"]
            + weights["popularity"]
            * result["popularity_score"]
        )

        return (
            result
            .sort_values(
                "final_score",
                ascending=False,
            )
            .head(top_n)
            .reset_index(drop=True)
        )


def available_cities(df: pd.DataFrame):
    return sorted(
        df["city"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
