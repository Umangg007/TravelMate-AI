import requests
import pandas as pd
import streamlit as st
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
    layout="wide",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "api_error" not in st.session_state:
    st.session_state.api_error = None


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

@st.cache_data(ttl=300)
def get_supported_cities():
    response = requests.get(
        f"{API_BASE_URL}/cities",
        timeout=20,
    )
    response.raise_for_status()

    return response.json().get("cities", [])


def generate_trip(
    destination,
    query,
    days,
    top_n,
    preferences,
):
    payload = {
        "destination": destination,
        "query": query,
        "days": int(days),
        "top_n": int(top_n),
        "preferences": preferences,
    }

    recommendation_response = requests.post(
        f"{API_BASE_URL}/recommend",
        json=payload,
        timeout=120,
    )
    recommendation_response.raise_for_status()

    itinerary_response = requests.post(
        f"{API_BASE_URL}/itinerary",
        json=payload,
        timeout=120,
    )
    itinerary_response.raise_for_status()

    return {
        "destination": destination,
        "query": query,
        "recommendations":
            recommendation_response.json().get(
                "recommendations",
                [],
            ),
        "itinerary":
            itinerary_response.json().get(
                "itinerary",
                [],
            ),
    }


def format_rating(rating):
    try:
        return f"{float(rating):.1f}"
    except (TypeError, ValueError):
        return "N/A"


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.header("🧳 Trip Preferences")


try:
    cities = get_supported_cities()
except Exception as exc:
    cities = []
    st.sidebar.error(
        "❌ FastAPI is not available. "
        "Start it with: uvicorn app.main:app --reload"
    )


if cities:
    default_index = (
        cities.index("Manali")
        if "Manali" in cities
        else 0
    )

    destination = st.sidebar.selectbox(
        "Destination",
        cities,
        index=default_index,
    )
else:
    destination = st.sidebar.text_input(
        "Destination",
        value="Manali",
    )


days = st.sidebar.number_input(
    "Number of days",
    min_value=1,
    max_value=14,
    value=3,
    step=1,
)

top_n = st.sidebar.slider(
    "Number of recommendations",
    min_value=3,
    max_value=15,
    value=6,
)

st.sidebar.markdown("### ❤️ What do you like?")

nature = st.sidebar.slider(
    "🌿 Nature",
    0.0, 1.0, 0.8, 0.1
)

history = st.sidebar.slider(
    "🏛️ History",
    0.0, 1.0, 0.2, 0.1
)

culture = st.sidebar.slider(
    "🎭 Culture",
    0.0, 1.0, 0.3, 0.1
)

adventure = st.sidebar.slider(
    "🥾 Adventure",
    0.0, 1.0, 0.4, 0.1
)

photography = st.sidebar.slider(
    "📸 Photography",
    0.0, 1.0, 0.8, 0.1
)

shopping = st.sidebar.slider(
    "🛍️ Shopping",
    0.0, 1.0, 0.2, 0.1
)

religious = st.sidebar.slider(
    "🛕 Religious",
    0.0, 1.0, 0.1, 0.1
)

family = st.sidebar.slider(
    "👨‍👩‍👧 Family",
    0.0, 1.0, 0.4, 0.1
)


preferences = {
    "nature": nature,
    "history": history,
    "culture": culture,
    "adventure": adventure,
    "photography": photography,
    "shopping": shopping,
    "religious": religious,
    "family": family,
}


# ---------------------------------------------------------
# Main page
# ---------------------------------------------------------

st.title("🌍 TravelMate AI")

st.subheader(
    "Your personalized AI travel planner ✈️"
)

st.write(
    "Choose a destination, describe your trip, "
    "and TravelMate will recommend places and build "
    "a day-by-day itinerary."
)


query = st.text_area(
    "💬 Describe your trip",
    value=(
        "I want a peaceful scenic trip "
        "with beautiful places for photography."
    ),
    height=110,
)


generate = st.button(
    "✨ Generate My Trip",
    type="primary",
    width="stretch",
)


if generate:

    try:
        with st.spinner(
            "🤖 TravelMate is creating your trip..."
        ):

            st.session_state.trip_result = (
                generate_trip(
                    destination=destination,
                    query=query,
                    days=days,
                    top_n=top_n,
                    preferences=preferences,
                )
            )

        st.session_state.api_error = None

    except requests.exceptions.ConnectionError:

        st.session_state.trip_result = None

        st.session_state.api_error = (
            "❌ Cannot connect to FastAPI. "
            "Run `uvicorn app.main:app --reload` first."
        )

    except requests.exceptions.Timeout:

        st.session_state.trip_result = None

        st.session_state.api_error = (
            "⏳ The AI backend took too long to respond."
        )

    except requests.exceptions.HTTPError as exc:

        st.session_state.trip_result = None

        detail = str(exc)

        try:
            detail = exc.response.json().get(
                "detail",
                detail,
            )
        except Exception:
            pass

        st.session_state.api_error = (
            f"❌ API error: {detail}"
        )

    except Exception as exc:

        st.session_state.trip_result = None

        st.session_state.api_error = (
            f"❌ Unexpected error: {exc}"
        )


# ---------------------------------------------------------
# Error display
# ---------------------------------------------------------

if st.session_state.api_error:
    st.error(
        st.session_state.api_error
    )


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

result = st.session_state.trip_result

