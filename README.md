# 🌍 TravelMate AI

TravelMate AI is a multi-city AI travel recommendation and itinerary-planning system.

It combines:
- structured preference matching
- TF-IDF text similarity
- SentenceTransformer semantic similarity
- rating and popularity signals
- personalized hybrid weighting
- city-aware filtering
- constraint-based itinerary generation
- FastAPI backend
- Streamlit frontend
- interactive Folium maps

## ✨ Supported destinations

The current dataset contains six destinations:

`Manali`, `Goa`, `Jaipur`, `Udaipur`, `Rishikesh`, `Shimla`

The backend reads supported cities from the processed dataset rather than hard-coding recommendation results.

---

## 🧠 Recommendation pipeline

```text
User destination + query + preferences
                 ↓
        City-aware filtering
                 ↓
 ┌───────────────┼────────────────┐
 ↓               ↓                ↓
Structured      TF-IDF       Semantic embedding
matching        similarity       similarity
 └───────────────┼────────────────┘
                 ↓
       Personalized weighting
                 ↓
     Rating + popularity signals
                 ↓
        Final recommendation score
                 ↓
          Top-N places
```

The personalized engine increases the influence of structured preference matching when the user's preferences are meaningful, while preserving text, semantic, rating, and popularity signals.

## 🗺️ Itinerary pipeline

```text
Recommended places
       ↓
Planning metadata
       ↓
Distance calculation
(Haversine)
       ↓
Estimated travel time
       ↓
Day-by-day packing
       ↓
420 minute/day budget
       ↓
Validated itinerary
```

The current prototype uses an estimated average travel speed of 25 km/h. Travel time is therefore an approximation, not live road-routing data.

---

## 📁 Project structure

```text
TravelMate-AI/
│
├── app/
│   ├── main.py
│   └── streamlit_app.py
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── recommender.py
│   ├── itinerary.py
│   └── utils.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   │   └── multi_city_recommendation_features.csv
│   └── embeddings/
│       └── multi_city_place_embeddings.npy
│
├── notebooks/
│   └── project development notebooks
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

> Keep the real `.env` file private. Never commit the SerpAPI key.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd TravelMate-AI
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your real SerpAPI key.

---

## 🚀 Run the application

### Terminal 1 - FastAPI

Run from the project root:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 - Streamlit

Run from the same project root:

```bash
streamlit run app/streamlit_app.py
```

Frontend:

```text
http://localhost:8501
```

---

## 🔌 API endpoints

### `GET /`

Returns basic application information and supported cities.

### `GET /health`

Returns backend health and loaded dataset information.

### `GET /cities`

Returns the currently available destination list.

### `POST /recommend`

Generates personalized place recommendations.

Example request:

```json
{
  "destination": "Shimla",
  "query": "peaceful scenic trip for photography",
  "days": 3,
  "top_n": 6,
  "preferences": {
    "nature": 0.9,
    "history": 0.2,
    "culture": 0.4,
    "adventure": 0.3,
    "photography": 0.9,
    "shopping": 0.2,
    "religious": 0.1,
    "family": 0.4
  }
}
```

### `POST /itinerary`

Uses the recommendation engine and itinerary optimizer to create a day-by-day plan.

---

## ✅ Final automated test status

The final system test covered:

```text
✅ Dataset loaded
✅ All cities represented
✅ Recommendation city correctness
✅ Recommendation scores valid
✅ Recommendation coordinates valid
✅ Itinerary budget validity
✅ Itinerary city validity
✅ Itinerary coordinates valid
✅ Invalid city handled
✅ Repeated calls stable
✅ Legacy Manali-only text absent
```

Final gate:

```text
🎉 ALL AUTOMATED SYSTEM TESTS PASSED
```

---

## 📊 Model evaluation

The project uses proxy evaluation metrics because there is currently no human-labelled user-feedback dataset.

Final comparison after promoting the personalized hybrid engine showed:

- Preference alignment: `0.672733 → 0.684515`
- Mean recommendation score: `0.554864 → 0.568926`
- City correctness remained `1.000000`
- All five tested traveller profiles improved preference alignment

The earlier MMR diversification experiment was not promoted because its diversity improvement came with lower preference alignment, lower catalogue coverage, and lower personalization sensitivity.

---

## ⚠️ Current limitations

### Planning metadata
Activity type, visit duration, and price level are heuristic estimates inferred from place/category text.

### Travel time
The optimizer uses Haversine distance with an assumed average speed of 25 km/h. It does not use live traffic or road-network routing.

### Evaluation
The evaluation suite is based primarily on proxy metrics and system constraints, not real user satisfaction labels.

### Data freshness
Place data depends on the collected dataset and is not automatically refreshed unless the data-collection workflow is run again.

---

## 🔒 Security checklist

Before pushing to GitHub:

```text
[ ] .env is not committed
[ ] SERPAPI_KEY is not present in source code
[ ] secrets.toml is not committed
[ ] local caches are ignored
[ ] generated embeddings/model files are handled intentionally
```

---

## 🧪 Recommended final smoke test

From the project root:

```bash
uvicorn app.main:app --reload
```

Then in another terminal:

```bash
streamlit run app/streamlit_app.py
```

Test at least:

```text
Goa
Jaipur
Manali
Shimla
```

Change the preference sliders and confirm that recommendations change.

---

## 💼 Portfolio description

**TravelMate AI** is an AI-powered multi-city travel recommendation and itinerary planning system built with Python, machine learning, NLP, FastAPI, and Streamlit. It combines structured preference matching, TF-IDF, SentenceTransformer semantic similarity, popularity/rating signals, and personalized hybrid ranking to recommend travel places and generate constraint-aware daily itineraries with interactive maps.

---

## 👨‍💻 Development philosophy

The project follows a shared-engine design:

```text
Frontend
   ↓
FastAPI
   ↓
Reusable src/ ML engine
   ↓
Data + embeddings
```

This keeps recommendation and itinerary logic separate from the UI and API layers and makes the system easier to test, maintain, and deploy.
