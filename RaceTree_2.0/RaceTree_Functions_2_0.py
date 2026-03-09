# RaceTree-Functions_2_0.py - DB-Free Functions

import json
import requests
import os
import sys

def fetch_json(url):
    """
    Fetches JSON data from a given URL using browser-like headers.
    Returns the parsed JSON object, or None on failure.
    """
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Origin': 'https://speedhive.mylaps.com',
        'Referer': 'https://speedhive.mylaps.com/',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch {url} - Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def save_json(filename, data):
    """
    Saves a Python dictionary to a JSON file with indentation.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_json(filename):
    """
    Loads and returns the contents of a JSON file as a Python object.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_driver_codes(classification_data):
    """
    Extracts a list of (name, chip code) tuples from classification data.
    """
    return [(row['name'], row['user']['chip']['code']) for row in classification_data['rows']]

def update_kart_numbers_json(session_id):
    """
    Updates kart numbers in the lap data JSON file for a session,
    converting suffixes like G/H/M to numerical values.
    """
    filename = f"laps_{session_id}.json"
    if not os.path.exists(filename):
        print(f"⚠️ File not found: {filename}")
        return
    with open(filename, 'r') as f:
        lap_data_all = json.load(f)

    for driver_data in lap_data_all:
        try:
            kart_number = driver_data['lapDataInfo']['participantInfo']['startNr']
            if kart_number and kart_number[-1] in {'G', 'H', 'M'}:
                mapping = {'G': '1', 'H': '2', 'M': '3'}
                new_kart = kart_number[:-1] + mapping[kart_number[-1]]
                driver_data['lapDataInfo']['participantInfo']['startNr'] = new_kart
        except:
            continue

    with open(filename, 'w') as f:
        json.dump(lap_data_all, f, indent=2)

def build_starting_grid(lap_data_all):
    """
    Constructs and returns a sorted starting grid dictionary from lap data.
    """
    grid = []
    for entry in lap_data_all:
        info = entry['lapDataInfo']['participantInfo']
        grid.append({
            "position": info.get('startPos'),
            "name": info.get('name'),
            "kartNumber": info.get('startNr')
        })
    grid = [g for g in grid if g['position'] is not None]
    return {"startingGrid": sorted(grid, key=lambda x: x['position'])}

def calculate_race_start(lap_data_all):
    """
    Calculates and returns the race start time (TOD in seconds)
    by subtracting lap time from the first recorded time of day.
    """
    for driver in lap_data_all:
        if driver['laps']:
            first_lap = driver['laps'][0]
            #print("first_lap", first_lap)
            time_str = first_lap['timeOfDay'].split("T")[1]
            #print ("time_str", time_str)
            lap_end = time_to_seconds(time_str)
            #print("lap_end", lap_end)
            lap_time_str = first_lap['lapTime']
            lap_duration = first_lap_time_to_seconds(lap_time_str)
            #print ("lap_duration:", lap_duration)
            #lap_duration = float(first_lap['lapTime'])
            #print("first_Lap[laptime]:",first_lap['lapTime'])
            return lap_end - lap_duration
    return 0

def get_total_laps(lap_data_all):
    """
    Retrieves and returns the total number of laps (plus one) from lap data.
    """
    for driver in lap_data_all:
        count = driver.get('lapDataInfo', {}).get('lapCount')
        if count:
            return count + 1
    return 0


#########################   CREATE LAP DATA   #######################################################

def create_lap_files(all_data, race_start, grid_order, lap_number, total_laps):
    #print("LAP NUMBER IS:", lap_number)
    lap_key = f"Lap{lap_number}"
    first_lap_data = {lap_key: []}

    # Extract grid order
    grid_list = grid_order['startingGrid']
    kart_numbers = [entry['kartNumber'] for entry in grid_list]

    lap_num = lap_number
    driver_data = []

    for ii, driver in enumerate(all_data):
        try:
            name = driver["lapDataInfo"]["participantInfo"]["name"]
            start_nr = driver["lapDataInfo"]["participantInfo"]["startNr"]
            start_pos = driver["lapDataInfo"]["participantInfo"]["startPos"]

            # Get the data for this lap number
            lap = next((lap for lap in driver["laps"] if lap["lapNr"] == lap_num), None)

            if lap:
                time_of_day_str = str(lap["timeOfDay"])
                time_of_day = convert_time(time_of_day_str)
                time_of_day = time_of_day - race_start
                time_of_day = round(time_of_day, 3)  # Round to 3 decimal places
                print("time_of_day:", time_of_day)
                position = lap["fieldComparison"]["position"]

                # Create driver record dictionary
                driver_record = {
                    "TimeOfDay": time_of_day,
                    "position": position,
                    "name": name,
                    "kartNumber": start_nr,
                    "StartPosition": start_pos
                }

                # Compare current kart number with expected from grid
                expected_kart = grid_list[ii]["kartNumber"] if ii < len(grid_list) else "N/A"

                #print("Lap Number:", lap_num)
                #print(f"--------- Kart at P{ii+1}: {start_nr} | timeOfDay: {time_of_day}")
                #print(f"Expected kart at P{ii+1}: {expected_kart}")

                if expected_kart != start_nr:
                    #print("❌ Position mismatch ❌")
                    kart_to_move = start_nr

                    # Remove the object from current location
                    moved_object = None
                    for i, obj in enumerate(grid_list):
                        if obj["kartNumber"] == kart_to_move:
                            moved_object = grid_list.pop(i)
                            break

                    # Reinsert at new index
                    if moved_object:
                        new_index = ii
                        grid_list.insert(new_index, moved_object)

                        # Build Assumed_Positions dictionary
                        assumed_positions = {}
                        for i, obj in enumerate(grid_list, start=1):
                            print(f"P{i}: {obj['kartNumber']}")
                            assumed_positions[f"P{i}"] = obj["kartNumber"]

                        # Add assumed positions to current driver
                        driver_record["Assumed_Positions"] = assumed_positions

                # Append this driver record to the full list
                driver_data.append(driver_record)

            else:
                print(f"⚠️ No lap {lap_num} found for {name}")

        except KeyError as e:
            print(f"❌ Missing expected key in lap {lap_num}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in lap {lap_num}: {e}")

        #print("############################################################################################")

    # Attach to lap key
    first_lap_data[lap_key].extend(driver_data)

    updated_grid_order = grid_order
    return first_lap_data, updated_grid_order






