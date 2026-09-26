#!/usr/bin/env python3
"""
Pixel-perfect 128x128 Claude usage screen renderer for Divoom MiniToo.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def get_fonts():
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")
    
    # Try high-legibility crisp fonts
    try:
        f_header = ImageFont.truetype(os.path.join(fonts_dir, "segoeuib.ttf"), 13)
        f_badge = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 9)
        f_label = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 11)
        f_value = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 12)
        f_reset = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 9)
    except Exception:
        f_header = ImageFont.load_default()
        f_badge = f_header
        f_label = f_header
        f_value = f_header
        f_reset = f_header

    return {
        "header": f_header,
        "badge": f_badge,
        "label": f_label,
        "value": f_value,
        "reset": f_reset
    }

def draw_progress_bar(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, percent: int, active_color: tuple, empty_color=(30, 40, 60), border_color=(45, 60, 90), num_blocks: int = 10):
    """Draw a segmented block progress bar (e.g. 10 blocks) matching ████████░░."""
    gap = 2
    total_gaps = (num_blocks - 1) * gap
    block_width = (width - total_gaps) // num_blocks
    filled_blocks = round((percent / 100.0) * num_blocks)

    for i in range(num_blocks):
        bx = x + i * (block_width + gap)
        by = y
        if i < filled_blocks:
            draw.rectangle([bx, by, bx + block_width, by + height], fill=active_color)
        else:
            draw.rectangle([bx, by, bx + block_width, by + height], fill=empty_color, outline=border_color)

def render_screen(
    five_hour_pct: int = 63,
    five_hour_reset: str = "2H 14M",
    week_pct: int = 41,
    week_reset: str = "3D 8H",
    model_name: str = "OPUS 5",
    is_live: bool = False
) -> Image.Image:
    # 128x128 canvas
    img = Image.new("RGB", (128, 128), (11, 15, 25))  # Deep night blue
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Outer border (subtle 1px frame)
    draw.rectangle([0, 0, 127, 127], outline=(25, 35, 55))

    # --- Header ---
    # CLAUDE title in warm Anthropic coral/amber
    draw.text((8, 6), "CLAUDE", fill=(245, 140, 60), font=fonts["header"])

    # Model Badge (top-right)
    if model_name:
        badge_text = model_name.upper()
        # Measure text box
        bbox = fonts["badge"].getbbox(badge_text)
        bw = bbox[2] - bbox[0] + 6
        bx = 120 - bw
        by = 8
        draw.rectangle([bx, by, 120, by + 12], fill=(22, 33, 50), outline=(50, 75, 110))
        draw.text((bx + 3, by), badge_text, fill=(130, 190, 240), font=fonts["badge"])

    # Header divider line
    draw.line([(8, 22), (120, 22)], fill=(25, 38, 60), width=1)

    # --- 5-Hour Block ---
    # Label & Value
    draw.text((8, 26), "5H", fill=(140, 155, 175), font=fonts["label"])
    val_str = f"{five_hour_pct}%"
    v_bbox = fonts["value"].getbbox(val_str)
    vw = v_bbox[2] - v_bbox[0]
    # Color warning based on percentage
    if five_hour_pct >= 90:
        c_val = (245, 75, 75)   # Red
    elif five_hour_pct >= 75:
        c_val = (245, 175, 50)  # Amber
    else:
        c_val = (50, 230, 140)  # Emerald
    draw.text((120 - vw, 25), val_str, fill=c_val, font=fonts["value"])

    # 5H Bar: 10 blocks, width 112px, height 7px
    draw_progress_bar(draw, 8, 41, 112, 7, five_hour_pct, active_color=c_val)

    # 5H Reset
    draw.text((8, 52), f"RESET  {five_hour_reset}", fill=(90, 115, 145), font=fonts["reset"])

    # Section divider
    draw.line([(8, 66), (120, 66)], fill=(20, 30, 48), width=1)

    # --- Weekly Block ---
    draw.text((8, 70), "WEEK", fill=(140, 155, 175), font=fonts["label"])
    w_val_str = f"{week_pct}%"
    wv_bbox = fonts["value"].getbbox(w_val_str)
    wvw = wv_bbox[2] - wv_bbox[0]
    if week_pct >= 90:
        c_wval = (245, 75, 75)
    elif week_pct >= 75:
        c_wval = (245, 175, 50)
    else:
        c_wval = (55, 185, 245)  # Cyan/blue
    draw.text((120 - wvw, 69), w_val_str, fill=c_wval, font=fonts["value"])

    # Week Bar: 10 blocks
    draw_progress_bar(draw, 8, 85, 112, 7, week_pct, active_color=c_wval)

    # Week Reset
    draw.text((8, 96), f"RESET  {week_reset}", fill=(90, 115, 145), font=fonts["reset"])

    # --- Footer status ---
    # Dot indicator + status text
    status_color = (50, 230, 140) if is_live else (100, 120, 150)
    draw.ellipse([8, 113, 13, 118], fill=status_color)
    status_label = "LIVE LOCAL" if is_live else "CACHED UTIL"
    draw.text((18, 111), status_label, fill=(90, 110, 135), font=fonts["reset"])

    return img

if __name__ == "__main__":
    # Test rendering sample matching user prompt
    img = render_screen(five_hour_pct=63, five_hour_reset="2H 14M", week_pct=41, week_reset="3D 8H", model_name="OPUS 5", is_live=False)
    img.save("preview_prompt_spec.png")
    print("Saved preview_prompt_spec.png (128x128)")
