import json
import os
from RaceTreeFunctions2_1 import (
    fetch_json, save_json, calculate_race_start, get_total_laps,
    build_starting_grid, create_lap_files, convert_time
)

# ---------------------------- USER INPUT ----------------------------
Session_ID = input("Enter Session ID: ")
print("Session ID =", Session_ID)

# ---------------------------- BASE URLS ----------------------------
base_url = "https://eventresults-api.speedhive.com/api/v0.2.3/eventresults/sessions/"
my_session_url = base_url + Session_ID
my_classification_url = f"{base_url}{Session_ID}/classification"
laps_base_url = f"{base_url}{Session_ID}/lapdata/"

# ---------------------------- LOCAL FILES ----------------------------
session_file = f"session_{Session_ID}.json"
classification_file = f"classification_{Session_ID}.json"
lap_data_file = f"laps_{Session_ID}.json"

# ---------------------------- SESSION DATA ----------------------------
if os.path.exists(session_file):
    print("Session data already exists. Skipping download.")
else:
    session_json = fetch_json(my_session_url)
    if session_json:
        save_json(session_file, session_json)

# ---------------------------- CLASSIFICATION DATA ----------------------------
if os.path.exists(classification_file):
    print("Classification data already exists. Skipping download.")
    with open(classification_file, "r") as f:
        classification_data = json.load(f)
else:
    classification_data = fetch_json(my_classification_url)
    if classification_data:
        save_json(classification_file, classification_data)

# ---------------------------- NUM DRIVERS ----------------------------
num_drivers = len(classification_data["rows"])
print("Number of drivers:", num_drivers)

# ---------------------------- FIRST LAP & RACE START ----------------------------
first_driver = classification_data["rows"][0]
first_lap = first_driver.get("laps", [])[0]
print("first_lap", first_lap)

lap_duration = convert_time(first_lap["lapTime"])
time_str = first_lap["timeOfDay"].split("T")[1]
lap_end = convert_time(time_str)
race_start = round(lap_end - lap_duration, 3)
print("Calculated race start time (TOD):", race_start)

# ---------------------------- LOAD ALL LAP DATA ----------------------------
with open(lap_data_file, "r", encoding="utf-8") as f:
    lap_data_all = json.load(f)

# ---------------------------- STARTING GRID ----------------------------
starting_grid = build_starting_grid(lap_data_all)
save_json("Starting_Grid.json", starting_grid)
grid_order = starting_grid

# ---------------------------- LAP COUNT ----------------------------
total_laps = get_total_laps(lap_data_all)
print("Total number of laps:", total_laps)

# ---------------------------- GENERATE PER-LAP FILES ----------------------------
laps_folder = "Laps"
if not os.path.exists(laps_folder):
    os.makedirs(laps_folder)

for lap_num in range(1, total_laps):
    lap_data, grid_order = create_lap_files(lap_data_all, race_start, grid_order, lap_num, total_laps)
    lap_filename = os.path.join(laps_folder, f"Lap_{lap_num}.json")
    with open(lap_filename, 'w') as file:
        json.dump(lap_data, file, indent=4)
