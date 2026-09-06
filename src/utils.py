
def validate_city_output(result, requested_city):
    if result.empty:
        return False

    return (
        result["city"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(requested_city.strip().lower())
        .all()
    )

def validate_daily_budget(result, max_day_minutes):
    if result.empty:
        return True

    totals = (
        result
        .assign(
            total_minutes=lambda x:
                x["travel_before_minutes"] + x["visit_minutes"]
        )
        .groupby(["city", "day"])["total_minutes"]
        .sum()
    )

    return bool(
        (totals <= max_day_minutes + 1e-9).all()
    )
