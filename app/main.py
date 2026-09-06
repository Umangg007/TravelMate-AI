from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.data_loader import load_places, available_cities, load_embeddings
from src.recommender import TravelRecommender
from src.itinerary import generate_itinerary


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "multi_city_recommendation_features.csv"
)

EMBEDDING_PATH = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
    / "multi_city_place_embeddings.npy"
)

MAX_DAY_MINUTES = 7 * 60
DEFAULT_DAYS = 3
DEFAULT_TOP_N = 5


places = load_places(DATA_PATH)

if EMBEDDING_PATH.exists():
    embeddings = load_embeddings(EMBEDDING_PATH)
else:
    embeddings = None

recommender = TravelRecommender(
    df=places,
    place_embeddings=embeddings,
)


def infer_activity_type(text: str) -> str:
    text = str(text).lower()

    if "waterfall" in text or "falls" in text:
        return "waterfall"
    if "rafting" in text:
        return "rafting"
    if "trek" in text:
        return "trekking"
    if "viewpoint" in text or "view point" in text:
        return "viewpoint"
    if any(x in text for x in ["temple", "church", "mosque", "gurudwara", "monastery"]):
        return "religious_site"
    if any(x in text for x in ["fort", "palace", "museum", "heritage", "castle"]):
        return "heritage"
    if any(x in text for x in ["market", "bazaar", "mall", "shopping"]):
        return "shopping"
    if any(x in text for x in ["beach", "lake", "river", "park", "forest", "garden"]):
        return "nature"
    if "snow" in text or "ski" in text:
        return "winter_experience"

    return "sightseeing"


def estimate_visit_minutes(activity_type: str) -> int:
    return {
        "waterfall": 90,
        "rafting": 120,
        "trekking": 150,
        "viewpoint": 45,
        "religious_site": 60,
        "heritage": 120,
        "shopping": 90,
        "nature": 90,
        "winter_experience": 90,
        "sightseeing": 60,
    }.get(activity_type, 60)


def estimate_price_level(text: str) -> int:
    text = str(text).lower()

    if "rafting" in text or "ski" in text or "adventure" in text:
        return 3

    if any(x in text for x in ["shopping", "market", "bazaar", "mall"]):
        return 2

    return 1


def add_planning_metadata(candidates: pd.DataFrame) -> pd.DataFrame:
    result = candidates.copy()

    planning_text = (
        result["name"].fillna("").astype(str)
        + " "
        + result["category"].fillna("").astype(str)
    )

    result["activity_type"] = planning_text.apply(
        infer_activity_type
    )

    result["estimated_visit_minutes"] = (
        result["activity_type"].apply(
            estimate_visit_minutes
        )
    )

    result["estimated_price_level"] = (
        planning_text.apply(
            estimate_price_level
        )
    )

    return result


class Preferences(BaseModel):
    nature: float = Field(0.5, ge=0.0, le=1.0)
    history: float = Field(0.3, ge=0.0, le=1.0)
    culture: float = Field(0.4, ge=0.0, le=1.0)
    adventure: float = Field(0.3, ge=0.0, le=1.0)
    photography: float = Field(0.5, ge=0.0, le=1.0)
    shopping: float = Field(0.2, ge=0.0, le=1.0)
    religious: float = Field(0.2, ge=0.0, le=1.0)
    family: float = Field(0.4, ge=0.0, le=1.0)


class TravelRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    days: int = Field(DEFAULT_DAYS, ge=1, le=14)
    top_n: int = Field(DEFAULT_TOP_N, ge=1, le=15)
    preferences: Preferences


app = FastAPI(
    title="TravelMate AI API",
    description="City-aware AI travel recommendation and itinerary backend.",
    version="2.0.0",
)


@app.get("/")
def root():
    return {
        "app": "TravelMate AI",
        "version": "2.0.0",
        "status": "running",
        "supported_cities": available_cities(places),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "places_loaded": len(places),
        "cities_loaded": len(available_cities(places)),
        "embedding_rows": len(recommender.place_embeddings),
    }


@app.get("/cities")
def cities():
    return {
        "cities": available_cities(places)
    }


@app.post("/recommend")
def recommend(request: TravelRequest):
    try:
        result = recommender.recommend(
            destination=request.destination,
            query=request.query,
            user_preferences=request.preferences.model_dump(),
            top_n=request.top_n,
        )

        result = add_planning_metadata(result)

        columns = [
            "name",
            "city",
            "category",
            "rating",
            "reviews",
            "travel_tags",
            "activity_type",
            "estimated_visit_minutes",
            "estimated_price_level",
            "structured_score",
            "tfidf_score",
            "semantic_score",
            "final_score",
            "latitude",
            "longitude",
        ]

        result = result[
            [c for c in columns if c in result.columns]
        ]

        return {
            "destination": request.destination,
            "query": request.query,
            "count": len(result),
            "recommendations": result.to_dict(
                orient="records"
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/itinerary")
def itinerary(request: TravelRequest):
    try:
        candidate_count = min(
            max(request.top_n, request.days * 4),
            len(places),
        )

        candidates = recommender.recommend(
            destination=request.destination,
            query=request.query,
            user_preferences=request.preferences.model_dump(),
            top_n=candidate_count,
        )

        candidates = add_planning_metadata(candidates)

        plan = generate_itinerary(
            candidates=candidates,
            days=request.days,
            max_day_minutes=MAX_DAY_MINUTES,
            average_speed_kmph=25,
        )

        return {
            "destination": request.destination,
            "query": request.query,
            "days_requested": request.days,
            "scheduled_stops": len(plan),
            "daily_budget_minutes": MAX_DAY_MINUTES,
            "itinerary": plan.to_dict(
                orient="records"
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
