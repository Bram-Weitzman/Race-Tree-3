"""
RaceTree 3.0 Video Generator
============================

This script ingests a `RaceSessionData_<session_id>.json` file and outputs
a 60FPS green screen (.mp4) video overlay. The video perfectly syncs F1-style
slotted positioning animations with the race timestamps.

Requirements:
    pip install opencv-python Pillow numpy

Usage:
    python race_tree_video.py <session_id> [--test]
"""

import sys
import json
import os
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------------------------------
# VIDEO / RENDER CONFIGURATION
# -------------------------------------------------------------------------
FPS = 30
WIDTH, HEIGHT = 1920, 1080
BG_COLOR = (0, 255, 0)  # Pure Green for Chroma Keying

# Kart UI configuration
MAX_DISPLAY = 40           # Maximum number of karts to display at once in the tree
SLOT_WIDTH = 125           # Original width + user adjustment
SLOT_HEIGHT = 34           # Original 28 * 1.2 = 33.6 ~ 34px
SLOT_MARGIN = 4
START_X = 50               # X offset from the left edge of the screen
START_Y = 180              # Y offset from the top
COLUMN_SPACING = 145       # SLOT_WIDTH (125) + 20px space between columns
ANIMATION_DURATION = 1.0   # seconds for a position swap animation to complete
FONT_SIZE = 18             # Bumped from 14 to 18
FONT_PATH = "Montserrat-ExtraBold.ttf"  # Custom Google Font

def format_name(name: str, full_last: bool = False) -> str:
    """Extracts first initial and last name based on full_last flag."""
    parts = name.strip().split()
    if not parts:
        return "UNK"
    if len(parts) == 1:
        return parts[0].upper() if full_last else parts[0][:3].upper()
    
    first_initial = parts[0][0].upper()
    last_name = parts[-1].upper() if full_last else parts[-1][:3].upper()
    return f"{first_initial}. {last_name}"

def ease_in_out(t: float) -> float:
    """
    Standard cubic ease-in-out easing function.
    t: float [0.0 - 1.0] representing animation progress.
    """
    if t < 0.5:
        return 4.0 * t * t * t
    else:
        f = (2.0 * t) - 2.0
        return 0.5 * f * f * f + 1.0

# Setup CLI parsing
try:
    import argparse
except ImportError:
    pass

output_file_override = None
sponsor_images_paths = []

if len(sys.argv) > 1:
    # Basic backwards compatibility parser for existing calls + new args
    parser = argparse.ArgumentParser(description="RaceTree Video Generator")
    parser.add_argument("session_id", type=str, help="Speedhive Session ID")
    parser.add_argument("--test", action="store_true", help="Limit to 120s test render")
    parser.add_argument("--output", type=str, help="Output MP4 file path")
    parser.add_argument("--sponsors", type=str, nargs='*', help="Paths to sponsor images")
    
    args = parser.parse_args()
    session_id = args.session_id
    is_test = args.test
    output_file_override = args.output
    if args.sponsors:
        sponsor_images_paths = args.sponsors
else:
    print("Usage: python race_tree_video.py <session_id> [--test] [--output file] [--sponsors img1 img2]")
    sys.exit(1)

input_file = f"RaceSessionData_{session_id}.json"
raw_output = output_file_override if output_file_override else f"Overlay_{session_id}.mp4"
output_file = raw_output.replace('\\', '/')

