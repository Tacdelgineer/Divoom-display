#!/usr/bin/env python3
"""
Pixel-perfect 128x128 multi-provider AI usage screen renderer for Divoom MiniToo.
Renders screens for Claude, Codex, and Gemini matching the specification.
"""
from __future__ import annotations

import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from providers import UsageData


def get_fonts():
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")

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
        "reset": f_reset,
    }


def draw_progress_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
    percent: Optional[int],
    active_color: tuple[int, int, int],
    empty_color=(25, 33, 50),
    border_color=(40, 50, 75),
    num_blocks: int = 10,
):
    """Draw a segmented block progress bar (e.g. 10 blocks) matching ████████░░."""
    gap = 2
    total_gaps = (num_blocks - 1) * gap
    block_width = (width - total_gaps) // num_blocks
    filled_blocks = 0
    if percent is not None:
        filled_blocks = max(0, min(num_blocks, round((percent / 100.0) * num_blocks)))

    for i in range(num_blocks):
        bx = x + i * (block_width + gap)
        by = y
        if i < filled_blocks:
            draw.rectangle([bx, by, bx + block_width, by + height], fill=active_color)
        else:
            draw.rectangle(
                [bx, by, bx + block_width, by + height],
                fill=empty_color,
                outline=border_color,
            )


