import os

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

try:
    API_BASE_URL = st.secrets.get(
        "API_BASE_URL",
        os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
    )
except Exception:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="TravelMate AI", page_icon="🌍", layout="wide")

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None


@st.cache_data(ttl=300)
def get_supported_cities():
    response = requests.get(f"{API_BASE_URL}/cities", timeout=20)
    response.raise_for_status()
    return response.json().get("cities", [])


def generate_trip(destination, query, days, top_n, preferences):
    payload = {
        "destination": destination,
        "query": query,
        "days": int(days),
        "top_n": int(top_n),
        "preferences": preferences,
    }

    recommendation_response = requests.post(
        f"{API_BASE_URL}/recommend", json=payload, timeout=120
    )
    recommendation_response.raise_for_status()

    itinerary_response = requests.post(
        f"{API_BASE_URL}/itinerary", json=payload, timeout=120
    )
    itinerary_response.raise_for_status()

    return {
        "destination": destination,
        "query": query,
        "recommendations": recommendation_response.json().get("recommendations", []),
        "itinerary": itinerary_response.json().get("itinerary", []),
    }


def format_rating(rating):
    try:
        return f"{float(rating):.1f}"
    except (TypeError, ValueError):
        return "N/A"


def marker_color(day):
    palette = [
        "#E74C3C",
        "#3498DB",
        "#27AE60",
        "#8E44AD",
        "#F39C12",
        "#16A085",
        "#D35400",
    ]
    return palette[(int(day) - 1) % len(palette)]


def add_trip_marker(travel_map, item):
    """Create a clean numbered marker without external Leaflet PNG assets."""
    day = int(item["day"])
    stop = int(item["stop"])
    color = marker_color(day)

    marker_html = f"""
    <div style="
        width:34px;
        height:34px;
        border-radius:50%;
        background:{color};
        border:3px solid white;
        box-shadow:0 2px 7px rgba(0,0,0,.35);
        display:flex;
        align-items:center;
        justify-content:center;
        color:white;
        font-size:15px;
        font-weight:700;
        font-family:Arial,sans-serif;
    ">{stop}</div>
    """

    popup_html = f"""
    <div style="min-width:180px;font-family:Arial,sans-serif;">
        <div style="font-size:14px;font-weight:700;margin-bottom:5px;">
            📍 {item["place"]}
        </div>
        <div><b>Day:</b> {day}</div>
        <div><b>Stop:</b> {stop}</div>
        <div><b>Time:</b> {item["arrival"]} - {item["departure"]}</div>
        <div><b>Activity:</b> {item["activity_type"]}</div>
    </div>
    """

    folium.Marker(
        location=[float(item["latitude"]), float(item["longitude"])],
        icon=folium.DivIcon(
            html=marker_html,
            icon_size=(40, 40),
            icon_anchor=(20, 20),
            class_name="travelmate-custom-marker",
        ),
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Day {day} • Stop {stop} • {item['place']}",
    ).add_to(travel_map)


# ---------------- Sidebar ----------------
st.sidebar.header("🧳 Trip Preferences")

try:
    cities = get_supported_cities()
except Exception:
    cities = []
    st.sidebar.error("❌ Cannot connect to the TravelMate API.")

if cities:
    default_index = cities.index("Manali") if "Manali" in cities else 0
    destination = st.sidebar.selectbox("Destination", cities, index=default_index)
else:
    destination = st.sidebar.text_input("Destination", value="Manali")

days = st.sidebar.number_input("Number of days", min_value=1, max_value=14, value=3, step=1)
top_n = st.sidebar.slider("Number of recommendations", min_value=3, max_value=15, value=6)

st.sidebar.markdown("### ❤️ What do you like?")
nature = st.sidebar.slider("🌿 Nature", 0.0, 1.0, 0.8, 0.1)
history = st.sidebar.slider("🏛️ History", 0.0, 1.0, 0.2, 0.1)
culture = st.sidebar.slider("🎭 Culture", 0.0, 1.0, 0.3, 0.1)
adventure = st.sidebar.slider("🥾 Adventure", 0.0, 1.0, 0.4, 0.1)
photography = st.sidebar.slider("📸 Photography", 0.0, 1.0, 0.8, 0.1)
shopping = st.sidebar.slider("🛍️ Shopping", 0.0, 1.0, 0.2, 0.1)
religious = st.sidebar.slider("🛕 Religious", 0.0, 1.0, 0.1, 0.1)
family = st.sidebar.slider("👨‍👩‍👧 Family", 0.0, 1.0, 0.4, 0.1)

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

# ---------------- Main page ----------------
st.title("🌍 TravelMate AI")
st.subheader("Your personalized AI travel planner ✈️")
st.write(
    "Choose a destination, describe your trip, and TravelMate will recommend "
    "places and build a day-by-day itinerary."
)

query = st.text_area(
    "💬 Describe your trip",
    value="I want a peaceful scenic trip with beautiful places for photography.",
    height=110,
)

generate = st.button("✨ Generate My Trip", type="primary", width="stretch")

if generate:
    try:
        with st.spinner("🤖 TravelMate is creating your trip..."):
            st.session_state.trip_result = generate_trip(
                destination=destination,
                query=query,
                days=days,
                top_n=top_n,
                preferences=preferences,
            )
        st.session_state.api_error = None
    except requests.exceptions.ConnectionError:
        st.session_state.trip_result = None
        st.session_state.api_error = "❌ Cannot connect to the TravelMate API."
    except requests.exceptions.Timeout:
        st.session_state.trip_result = None
        st.session_state.api_error = "⏳ The AI backend took too long to respond."
    except requests.exceptions.HTTPError as exc:
        st.session_state.trip_result = None
        detail = str(exc)
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        st.session_state.api_error = f"❌ API error: {detail}"
    except Exception as exc:
        st.session_state.trip_result = None
        st.session_state.api_error = f"❌ Unexpected error: {exc}"