def generate_video():
    """
    Main renderer pipeline.
    """
    global session_id, is_test, input_file, output_file # Access script-level variables

    if not os.path.exists(input_file):
        print(f"❌ Cannot find data file: {input_file}")
        sys.exit(1)

    print(f"Loading session data from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # We need to know the total duration of the race to set our video length.
    # We look at the final lap of the race, and the maximum TimeOfDay.
    laps = data.get("Laps", [])
    if not laps:
        print("❌ No laps found in data. Cannot generate video.")
        sys.exit(1)

    # Let's find the max TimeOfDay in the entire dataset
    max_time = 0.0
    for lap in laps:
        for record in lap.get("driver_records", []):
            t = record.get("TimeOfDay", 0.0)
            if t > max_time:
                max_time = t

    total_frames = int(math.ceil(max_time * FPS)) + (FPS * 2) # Adding 2 seconds buffer at the end
    
    if is_test:
        print(">>> TEST MODE ENABLED: Limiting render to 120 seconds <<<")
        max_time = 120.0
        total_frames = int(max_time * FPS)
    
    duration_secs = total_frames / FPS

    print(f"Race Duration: {max_time:.2f} seconds")
    print(f"Generating Video: {output_file} ({FPS} fps, {total_frames} frames, {duration_secs:.2f}s)")

    # Set up Hardware-Accelerated FFmpeg Pipe
    # We use NVENC h264 for massive speedup of the video compression step.
    ffmpeg_cmd = [
        'f:\\RACE_TREE_3.0\\ffmpeg-8.0.1-essentials_build\\ffmpeg-8.0.1-essentials_build\\bin\\ffmpeg.exe',
        '-y',                            # Overwrite output
        '-f', 'rawvideo',                # Input format
        '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}',       # Frame size
        '-pix_fmt', 'rgb24',             # Raw RGB pixel format directly from Pillow Memory
        '-r', str(FPS),                  # Framerate
        '-i', '-',                       # Read from STDIN
        '-c:v', 'h264_nvenc',            # Hardware encoding on NVIDIA GPU
        '-preset', 'p6',                 # High quality
        '-tune', 'hq',
        '-b:v', '15M',                   # 15 Mbps Bitrate
        '-pix_fmt', 'yuv420p',           # Needed for compatibility in Premiere
        output_file
    ]

    print(f"Opening FFmpeg NVENC Render Pipeline: {' '.join(ffmpeg_cmd)}\n")
    try:
        # We allow stderr to print to console so we can debug NVENC errors
        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    except FileNotFoundError:
        print("❌ `ffmpeg` is not installed or not in system PATH.")
        sys.exit(1)

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        # Fallback if arial isn't available
        font = ImageFont.load_default()

    # Get the starting grid
    starting_grid = data.get("StartingGrid", [])
    
    SINGLE_COLUMN_MODE = len(starting_grid) <= 24
    active_slot_width = SLOT_WIDTH * 2 + 20 if SINGLE_COLUMN_MODE else SLOT_WIDTH
    active_column_spacing = 0 if SINGLE_COLUMN_MODE else COLUMN_SPACING
    
    # Extract total laps from data
    total_laps = data.get("TotalLaps", 0)
    lap_starts = [(0.0, 1)] # Lap 1 starts at time 0.0 relative to race start
    for lap in data.get("Laps", []):
        records = sorted(lap.get("driver_records", []), key=lambda x: x["position"])
        if records:
            # The leader crossing the line starts the next lap
            leader_tod = records[0]["TimeOfDay"]
            lap_num = lap.get("lapNumber")
            lap_starts.append((leader_tod, lap_num + 1))
            
    # kart_positions stores the "logical" index (0-based) for each kart number at a given timestamp.
    # We rebuild the state linearly per frame.
    
    # ---------------------------------------------------------------------
    # PRE-CALCULATE TIMELINE EVENTS & FASTEST LAP
    # ---------------------------------------------------------------------
    # Instead of recalculating every frame, we build interpolation tables.
    # driver_positions["kart123"] = list of (timestamp_seconds, position_index)
    
    # Initialize everybody at position index based on StartingGrid
    driver_positions = {}
    for grid_item in starting_grid:
        kart = grid_item["kartNumber"]
        pos_idx = grid_item["position"] - 1  # 0-based
        driver_positions[kart] = [(0.0, pos_idx)]
        
    # Fastest lap tracking
    # fastest_lap_timeline = list of (timestamp_seconds, kartNumber)
    fastest_lap_timeline = []
    current_fastest_time = float('inf')
    kart_last_tod = {}  # Tracks the driver's previous crossing TimeOfDay
    
    for lap in laps:
        lap_num = lap.get("lapNumber", 0)
        
        # Sort records by actual position crossing the line
        records = sorted(lap.get("driver_records", []), key=lambda x: x["position"])
        if not records:
            continue
            
        assumed = records[0].get("Assumed_Positions", {})
        
        for record in records:
            kart = record["kartNumber"]
            tod = record["TimeOfDay"]
            
            # FASTEST LAP CHECK
            # We calculate actual lap time by subtracting the driver's past TimeOfDay
            if kart in kart_last_tod:
                lap_time_secs = tod - kart_last_tod[kart]
                # Filter out obvious glitches/outlaps by requiring lap time to be reasonable (> 20s)
                if lap_time_secs > 20.0 and lap_time_secs < current_fastest_time:
                    current_fastest_time = lap_time_secs
                    fastest_lap_timeline.append((tod, kart))
            
            # Save this crossing for the next lap's math
            kart_last_tod[kart] = tod
            
            # POSITION OVEERTkAEKs
            # Find what assumed pos this kart holds NOW
            current_assumed_idx = -1
            for p_key, p_kart in assumed.items():
                if p_kart == kart:
                    current_assumed_idx = int(p_key.replace("P", "")) - 1
                    break
            
            if current_assumed_idx != -1:
                # Append this timeline event
                # Only add if it's a NEW position (an overtake) or if it's the very last lap 
                # (so we have a final anchor point)
                if kart not in driver_positions:
                    driver_positions[kart] = []
                    
                last_pos = driver_positions[kart][-1][1] if driver_positions[kart] else -1
                if current_assumed_idx != last_pos:
                    driver_positions[kart].append((tod, current_assumed_idx))
                    
    # Add a final anchor at the end of the race for all karts so they stay put
    for kart in driver_positions:
        last_idx = driver_positions[kart][-1][1]
        driver_positions[kart].append((max_time + 10.0, last_idx))

    def get_pos_xy(idx_int: int) -> tuple[float, float]:
        if SINGLE_COLUMN_MODE:
            col = 0
            row = idx_int
        else:
            col = idx_int % 2
            row = idx_int // 2
        x = START_X + (col * active_column_spacing)
        y = START_Y + (row * (SLOT_HEIGHT + SLOT_MARGIN))
        return float(x), float(y)

    def get_interpolated_xy(kart: str, current_time: float) -> tuple[float, float, float]:
        """
        Determines the X, Y, and visual_index coordinate for a kart at the given time,
        applying smooth easing if it's actively moving between positions.
        """
        timeline = driver_positions.get(kart, [(0.0, 0)])
        
        start_t = 0.0
        start_pos = timeline[0][1]
        
        end_t = 0.0
        end_pos = start_pos
        
        for i in range(len(timeline)):
            if timeline[i][0] > current_time:
                end_t = timeline[i][0]
                end_pos = timeline[i][1]
                if i > 0:
                    start_t = timeline[i-1][0]
                    start_pos = timeline[i-1][1]
                break
        else:
            # We are past the last event
            x, y = get_pos_xy(timeline[-1][1])
            return x, y, float(timeline[-1][1])

        anim_start_time = end_t - ANIMATION_DURATION
        
        if current_time < anim_start_time:
            x, y = get_pos_xy(start_pos)
            return x, y, float(start_pos)
        elif current_time >= end_t:
            x, y = get_pos_xy(end_pos)
            return x, y, float(end_pos)
        else:
            # Interpolating
            progress = (current_time - anim_start_time) / ANIMATION_DURATION
            eased = ease_in_out(progress)
            
            sx, sy = get_pos_xy(start_pos)
            ex, ey = get_pos_xy(end_pos)
            
            x = sx + (ex - sx) * eased
            y = sy + (ey - sy) * eased
            v_idx = start_pos + (end_pos - start_pos) * eased
            
        return x, y, float(v_idx)

    def get_current_fastest_kart(current_time: float) -> str:
        """Finds who holds the fastest lap at the current time"""
        current_holder = None
        for stamp, kart in fastest_lap_timeline:
            if current_time >= stamp:
                current_holder = kart
            else:
                break
        return current_holder

    # Pre-lookup table for formatted names
    kart_to_name = {g["kartNumber"]: format_name(g["name"], full_last=SINGLE_COLUMN_MODE) for g in starting_grid}

    # ---------------------------------------------------------------------
    # PRE-RENDER KART PLATES (Massive CPU Speedup)
    # ---------------------------------------------------------------------
    print("Pre-rendering UI components for maximum speed...")
    
    # dict structure: pre_drawn_karts[kart_id][position_index][is_fastest_lap_boolean] = Image
    pre_drawn_karts = {}
    for kart in driver_positions:
        pre_drawn_karts[kart] = {}
        name = kart_to_name.get(kart, "UNK")
        
        # Positions can technically shift out of bounds during easing animations
        # so we generate plates for positions -1 through MAX_DISPLAY + 2
        for p_idx in range(-1, MAX_DISPLAY + 2):
            pre_drawn_karts[kart][p_idx] = {False: None, True: None}
            pos_int = p_idx + 1
            if pos_int < 1:
                pos_int = 1
                
            disp_text = f"{pos_int}.  {name}"
            accent_color = (255, 0, 0) if pos_int == 1 else (0, 100, 255)
            
            # Generate Standard Plate (Dark Grey) and Fastest Lap Plate (Purple)
            for is_purple in [False, True]:
                bg_color = (103, 58, 183) if is_purple else (30, 30, 30) # F1 style deep purple
                
                plate = Image.new('RGBA', (active_slot_width, SLOT_HEIGHT), color=(0, 0, 0, 0))
                p_draw = ImageDraw.Draw(plate)
                
                try:
                    p_draw.rounded_rectangle([0, 0, active_slot_width, SLOT_HEIGHT], radius=8, fill=bg_color, corners=(False, True, True, False))
                    p_draw.rounded_rectangle([0, 0, active_slot_width-10, SLOT_HEIGHT], radius=2, fill=bg_color, corners=(True, False, False, True))
                except:
                    p_draw.rounded_rectangle([0, 0, active_slot_width, SLOT_HEIGHT], radius=8, fill=bg_color)
                
                try:
                    p_draw.rounded_rectangle([0, 0, 6, SLOT_HEIGHT], radius=2, fill=accent_color, corners=(True, False, False, True))
                except:
                    p_draw.rectangle([0, 0, 5, SLOT_HEIGHT], fill=accent_color)
                
                p_draw.text((12, 8), disp_text, font=font, fill=(255, 255, 255))
                
                plate_rgb = Image.new("RGB", plate.size, BG_COLOR)
                plate_rgb.paste(plate, mask=plate)
                
                pre_drawn_karts[kart][p_idx][is_purple] = plate_rgb

    # ---------------------------------------------------------------------
    # RENDER LOOP OPTIMIZATIONS
    # ---------------------------------------------------------------------
    # Drawing static elements over and over is very heavy for CPU in Python
    # So we pre-render the green background and standard UI into a base image
    base_frame = Image.new('RGB', (WIDTH, HEIGHT), color=BG_COLOR)
    base_draw = ImageDraw.Draw(base_frame)
    
    # Load and Prepare Sponsor Images (Crop to fit placeholder)
    placeholder_width = active_slot_width if SINGLE_COLUMN_MODE else COLUMN_SPACING + SLOT_WIDTH
    placeholder_rect = [START_X, 30, START_X + placeholder_width, START_Y - 45]
    sponsor_images = []
    
    if sponsor_images_paths:
        target_w = placeholder_rect[2] - placeholder_rect[0]
        target_h = placeholder_rect[3] - placeholder_rect[1]
        for sp_path in sponsor_images_paths:
            try:
                img = Image.open(sp_path).convert("RGBA")
                # Scale and Crop to Fill the target dimensions without modifying aspect ratio
                img_ratio = img.width / img.height
                tgt_ratio = target_w / target_h
                
                if img_ratio > tgt_ratio:
                    # Too wide, scale to height, center crop width
                    scaled_h = target_h
                    scaled_w = int(scaled_h * img_ratio)
                    img = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                    diff = scaled_w - target_w
                    img = img.crop((diff // 2, 0, diff // 2 + target_w, target_h))
                else:
                    # Too tall, scale to width, center crop height
                    scaled_w = target_w
                    scaled_h = int(scaled_w / img_ratio)
                    img = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                    diff = scaled_h - target_h
                    img = img.crop((0, diff // 2, target_w, diff // 2 + target_h))
                    
                # Create a black background base for transparent PNGs
                base_sp = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                base_sp.paste(img, (0, 0), img)
                sponsor_images.append(base_sp)
            except Exception as e:
                print(f"Warning: Failed to load sponsor image {sp_path}: {e}")
                
    if not sponsor_images:
        # Fallback to grey placeholder if none specified or all failed
        base_draw.rectangle(placeholder_rect, fill=(100, 100, 100))
        base_draw.text((START_X + 20, 70), "IMAGE PLACEHOLDER", font=font, fill=(255, 255, 255))

    for frame_idx in range(total_frames):
        current_time = frame_idx / FPS

        # Create a fresh frame by copying the pre-drawn static base in memory (huge speedup)
        frame_pil = base_frame.copy()
        draw = ImageDraw.Draw(frame_pil)
        
        # Determine current lap out of total laps
        current_lap = 1
        for tod, l_num in lap_starts:
            if current_time >= tod:
                current_lap = l_num
            else:
                break
                
        if current_lap > total_laps:
            current_lap = total_laps
            
        # Draw dynamic Lap Counter box below the Image Placeholder
        lap_box_rect = [START_X, START_Y - 38, START_X + placeholder_width, START_Y - 5]
        try:
            draw.rounded_rectangle(lap_box_rect, radius=4, fill=(40, 40, 40))
        except:
            draw.rectangle(lap_box_rect, fill=(40, 40, 40))
            
        lap_text = f"Lap {int(current_lap)} / {int(total_laps)}"
        # Rough optical centering across the two-column placeholder width
        draw.text((START_X + 85, START_Y - 30), lap_text, font=font, fill=(255, 255, 255))
        
        # Draw dynamic rotating Sponsor Image in the placeholder rect area
        if sponsor_images:
            # Change image every 10 seconds
            sp_idx = int(current_time / 10.0) % len(sponsor_images)
            active_sponsor = sponsor_images[sp_idx]
            frame_pil.paste(active_sponsor, (placeholder_rect[0], placeholder_rect[1]))
            
        # Find out who holds the purple lap at this exact moment
        fastest_kart_now = get_current_fastest_kart(current_time)
        
        # Calculate all active renders
        active_renders = []
        for kart in driver_positions:
            x, y, vis_index = get_interpolated_xy(kart, current_time)
            if vis_index < MAX_DISPLAY:
                active_renders.append((kart, x, y, vis_index))
                
        # Draw everyone
        active_renders.sort(key=lambda item: item[3])
        for kart, x, y, vis_index in active_renders:
            p_idx = int(round(vis_index))
            
            # Fetch the pre-rendered plate (Purple if they own fastest lap, Dark Grey if not)
            is_purple = (kart == fastest_kart_now)
            plate = pre_drawn_karts[kart][p_idx][is_purple]
            
            if plate:
                # Fast C-optimized paste!
                frame_pil.paste(plate, (int(x), int(y)))

        # Write Pillow RGB Bytes directly to FFmpeg STDIN (Bypasses numpy entirely)
        ffmpeg_process.stdin.write(frame_pil.tobytes())
        
        # Explicitly delete objects to keep memory in check
        del frame_pil

        # Progress reporting
        if frame_idx % FPS == 0:
            sys.stdout.write(f"\rRendering frame {frame_idx}/{total_frames}...")
            sys.stdout.flush()

    # Close the pipe and wait for ffmpeg to finalize the mp4 wrapper
    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()
    
    print("\n✅ Video successfully generated with HW Acceleration!")


if __name__ == "__main__":
    generate_video()
