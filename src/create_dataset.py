import json
import pandas as pd


def load_raw_data(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def extract_places(data):

    places = []

    for place in data.get("local_results", []):

        gps = place.get(
            "gps_coordinates",
            {}
        )

        places.append({

            "place_id":
                place.get("place_id"),

            "name":
                place.get("title"),

            "address":
                place.get("address"),

            "country":
                place.get("country"),

            "latitude":
                gps.get("latitude"),

            "longitude":
                gps.get("longitude"),

            "rating":
                place.get("rating"),

            "reviews":
                place.get("reviews"),

            "category":
                place.get("type")

        })

    return places


if __name__ == "__main__":

    file_path = (
        "data/raw/manali_places.json"
    )

    data = load_raw_data(file_path)

    places = extract_places(data)

    df = pd.DataFrame(places)

    print("\nDataset Preview:\n")

    print(df.head())

    print("\nDataset Shape:")
    print(df.shape)

    print("\nMissing Values:")
    print(df.isnull().sum())

    df.to_csv(
        "data/processed/manali_places.csv",
        index=False
    )

    print(
        "\n✅ Dataset saved successfully!"
    )