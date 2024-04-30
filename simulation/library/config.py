# Config environment
h3_res = 7
min_res = 5
max_res = 8

# Config hexagons
# Define bounding box coordinates
min_lat, min_lon = -2.984188,  51.269558
max_lat, max_lon = -2.416278, 51.56
geo_json_polygon = {
    "type": "Polygon",
    "coordinates": [
        [
            [min_lon, min_lat],
            [min_lon, max_lat],
            [max_lon, max_lat],
            [max_lon, min_lat],
            [min_lon, min_lat]
        ]
    ]
}


simulation_res = 7

user_count = 4671
miles_per_day = 18
miles_per_charge = 211

user_per_day = int(user_count*miles_per_day/miles_per_charge)