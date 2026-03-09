import json

def convert_time(time_str):
    if "." in time_str:
        h, m, s = time_str.split(":")
        return round(int(h) * 3600 + int(m) * 60 + float(s), 3)
    else:
        return 0.0

def fetch_json(url):
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch {url} - Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def calculate_race_start(data):
    try:
        first_driver = data[0]
        first_lap = first_driver.get("laps", [])[0]
        lap_duration = convert_time(first_lap["lapTime"])
        time_str = first_lap["timeOfDay"].split("T")[1]
        lap_end = convert_time(time_str)
        return round(lap_end - lap_duration, 3)
    except Exception as e:
        print(f"❌ Error calculating race start time: {e}")
        return 0.0

def get_total_laps(data):
    try:
        return max(len(driver["laps"]) for driver in data)
    except Exception as e:
        print(f"❌ Error getting total laps: {e}")
        return 0

def build_starting_grid(data):
    try:
        grid = sorted([
            {
                "position": driver["lapDataInfo"]["participantInfo"]["startPos"],
                "name": driver["lapDataInfo"]["participantInfo"]["name"],
                "kartNumber": driver["lapDataInfo"]["participantInfo"]["startNr"]
            }
            for driver in data
        ], key=lambda x: x["position"])
        return {"startingGrid": grid}
    except Exception as e:
        print(f"❌ Error building starting grid: {e}")
        return {"startingGrid": []}

def create_lap_files(all_data, adjustment_time, grid_order, lap_number, total_laps):
    print("LAP NUMBER IS:", lap_number)
    lap_key = f"Lap{lap_number}"
    first_lap_data = {lap_key: []}

    grid_list = grid_order['startingGrid']
    driver_data = []

    for ii, driver in enumerate(all_data):
        try:
            participant = driver["lapDataInfo"]["participantInfo"]
            name = participant["name"]
            start_nr = participant["startNr"]
            start_pos = participant["startPos"]

            lap = next((lap for lap in driver["laps"] if lap["lapNr"] == lap_number), None)

            if lap:
                time_of_day = convert_time(str(lap["timeOfDay"]))
                position = lap["fieldComparison"]["position"]

                driver_record = {
                    "TimeOfDay": time_of_day,
                    "position": position,
                    "name": name,
                    "kartNumber": start_nr,
                    "StartPosition": start_pos
                }

                expected_kart = grid_list[ii]["kartNumber"] if ii < len(grid_list) else "N/A"

                print(f"Lap {lap_number} - Kart at P{ii+1}: {start_nr} (Expected: {expected_kart})")

                if expected_kart != start_nr:
                    print("❌ Position mismatch ❌")
                    moved_object = None
                    for i, obj in enumerate(grid_list):
                        if obj["kartNumber"] == start_nr:
                            moved_object = grid_list.pop(i)
                            break

                    if moved_object:
                        grid_list.insert(ii, moved_object)
                        assumed_positions = {
                            f"P{i+1}": obj["kartNumber"] for i, obj in enumerate(grid_list)
                        }
                        driver_record["Assumed_Positions"] = assumed_positions

                driver_data.append(driver_record)
            else:
                print(f"⚠️ No lap {lap_number} found for {name}")

        except KeyError as e:
            print(f"❌ Missing expected key in lap {lap_number}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in lap {lap_number}: {e}")

    first_lap_data[lap_key].extend(driver_data)
    return first_lap_data, grid_order
