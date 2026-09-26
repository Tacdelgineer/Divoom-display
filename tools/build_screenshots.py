#!/usr/bin/env python3
"""
Generate crisp, clean, high-resolution screenshots for AI Desk Dashboard documentation:
1. assets/screenshots/01_desktop_overview.png (Complete desktop companion app window)
2. assets/screenshots/02_quota_remaining_cards.png (Codex & Gemini % LEFT cards)
3. assets/screenshots/03_btc_sparkline.png (BTC live price & phosphor sparkline)
4. assets/screenshots/04_gpu_and_dgx_monitoring.png (Local RTX & Remote DGX Spark)
5. assets/screenshots/05_ai_activity_and_services.png (AI Activity feed & Services table)
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    font_paths = [
        "C:\\Windows\\Fonts\\consola.ttf" if not bold else "C:\\Windows\\Fonts\\consolab.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf" if not bold else "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arial.ttf" if not bold else "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

# Colors
C_BG = (10, 14, 23)
C_HEADER_BG = (8, 12, 18)
C_CARD_BG = (17, 22, 34)
C_CARD_BORDER = (30, 39, 58)
C_ACTIVE_CYAN = (0, 229, 255)
C_ACTIVE_TAG_BG = (8, 43, 56)
C_TEXT_WHITE = (230, 237, 245)
C_TEXT_MUTED = (125, 140, 159)
C_TEXT_DIM = (80, 94, 115)
C_GREEN = (50, 230, 140)
C_AMBER = (245, 175, 50)
C_RED = (245, 75, 75)
C_BLUE = (90, 165, 255)
C_CORAL = (245, 140, 60)
C_PURPLE = (185, 140, 255)
C_GOLD = (247, 147, 26)
C_NVIDIA = (118, 185, 0)

def draw_segmented_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float | None, color: tuple):
    segments = 20
    gap = 2
    seg_w = (w - (segments - 1) * gap) / segments
    active_count = int(round((pct / 100.0) * segments)) if pct is not None else 0

    for i in range(segments):
        sx = x + i * (seg_w + gap)
        fill = color if i < active_count else (24, 32, 46)
        draw.rectangle([sx, y, sx + seg_w, y + h], fill=fill)

def draw_card(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    title: str,
    title_color: tuple,
    badge_text: str,
    badge_color: tuple,
    is_active: bool = False,
):
    border_col = C_ACTIVE_CYAN if is_active else C_CARD_BORDER
    border_w = 2 if is_active else 1
    bg_col = (18, 26, 43) if is_active else C_CARD_BG

    draw.rectangle([x, y, x + w, y + h], fill=bg_col, outline=border_col, width=border_w)

    f_title = get_font(12, bold=True)
    f_badge = get_font(9, bold=True)

    draw.text((x + 8, y + 6), title, fill=title_color, font=f_title)

    # Top right tag
    if is_active:
        draw.rectangle([x + w - 74, y + 4, x + w - 6, y + 18], fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
        draw.text((x + w - 66, y + 5), "ON MINITOO", fill=C_ACTIVE_CYAN, font=f_badge)
    else:
        draw.rectangle([x + w - 64, y + 4, x + w - 6, y + 18], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.ellipse([x + w - 58, y + 9, x + w - 53, y + 14], fill=badge_color)
        draw.text((x + w - 48, y + 5), badge_text, fill=C_TEXT_WHITE, font=f_badge)

    draw.line([x + 6, y + 23, x + w - 6, y + 23], fill=(27, 35, 53), width=1)


def render_full_desktop_overview(out_path: str):
    """Renders the full 628x512 Desktop Dashboard Companion app window."""
    w, h = 628, 512
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_ui = get_font(11, bold=True)
    f_sub = get_font(9, bold=False)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)

    # Header Bar
    draw.rectangle([0, 0, w, 40], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    # Title
    draw.text((12, 10), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_ui)
    draw.text((160, 13), "v0.1.0", fill=C_TEXT_DIM, font=f_sub)

    # Status / Controls in Header
    # Auto-cycle tag
    draw.rectangle([w - 280, 8, w - 195, 30], fill=(16, 24, 38), outline=C_GREEN)
    draw.ellipse([w - 274, 16, w - 268, 22], fill=C_GREEN)
    draw.text((w - 262, 11), "CYCLE 5S", fill=C_GREEN, font=f_sub)

    # MiniToo status tag
    draw.rectangle([w - 185, 8, w - 68, 30], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.ellipse([w - 179, 16, w - 173, 22], fill=C_ACTIVE_CYAN)
    draw.text((w - 167, 11), "MINITOO OK", fill=C_ACTIVE_CYAN, font=f_sub)

    # Settings button
    draw.rectangle([w - 58, 8, w - 12, 30], fill=(20, 28, 44), outline=(40, 52, 75))
    draw.text((w - 48, 11), "GEAR", fill=C_TEXT_MUTED, font=f_sub)

    # 3x3 Grid of Cards
    margin = 8
    gap = 8
    card_w = 196
    card_h = 136

    # Card 1: CODEX
    c1_x = margin
    c1_y = 48
    draw_card(draw, c1_x, c1_y, card_w, card_h, "CODEX", C_GREEN, "ACTIVE", C_GREEN, is_active=True)
    draw.text((c1_x + 8, c1_y + 34), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c1_x + card_w - 65, c1_y + 34), "78% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 47, card_w - 16, 6, 78, C_GREEN)
    draw.text((c1_x + 8, c1_y + 58), "RESET 2H 14M", fill=C_TEXT_DIM, font=f_small)

    draw.text((c1_x + 8, c1_y + 74), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c1_x + card_w - 65, c1_y + 74), "82% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 87, card_w - 16, 6, 82, C_GREEN)
    draw.text((c1_x + 8, c1_y + 98), "RESET 4D 18H", fill=C_TEXT_DIM, font=f_small)

    draw.line([c1_x + 8, c1_y + 114, c1_x + card_w - 8, c1_y + 114], fill=(24, 32, 48))
    draw.text((c1_x + 8, c1_y + 118), "PLUS", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + card_w - 55, c1_y + 118), "GPT-4O", fill=C_TEXT_DIM, font=f_small)

    # Card 2: GEMINI
    c2_x = margin + card_w + gap
    c2_y = 48
    draw_card(draw, c2_x, c2_y, card_w, card_h, "GEMINI", C_BLUE, "LIVE", C_GREEN)
    draw.text((c2_x + 8, c2_y + 34), "FLASH", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2_x + card_w - 65, c2_y + 34), "94% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 47, card_w - 16, 6, 94, C_GREEN)
    draw.text((c2_x + 8, c2_y + 58), "RESET 23H 45M", fill=C_TEXT_DIM, font=f_small)

    draw.text((c2_x + 8, c2_y + 74), "PRO", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2_x + card_w - 65, c2_y + 74), "88% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 87, card_w - 16, 6, 88, C_GREEN)
    draw.text((c2_x + 8, c2_y + 98), "RESET 23H 45M", fill=C_TEXT_DIM, font=f_small)

    draw.line([c2_x + 8, c2_y + 114, c2_x + card_w - 8, c2_y + 114], fill=(24, 32, 48))
    draw.text((c2_x + 8, c2_y + 118), "GOOGLE ONE", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2_x + card_w - 75, c2_y + 118), "ANTIGRAVITY", fill=C_TEXT_DIM, font=f_small)

    # Card 3: CLAUDE
    c3_x = margin + (card_w + gap) * 2
    c3_y = 48
    draw_card(draw, c3_x, c3_y, card_w, card_h, "CLAUDE", C_CORAL, "READY", C_TEXT_MUTED)
    draw.text((c3_x + 8, c3_y + 34), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c3_x + card_w - 38, c3_y + 34), "N/A", fill=C_TEXT_MUTED, font=f_bold)
    draw_segmented_bar(draw, c3_x + 8, c3_y + 47, card_w - 16, 6, None, C_TEXT_MUTED)
    draw.text((c3_x + 8, c3_y + 58), "NO METRIC API", fill=C_TEXT_DIM, font=f_small)

    draw.text((c3_x + 8, c3_y + 74), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c3_x + card_w - 38, c3_y + 74), "N/A", fill=C_TEXT_MUTED, font=f_bold)
    draw_segmented_bar(draw, c3_x + 8, c3_y + 87, card_w - 16, 6, None, C_TEXT_MUTED)
    draw.text((c3_x + 8, c3_y + 98), "NO LOCAL EXPORT", fill=C_TEXT_DIM, font=f_small)

    draw.line([c3_x + 8, c3_y + 114, c3_x + card_w - 8, c3_y + 114], fill=(24, 32, 48))
    draw.text((c3_x + 8, c3_y + 118), "PRO PLAN", fill=C_TEXT_DIM, font=f_small)
    draw.text((c3_x + card_w - 55, c3_y + 118), "SONNET 3.7", fill=C_TEXT_DIM, font=f_small)

    # Card 4: LOCAL PC (GPU)
    c4_x = margin
    c4_y = 48 + card_h + gap
    draw_card(draw, c4_x, c4_y, card_w, card_h, "LOCAL PC", (55, 195, 245), "52C OK", C_GREEN)
    draw.text((c4_x + 8, c4_y + 32), "GPU 42%", fill=C_GREEN, font=f_bold)
    draw.text((c4_x + card_w - 55, c4_y + 32), "52 C", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c4_x + 8, c4_y + 44, card_w - 16, 5, 42, C_GREEN)

    draw.text((c4_x + 8, c4_y + 56), "VRAM 11.2 / 24 GB", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c4_x + 8, c4_y + 68, card_w - 16, 5, 47, (55, 195, 245))

    draw.text((c4_x + 8, c4_y + 80), "RAM 38.4 / 64 GB (60%)", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c4_x + 8, c4_y + 92, card_w - 16, 5, 60, (55, 195, 245))

    draw.line([c4_x + 8, c4_y + 114, c4_x + card_w - 8, c4_y + 114], fill=(24, 32, 48))
    draw.text((c4_x + 8, c4_y + 118), "RTX 4090", fill=C_TEXT_DIM, font=f_small)
    draw.text((c4_x + card_w - 65, c4_y + 118), "CPU 18%", fill=C_TEXT_DIM, font=f_small)

    # Card 5: DGX SPARK
    c5_x = margin + card_w + gap
    c5_y = 48 + card_h + gap
    draw_card(draw, c5_x, c5_y, card_w, card_h, "DGX SPARK", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((c5_x + 8, c5_y + 32), "GPU 85%", fill=C_AMBER, font=f_bold)
    draw.text((c5_x + card_w - 55, c5_y + 32), "64 C", fill=C_AMBER, font=f_bold)
    draw_segmented_bar(draw, c5_x + 8, c5_y + 44, card_w - 16, 5, 85, C_AMBER)

    draw.text((c5_x + 8, c5_y + 56), "VRAM 72.4 / 96 GB", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c5_x + 8, c5_y + 68, card_w - 16, 5, 75, C_NVIDIA)

    draw.text((c5_x + 8, c5_y + 80), "MEM 214 / 512 GB (42%)", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c5_x + 8, c5_y + 92, card_w - 16, 5, 42, C_NVIDIA)

    draw.line([c5_x + 8, c5_y + 114, c5_x + card_w - 8, c5_y + 114], fill=(24, 32, 48))
    draw.text((c5_x + 8, c5_y + 118), "GB10 (DGX)", fill=C_TEXT_DIM, font=f_small)
    draw.text((c5_x + card_w - 65, c5_y + 118), "LOAD 4.2", fill=C_TEXT_DIM, font=f_small)

    # Card 6: BTC SPARKLINE
    c6_x = margin + (card_w + gap) * 2
    c6_y = 48 + card_h + gap
    draw_card(draw, c6_x, c6_y, card_w, card_h, "BITCOIN", C_GOLD, "+3.8%", C_GREEN)
    draw.text((c6_x + 8, c6_y + 32), "$96,420", fill=C_GOLD, font=f_bold)
    draw.text((c6_x + card_w - 48, c6_y + 32), "24H", fill=C_TEXT_DIM, font=f_small)

    # BTC Sparkline graph box
    gx = c6_x + 8
    gy = c6_y + 48
    gw = card_w - 16
    gh = 48
    draw.rectangle([gx, gy, gx + gw, gy + gh], fill=(12, 17, 26), outline=(24, 34, 52))

    # Sparkline points
    btc_pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = gw / (len(btc_pts) - 1)
    coords = []
    for i, v in enumerate(btc_pts):
        coords.append((gx + i * step, gy + gh - v * (gh - 6) - 3))
    for i in range(len(coords) - 1):
        draw.line([coords[i], coords[i+1]], fill=C_GREEN, width=2)
        draw.line([coords[i+1][0], coords[i+1][1], coords[i+1][0], gy + gh - 1], fill=(16, 42, 34), width=1)

    draw.line([c6_x + 8, c6_y + 114, c6_x + card_w - 8, c6_y + 114], fill=(24, 32, 48))
    draw.text((c6_x + 8, c6_y + 118), "L: $92,800", fill=C_TEXT_DIM, font=f_small)
    draw.text((c6_x + card_w - 65, c6_y + 118), "H: $97,100", fill=C_TEXT_DIM, font=f_small)

    # Card 7: AI ACTIVITY
    c7_x = margin
    c7_y = 48 + (card_h + gap) * 2
    draw_card(draw, c7_x, c7_y, card_w, card_h, "AI ACTIVITY", C_PURPLE, "ACTIVE", C_GREEN)
    draw.text((c7_x + 8, c7_y + 32), "CODEX", fill=C_GREEN, font=f_bold)
    draw.text((c7_x + card_w - 65, c7_y + 32), "12M AGO", fill=C_TEXT_DIM, font=f_small)
    draw.text((c7_x + 8, c7_y + 46), "Prompt spec & tests", fill=C_TEXT_WHITE, font=f_small)
    draw.text((c7_x + 8, c7_y + 58), "+142 -28 lines", fill=(55, 195, 245), font=f_small)

    draw.line([c7_x + 8, c7_y + 72, c7_x + card_w - 8, c7_y + 72], fill=(22, 30, 46))
    draw.text((c7_x + 8, c7_y + 78), "ANTIGRAVITY", fill=C_BLUE, font=f_bold)
    draw.text((c7_x + card_w - 65, c7_y + 78), "1H AGO", fill=C_TEXT_DIM, font=f_small)
    draw.text((c7_x + 8, c7_y + 92), "Subprocess window fix", fill=C_TEXT_WHITE, font=f_small)

    draw.line([c7_x + 8, c7_y + 114, c7_x + card_w - 8, c7_y + 114], fill=(24, 32, 48))
    draw.text((c7_x + 8, c7_y + 118), "2 RUNS", fill=C_TEXT_DIM, font=f_small)
    draw.text((c7_x + card_w - 65, c7_y + 118), "TODAY", fill=C_TEXT_DIM, font=f_small)

    # Card 8: SERVICES
    c8_x = margin + card_w + gap
    c8_y = 48 + (card_h + gap) * 2
    draw_card(draw, c8_x, c8_y, card_w, card_h, "SERVICES", C_GREEN, "5/5 UP", C_GREEN)
    svcs = [("DGX (SSH)", True), ("OLLAMA", True), ("COMFYUI", True), ("FORGE3D", True), ("HERMES", True)]
    sy = c8_y + 30
    for s_name, s_up in svcs:
        draw.ellipse([c8_x + 10, sy + 3, c8_x + 16, sy + 9], fill=C_GREEN if s_up else C_RED)
        draw.text((c8_x + 22, sy), s_name, fill=C_TEXT_WHITE if s_up else C_TEXT_MUTED, font=f_small)
        draw.text((c8_x + card_w - 36, sy), "UP" if s_up else "DOWN", fill=C_GREEN if s_up else C_RED, font=f_small)
        sy += 16

    draw.line([c8_x + 8, c8_y + 114, c8_x + card_w - 8, c8_y + 114], fill=(24, 32, 48))
    draw.text((c8_x + 8, c8_y + 118), "TAILSCALE", fill=C_TEXT_DIM, font=f_small)
    draw.text((c8_x + card_w - 55, c8_y + 118), "HEALTH", fill=C_TEXT_DIM, font=f_small)

    # Card 9: CODING
    c9_x = margin + (card_w + gap) * 2
    c9_y = 48 + (card_h + gap) * 2
    draw_card(draw, c9_x, c9_y, card_w, card_h, "CODING", C_PURPLE, "CLEAN", C_GREEN)
    draw.text((c9_x + 8, c9_y + 32), "BRANCH", fill=C_TEXT_MUTED, font=f_small)
    draw.text((c9_x + card_w - 55, c9_y + 32), "main", fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((c9_x + 8, c9_y + 52), "STATUS", fill=C_TEXT_MUTED, font=f_small)
    draw.text((c9_x + card_w - 65, c9_y + 52), "WORKING", fill=C_GREEN, font=f_bold)

    draw.text((c9_x + 8, c9_y + 72), "COMMIT", fill=C_TEXT_MUTED, font=f_small)
    draw.text((c9_x + card_w - 65, c9_y + 72), "v0.1.0", fill=C_TEXT_WHITE, font=f_bold)

    draw.line([c9_x + 8, c9_y + 114, c9_x + card_w - 8, c9_y + 114], fill=(24, 32, 48))
    draw.text((c9_x + 8, c9_y + 118), "LOCAL REPO", fill=C_TEXT_DIM, font=f_small)
    draw.text((c9_x + card_w - 65, c9_y + 118), "GIT 2.44", fill=C_TEXT_DIM, font=f_small)

    # Footer Status Bar
    draw.rectangle([0, h - 28, w, h], fill=(7, 10, 16), outline=(20, 28, 42), width=1)
    draw.text((12, h - 20), "Space / Arrows: Navigate Pages  ·  Click: Send Card to MiniToo", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((w - 180, h - 20), "MiniToo: Bluetooth Connected", fill=C_ACTIVE_CYAN, font=f_sub)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_quota_cards_screenshot(out_path: str):
    """Close up: Codex & Gemini quota cards showing % LEFT."""
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_bold = get_font(11, bold=True)
    f_small = get_font(9, bold=False)

    card_w = 196
    card_h = 144
    gap = 12

    # Codex Card
    c1_x = 8
    c1_y = 8
    draw_card(draw, c1_x, c1_y, card_w, card_h, "CODEX", C_GREEN, "ACTIVE", C_GREEN, is_active=True)
    draw.text((c1_x + 8, c1_y + 34), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c1_x + card_w - 72, c1_y + 34), "78% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 48, card_w - 16, 7, 78, C_GREEN)
    draw.text((c1_x + 8, c1_y + 60), "RESET 2H 14M", fill=C_TEXT_DIM, font=f_small)

    draw.text((c1_x + 8, c1_y + 78), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c1_x + card_w - 72, c1_y + 78), "82% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 92, card_w - 16, 7, 82, C_GREEN)
    draw.text((c1_x + 8, c1_y + 104), "RESET 4D 18H", fill=C_TEXT_DIM, font=f_small)

    draw.line([c1_x + 8, c1_y + 120, c1_x + card_w - 8, c1_y + 120], fill=(24, 32, 48))
    draw.text((c1_x + 8, c1_y + 124), "PLUS ACCOUNT", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + card_w - 60, c1_y + 124), "GPT-4O", fill=C_TEXT_DIM, font=f_small)

    # Gemini Card
    c2_x = c1_x + card_w + gap
    c2_y = 8
    draw_card(draw, c2_x, c2_y, card_w, card_h, "GEMINI", C_BLUE, "LIVE", C_GREEN)
    draw.text((c2_x + 8, c2_y + 34), "FLASH", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2_x + card_w - 72, c2_y + 34), "94% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 48, card_w - 16, 7, 94, C_GREEN)
    draw.text((c2_x + 8, c2_y + 60), "RESET 23H 45M", fill=C_TEXT_DIM, font=f_small)

    draw.text((c2_x + 8, c2_y + 78), "PRO", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2_x + card_w - 72, c2_y + 78), "88% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 92, card_w - 16, 7, 88, C_GREEN)
    draw.text((c2_x + 8, c2_y + 104), "RESET 23H 45M", fill=C_TEXT_DIM, font=f_small)

    draw.line([c2_x + 8, c2_y + 120, c2_x + card_w - 8, c2_y + 120], fill=(24, 32, 48))
    draw.text((c2_x + 8, c2_y + 124), "GOOGLE ONE", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2_x + card_w - 80, c2_y + 124), "ANTIGRAVITY", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_btc_sparkline_screenshot(out_path: str):
    """Close up: BTC price & 16-point live sparkline."""
    w, h = 260, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_bold = get_font(12, bold=True)
    f_price = get_font(18, bold=True)
    f_small = get_font(9, bold=False)

    card_w = 244
    card_h = 144
    cx, cy = 8, 8

    draw_card(draw, cx, cy, card_w, card_h, "BITCOIN", C_GOLD, "+3.8%", C_GREEN)
    draw.text((cx + 10, cy + 30), "$96,420", fill=C_GOLD, font=f_price)
    draw.text((cx + card_w - 55, cy + 34), "24H CHG", fill=C_TEXT_DIM, font=f_small)

    gx = cx + 8
    gy = cy + 54
    gw = card_w - 16
    gh = 52
    draw.rectangle([gx, gy, gx + gw, gy + gh], fill=(12, 17, 26), outline=(24, 34, 52))

    btc_pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = gw / (len(btc_pts) - 1)
    coords = []
    for i, v in enumerate(btc_pts):
        coords.append((gx + i * step, gy + gh - v * (gh - 6) - 3))
    for i in range(len(coords) - 1):
        draw.line([coords[i], coords[i+1]], fill=C_GREEN, width=2)
        draw.line([coords[i+1][0], coords[i+1][1], coords[i+1][0], gy + gh - 1], fill=(16, 42, 34), width=1)

    draw.line([cx + 8, cy + 118, cx + card_w - 8, cy + 118], fill=(24, 32, 48))
    draw.text((cx + 8, cy + 122), "L: $92,800", fill=C_TEXT_DIM, font=f_small)
    draw.text((cx + card_w - 80, cy + 122), "H: $97,100", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_gpu_dgx_screenshot(out_path: str):
    """Close up: Local PC (RTX GPU) & Remote DGX Spark."""
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_bold = get_font(11, bold=True)
    f_small = get_font(9, bold=False)

    card_w = 196
    card_h = 144
    gap = 12

    # Local PC
    c1_x = 8
    c1_y = 8
    draw_card(draw, c1_x, c1_y, card_w, card_h, "LOCAL PC", (55, 195, 245), "52C OK", C_GREEN)
    draw.text((c1_x + 8, c1_y + 32), "GPU 42%", fill=C_GREEN, font=f_bold)
    draw.text((c1_x + card_w - 55, c1_y + 32), "52 C", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 45, card_w - 16, 6, 42, C_GREEN)

    draw.text((c1_x + 8, c1_y + 58), "VRAM 11.2 / 24 GB", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 71, card_w - 16, 6, 47, (55, 195, 245))

    draw.text((c1_x + 8, c1_y + 84), "RAM 38.4 / 64 GB (60%)", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c1_x + 8, c1_y + 97, card_w - 16, 6, 60, (55, 195, 245))

    draw.line([c1_x + 8, c1_y + 118, c1_x + card_w - 8, c1_y + 118], fill=(24, 32, 48))
    draw.text((c1_x + 8, c1_y + 122), "RTX 4090", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + card_w - 65, c1_y + 122), "CPU 18%", fill=C_TEXT_DIM, font=f_small)

    # DGX Spark
    c2_x = c1_x + card_w + gap
    c2_y = 8
    draw_card(draw, c2_x, c2_y, card_w, card_h, "DGX SPARK", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((c2_x + 8, c2_y + 32), "GPU 85%", fill=C_AMBER, font=f_bold)
    draw.text((c2_x + card_w - 55, c2_y + 32), "64 C", fill=C_AMBER, font=f_bold)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 45, card_w - 16, 6, 85, C_AMBER)

    draw.text((c2_x + 8, c2_y + 58), "VRAM 72.4 / 96 GB", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 71, card_w - 16, 6, 75, C_NVIDIA)

    draw.text((c2_x + 8, c2_y + 84), "MEM 214 / 512 GB (42%)", fill=C_TEXT_MUTED, font=f_small)
    draw_segmented_bar(draw, c2_x + 8, c2_y + 97, card_w - 16, 6, 42, C_NVIDIA)

    draw.line([c2_x + 8, c2_y + 118, c2_x + card_w - 8, c2_y + 118], fill=(24, 32, 48))
    draw.text((c2_x + 8, c2_y + 122), "GB10 (DGX)", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2_x + card_w - 65, c2_y + 122), "LOAD 4.2", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_activity_services_screenshot(out_path: str):
    """Close up: AI Activity & Services status."""
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_bold = get_font(11, bold=True)
    f_small = get_font(9, bold=False)

    card_w = 196
    card_h = 144
    gap = 12

    # AI Activity
    c1_x = 8
    c1_y = 8
    draw_card(draw, c1_x, c1_y, card_w, card_h, "AI ACTIVITY", C_PURPLE, "ACTIVE", C_GREEN)
    draw.text((c1_x + 8, c1_y + 32), "CODEX", fill=C_GREEN, font=f_bold)
    draw.text((c1_x + card_w - 65, c1_y + 32), "12M AGO", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + 8, c1_y + 48), "Prompt spec & tests", fill=C_TEXT_WHITE, font=f_small)
    draw.text((c1_x + 8, c1_y + 62), "+142 -28 lines", fill=(55, 195, 245), font=f_small)

    draw.line([c1_x + 8, c1_y + 78, c1_x + card_w - 8, c1_y + 78], fill=(22, 30, 46))
    draw.text((c1_x + 8, c1_y + 84), "ANTIGRAVITY", fill=C_BLUE, font=f_bold)
    draw.text((c1_x + card_w - 65, c1_y + 84), "1H AGO", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + 8, c1_y + 98), "Subprocess window fix", fill=C_TEXT_WHITE, font=f_small)

    draw.line([c1_x + 8, c1_y + 118, c1_x + card_w - 8, c1_y + 118], fill=(24, 32, 48))
    draw.text((c1_x + 8, c1_y + 122), "2 RUNS TODAY", fill=C_TEXT_DIM, font=f_small)
    draw.text((c1_x + card_w - 65, c1_y + 122), "SYNC OK", fill=C_TEXT_DIM, font=f_small)

    # Services
    c2_x = c1_x + card_w + gap
    c2_y = 8
    draw_card(draw, c2_x, c2_y, card_w, card_h, "SERVICES", C_GREEN, "5/5 UP", C_GREEN)
    svcs = [("DGX (SSH)", True), ("OLLAMA", True), ("COMFYUI", True), ("FORGE3D", True), ("HERMES", True)]
    sy = c2_y + 30
    for s_name, s_up in svcs:
        draw.ellipse([c2_x + 10, sy + 3, c2_x + 16, sy + 9], fill=C_GREEN if s_up else C_RED)
        draw.text((c2_x + 22, sy), s_name, fill=C_TEXT_WHITE if s_up else C_TEXT_MUTED, font=f_small)
        draw.text((c2_x + card_w - 36, sy), "UP" if s_up else "DOWN", fill=C_GREEN if s_up else C_RED, font=f_small)
        sy += 17

    draw.line([c2_x + 8, c2_y + 118, c2_x + card_w - 8, c2_y + 118], fill=(24, 32, 48))
    draw.text((c2_x + 8, c2_y + 122), "TAILSCALE", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2_x + card_w - 55, c2_y + 122), "HEALTH", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    os.makedirs("assets/screenshots", exist_ok=True)
    render_full_desktop_overview("assets/screenshots/01_desktop_overview.png")
    render_quota_cards_screenshot("assets/screenshots/02_quota_remaining_cards.png")
    render_btc_sparkline_screenshot("assets/screenshots/03_btc_sparkline.png")
    render_gpu_dgx_screenshot("assets/screenshots/04_gpu_and_dgx_monitoring.png")
    render_activity_services_screenshot("assets/screenshots/05_ai_activity_and_services.png")
