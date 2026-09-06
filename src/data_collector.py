import os
import json
import serpapi

from dotenv import load_dotenv


class TravelDataCollector:

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("SERPAPI_KEY")

        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY is not found in .env"
            )

        self.client = serpapi.Client(
            api_key=self.api_key
        )

    def search_places(self, city):

        query = f"tourist attractions in {city}"

        print(f"Searching for: {query}")

        result = self.client.search({
            "engine": "google_maps",
            "q": query
        })

        return result

    def save_raw_data(self, result, city):

        os.makedirs("data/raw", exist_ok=True)

        file_path = (
            f"data/raw/{city.lower()}_places.json"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                dict(result),
                file,
                indent=4,
                ensure_ascii=False
            )

        print(f"✅ Raw data saved to: {file_path}")


if __name__ == "__main__":

    collector = TravelDataCollector()

    city = "goa"

    result = collector.search_places(city)

    collector.save_raw_data(
        result,
        city
    )