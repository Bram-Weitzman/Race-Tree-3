import sys
import json
import os
import math
from PIL import Image, ImageDraw, ImageFont

# Brand Colors
BLUE = (27, 38, 49)      # #1B2631
YELLOW = (241, 196, 15)  # #F1C40F
WHITE = (255, 255, 255)
CYAN = (93, 173, 226)    # #5DADE2
RED = (220, 30, 30)      # TR2 Badge
GREY = (100, 100, 100)   # X2 Badge
BLACK = (0, 0, 0)
DARK_GREY = (40, 50, 60) # Position Circle
BANNER_GREY = (44, 62, 80) # #2C3E50

WIDTH, HEIGHT = 1920, 1080
FONT_PATH = "Montserrat-ExtraBold.ttf"

def parse_driver(name: str) -> tuple[str, str]:
    """Extracts first initial and full last name, plus TR2/X2 badge."""
    name = name.strip().upper()
    badge = None
    
    # Check for badges
    if " TR2" in name:
        badge = "TR2"
        name = name.replace(" TR2", "").strip()
    elif " X2" in name:
        badge = "X2"
        name = name.replace(" X2", "").strip()
        
    parts = name.split()
    if not parts:
        formatted_name = "UNK"
    else:
        formatted_name = " ".join(parts)
        
    return formatted_name, badge

