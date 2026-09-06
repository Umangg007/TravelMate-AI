# 🚀 TravelMate AI - Deployment Checklist

## Code
- [ ] `src/recommender.py` contains the promoted personalized hybrid ranker.
- [ ] `app/main.py` imports the shared engine.
- [ ] `app/streamlit_app.py` calls the FastAPI backend.
- [ ] No Manali-only hard-coded recommendation restriction remains.

## Data
- [ ] `data/processed/multi_city_recommendation_features.csv` exists.
- [ ] `data/embeddings/multi_city_place_embeddings.npy` exists.
- [ ] Dataset contains Manali, Goa, Jaipur, Udaipur, Rishikesh, and Shimla.

## Secrets
- [ ] `.env` exists locally.
- [ ] `.env` is ignored by Git.
- [ ] `.env.example` contains only placeholder values.
- [ ] No API key appears in notebooks, source files, screenshots, or README.

## Dependencies
- [ ] `requirements.txt` exists.
- [ ] A fresh virtual environment can install it successfully.
- [ ] FastAPI starts.
- [ ] Streamlit starts.

## Testing
- [ ] Run notebook 25 final system testing.
- [ ] All automated tests pass.
- [ ] Test at least four destinations manually.
- [ ] Change preference sliders and verify recommendations react.

## GitHub
- [ ] Remove unnecessary temporary files.
- [ ] Keep development notebooks only when useful for the project story.
- [ ] Add README.
- [ ] Add screenshots / demo GIF separately.
- [ ] Do not commit `.env`, caches, or unnecessary large artifacts.

## Deployment
- [ ] Choose a host for FastAPI.
- [ ] Configure `SERPAPI_KEY` as a platform secret.
- [ ] Configure the Streamlit frontend to use the deployed API URL.
- [ ] Replace local `127.0.0.1:8000` with an environment-configured backend URL.
- [ ] Run one final end-to-end smoke test after deployment.
