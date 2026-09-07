import os

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium


# ---------------- API Configuration ----------------

try:
    API_BASE_URL = st.secrets.get(
        "API_BASE_URL",
        os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
    )
except Exception:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


# ---------------- Page Configuration ----------------

st.set_page_config(
    page_title="TravelMate AI",
    page_icon="🌍",
    layout="wide",
)


# ---------------- Session State ----------------

if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

if "api_error" not in st.session_state:
    st.session_state.api_error = None


# ---------------- API Functions ----------------

@st.cache_data(ttl=300)
def get_supported_cities():
    response = requests.get(
        f"{API_BASE_URL}/cities",
        timeout=20,
    )
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
        "recommendations": recommendation_response.json().get(
            "recommendations",
            [],
        ),
        "itinerary": itinerary_response.json().get(
            "itinerary",
            [],
        ),
    }


# ---------------- Helper Functions ----------------

def format_rating(rating):
    try:
        return f"{float(rating):.1f}"
    except (TypeError, ValueError):
        return "N/A"


def marker_color(day):
    palette = [
        "#E74C3C",  # Red
        "#3498DB",  # Blue
        "#27AE60",  # Green
        "#8E44AD",  # Purple
        "#F39C12",  # Orange
        "#16A085",  # Teal
        "#D35400",  # Dark Orange
    ]

    return palette[(int(day) - 1) % len(palette)]