if result:

    st.success(
        f"✅ Trip generated for "
        f"{result['destination']}"
    )

    recommendations = result[
        "recommendations"
    ]

    itinerary = result["itinerary"]


    # -----------------------------------------------------
    # Recommendations
    # -----------------------------------------------------

    st.header("🎯 Recommended Places")

    if recommendations:

        rec_df = pd.DataFrame(
            recommendations
        )

        for column in [
            "final_score",
            "semantic_score",
            "tfidf_score",
            "structured_score",
        ]:
            if column in rec_df.columns:
                rec_df[column] = rec_df[column].round(4)

        display_columns = [
            "name",
            "activity_type",
            "rating",
            "reviews",
            "estimated_visit_minutes",
            "final_score",
        ]

        available = [
            column
            for column in display_columns
            if column in rec_df.columns
        ]

        st.dataframe(
            rec_df[available],
            width="stretch",
            hide_index=True,
        )

        # Top place cards
        st.subheader("⭐ Top Picks")

        card_columns = st.columns(
            min(3, len(rec_df))
        )

        for column, (_, row) in zip(
            card_columns,
            rec_df.head(3).iterrows(),
        ):

            with column:

                st.markdown(
                    f"### 📍 {row['name']}"
                )

                st.write(
                    f"⭐ Rating: "
                    f"{format_rating(row.get('rating'))}"
                )

                st.write(
                    f"📝 Reviews: "
                    f"{int(row.get('reviews', 0)):,}"
                )

                if "activity_type" in row:
                    st.write(
                        f"🎯 Activity: "
                        f"{row['activity_type']}"
                    )

                if "final_score" in row:
                    st.write(
                        f"🤖 AI Score: "
                        f"{float(row['final_score']):.3f}"
                    )

    else:

        st.warning(
            "No recommendations were returned."
        )


    # -----------------------------------------------------
    # Itinerary
    # -----------------------------------------------------

    st.header("📅 Your Personalized Itinerary")

    if itinerary:

        itinerary_df = pd.DataFrame(
            itinerary
        )

        # Summary metrics
        total_visit_minutes = int(
            itinerary_df[
                "visit_minutes"
            ].sum()
        )

        total_travel_minutes = float(
            itinerary_df[
                "travel_before_minutes"
            ].sum()
        )

        scheduled_stops = len(
            itinerary_df
        )

        metric_cols = st.columns(3)

        metric_cols[0].metric(
            "📍 Stops",
            scheduled_stops,
        )

        metric_cols[1].metric(
            "⏱️ Visit Time",
            f"{total_visit_minutes} min",
        )

        metric_cols[2].metric(
            "🚗 Travel Time",
            f"{total_travel_minutes:.1f} min",
        )


        for day in sorted(
            itinerary_df["day"].unique()
        ):

            day_df = (
                itinerary_df[
                    itinerary_df["day"] == day
                ]
                .sort_values("stop")
            )

            st.subheader(
                f"📍 Day {int(day)}"
            )

            for _, row in day_df.iterrows():

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### Stop {int(row['stop'])} "
                        f"• {row['place']}"
                    )

                    left, right = st.columns(2)

                    with left:
                        st.write(
                            f"🕘 "
                            f"{row['arrival']} → "
                            f"{row['departure']}"
                        )

                        st.write(
                            f"🎯 "
                            f"{row['activity_type']}"
                        )

                    with right:
                        st.write(
                            f"⏱️ Visit: "
                            f"{int(row['visit_minutes'])} min"
                        )

                        st.write(
                            f"🚗 Travel before: "
                            f"{float(row['travel_before_minutes']):.1f} min"
                        )

            st.divider()

    else:

        st.warning(
            "No itinerary could be generated."
        )


    # -----------------------------------------------------
    # Map
    # -----------------------------------------------------

    st.header("🗺️ Interactive Trip Map")

    map_points = [
        item
        for item in itinerary
        if item.get("latitude") is not None
        and item.get("longitude") is not None
    ]

    if map_points:

        center_lat = sum(
            item["latitude"]
            for item in map_points
        ) / len(map_points)

        center_lon = sum(
            item["longitude"]
            for item in map_points
        ) / len(map_points)

        travel_map = folium.Map(
            location=[
                center_lat,
                center_lon,
            ],
            zoom_start=12,
        )

        for item in map_points:

            popup_html = (
                f"<b>Day {item['day']} "
                f"• Stop {item['stop']}</b><br>"
                f"{item['place']}<br>"
                f"{item['arrival']} - "
                f"{item['departure']}"
            )

            folium.Marker(
                location=[
                    item["latitude"],
                    item["longitude"],
                ],
                popup=popup_html,
                tooltip=item["place"],
            ).add_to(travel_map)

        # Draw a separate line for each day.
        for day in sorted(
            {
                item["day"]
                for item in map_points
            }
        ):

            day_points = sorted(
                [
                    item
                    for item in map_points
                    if item["day"] == day
                ],
                key=lambda item: item["stop"],
            )

            coordinates = [
                [
                    item["latitude"],
                    item["longitude"],
                ]
                for item in day_points
            ]

            if len(coordinates) >= 2:

                folium.PolyLine(
                    coordinates,
                    tooltip=f"Day {day} route",
                ).add_to(travel_map)

        st_folium(
            travel_map,
            height=600,
            width=None,
        )

    else:

        st.info(
            "Map coordinates are unavailable "
            "for this itinerary."
        )


else:

    st.info(
        "👈 Choose your destination and "
        "preferences, then click "
        "**Generate My Trip**."
    )


st.caption(
    "TravelMate AI • Hybrid Recommendation "
    "• Itinerary Optimization • Interactive Map"
)
