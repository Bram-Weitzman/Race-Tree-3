# RaceTree_2.0.py - DB-Free Version

import json
import os
import shutil
from RaceTree_Functions_2_0 import *
import sys

#########  NEED TO CHECK IF THE LAP FILES NEED TO BE SORTED BEFORE CALLING CREATE_LAP_FILES ##########################
#########  RESET TO TEMPORARY OFFLINE MODE FOR TESTING ###############################################################

# Prompt for session ID
print("Welcome to RaceTree 2.0!")
print("This version does not require a database.")
Session_ID = input("Enter Session ID: ")
print("Session ID =", Session_ID)

# Set up API URLs
base_url = "https://eventresults-api.speedhive.com/api/v0.2.3/eventresults/sessions/"
classification_url = f"{base_url}{Session_ID}/classification"
laps_base_url = f"{base_url}{Session_ID}/lapdata/"

# Check if session JSON already exists
session_file = f"session_{Session_ID}.json"
if os.path.exists(session_file):
    print("Session data already exists. Skipping download.")
    update_kart_numbers_json(Session_ID)  # Assuming this is used elsewhere
else:
    classification_data = fetch_json(classification_url)
    if not classification_data:
        print("Failed to fetch classification data.")
        exit(1)
    save_json(session_file, classification_data)

# Load classification
classification_data = load_json(session_file)
driver_codes = extract_driver_codes(classification_data)
num_drivers = len(driver_codes)
print("Number of drivers:", num_drivers)

# ------------------- TEMPORARY OFFLINE MODE -------------------
# The following block is normally used to download data.
# Temporarily commented out to use local data only.

lap_data_all = []
print("DOWNLOADING LAP DATA")
for i in range(1, num_drivers + 1):
    lap_url = f"{laps_base_url}{i}/laps"
    lap_json = fetch_json(lap_url)
    
    if lap_json:
        lap_data_all.append(lap_json)
        print_progress(i, num_drivers, prefix='Progress', suffix=f'Lap {i}/{num_drivers}')
    else:
        print(f"⚠️ Failed to fetch lap data for driver index {i}")

lap_data_file = f"laps_{Session_ID}.json"
save_json(lap_data_file, lap_data_all)
grid = build_starting_grid(lap_data_all)
save_json("Starting_Grid.json", grid)
grid_order = grid

# ------------------- USING LOCAL DATA -------------------
# Load previously downloaded lap data and grid from file
lap_data_file = f"laps_{Session_ID}.json"
with open(lap_data_file, "r", encoding="utf-8") as f:
    lap_data_all = json.load(f)

with open("Starting_Grid.json", "r", encoding="utf-8") as f:
    grid_order = json.load(f)

# Calculate race start TOD
race_start = calculate_race_start(lap_data_all)
print("Calculated race start time (TOD):", race_start)

# Get total lap count
total_laps = get_total_laps(lap_data_all)
print("Total number of laps:", total_laps)

# Define the folder path
laps_folder = "Laps"

# Check if the folder exists
if os.path.exists(laps_folder):
    shutil.rmtree(laps_folder)

# Recreate the folder
os.makedirs(laps_folder)

# Save lap count to file
lap_num_file = "lapNumFile.txt"
with open(lap_num_file, "w") as f:
    f.write(str(total_laps - 1))

# Process each lap
for i in range(1, total_laps):
    my_lap_number = i
    print("i: ", i)
    if my_lap_number == 1:
        with open(lap_data_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        # Sort by position for current lap
        all_data.sort(key=lambda d: get_position_for_lap(d, my_lap_number))

        kartnumber = grid_order["startingGrid"][i]["kartNumber"]
        
        starting_grid_list = grid_order["startingGrid"]

        grid_index = next(
            (i for i, entry in enumerate(starting_grid_list) if entry["kartNumber"] == kartnumber),
            None
        )

        if grid_index is not None:
            print("KartNumber: ", kartnumber, "Index:", grid_index)
        else:
            print(f"⚠️ Kart {kartnumber} not found in starting grid")

        print("calling create_lap_data for lap 1")
        print("race_start: ", race_start)
        lap_data, grid_order = create_lap_files(all_data, race_start, grid_order, my_lap_number, total_laps)

    else:
        with open(lap_data_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        # Sort by position for current lap
        all_data.sort(key=lambda d: get_position_for_lap(d, my_lap_number))

        kartnumber = grid_order["startingGrid"][i]["kartNumber"]
        
        # starting_grid_list = grid_order["startingGrid"]  # Already defined above

        grid_index = next(
            (i for i, entry in enumerate(starting_grid_list) if entry["kartNumber"] == kartnumber),
            None
        )

        if grid_index is not None:
            print("KartNumber: ", kartnumber, "Index:", grid_index)
        else:
            print(f"⚠️ Kart {kartnumber} not found in starting grid")
        
        print("calling create_lap_data")
        lap_data, grid_order = create_lap_files(all_data, race_start, grid_order, my_lap_number, total_laps)        
        
    # To re-enable saving per-lap files, uncomment below:
    lap_filename = os.path.join(laps_folder, f"Lap_{my_lap_number}.json")
    with open(lap_filename, 'w') as file:
        json.dump(lap_data, file, indent=4)