def render_provider_screen(
    data: UsageData,
    page_num: int = 1,
    total_pages: int = 3,
) -> Image.Image:
    # 128x128 canvas
    img = Image.new("RGB", (128, 128), (11, 15, 25))  # Deep slate night blue
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Outer border (subtle 1px frame)
    draw.rectangle([0, 0, 127, 127], outline=(25, 35, 55))

    # --- Header Colors by Provider ---
    p_name = data.provider_name.upper()
    if p_name == "CLAUDE":
        c_title = (245, 140, 60)    # Anthropic coral/amber
        c_badge_bg = (35, 25, 20)
        c_badge_border = (80, 50, 30)
        c_badge_fg = (250, 175, 100)
    elif p_name == "CODEX":
        c_title = (50, 215, 145)    # OpenAI emerald
        c_badge_bg = (18, 35, 28)
        c_badge_border = (30, 80, 60)
        c_badge_fg = (120, 240, 180)
    elif p_name == "GEMINI":
        c_title = (90, 165, 255)    # Google Gemini azure
        c_badge_bg = (20, 30, 48)
        c_badge_border = (40, 70, 115)
        c_badge_fg = (150, 200, 255)
    else:
        c_title = (200, 200, 220)
        c_badge_bg = (25, 30, 40)
        c_badge_border = (50, 60, 80)
        c_badge_fg = (180, 190, 210)

    # Header Title
    draw.text((8, 6), p_name, fill=c_title, font=fonts["header"])

    # Model / Plan Badge (top-right)
    badge_label = (data.model or p_name).upper()
    bbox = fonts["badge"].getbbox(badge_label)
    bw = bbox[2] - bbox[0] + 6
    bx = 120 - bw
    by = 8
    draw.rectangle([bx, by, 120, by + 12], fill=c_badge_bg, outline=c_badge_border)
    draw.text((bx + 3, by), badge_label, fill=c_badge_fg, font=fonts["badge"])

    # Header divider line
    draw.line([(8, 22), (120, 22)], fill=(25, 38, 60), width=1)

    # --- Primary Block (5H, USAGE, or SESSION) ---
    p_label = data.primary_label.upper()
    draw.text((8, 26), p_label, fill=(140, 155, 175), font=fonts["label"])

    if data.primary_pct is not None:
        p_val_str = f"{data.primary_pct}%"
        if data.primary_pct >= 90:
            c_pval = (245, 75, 75)   # Red
        elif data.primary_pct >= 75:
            c_pval = (245, 175, 50)  # Amber
        else:
            c_pval = (50, 230, 140)  # Emerald
    else:
        p_val_str = "N/A"
        c_pval = (110, 125, 145)     # Muted gray

    pv_bbox = fonts["value"].getbbox(p_val_str)
    pvw = pv_bbox[2] - pv_bbox[0]
    draw.text((120 - pvw, 25), p_val_str, fill=c_pval, font=fonts["value"])

    # Primary Bar: 10 blocks, width 112px, height 7px
    draw_progress_bar(draw, 8, 41, 112, 7, data.primary_pct, active_color=c_pval)

    # Primary Reset
    reset_str = data.primary_reset or "N/A"
    draw.text((8, 52), f"RESET  {reset_str}", fill=(90, 115, 145), font=fonts["reset"])

    # Section divider
    draw.line([(8, 66), (120, 66)], fill=(20, 30, 48), width=1)

    # --- Secondary Block (WEEK) ---
    s_label = data.secondary_label.upper()
    draw.text((8, 70), s_label, fill=(140, 155, 175), font=fonts["label"])

    if data.secondary_pct is not None:
        s_val_str = f"{data.secondary_pct}%"
        if data.is_stale:
            c_sval = (245, 175, 50)  # Amber for stale cached metric
        elif data.secondary_pct >= 90:
            c_sval = (245, 75, 75)
        elif data.secondary_pct >= 75:
            c_sval = (245, 175, 50)
        else:
            c_sval = (55, 185, 245)  # Cyan/Blue
    else:
        s_val_str = "N/A"
        c_sval = (110, 125, 145)

    sv_bbox = fonts["value"].getbbox(s_val_str)
    svw = sv_bbox[2] - sv_bbox[0]
    draw.text((120 - svw, 69), s_val_str, fill=c_sval, font=fonts["value"])

    # Secondary Bar: 10 blocks
    draw_progress_bar(draw, 8, 85, 112, 7, data.secondary_pct, active_color=c_sval)

    # Secondary Reset
    s_reset_str = data.secondary_reset or "N/A"
    draw.text((8, 96), f"RESET  {s_reset_str}", fill=(90, 115, 145), font=fonts["reset"])

    # --- Footer Info & Pagination ---
    # Dot indicator & status label according to rendering rules
    if data.is_stale:
        dot_color = (245, 175, 50)   # Amber
        sub_text = "STALE (8D)" if "8" in (data.freshness or "") else "STALE CACHE"
    elif data.primary_status == "LOCAL ONLY":
        dot_color = (80, 115, 160)   # Slate blue
        sub_text = "LOCAL ONLY"
    elif data.primary_status == "ACTIVE":
        dot_color = (50, 230, 140)   # Emerald
        sub_text = "ACTIVE"
    elif data.primary_pct is not None:
        dot_color = (100, 150, 220)  # Cyan
        sub_text = data.plan_tier or "READY"
    else:
        dot_color = (90, 100, 120)   # Neutral gray
        sub_text = data.primary_status or "LOCAL ONLY"

    draw.ellipse([8, 114, 13, 119], fill=dot_color)
    draw.text((17, 111), sub_text, fill=(90, 110, 135), font=fonts["reset"])

    # Page indicator (e.g. 1/3)
    if total_pages > 1:
        page_str = f"{page_num}/{total_pages}"
        pb_bbox = fonts["reset"].getbbox(page_str)
        pbw = pb_bbox[2] - pb_bbox[0]
        draw.text((120 - pbw, 111), page_str, fill=(75, 95, 125), font=fonts["reset"])

    return img


if __name__ == "__main__":
    from providers import ClaudeProvider, CodexProvider, GeminiProvider

    for idx, prov in enumerate([ClaudeProvider(), CodexProvider(), GeminiProvider()], start=1):
        d = prov.get_usage()
        im = render_provider_screen(d, page_num=idx, total_pages=3)
        fn = f"preview_{d.provider_name.lower()}.png"
        im.save(fn)
        print(f"Saved {fn} (128x128)")
