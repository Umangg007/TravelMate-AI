
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "multi_city_recommendation_features.csv"
DEFAULT_EMBEDDING_PATH = PROJECT_ROOT / "data" / "embeddings" / "multi_city_place_embeddings.npy"

def load_places(data_path=DEFAULT_DATA_PATH):
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Place dataset not found: {path}")
    return pd.read_csv(path)

def load_embeddings(embedding_path=DEFAULT_EMBEDDING_PATH):
    path = Path(embedding_path)
    if not path.exists():
        raise FileNotFoundError(f"Embedding file not found: {path}")
    return np.load(path)

def available_cities(df):
    if "city" not in df.columns:
        raise KeyError("Expected a city column.")
    return sorted(df["city"].dropna().astype(str).str.strip().unique().tolist())