def add_trip_marker(travel_map, item):
    """
    Create a clean numbered marker without external Leaflet PNG assets.
    """

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
    ">
        {stop}
    </div>
    """

    popup_html = f"""
    <div style="
        min-width:180px;
        font-family:Arial,sans-serif;
    ">

        <div style="
            font-size:14px;
            font-weight:700;
            margin-bottom:5px;
        ">
            📍 {item["place"]}
        </div>

        <div>
            <b>Day:</b> {day}
        </div>

        <div>
            <b>Stop:</b> {stop}
        </div>

        <div>
            <b>Time:</b> {item["arrival"]} - {item["departure"]}
        </div>

        <div>
            <b>Activity:</b> {item["activity_type"]}
        </div>

    </div>
    """

    folium.Marker(
        location=[
            float(item["latitude"]),
            float(item["longitude"]),
        ],
        icon=folium.DivIcon(
            html=marker_html,
            icon_size=(40, 40),
            icon_anchor=(20, 20),
            class_name="travelmate-custom-marker",
        ),
        popup=folium.Popup(
            popup_html,
            max_width=300,
        ),
        tooltip=(
            f"Day {day} • "
            f"Stop {stop} • "
            f"{item['place']}"
        ),
    ).add_to(travel_map)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("🧳 Trip Preferences")


# ---------------- Cities ----------------

try:
    cities = get_supported_cities()

except Exception:
    cities = []

    st.sidebar.error(
        "❌ Cannot connect to the TravelMate API."
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


# ---------------- Trip Settings ----------------

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


# ---------------- Preferences ----------------

st.sidebar.markdown("### ❤️ What do you like?")

nature = st.sidebar.slider(
    "🌿 Nature",
    0.0,
    1.0,
    0.8,
    0.1,
)

history = st.sidebar.slider(
    "🏛️ History",
    0.0,
    1.0,
    0.2,
    0.1,
)

culture = st.sidebar.slider(
    "🎭 Culture",
    0.0,
    1.0,
    0.3,
    0.1,
)

adventure = st.sidebar.slider(
    "🥾 Adventure",
    0.0,
    1.0,
    0.4,
    0.1,
)

photography = st.sidebar.slider(
    "📸 Photography",
    0.0,
    1.0,
    0.8,
    0.1,
)

shopping = st.sidebar.slider(
    "🛍️ Shopping",
    0.0,
    1.0,
    0.2,
    0.1,
)

religious = st.sidebar.slider(
    "🛕 Religious",
    0.0,
    1.0,
    0.1,
    0.1,
)

family = st.sidebar.slider(
    "👨‍👩‍👧 Family",
    0.0,
    1.0,
    0.4,
    0.1,
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


# =========================================================
# MAIN PAGE
# =========================================================

st.title("🌍 TravelMate AI")

st.subheader(
    "Your personalized AI travel planner ✈️"
)

st.write(
    "Choose a destination, describe your trip, "
    "and TravelMate will recommend places and "
    "build a day-by-day itinerary."
)


# ---------------- Trip Query ----------------

query = st.text_area(
    "💬 Describe your trip",
    value=(
        "I want a peaceful scenic trip "
        "with beautiful places for photography."
    ),
    height=110,
)


# ---------------- Generate Button ----------------

generate = st.button(
    "✨ Generate My Trip",
    type="primary",
    width="stretch",
)


# =========================================================
# GENERATE TRIP
# =========================================================

if generate:

    try:

        with st.spinner(
            "🤖 TravelMate is creating your trip..."
        ):

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

        st.session_state.api_error = (
            "❌ Cannot connect to the TravelMate API."
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


# =========================================================
# ERROR MESSAGE
# =========================================================

if st.session_state.api_error:

    st.error(
        st.session_state.api_error
    )


# =========================================================
# RESULT
# =========================================================

result = st.session_state.trip_result


if result:

    st.success(
        f"✅ Trip generated for {result['destination']}"
    )

    recommendations = result["recommendations"]

    itinerary = result["itinerary"]


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.header("🎯 Recommended Places")


    if recommendations:

        rec_df = pd.DataFrame(
            recommendations
        )


        # ---------------- Round Scores ----------------

        for column in [
            "final_score",
            "semantic_score",
            "tfidf_score",
            "structured_score",
        ]:

            if column in rec_df.columns:

                rec_df[column] = rec_df[
                    column
                ].round(4)


        # ---------------- Table ----------------

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


        # =================================================
        # TOP PICKS
        # =================================================

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


    # =====================================================
    # ITINERARY
    # =====================================================

    st.header(
        "📅 Your Personalized Itinerary"
    )


    if itinerary:

        itinerary_df = pd.DataFrame(
            itinerary
        )


        # ---------------- Metrics ----------------

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


        # ---------------- Day-by-Day Itinerary ----------------

        for day in sorted(
            itinerary_df["day"].unique()
        ):

            day_df = itinerary_df[
                itinerary_df["day"] == day
            ].sort_values("stop")


            st.subheader(
                f"📍 Day {int(day)}"
            )


            for _, row in day_df.iterrows():

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### Stop "
                        f"{int(row['stop'])} • "
                        f"{row['place']}"
                    )


                    left, right = st.columns(2)


                    with left:

                        st.write(
                            f"🕘 "
                            f"{row['arrival']} "
                            f"→ "
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


    # =====================================================
    # INTERACTIVE MAP
    # =====================================================

    st.header(
        "🗺️ Interactive Trip Map"
    )


    # ---------------- Map Points ----------------

    map_points = [
        item
        for item in itinerary
        if item.get("latitude") is not None
        and item.get("longitude") is not None
    ]


    if map_points:

        # ---------------- Map Center ----------------

        center_lat = (
            sum(
                float(item["latitude"])
                for item in map_points
            )
            / len(map_points)
        )


        center_lon = (
            sum(
                float(item["longitude"])
                for item in map_points
            )
            / len(map_points)
        )


        # ---------------- Create Map ----------------

        travel_map = folium.Map(
            location=[
                center_lat,
                center_lon,
            ],
            zoom_start=12,
            control_scale=True,
        )


        # =================================================
        # CUSTOM NUMBERED MARKERS
        # =================================================

        for item in map_points:

            add_trip_marker(
                travel_map,
                item,
            )


        # =================================================
        # ROUTE LINE FOR EACH DAY
        # =================================================

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
                    float(item["latitude"]),
                    float(item["longitude"]),
                ]
                for item in day_points
            ]


            if len(coordinates) >= 2:

                folium.PolyLine(
                    coordinates,
                    tooltip=f"Day {day} route",
                ).add_to(travel_map)


        # =================================================
        # DAY LEGEND
        # =================================================

        # FIX:
        # Create legend_items before using it.
        #
        # This prevents:
        # NameError: name 'legend_items' is not defined

        legend_items = sorted(
            {
                int(item["day"])
                for item in map_points
                if item.get("day") is not None
            }
        )


        # ---------------- Legend HTML ----------------

        legend_html = """
        <div style="
            position: fixed;
            bottom: 25px;
            left: 25px;

            z-index: 99999;

            background-color: #ffffff !important;
            color: #111111 !important;

            padding: 14px 18px;

            border: 2px solid #777777;
            border-radius: 10px;

            box-shadow:
                0 4px 12px
                rgba(0,0,0,0.35);

            font-family: Arial, sans-serif;

            font-size: 15px;

            min-width: 120px;

            opacity: 1 !important;
        ">

            <div style="
                font-weight: 700;

                font-size: 16px;

                margin-bottom: 8px;

                color: #111111 !important;

                opacity: 1 !important;
            ">
                🗺️ Trip Days
            </div>
        """


        # ---------------- Add Days ----------------

        for day in legend_items:

            legend_html += f"""
            <div style="
                display: flex;

                align-items: center;

                margin-top: 8px;

                color: #111111 !important;

                font-weight: 600;

                opacity: 1 !important;
            ">

                <span style="
                    display: inline-block;

                    width: 14px;
                    height: 14px;

                    border-radius: 50%;

                    background: {marker_color(day)}
                        !important;

                    margin-right: 9px;

                    border: 2px solid #ffffff;

                    box-shadow:
                        0 1px 3px
                        rgba(0,0,0,0.4);
                "></span>


                <span style="
                    color: #111111 !important;

                    opacity: 1 !important;
                ">
                    Day {day}
                </span>

            </div>
            """


        # ---------------- Close Legend ----------------

        legend_html += "</div>"


        # ---------------- Add Legend to Map ----------------

        travel_map.get_root().html.add_child(
            folium.Element(
                legend_html
            )
        )


        # ---------------- Display Map ----------------

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


# =========================================================
# INITIAL MESSAGE
# =========================================================

else:

    st.info(
        "👈 Choose your destination and "
        "preferences, then click "
        "**Generate My Trip**."
    )


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "TravelMate AI • "
    "Personalized Hybrid Recommendation • "
    "Itinerary Optimization • "
    "Interactive Map"
)