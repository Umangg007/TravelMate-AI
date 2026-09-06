from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


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
    """Shared city-aware personalized hybrid travel recommender."""

    def __init__(
        self,
        df,
        place_embeddings=None,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
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

        missing = sorted(
            required - set(self.df.columns)
        )

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

        self.df["rating_score"] = (
            self._minmax(self.df["rating"])
        )

        review_values = (
            pd.to_numeric(
                self.df["reviews"],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
        )

        self.df["popularity_score"] = (
            self._minmax(
                np.log1p(review_values)
            )
        )

        self.structured_matrix = (
            self.df[
                FEATURE_COLUMNS
            ]
            .fillna(0)
            .astype(float)
            .to_numpy()
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

        self.tfidf_vectorizer = (
            TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
            )
        )

        self.tfidf_matrix = (
            self.tfidf_vectorizer.fit_transform(
                self.df[
                    "recommendation_text"
                ]
            )
        )

        self.semantic_model = (
            SentenceTransformer(model_name)
        )

        if place_embeddings is None:

            self.place_embeddings = (
                self.semantic_model.encode(
                    self.df[
                        "recommendation_text"
                    ].tolist(),
                    normalize_embeddings=True,
                    show_progress_bar=True,
                )
            )

        else:

            if len(place_embeddings) != len(
                self.df
            ):
                raise ValueError(
                    "Embedding row count does not match dataset."
                )

            self.place_embeddings = (
                place_embeddings
            )

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
                np.ones(len(values)),
                index=values.index,
            )

        return (
            (values - low)
            / (high - low)
        )

    @staticmethod
    def get_personalized_weights(
        preferences,
        emphasis=0.15,
    ):
        values = {
            feature: float(
                preferences.get(
                    feature,
                    0.0,
                )
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

        weights["structured"] += (
            structured_boost
        )

        weights["semantic"] -= (
            structured_boost / 2
        )

        weights["tfidf"] -= (
            structured_boost / 2
        )

        return weights

    def _personalized_structured_score(
        self,
        result,
        preferences,
    ):
        matrix = (
            result[
                FEATURE_COLUMNS
            ]
            .fillna(0)
            .astype(float)
            .to_numpy()
        )

        preference_vector = np.array(
            [
                float(
                    preferences.get(
                        feature,
                        0.0,
                    )
                )
                for feature in FEATURE_COLUMNS
            ],
            dtype=float,
        )

        numerator = (
            matrix @ preference_vector
        )

        denominator = (
            np.linalg.norm(
                matrix,
                axis=1,
            )
            * np.linalg.norm(
                preference_vector
            )
        )

        result = np.zeros(
            len(matrix),
            dtype=float,
        )

        valid = denominator > 0

        result[valid] = (
            numerator[valid]
            / denominator[valid]
        )

        return result

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
            float(
                user_preferences[
                    feature
                ]
            )
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
            (
                self.df["city"]
                .str.lower()
                .eq(requested_city)
            ).to_numpy()
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
            self.df
            .iloc[positions]
            .copy()
            .reset_index(drop=True)
        )

        preference_vector = np.array(
            preference_values,
            dtype=float,
        ).reshape(1, -1)

        result["structured_score"] = (
            cosine_similarity(
                preference_vector,
                self.structured_matrix[
                    positions
                ],
            ).flatten()
        )

        query_text = (
            f"{destination}. {query}"
        ).lower()

        query_tfidf = (
            self.tfidf_vectorizer.transform(
                [query_text]
            )
        )

        result["tfidf_score"] = (
            cosine_similarity(
                query_tfidf,
                self.tfidf_matrix[
                    positions
                ],
            ).flatten()
        )

        query_embedding = (
            self.semantic_model.encode(
                [query_text],
                normalize_embeddings=True,
            )
        )

        result["semantic_score"] = (
            cosine_similarity(
                query_embedding,
                self.place_embeddings[
                    positions
                ],
            ).flatten()
        )

        weights = (
            self.get_personalized_weights(
                user_preferences
            )
        )

        result[
            "personalized_structured_score"
        ] = self._personalized_structured_score(
            result,
            user_preferences,
        )

        result["final_score"] = (
            weights["structured"]
            * result[
                "personalized_structured_score"
            ]
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


def available_cities(df):
    return sorted(
        df["city"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