if st.session_state.api_error:
    st.error(st.session_state.api_error)

result = st.session_state.trip_result

if result:
    st.success(f"✅ Trip generated for {result['destination']}")
    recommendations = result["recommendations"]
    itinerary = result["itinerary"]

    # ---------------- Recommendations ----------------
    st.header("🎯 Recommended Places")
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        for column in ["final_score", "semantic_score", "tfidf_score", "structured_score"]:
            if column in rec_df.columns:
                rec_df[column] = rec_df[column].round(4)

        display_columns = [
            "name", "activity_type", "rating", "reviews",
            "estimated_visit_minutes", "final_score",
        ]
        available = [c for c in display_columns if c in rec_df.columns]
        st.dataframe(rec_df[available], width="stretch", hide_index=True)

        st.subheader("⭐ Top Picks")
        card_columns = st.columns(min(3, len(rec_df)))
        for column, (_, row) in zip(card_columns, rec_df.head(3).iterrows()):
            with column:
                st.markdown(f"### 📍 {row['name']}")
                st.write(f"⭐ Rating: {format_rating(row.get('rating'))}")
                st.write(f"📝 Reviews: {int(row.get('reviews', 0)):,}")
                if "activity_type" in row:
                    st.write(f"🎯 Activity: {row['activity_type']}")
                if "final_score" in row:
                    st.write(f"🤖 AI Score: {float(row['final_score']):.3f}")
    else:
        st.warning("No recommendations were returned.")

    # ---------------- Itinerary ----------------
    st.header("📅 Your Personalized Itinerary")
    if itinerary:
        itinerary_df = pd.DataFrame(itinerary)
        total_visit_minutes = int(itinerary_df["visit_minutes"].sum())
        total_travel_minutes = float(itinerary_df["travel_before_minutes"].sum())
        scheduled_stops = len(itinerary_df)

        metric_cols = st.columns(3)
        metric_cols[0].metric("📍 Stops", scheduled_stops)
        metric_cols[1].metric("⏱️ Visit Time", f"{total_visit_minutes} min")
        metric_cols[2].metric("🚗 Travel Time", f"{total_travel_minutes:.1f} min")

        for day in sorted(itinerary_df["day"].unique()):
            day_df = itinerary_df[itinerary_df["day"] == day].sort_values("stop")
            st.subheader(f"📍 Day {int(day)}")
            for _, row in day_df.iterrows():
                with st.container(border=True):
                    st.markdown(f"### Stop {int(row['stop'])} • {row['place']}")
                    left, right = st.columns(2)
                    with left:
                        st.write(f"🕘 {row['arrival']} → {row['departure']}")
                        st.write(f"🎯 {row['activity_type']}")
                    with right:
                        st.write(f"⏱️ Visit: {int(row['visit_minutes'])} min")
                        st.write(
                            f"🚗 Travel before: "
                            f"{float(row['travel_before_minutes']):.1f} min"
                        )
            st.divider()
    else:
        st.warning("No itinerary could be generated.")

    # ---------------- Map ----------------
    st.header("🗺️ Interactive Trip Map")
    map_points = [
        item for item in itinerary
        if item.get("latitude") is not None and item.get("longitude") is not None
    ]

    if map_points:
        center_lat = sum(float(item["latitude"]) for item in map_points) / len(map_points)
        center_lon = sum(float(item["longitude"]) for item in map_points) / len(map_points)

        travel_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            control_scale=True,
        )

        # Custom numbered DivIcon markers: no broken default Leaflet PNG icon.
        for item in map_points:
            add_trip_marker(travel_map, item)

        # Route line for each day.
        for day in sorted({item["day"] for item in map_points}):
            day_points = sorted(
                [item for item in map_points if item["day"] == day],
                key=lambda item: item["stop"],
            )
            coordinates = [
                [float(item["latitude"]), float(item["longitude"])]
                for item in day_points
            ]
            if len(coordinates) >= 2:
                folium.PolyLine(
                    coordinates,
                    tooltip=f"Day {day} route",
                ).add_to(travel_map)

        # Day legend.
        legend_html = """
        <div style="
            position:fixed;
            bottom:25px;
            left:25px;
            z-index:9999;
            background:white;
            padding:10px 12px;
            border:1px solid #ccc;
            border-radius:8px;
            box-shadow:0 2px 7px rgba(0,0,0,.20);
            font-family:Arial,sans-serif;
            font-size:13px;
        "><b>Trip Days</b><br>
        """
        for day in sorted({int(item["day"]) for item in map_points}):
            legend_html += f"""
            <div style="margin-top:5px;">
                <span style="display:inline-block;width:12px;height:12px;"
                      "border-radius:50%;background:{marker_color(day)};"
                      "margin-right:6px;"></span>
                Day {day}
            </div>
            """
        legend_html += "</div>"
        travel_map.get_root().html.add_child(folium.Element(legend_html))

        st_folium(travel_map, height=600, width=None)
    else:
        st.info("Map coordinates are unavailable for this itinerary.")
else:
    st.info("👈 Choose your destination and preferences, then click **Generate My Trip**.")

st.caption(
    "TravelMate AI • Personalized Hybrid Recommendation • "
    "Itinerary Optimization • Interactive Map"
)