def main():
    if len(sys.argv) < 2:
        print("Usage: python race_tree_grid.py <session_id>")
        sys.exit(1)
        
    session_id = sys.argv[1].strip()
    input_file = f"RaceSessionData_{session_id}.json"
    
    if not os.path.exists(input_file):
        print(f"❌ Cannot find data file: {input_file}")
        sys.exit(1)
        
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    starting_grid = data.get("StartingGrid", [])
    if not starting_grid:
        print("❌ No starting grid found in data.")
        sys.exit(1)
        
    # Create Canvas (Transparent)
    img = Image.new('RGBA', (WIDTH, HEIGHT), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw Main Board (Deep Navy Blue)
    draw.rounded_rectangle([0, 0, WIDTH, HEIGHT], radius=50, fill=BLUE)
    
    # Draw 20px inset white rounded border
    border_margin = 20
    try:
        draw.rounded_rectangle(
            [border_margin, border_margin, WIDTH - border_margin, HEIGHT - border_margin],
            radius=30, outline=WHITE, width=2
        )
    except:
        draw.rectangle(
            [border_margin, border_margin, WIDTH - border_margin, HEIGHT - border_margin],
            outline=WHITE, width=2
        )    
    # Load and draw Logo
    logo_path = "assets/canadianminiindy_logo.png"
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Resize logo to fit nicely (e.g. 800px wide)
            target_w = 800
            ratio = target_w / logo.width
            target_h = int(logo.height * ratio)
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            logo_x = (WIDTH - target_w) // 2
            logo_y = border_margin + 20
            img.paste(logo, (logo_x, logo_y), mask=logo)
        except Exception as e:
            print(f"Warning: Could not draw logo: {e}")
    
    # Fonts
    try:
        banner_font = ImageFont.truetype(FONT_PATH, 42)
        row_font = ImageFont.truetype(FONT_PATH, 24)
        num_font = ImageFont.truetype(FONT_PATH, 24)
        badge_font = ImageFont.truetype(FONT_PATH, 16)
        subtitle_font = ImageFont.truetype(FONT_PATH, 22)
    except:
        banner_font = ImageFont.load_default()
        row_font = ImageFont.load_default()
        num_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        
    # Official Starting Grid Text & Event Name
    event_y = border_margin + 160
    
    event_name = data.get("EventName", "UNKNOWN EVENT").upper()
    session_name = data.get("SessionName", "UNKNOWN SESSION").upper()
    
    try:
        event_font = ImageFont.truetype(FONT_PATH, 32)
        sess_font = ImageFont.truetype(FONT_PATH, 26)
        
        w_e = draw.textlength(event_name, font=event_font)
        draw.text(((WIDTH - w_e) // 2, event_y), event_name, font=event_font, fill=WHITE)
        
        w_s = draw.textlength(session_name, font=sess_font)
        draw.text(((WIDTH - w_s) // 2, event_y + 45), session_name, font=sess_font, fill=WHITE)
    except:
        draw.text((WIDTH//2 - 200, event_y), event_name, fill=WHITE)
        draw.text((WIDTH//2 - 200, event_y + 40), session_name, fill=WHITE)

    # 3 Column Layout Configuration Basics
    # Define these BEFORE banner so banner segments match columns
    banner_margin = 100
    rows_per_col = 11
    SLOT_HEIGHT = 45
    START_X = banner_margin + 40
    X_SPACING = (WIDTH - (banner_margin * 2)) // 3
    Y_SPACING = 50
    
    # Banner replace
    banner_y = event_y + 100
    banner_path = "assets/starting-grid-banner.png"
    banner_height = 60
    
    if os.path.exists(banner_path):
        try:
            banner_img = Image.open(banner_path).convert("RGBA")
            target_w = WIDTH - (2 * banner_margin)
            ratio = target_w / banner_img.width
            target_h = int(banner_img.height * ratio)
            banner_img = banner_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            img.paste(banner_img, (banner_margin, banner_y), mask=banner_img)
            banner_height = target_h
        except Exception as e:
            print(f"Warning: Could not draw banner: {e}")

    # Begin driver loop setup mapping
    START_Y = banner_y + banner_height + 30

    for i, driver in enumerate(starting_grid):
        col = i // rows_per_col
        row = i % rows_per_col
        if col >= 3:
            break 
            
        x = START_X + (col * X_SPACING)
        y = START_Y + (row * Y_SPACING)
        
        pos_str = str(driver["position"])
        kart_num = str(driver["kartNumber"])
        name_str, badge = parse_driver(driver["name"])
        
        # 1. Position Background Circle (Dark Grey)
        circle_radius = 16
        circle_x = x
        circle_y = y + (SLOT_HEIGHT // 2) - circle_radius
        draw.ellipse([circle_x, circle_y, circle_x + (circle_radius*2), circle_y + (circle_radius*2)], fill=DARK_GREY)
        
        # Position Number (White, centered in circle)
        try:
            w_pos = draw.textlength(pos_str, font=num_font)
            # Offset slightly to center optically
            draw.text((circle_x + circle_radius - (w_pos/2), circle_y + 2), pos_str, font=num_font, fill=WHITE)
        except:
            draw.text((circle_x + 8, circle_y + 4), pos_str, font=num_font, fill=WHITE)
            
        # 2. Kart Number (White)
        kart_x = circle_x + 50
        draw.text((kart_x, y + 8), kart_num, font=row_font, fill=WHITE)
        
        # 3. Badge (TR2 / X2)
        badge_offset = 0
        try:
            w_kart = draw.textlength(kart_num, font=row_font)
        except:
            w_kart = 40
            
        if badge:
            badge_x = kart_x + w_kart + 15
            badge_bg = RED if badge == "TR2" else GREY
            try:
                draw.rounded_rectangle([badge_x, y + 10, badge_x + 35, y + 32], radius=3, fill=badge_bg)
            except:
                draw.rectangle([badge_x, y + 10, badge_x + 35, y + 32], fill=badge_bg)
            
            # Draw badge text
            draw.text((badge_x + 4, y + 12), badge, font=badge_font, fill=WHITE)
            badge_offset = 50
            
        # 4. Driver Name (Cyan, UPPERCASE)
        # We start rendering the name far enough to clear a long kart number + badge
        name_x = kart_x + 110
        draw.text((name_x, y + 8), name_str, font=row_font, fill=CYAN)
        
    output_filename = f"StartingGrid_{session_id}.png"
    img.save(output_filename)
    print(f"✅ Saved transparent grid to {output_filename}")

if __name__ == "__main__":
    main()