##################################################################################################
"""
def convert_time(time_str):
    # Dummy implementation for conversion
    # You need to replace this with actual logic if necessary
    Print ("Converting time string:", time_str)
    return float(time_str.replace(':', '.'))

def resort_positions(kart_numbers, kart_number, position):
    # Dummy implementation for resorting positions
    # You need to replace this with actual logic if necessary
    print("Resorting positions")   
    if kart_number in kart_numbers:
        print("kart_number", kart_number)
        kart_numbers.remove(kart_number)
    kart_numbers.insert(position - 1, kart_number)
    return kart_numbers
"""



#########################  END OF CREATE LAP DAT ################################################


def create_lap_json(lap_data_all, start_tod, grid, lap_num):
    """
    Creates and returns the lap JSON dictionary and updated grid order
    for a specific lap number, including Assumed_Positions.
    """
    lap_key = f"Lap{lap_num}"
    output = {lap_key: []}
    kart_order = [g['kartNumber'] for g in grid['startingGrid']]

    # Gather all driver lap entries for this lap
    lap_entries = []
    for driver in lap_data_all:
        laps = driver.get('laps', [])
        for lap in laps:
            if lap.get('lapNr') == lap_num:
                tod = time_to_seconds(lap['timeOfDay'].split("T")[1]) - start_tod
                info = driver['lapDataInfo']['participantInfo']
                lap_entries.append({
                    "TimeOfDay": round(tod, 3),
                    "position": lap['fieldComparison']['position'],
                    "name": info['name'],
                    "kartNumber": info['startNr'],
                    "StartPosition": info.get('startPos')
                })

    # Sort by position to build Assumed_Positions
    sorted_lap = sorted(lap_entries, key=lambda x: x['position'])
    assumed = {f"P{i+1}": d['kartNumber'] for i, d in enumerate(sorted_lap)}

    # Add Assumed_Positions to each entry
    for entry in sorted_lap:
        entry['Assumed_Positions'] = assumed.copy()
        #output[lap_key].append(entry)

    # Build updated grid (preserve kart order from previous grid)
    new_grid = {"startingGrid": [
        {"position": i + 1, "name": "", "kartNumber": k}
        for i, k in enumerate(kart_order)
    ]}

    return output, new_grid

def time_to_seconds(t):
    """
    Converts a time string (HH:MM:SS.ms) to total seconds as float.
    """
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)
    

def first_lap_time_to_seconds(lap_time_str):
    # Example input: "1:21.633" or "21.633"
    # Check if the string contains a colon (indicating minutes and seconds)
    # Split the string into minutes and seconds
    if ":" not in lap_time_str:
        return float(lap_time_str)
    # Split by colon and get the first part (minutes) and second part (seconds)
    minutes, seconds = lap_time_str.split(":")
    total_seconds = int(minutes) * 60 + float(seconds)
    return total_seconds


##################################### Time Converter ############################################

def convert_time(time_str):
    #debug
    #print("time_str: " + time_str)
    # Split by space and get the second part (time)
    time_str = time_str.split('T')[1]  
    # Split the time string into hours, minutes, seconds, and milliseconds
    hours, minutes, seconds = time_str.split(":")
    #seconds, milliseconds = seconds_ms.split(".")

    # Convert each part to integers or floats
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)
    #milliseconds = int(milliseconds)

    # Convert hours and minutes to seconds
    hours_seconds = hours * 3600
    minutes_seconds = minutes * 60

    # Calculate total seconds and milliseconds
    total_seconds = hours_seconds + minutes_seconds + seconds
    #total_milliseconds = (total_seconds * 1000)

    #print(type(total_milliseconds))
    #print("Total seconds:", total_seconds)
    #print("Milliseconds;", milliseconds)
    #print("Total milliseconds:", total_milliseconds)
    #print(type(total_seconds))

    return total_seconds
    

#########################  END OF TIME OF DAY CONVERSION  #######################################

#####################   Progress Bar  ####################################
def print_progress(current, total, prefix='', suffix='', length=40):
    percent = f"{100 * (current / float(total)):.1f}"
    filled_len = int(length * current // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

    if current == total:
        print()  # Move to next line


def get_position_for_lap(driver, lap_num):
    try:
        lap = next((lap for lap in driver["laps"] if lap["lapNr"] == lap_num), None)
        if lap and "fieldComparison" in lap:
            return lap["fieldComparison"].get("position", float("inf"))
    except:
        pass
    return float("inf")  # fallback if no valid position