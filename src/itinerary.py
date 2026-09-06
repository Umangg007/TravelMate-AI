
import math
import numpy as np
import pandas as pd

DEFAULT_SPEED_KMPH = 25.0
DEFAULT_DAY_START_MINUTES = 9 * 60
DEFAULT_MAX_DAY_MINUTES = 7 * 60

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = lat2 - lat1, lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

def format_time(minutes):
    minutes = int(round(minutes))
    hour = (minutes // 60) % 24
    minute = minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    return f"{display_hour}:{minute:02d} {suffix}"

def build_travel_time_matrix(
    candidates,
    average_speed_kmph=DEFAULT_SPEED_KMPH
):
    if average_speed_kmph <= 0:
        raise ValueError("average_speed_kmph must be > 0.")

    n = len(candidates)
    matrix = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            distance = haversine_km(
                candidates.iloc[i]["latitude"],
                candidates.iloc[i]["longitude"],
                candidates.iloc[j]["latitude"],
                candidates.iloc[j]["longitude"]
            )
            matrix[i, j] = distance / average_speed_kmph * 60

    return matrix

def generate_itinerary(
    candidates,
    days=3,
    max_day_minutes=DEFAULT_MAX_DAY_MINUTES,
    average_speed_kmph=DEFAULT_SPEED_KMPH,
    day_start_minutes=DEFAULT_DAY_START_MINUTES
):
    required = {
        "city", "name", "latitude", "longitude",
        "activity_type", "estimated_visit_minutes",
        "estimated_price_level", "final_score"
    }

    missing = sorted(required - set(candidates.columns))
    if missing:
        raise ValueError(f"Missing itinerary columns: {missing}")

    if days < 1 or max_day_minutes <= 0:
        raise ValueError("days and max_day_minutes must be positive.")

    candidates = candidates.copy().reset_index(drop=True)

    if candidates.empty:
        return pd.DataFrame()

    matrix = build_travel_time_matrix(
        candidates,
        average_speed_kmph
    )

    remaining = set(range(len(candidates)))
    rows = []

    for day in range(1, days + 1):
        if not remaining:
            break

        current = max(
            remaining,
            key=lambda idx: float(
                candidates.iloc[idx]["final_score"]
            )
        )

        used = 0.0
        stop = 1

        while remaining:
            feasible = []

            for idx in remaining:
                travel = (
                    0.0
                    if used == 0
                    else matrix[current, idx]
                )

                visit = float(
                    candidates.iloc[idx]["estimated_visit_minutes"]
                )

                total = used + travel + visit

                if total <= max_day_minutes + 1e-9:
                    score = float(
                        candidates.iloc[idx]["final_score"]
                    )
                    efficiency = score / (1.0 + travel)
                    feasible.append(
                        (idx, travel, visit, efficiency)
                    )

            if not feasible:
                break

            idx, travel, visit, _ = max(
                feasible,
                key=lambda item: item[3]
            )

            arrival = day_start_minutes + used + travel
            departure = arrival + visit

            rows.append({
                "city": candidates.iloc[idx]["city"],
                "day": day,
                "stop": stop,
                "place": candidates.iloc[idx]["name"],
                "activity_type": candidates.iloc[idx]["activity_type"],
                "arrival": format_time(arrival),
                "departure": format_time(departure),
                "travel_before_minutes": round(travel, 2),
                "visit_minutes": int(round(visit)),
                "estimated_price_level": int(
                    round(candidates.iloc[idx]["estimated_price_level"])
                ),
                "final_score": round(
                    float(candidates.iloc[idx]["final_score"]),
                    4
                ),
                "latitude": float(candidates.iloc[idx]["latitude"]),
                "longitude": float(candidates.iloc[idx]["longitude"]),
            })

            used += travel + visit
            current = idx
            remaining.remove(idx)
            stop += 1

    result = pd.DataFrame(rows)

    if not result.empty:
        totals = (
            result
            .assign(
                total_minutes=lambda x:
                    x["travel_before_minutes"] + x["visit_minutes"]
            )
            .groupby(["city", "day"])["total_minutes"]
            .sum()
        )

        if (totals > max_day_minutes + 1e-9).any():
            raise RuntimeError(
                "Generated itinerary violates daily budget."
            )

    return result
