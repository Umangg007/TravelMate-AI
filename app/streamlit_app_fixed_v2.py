import requests
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

import os

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)
st.set_page_config(
    page_title="TravelMate AI",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 TravelMate AI")
st.subheader("Your personalized AI travel planner ✈️")

st.write(
    "Tell TravelMate what kind of trip you want, "
    "and it will recommend places and build a day-by-day itinerary."
)

# -------------------------------------------------
# Session state
# -------------------------------------------------
# Streamlit reruns the script whenever a widget changes.
# The Generate button is True only for the click rerun.
# Therefore, results must be stored in session_state.
if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "api_error" not in st.session_state:
    st.session_state.api_error = None


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("🧳 Trip Preferences")

destination = st.sidebar.text_input(
    "Destination",
    value="Manali"
)

if destination.strip().lower() != "manali":
    st.sidebar.warning(
        "⚠️ The current model is trained on Manali data only. "
        "Use Manali until additional destination datasets are added."
    )

days = st.sidebar.number_input(
    "Number of days",
    min_value=1,
    max_value=14,
    value=3,
    step=1
)

top_n = st.sidebar.slider(
    "Number of recommendations",
    min_value=3,
    max_value=15,
    value=6
)

st.sidebar.markdown("### ❤️ What do you like?")

nature = st.sidebar.slider("🌿 Nature", 0.0, 1.0, 0.8, 0.1)
history = st.sidebar.slider("🏛️ History", 0.0, 1.0, 0.2, 0.1)
culture = st.sidebar.slider("🎭 Culture", 0.0, 1.0, 0.3, 0.1)
adventure = st.sidebar.slider("🥾 Adventure", 0.0, 1.0, 0.4, 0.1)
photography = st.sidebar.slider("📸 Photography", 0.0, 1.0, 0.8, 0.1)
shopping = st.sidebar.slider("🛍️ Shopping", 0.0, 1.0, 0.2, 0.1)
religious = st.sidebar.slider("🛕 Religious", 0.0, 1.0, 0.1, 0.1)
family = st.sidebar.slider("👨‍👩‍👧 Family", 0.0, 1.0, 0.4, 0.1)

query = st.text_area(
    "💬 Describe your trip",
    value=(
        "I want a peaceful scenic trip with "
        "beautiful places for photography."
    ),
    height=100
)

preferences = {
    "nature": nature,
    "history": history,
    "culture": culture,
    "adventure": adventure,
    "photography": photography,
    "shopping": shopping,
    "religious": religious,
    "family": family
}


# -------------------------------------------------
# Generate
# -------------------------------------------------
generate = st.button(
    "✨ Generate My Trip",
    type="primary",
    width="stretch"
)

if generate:
    if destination.strip().lower() != "manali":
        st.error(
            "❌ This prototype currently supports Manali only. "
            "We will add multi-city data next."
        )
        st.stop()

    request_payload = {
        "destination": destination,
        "query": query,
        "days": int(days),
        "top_n": int(top_n),
        "preferences": preferences
    }

    try:
        with st.spinner("TravelMate is thinking... 🤖"):

            recommendation_response = requests.post(
                f"{API_BASE_URL}/recommend",
                json=request_payload,
                timeout=60
            )

            itinerary_response = requests.post(
                f"{API_BASE_URL}/itinerary",
                json=request_payload,
                timeout=60
            )

        recommendation_response.raise_for_status()
        itinerary_response.raise_for_status()

        # Save successful result so it survives Streamlit reruns.
        st.session_state.trip_result = {
            "destination": destination,
            "query": query,
            "recommendations": recommendation_response.json().get(
                "recommendations",
                []
            ),
            "itinerary": itinerary_response.json().get(
                "itinerary",
                []
            )
        }

        st.session_state.api_error = None

    except requests.exceptions.ConnectionError:
        st.session_state.trip_result = None
        st.session_state.api_error = (
            "❌ FastAPI is not running. Start it with: "
            "`uvicorn app.main:app --reload`"
        )

    except requests.exceptions.Timeout:
        st.session_state.trip_result = None
        st.session_state.api_error = (
            "⏳ The backend took too long to respond."
        )

    except requests.exceptions.RequestException as exc:
        st.session_state.trip_result = None
        st.session_state.api_error = f"❌ API request failed: {exc}"

    except Exception as exc:
        st.session_state.trip_result = None
        st.session_state.api_error = f"❌ Unexpected error: {exc}"


# -------------------------------------------------
# Persistent output
# -------------------------------------------------
if st.session_state.api_error:
    st.error(st.session_state.api_error)

result = st.session_state.trip_result

if result:

    st.success(
        f"✅ Trip generated for {result['destination']}"
    )

    # ---------------------------------------------
    # Recommendations
    # ---------------------------------------------
    st.header("🎯 Recommended Places")

    recommendations = result["recommendations"]

    if recommendations:

        rec_df = pd.DataFrame(recommendations)

        display_columns = [
            "name",
            "activity_type",
            "rating",
            "reviews",
            "estimated_visit_minutes",
            "api_score"
        ]

        available = [
            col for col in display_columns
            if col in rec_df.columns
        ]

        st.dataframe(
            rec_df[available],
            width="stretch",
            hide_index=True
        )

    else:
        st.warning("No recommendations were returned.")

    # ---------------------------------------------
    # Itinerary
    # ---------------------------------------------
    st.header("📅 Your Itinerary")

    itinerary = result["itinerary"]

    if itinerary:

        itinerary_df = pd.DataFrame(itinerary)

        for day in sorted(itinerary_df["day"].unique()):

            day_df = itinerary_df[
                itinerary_df["day"] == day
            ].sort_values("stop")

            st.subheader(f"📍 Day {int(day)}")

            for _, row in day_df.iterrows():

                st.markdown(
                    f"""
**Stop {int(row['stop'])}: {row['place']}**  
🕘 {row['arrival']} → {row['departure']}  
🎯 Score: {row['score']}  
⏱️ Visit: {int(row['visit_minutes'])} min  
🚗 Travel before stop: {row['travel_before_minutes']} min
"""
                )

            st.divider()

    else:
        st.warning("No itinerary could be generated.")

    # ---------------------------------------------
    # Map
    # ---------------------------------------------
    st.header("🗺️ Trip Map")

    valid_points = [
        item for item in itinerary
        if item.get("latitude") is not None
        and item.get("longitude") is not None
    ]

    if valid_points:

        center_lat = sum(
            item["latitude"] for item in valid_points
        ) / len(valid_points)

        center_lon = sum(
            item["longitude"] for item in valid_points
        ) / len(valid_points)

        travel_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=13
        )

        for item in valid_points:

            folium.Marker(
                location=[
                    item["latitude"],
                    item["longitude"]
                ],
                popup=(
                    f"Day {item['day']} - Stop {item['stop']}<br>"
                    f"{item['place']}<br>"
                    f"{item['arrival']} - {item['departure']}"
                ),
                tooltip=(
                    f"Day {item['day']} - Stop {item['stop']}: "
                    f"{item['place']}"
                )
            ).add_to(travel_map)

        for day in sorted({
            item["day"] for item in valid_points
        }):

            day_points = sorted(
                [
                    item for item in valid_points
                    if item["day"] == day
                ],
                key=lambda x: x["stop"]
            )

            coordinates = [
                [item["latitude"], item["longitude"]]
                for item in day_points
            ]

            if len(coordinates) >= 2:
                folium.PolyLine(
                    coordinates,
                    tooltip=f"Day {day} route"
                ).add_to(travel_map)

        st_folium(
            travel_map,
            width=None,
            height=600
        )

else:
    st.info(
        "👈 Choose your preferences and click "
        "**Generate My Trip**."
    )

st.caption(
    "TravelMate AI • Recommendation + Itinerary + Map"
)
