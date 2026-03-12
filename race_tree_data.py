"""
RaceTree 3.0 Data Pipeline Tool
===============================

This script fetches race session data from the Speedhive API, cleans up the
participant information, calculates the precise race start time, and generates
a comprehensive summary of lap-by-lap data including assumed kart positions.

In previous versions (2.0, 2.1), the pipeline produced a separate JSON file for
every single lap. In Version 3.0, to facilitate building modern, programmatic
video overlays (e.g., using MoviePy, Canvas, etc.), all the data is collected
and exported into a SINGLE unified JSON structure: `RaceSessionData_<session_id>.json`.

Usage:
    Run the script directly and provide the Speedhive Session ID when prompted.
"""

import json
import os
import requests
import sys
import argparse
from typing import Dict, Any, List, Optional, Tuple

# -------------------------------------------------------------------------
# CONSTANTS & CONFIGURATION
# -------------------------------------------------------------------------

# The base URL for the Speedhive API for fetching session data
BASE_API_URL = "https://eventresults-api.speedhive.com/api/v0.2.3/eventresults/sessions/"

# Headers needed to pretend to be a normal web browser and access the API
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://speedhive.mylaps.com',
    'Referer': 'https://speedhive.mylaps.com/',
    'Connection': 'keep-alive'
}


# -------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------------

def fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """
    Downloads JSON data from a given API endpoint.
    
    Args:
        url (str): The full URL to fetch.
        
    Returns:
        dict: The parsed JSON response, or None if the request failed.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        print(f"❌ Failed to fetch {url} - Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def save_json(filename: str, data: Any) -> None:
    """
    Saves a Python dictionary or list to a JSON file.
    
    Args:
        filename (str): The path/name of the file to save.
        data (any): The data structure to serialize into JSON.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"✅ Successfully saved: {filename}")

