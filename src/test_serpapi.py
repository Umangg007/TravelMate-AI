# # import os
# # import serpapi 
# # from dotenv import load_dotenv

# # load_dotenv()

# # api_key = os.getenv("SERPAPI_KEY")

# # if not api_key:
# #     raise ValueError("SERPAPI is not found in .env")

# # client = serpapi.Client(api_key=api_key)

# # result = client.search({
# #     "engine": "google",
# #     "q": "tourist places in Manali"
# # })

# # print("Search successful !")

# # for i in result.get("organic_results", [])[:5]:
# #     print(i.get("title"))
    
# # print("\nAvailable response keys:")
# # print(result.keys())

# # print("\nTourist places:\n")

# # for place in result.get("local_results", [])[:10]:

# #     print("Name:", place.get("title"))
# #     print("Rating:", place.get("rating"))
# #     # print("Reviews:", place.get("reviews"))
# #     # print("Address:", place.get("address"))
# #     # print("Category:", place.get("type"))
# #     # print("Latitude:", place.get("gps_coordinates", {}).get("latitude"))
# #     # print("Longitude:", place.get("gps_coordinates",{}).get("longitude"))
# #     # print("-" * 50)

# import os
# import serpapi
# from dotenv import load_dotenv

# load_dotenv()

# api_key = os.getenv("SERPAPI_KEY")

# if not api_key:
#     raise ValueError("SERPAPI_KEY is not found in .env")

# client = serpapi.Client(api_key=api_key)

# result = client.search({
#     "engine": "google_maps",
#     "q": "I want to goa with girlfriend"
# })

# print("Google Maps search successful! ✅")

# print("\nAvailable response keys:")
# print(result.keys())

# print("\nTourist places:\n")

# for place in result.get("local_results", [])[:10]:

#     print("Name:", place.get("title"))
#     print("Rating:", place.get("rating"))
#     print("Reviews:", place.get("reviews"))
#     print("Address:", place.get("address"))
#     print("Category:", place.get("type"))
#     print("Latitude:", place.get("gps_coordinates", {}).get("latitude"))
#     print("Longitude:", place.get("gps_coordinates", {}).get("longitude"))
#     print("-" * 50)
import os
import serpapi
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SERPAPI_KEY")

if not api_key:
    raise ValueError("SERPAPI_KEY is not found in .env")

client = serpapi.Client(api_key=api_key)

result = client.search({
    "engine": "google_maps",
    "q": "tourist attractions in Manali"
})

print("Google Maps search successful! ✅")
print("\nQuery:")
print(result.get("search_parameters", {}).get("q"))

print("\nTourist places:\n")

for place in result.get("local_results", []):

    print("Name:", place.get("title"))
    print("Place ID:", place.get("place_id"))
    print("Address:", place.get("address"))
    print("Country:", place.get("country"))

    gps = place.get("gps_coordinates", {})

    print("Latitude:", gps.get("latitude"))
    print("Longitude:", gps.get("longitude"))

    print("Rating:", place.get("rating"))
    print("Reviews:", place.get("reviews"))

    print("-" * 50)