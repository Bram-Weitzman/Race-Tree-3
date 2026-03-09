import json

with open("f:/RACE_TREE_3.0/RaceSessionData_10929040.json", "r") as f:
    data = json.load(f)

for lap in data["Laps"][:10]:
    lap_num = lap["lapNumber"]
    
    # Let's see what Assumed Position Kart 324 gets
    records = lap.get("driver_records", [])
    if not records:
        continue
        
    assumed = records[0].get("Assumed_Positions", {})
    
    kart_324_pos = "Unknown"
    for k, v in assumed.items():
        if v == "324":
            kart_324_pos = k
            break
            
    # Did 324 cross the line this lap?
    crossed = any(r.get("kartNumber") == "324" for r in records)
    
    # What was 324's official position this lap?
    official_pos = "N/A"
    tod = "N/A"
    for r in records:
        if r.get("kartNumber") == "324":
            official_pos = r.get("position")
            tod = r.get("TimeOfDay")
            break
            
    print(f"Lap {lap_num}: Assumed={kart_324_pos} | Official={official_pos} | Crossed Line? {crossed} | TOD: {tod}")