def load_json(filename: str) -> Any:
    """
    Loads JSON data from a local file.
    
    Args:
        filename (str): The path/name of the file to read.
        
    Returns:
        The parsed Python object (usually a dict or list).
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def time_to_seconds(time_str: str) -> float:
    """
    Converts a standard Time-Of-Day string (HH:MM:SS.ms) into total seconds.
    
    Example:
        time_to_seconds("14:30:15.500") -> 52215.5
        
    Args:
        time_str (str): The time string to convert.
        
    Returns:
        float: Total seconds since midnight.
    """
    try:
        # Split into Hours, Minutes, and Seconds
        h, m, s = time_str.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        print(f"⚠️ Error parsing time_to_seconds ({time_str}): {e}")
        return 0.0

def convert_lap_time_to_seconds(lap_time_str: str) -> float:
    """
    Converts a lap duration string into total seconds.
    Lap times might come in "M:SS.ms" or just "SS.ms".
    
    Example:
        convert_lap_time_to_seconds("1:21.633") -> 81.633
        convert_lap_time_to_seconds("45.123") -> 45.123
        
    Args:
        lap_time_str (str): The lap time string.
        
    Returns:
        float: Duration of the lap in seconds.
    """
    if ":" not in lap_time_str:
        return float(lap_time_str)
    
    minutes, seconds = lap_time_str.split(":")
    return int(minutes) * 60 + float(seconds)

def clean_kart_number(kart_str: str) -> str:
    """
    Normalizes kart numbers. Sometimes transponders or registration
    adds a letter suffix depending on the rental class (e.g., G=1, H=2, M=3).
    
    Args:
        kart_str (str): The raw kart number string.
        
    Returns:
        str: The normalized numeric kart string.
    """
    if not kart_str:
        return ""
    
    # If the last character is a known modifier letter, replace it
    if kart_str[-1].upper() in {'G', 'H', 'M'}:
        mapping = {'G': '1', 'H': '2', 'M': '3'}
        return kart_str[:-1] + mapping[kart_str[-1].upper()]
    
    return kart_str

def print_progress(current: int, total: int, prefix: str = '', length: int = 40) -> None:
    """
    Draws a simple CLI progress bar.
    
    Args:
        current (int): Current step index.
        total (int): Total number of steps.
        prefix (str): Text to show before the progress bar.
        length (int): Character width of the progress bar.
    """
    percent = f"{100 * (current / float(total)):.1f}"
    filled_len = int(length * current // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}%')
    sys.stdout.flush()
    if current == total:
        print()


# -------------------------------------------------------------------------
# CORE DATA PROCESSING
# -------------------------------------------------------------------------

def get_starting_grid(classification_rows: List[Dict]) -> List[Dict]:
    """
    Extracts the starting grid (positions, names, and kart numbers) from 
    the classification data payload. This ensures we get the actual ending
    results for Qualification sessions, rather than their initial starting positions.
    
    Args:
        classification_rows (list): The 'rows' array from the classification API endpoint.
        
    Returns:
        List[Dict]: An ordered list of drivers representing the starting grid.
    """
    grid = []
    for entry in classification_rows:
        pos = entry.get('position')
        # We only care about drivers who actually placed
        if pos is not None:
            grid.append({
                "position": pos,
                "name": entry.get('name', "Unknown"),
                "kartNumber": clean_kart_number(entry.get('startNumber', "Unknown"))
            })
            
    # Sort the grid by position number ascending (1, 2, 3...)
    return sorted(grid, key=lambda x: x['position'])

def calculate_race_start_time(lap_data_all: List[Dict]) -> float:
    """
    Calculates the exact Time-of-Day (in seconds) the race officially started.
    Since Speedhive doesn't always provide an absolute "Start Time" timestamp, 
    we look at the FIRST recorded lap of the FIRST driver, take its recorded 
    TimeOfDay, and subtract its Duration.
    
    Args:
        lap_data_all (list): The full array of lap data.
        
    Returns:
        float: The race start time in seconds since midnight.
    """
    for driver in lap_data_all:
        laps = driver.get('laps', [])
        if laps:
            first_lap = laps[0]
            
            # The 'timeOfDay' string looks like "2024-05-18T14:30:15.500"
            tod_str = first_lap['timeOfDay'].split("T")[1]
            lap_end_seconds = time_to_seconds(tod_str)
            
            lap_duration_str = first_lap['lapTime']
            lap_duration = convert_lap_time_to_seconds(lap_duration_str)
            
            # Start Time = End Time - Duration
            return lap_end_seconds - lap_duration
            
    return 0.0

def get_total_lap_count(lap_data_all: List[Dict]) -> int:
    """
    Finds out the highest number of laps recorded by any single driver.
    
    Args:
        lap_data_all (list): The full array of lap data.
        
    Returns:
        int: Total number of laps (plus 1 to align with 1-based indexing logic).
    """
    max_laps = 0
    for driver in lap_data_all:
        count = driver.get('lapDataInfo', {}).get('lapCount', 0)
        if count > max_laps:
            max_laps = count
            
    # Return count + 1 to stay consistent with historical RaceTree behavior
    return max_laps + 1


def compile_lap_history(
    lap_data_all: List[Dict], 
    total_laps: int, 
    race_start: float, 
    starting_grid: List[Dict]
) -> List[Dict]:
    """
    Iterates through lap 1, lap 2, lap 3... up to 'total_laps' and records
    every driver's stats for that lap, comparing their position against the 
    previous lap (or starting grid) to track overtakes.
    
    Args:
        lap_data_all (list): The raw API payload.
        total_laps (int): The max number of laps to process.
        race_start (float): The base time to subtract from lap times.
        starting_grid (list): The initial starting order of karts.
        
    Returns:
        List[Dict]: An array containing data for each lap.
    """
    compiled_laps = []
    
    # We maintain a running list of who is currently in what position.
    # At lap 0, this is the starting grid.
    current_grid_state = [driver['kartNumber'] for driver in starting_grid]

    # Process each lap index starting from 1
    for lap_num in range(1, total_laps):
        
        # This list holds the snapshot details of all drivers during THIS specific lap
        lap_records = []
        
        for driver in lap_data_all:
            driver_info = driver.get('lapDataInfo', {}).get('participantInfo', {})
            name = driver_info.get('name', 'Unknown')
            kart_number = driver_info.get('startNr', 'Unknown')
            start_pos = driver_info.get('startPos', 'Unknown')
            
            # Find the exact lap object for the current lap number
            lap_obj = next((l for l in driver.get("laps", []) if l.get("lapNr") == lap_num), None)
            
            if lap_obj:
                # Calculate relative time of day since the race started
                tod_str = lap_obj["timeOfDay"].split("T")[1]
                absolute_tod = time_to_seconds(tod_str)
                relative_tod = round(absolute_tod - race_start, 3)
                
                # The position as reported by the timing loop
                official_position = lap_obj.get("fieldComparison", {}).get("position", 999)
                
                lap_records.append({
                    "TimeOfDay": relative_tod,
                    "position": official_position,
                    "name": name,
                    "kartNumber": kart_number,
                    "StartPosition": start_pos
                })
        
        # Sort the records for this lap purely by their official position 
        lap_records.sort(key=lambda d: d["position"])
        
        # Now we calculate "Assumed Positions"
        # This checks if the current running order has diverged from our expected `current_grid_state`
        for index, record in enumerate(lap_records):
            actual_kart = record["kartNumber"]
            
            # If the kart in this slot differs from our memory, a position change occurred
            expected_kart = current_grid_state[index] if index < len(current_grid_state) else None
            if expected_kart != actual_kart:
                if actual_kart in current_grid_state:
                    current_grid_state.remove(actual_kart)
                current_grid_state.insert(index, actual_kart)

        # current_grid_state now holds the full ordered list of all karts including DNFs at the bottom.
        assumed_positions = {f"P{i + 1}": kart for i, kart in enumerate(current_grid_state)}

        # Attach the final assumed standings to all records in this lap for the frontend to consume
        for record in lap_records:
            record["Assumed_Positions"] = dict(assumed_positions)

        # Add this lap to our overall collection
        compiled_laps.append({
            "lapNumber": lap_num,
            "driver_records": lap_records
        })

    return compiled_laps


# -------------------------------------------------------------------------
# MAIN EXECUTION THREAD
# -------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="RaceTree 3.0 - Data Processing Pipeline")
    parser.add_argument("session_id", nargs="?", help="Speedhive Session ID (e.g., 10415811)")
    parser.add_argument("--grid-source", dest="grid_source_id", default=None, help="Optional Session ID to pull the Starting Grid from")
    args = parser.parse_args()

    print("=" * 50)
    print("🏎️  RaceTree 3.0 - Data Processing Pipeline 🏎️")
    print("=" * 50)
    
    if args.session_id:
        session_id = args.session_id.strip()
        grid_source_id = args.grid_source_id.strip() if args.grid_source_id else None
    else:
        # Fallback to interactive input
        session_id = input("\nEnter Speedhive Session ID (e.g., 10415811): ").strip()
        if not session_id:
            print("❌ Invalid Session ID. Exiting.")
            sys.exit(1)
            
        grid_source_id = input("Enter Grid Source Session ID (Optional, press Enter to skip): ").strip()
        grid_source_id = grid_source_id if grid_source_id else None
        
    print(f"\n[1/5] 📡 Fetching Classification Data for Session {session_id}...")
    
    # Pre-Fetch Event/Session Info
    session_info_url = f"{BASE_API_URL}{session_id}"
    session_info = fetch_json(session_info_url)
    session_name = session_info.get('name', f"Session {session_id}") if session_info else f"Session {session_id}"
    
    event_id = session_info.get('eventId') if session_info else None
    event_name = "UNKNOWN EVENT"
    if event_id:
        event_url = f"https://eventresults-api.speedhive.com/api/v0.2.3/eventresults/events/{event_id}"
        event_info = fetch_json(event_url)
        event_name = event_info.get('name', f"Event {event_id}") if event_info else f"Event {event_id}"
        
    print(f"      📌 Event: {event_name}")
    print(f"      📌 Session: {session_name}")
    
    class_url = f"{BASE_API_URL}{session_id}/classification"
    classification_data = fetch_json(class_url)
    
    if not classification_data or 'rows' not in classification_data:
        print("❌ Could not extract driver classification. Ensure the Session ID is valid.")
        sys.exit(1)
        
    num_drivers = len(classification_data['rows'])
    print(f"      ✅ Found {num_drivers} drivers in session.")
    
    # 2. Download specific lap data for every driver
    print(f"\n[2/5] 📥 Downloading Individual Lap Data...")
    lap_data_all = []
    laps_base_url = f"{BASE_API_URL}{session_id}/lapdata/"
    
    for i in range(1, num_drivers + 1):
        lap_url = f"{laps_base_url}{i}/laps"
        lap_json = fetch_json(lap_url)
        if lap_json:
            lap_data_all.append(lap_json)
        print_progress(i, num_drivers, prefix='      Progress')

    if not lap_data_all:
        print("❌ No lap data found. Exiting.")
        sys.exit(1)

    # 3. Clean and prepare grid data
    print(f"\n[3/5] 🧼 Cleaning data and determining Starting Grid...")
    # clean_all_kart_numbers(lap_data_all)  # Removed since we clean directly in get_starting_grid
    
    if grid_source_id:
        print(f"      📡 Fetching Alternate Starting Grid from Session {grid_source_id}...")
        grid_class_url = f"{BASE_API_URL}{grid_source_id}/classification"
        grid_class_data = fetch_json(grid_class_url)
        
        if not grid_class_data or 'rows' not in grid_class_data:
            print("❌ Could not extract alternate grid classification.")
            sys.exit(1)
            
        grid_num_drivers = len(grid_class_data['rows'])
        grid_lap_data_all = []
        grid_laps_base_url = f"{BASE_API_URL}{grid_source_id}/lapdata/"
        
        for i in range(1, grid_num_drivers + 1):
            lap_url = f"{grid_laps_base_url}{i}/laps"
            lap_json = fetch_json(lap_url)
            if lap_json:
                grid_lap_data_all.append(lap_json)
                
        # Remove clean_all_kart_numbers since logic is moved inside get_starting_grid
        starting_grid = get_starting_grid(grid_class_data['rows'])
        print("      ✅ Successfully imported Starting Grid from alternate source.")
    else:
        starting_grid = get_starting_grid(classification_data['rows'])
    
    # 4. Perform lap and race math
    print(f"\n[4/5] ⏱️ Calculating race timeline and position histories...")
    race_start_time = calculate_race_start_time(lap_data_all)
    total_laps = get_total_lap_count(lap_data_all)
    
    print(f"      🏁 Race Start TimeOfDay (secs): {race_start_time:.3f}")
    print(f"      🔄 Total Laps Recorded: {total_laps - 1}")
    
    compiled_laps = compile_lap_history(
        lap_data_all=lap_data_all,
        total_laps=total_laps,
        race_start=race_start_time,
        starting_grid=starting_grid
    )
    
    # 5. Export Unified Output
    print(f"\n[5/5] 💾 Generating Master JSON structure...")
    output_filename = f"RaceSessionData_{session_id}.json"
    
    master_data = {
        "SessionID": session_id,
        "EventName": event_name,
        "SessionName": session_name,
        "TotalDrivers": num_drivers,
        "TotalLaps": total_laps - 1,
        "CalculatedRaceStart_Seconds": race_start_time,
        "StartingGrid": starting_grid,
        "Laps": compiled_laps
    }
    
    # Optional: ensure we output to a specific directory if needed. 
    # For now, saving in the current working directory next to the script.
    save_json("f:\\RACE_TREE_3.0\\" + output_filename, master_data)
    
    print("\n🎉 Pipeline Complete! 🏎️💨")
    print(f"File ready for ingestion by overlay generator: {output_filename}")


if __name__ == "__main__":
    main()
