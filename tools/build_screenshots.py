#!/usr/bin/env python3
"""
Generate crisp, clean, high-resolution screenshots for AI Desk Dashboard documentation:
1. assets/screenshots/preset-ai.png (AI hero preset: Codex, Gemini, Claude quotas + AI Activity)
2. assets/screenshots/preset-crypto.png (CRYPTO hero preset: BTC, ETH, SOL, DOGE, PEPE + sparklines)
3. assets/screenshots/preset-stocks.png (STOCKS hero preset: Top 10 Volatile Stocks Scanner)
4. assets/screenshots/preset-system.png (SYSTEM hero preset: Local RTX, DGX Spark, Services, Coding)
5. assets/screenshots/preset-all.png (ALL preset with all 4 dashboard sections)
6. assets/screenshots/settings-dashboard.png (Redesigned 5-tab Settings UI: DASHBOARD tab with Desktop & MiniToo toggles)
7. assets/screenshots/settings-minitoo.png (Redesigned 5-tab Settings UI: MINITOO tab with diagnostics & Low Interference mode)
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
C_SOLANA = (20, 241, 149)
C_ETH = (98, 126, 234)
C_DOGE = (194, 166, 51)
C_PEPE = (72, 199, 116)

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

    f_title = get_font(11, bold=True)
    f_badge = get_font(9, bold=True)

    draw.text((x + 8, y + 6), title, fill=title_color, font=f_title)

    if is_active:
        draw.rectangle([x + w - 76, y + 4, x + w - 6, y + 18], fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
        draw.text((x + w - 68, y + 5), "ON MINITOO", fill=C_ACTIVE_CYAN, font=f_badge)
    else:
        draw.rectangle([x + w - 66, y + 4, x + w - 6, y + 18], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.ellipse([x + w - 58, y + 9, x + w - 53, y + 14], fill=badge_color)
        draw.text((x + w - 48, y + 5), badge_text, fill=C_TEXT_WHITE, font=f_badge)

    draw.line([x + 6, y + 23, x + w - 6, y + 23], fill=(27, 35, 53), width=1)

def draw_header(draw: ImageDraw.ImageDraw, w: int, active_preset: str = "ALL"):
    f_ui = get_font(11, bold=True)
    f_sub = get_font(9, bold=False)
    f_btn = get_font(8, bold=True)

    draw.rectangle([0, 0, w, 64], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.text((12, 10), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_ui)
    draw.text((160, 13), "v0.3.0", fill=C_TEXT_DIM, font=f_sub)

    # MiniToo status pill
    draw.rectangle([w - 290, 8, w - 175, 28], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.ellipse([w - 284, 15, w - 278, 21], fill=C_GREEN)
    draw.text((w - 272, 11), "MINITOO ● COM13", fill=C_ACTIVE_CYAN, font=f_sub)

    # Autostart
    draw.rectangle([w - 168, 8, w - 84, 28], fill=(14, 36, 25), outline=C_GREEN)
    draw.text((w - 160, 11), "AUTOSTART: ON", fill=C_GREEN, font=f_btn)

    # Settings
    draw.rectangle([w - 78, 8, w - 12, 28], fill=(20, 28, 44), outline=(40, 52, 75))
    draw.text((w - 70, 11), "⚙ SETTINGS", fill=C_ACTIVE_CYAN, font=f_btn)

    # Line 2: Presets (Milestone 13: ALL | AI | CRYPTO | STOCKS | SYSTEM)
    draw.text((12, 42), "PRESET:", fill=C_TEXT_DIM, font=f_btn)
    px = 72
    for p in ["ALL", "AI", "CRYPTO", "STOCKS", "SYSTEM"]:
        is_act = (p == active_preset)
        p_bg = (11, 38, 56) if is_act else (16, 22, 34)
        p_fg = C_ACTIVE_CYAN if is_act else C_TEXT_MUTED
        p_bd = C_ACTIVE_CYAN if is_act else (28, 37, 54)
        btn_w = 68 if p in ["CRYPTO", "STOCKS", "SYSTEM"] else 52
        draw.rectangle([px, 34, px + btn_w, 54], fill=p_bg, outline=p_bd, width=1)
        draw.text((px + 8, 38), f"[ {p} ]", fill=p_fg, font=f_btn)
        px += btn_w + 6

# ---------------------------------------------------------------------------
# 1. PRESET ALL SCREENSHOT
# ---------------------------------------------------------------------------
def render_preset_all_screenshot(out_path: str):
    """Renders comprehensive ALL preset dashboard with all 4 sections."""
    w, h = 680, 760
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="ALL")

    f_sec = get_font(9, bold=True)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)

    curr_y = 74
    card_w = 212
    card_h = 120
    gap = 8
    m = 10

    # 1. SECTION: CRYPTO MARKETS
    draw.text((m, curr_y), "─── [ CRYPTO MARKETS ] ", fill=C_GOLD, font=f_sec)
    draw.rectangle([w - 88, curr_y - 2, w - m, curr_y + 14], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.text((w - 82, curr_y + 1), "🔍 FOCUS", fill=C_ACTIVE_CYAN, font=f_small)
    draw.line([m + 130, curr_y + 6, w - 96, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # BTC, ETH, SOL
    c1 = (m, curr_y)
    draw_card(draw, c1[0], c1[1], card_w, card_h, "₿ BTC", C_GOLD, "-0.9%", C_RED, is_active=True)
    draw.text((c1[0] + 8, c1[1] + 32), "$84,021", fill=C_GOLD, font=get_font(13, bold=True))
    draw.text((c1[0] + card_w - 55, c1[1] + 32), "-0.9%", fill=C_RED, font=f_bold)
    pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = (card_w - 20) / (len(pts) - 1)
    sp_pts = [(c1[0] + 10 + i * step, c1[1] + 85 - v * 35) for i, v in enumerate(pts)]
    for i in range(len(sp_pts) - 1):
        draw.line([sp_pts[i], sp_pts[i+1]], fill=C_GOLD, width=2)
    draw.text((c1[0] + 8, c1[1] + card_h - 14), "H $85,208  L $83,230", fill=C_TEXT_DIM, font=f_small)

    c2 = (m + card_w + gap, curr_y)
    draw_card(draw, c2[0], c2[1], card_w, card_h, "Ξ ETH", C_ETH, "-0.2%", C_RED)
    draw.text((c2[0] + 8, c2[1] + 32), "$2,691", fill=C_ETH, font=get_font(13, bold=True))
    draw.text((c2[0] + card_w - 55, c2[1] + 32), "-0.2%", fill=C_RED, font=f_bold)
    eth_pts = [(c2[0] + 10 + i * step, c2[1] + 85 - v * 30) for i, v in enumerate(pts[::-1])]
    for i in range(len(eth_pts) - 1):
        draw.line([eth_pts[i], eth_pts[i+1]], fill=C_ETH, width=2)
    draw.text((c2[0] + 8, c2[1] + card_h - 14), "H $2,740  L $2,667", fill=C_TEXT_DIM, font=f_small)

    c3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, c3[0], c3[1], card_w, card_h, "◎ SOL", C_SOLANA, "+3.3%", C_GREEN)
    draw.text((c3[0] + 8, c3[1] + 32), "$122.06", fill=C_SOLANA, font=get_font(13, bold=True))
    draw.text((c3[0] + card_w - 55, c3[1] + 32), "+3.3%", fill=C_GREEN, font=f_bold)
    sol_pts = [(c3[0] + 10 + i * step, c3[1] + 85 - (0.3 + 0.6 * (i/len(pts))) * 35) for i in range(len(pts))]
    for i in range(len(sol_pts) - 1):
        draw.line([sol_pts[i], sol_pts[i+1]], fill=C_SOLANA, width=2)
    draw.text((c3[0] + 8, c3[1] + card_h - 14), "H $122.75  L $115.92", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 8

    # 2. SECTION: AI USAGE
    draw.text((m, curr_y), "─── [ AI USAGE ] ", fill=C_CORAL, font=f_sec)
    draw.rectangle([w - 88, curr_y - 2, w - m, curr_y + 14], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.text((w - 82, curr_y + 1), "🔍 FOCUS", fill=C_ACTIVE_CYAN, font=f_small)
    draw.line([m + 100, curr_y + 6, w - 96, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # CODEX, GEMINI, CLAUDE
    a1 = (m, curr_y)
    draw_card(draw, a1[0], a1[1], card_w, card_h, "CODEX", C_GREEN, "READY", C_GREEN)
    draw.text((a1[0] + 8, a1[1] + 30), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a1[0] + card_w - 65, a1[1] + 30), "100% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a1[0] + 8, a1[1] + 43, card_w - 16, 5, 100, C_GREEN)
    draw.text((a1[0] + 8, a1[1] + 55), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a1[0] + card_w - 65, a1[1] + 55), "29% LEFT", fill=C_AMBER, font=f_bold)
    draw_segmented_bar(draw, a1[0] + 8, a1[1] + 68, card_w - 16, 5, 29, C_AMBER)
    draw.text((a1[0] + 8, a1[1] + card_h - 14), "GPT-5.6 · CHATGPT PLUS", fill=C_TEXT_DIM, font=f_small)

    a2 = (m + card_w + gap, curr_y)
    draw_card(draw, a2[0], a2[1], card_w, card_h, "GEMINI", C_BLUE, "ACTIVE", C_GREEN)
    draw.text((a2[0] + 8, a2[1] + 30), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a2[0] + card_w - 65, a2[1] + 30), "73% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a2[0] + 8, a2[1] + 43, card_w - 16, 5, 73, C_GREEN)
    draw.text((a2[0] + 8, a2[1] + 55), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a2[0] + card_w - 65, a2[1] + 55), "76% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a2[0] + 8, a2[1] + 68, card_w - 16, 5, 76, C_GREEN)
    draw.text((a2[0] + 8, a2[1] + card_h - 14), "GEMINI 3.8 · GOOGLE AI PRO", fill=C_TEXT_DIM, font=f_small)

    a3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, a3[0], a3[1], card_w, card_h, "CLAUDE", C_CORAL, "STALE", C_AMBER)
    draw.text((a3[0] + 8, a3[1] + 30), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a3[0] + card_w - 65, a3[1] + 30), "97% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a3[0] + 8, a3[1] + 43, card_w - 16, 5, 97, C_GREEN)
    draw.text((a3[0] + 8, a3[1] + 55), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a3[0] + card_w - 65, a3[1] + 55), "62% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a3[0] + 8, a3[1] + 68, card_w - 16, 5, 62, C_GREEN)
    draw.text((a3[0] + 8, a3[1] + card_h - 14), "no***@gmail.com · PRO", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 8

    # 3. SECTION: VOLATILE STOCKS SCANNER
    draw.text((m, curr_y), "─── [ VOLATILE STOCKS SCANNER ] ", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.rectangle([w - 88, curr_y - 2, w - m, curr_y + 14], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.text((w - 82, curr_y + 1), "🔍 FOCUS", fill=C_ACTIVE_CYAN, font=f_small)
    draw.line([m + 175, curr_y + 6, w - 96, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # Wide Stocks Card
    sw_w = w - m * 2
    sw_h = 135
    draw.rectangle([m, curr_y, m + sw_w, curr_y + sw_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 10, curr_y + 8), "TOP 10 MOST VOLATILE US STOCKS TODAY", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.rectangle([m + sw_w - 64, curr_y + 5, m + sw_w - 8, curr_y + 20], fill=(16, 24, 38), outline=C_GREEN)
    draw.text((m + sw_w - 48, curr_y + 7), "OPEN", fill=C_GREEN, font=f_small)

    stocks_sample = [
        ("1", "DKNG", "$22.02", "+3.5%", "VOL 8.3%"),
        ("2", "GME", "$23.39", "-6.5%", "VOL 7.6%"),
        ("3", "MARA", "$12.55", "-2.9%", "VOL 6.4%"),
        ("4", "RIOT", "$23.00", "-2.0%", "VOL 5.7%"),
        ("5", "TSLA", "$372.11", "-1.5%", "VOL 5.1%"),
        ("6", "ARM", "$310.32", "+1.3%", "VOL 5.0%"),
        ("7", "SMCI", "$43.26", "+4.2%", "VOL 4.5%"),
        ("8", "MSFT", "$516.17", "+3.7%", "VOL 4.4%"),
        ("9", "MSTR", "$158.61", "-1.9%", "VOL 3.7%"),
        ("10", "COIN", "$195.11", "-2.1%", "VOL 3.6%"),
    ]

    mid_x = m + sw_w // 2
    for idx, (rk, sym, pr, chg, vol) in enumerate(stocks_sample[:5]):
        ry = curr_y + 28 + idx * 18
        draw.text((m + 12, ry), rk, fill=C_TEXT_DIM, font=f_small)
        draw.text((m + 28, ry), sym, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((m + 85, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((m + 175, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((mid_x - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.line([mid_x, curr_y + 24, mid_x, curr_y + sw_h - 16], fill=(24, 32, 48), width=1)

    for idx, (rk, sym, pr, chg, vol) in enumerate(stocks_sample[5:]):
        ry = curr_y + 28 + idx * 18
        draw.text((mid_x + 12, ry), rk, fill=C_TEXT_DIM, font=f_small)
        draw.text((mid_x + 30, ry), sym, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((mid_x + 90, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((mid_x + 180, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((m + sw_w - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((m + 10, curr_y + sw_h - 12), "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance Public Crumb API", fill=C_TEXT_DIM, font=f_small)

    curr_y += sw_h + gap + 8

    # 4. SECTION: SYSTEM & SERVICES
    draw.text((m, curr_y), "─── [ SYSTEM & SERVICES ] ", fill=C_BLUE, font=f_sec)
    draw.rectangle([w - 88, curr_y - 2, w - m, curr_y + 14], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.text((w - 82, curr_y + 1), "🔍 FOCUS", fill=C_ACTIVE_CYAN, font=f_small)
    draw.line([m + 150, curr_y + 6, w - 96, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # Local PC & DGX Spark
    s1 = (m, curr_y)
    draw_card(draw, s1[0], s1[1], card_w, 110, "LOCAL PC", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((s1[0] + 8, s1[1] + 30), "GPU", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((s1[0] + card_w - 50, s1[1] + 30), "3%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, s1[0] + 8, s1[1] + 44, card_w - 16, 5, 3, C_GREEN)
    draw.text((s1[0] + 8, s1[1] + 56), "TEMP 38C  VRAM 3.0G", fill=C_TEXT_DIM, font=f_small)
    draw.text((s1[0] + 8, s1[1] + 70), "RAM 44%", fill=C_TEXT_MUTED, font=f_small)
    draw.text((s1[0] + 8, s1[1] + 92), "RTX 5080 · 16G", fill=C_TEXT_DIM, font=f_small)

    s2 = (m + card_w + gap, curr_y)
    draw_card(draw, s2[0], s2[1], card_w, 110, "DGX SPARK", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((s2[0] + 8, s2[1] + 30), "GPU", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((s2[0] + card_w - 50, s2[1] + 30), "0%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, s2[0] + 8, s2[1] + 44, card_w - 16, 5, 0, C_GREEN)
    draw.text((s2[0] + 8, s2[1] + 56), "TEMP 39C  LOAD 1.72", fill=C_TEXT_DIM, font=f_small)
    draw.text((s2[0] + 8, s2[1] + 70), "RAM 40%", fill=C_TEXT_MUTED, font=f_small)
    draw.text((s2[0] + 8, s2[1] + 92), "GB10 · SPARK LIVE", fill=C_TEXT_DIM, font=f_small)

    s3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, s3[0], s3[1], card_w, 110, "SERVICES", C_GREEN, "ONLINE", C_GREEN)
    svcs = [("DGX (SSH)", True), ("OLLAMA", True), ("COMFYUI", True), ("FORGE3D", True)]
    sy = s3[1] + 30
    for s_name, s_up in svcs:
        draw.ellipse([s3[0] + 10, sy + 3, s3[0] + 16, sy + 9], fill=C_GREEN if s_up else C_RED)
        draw.text((s3[0] + 22, sy), s_name, fill=C_TEXT_WHITE, font=f_small)
        sy += 16
    draw.text((s3[0] + 8, s3[1] + 92), "TAILSCALE WORKSTATION", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 2. PRESET CRYPTO SCREENSHOT (Hero cards: BTC, ETH, SOL, DOGE, PEPE)
# ---------------------------------------------------------------------------
def render_preset_crypto_screenshot(out_path: str):
    """Renders CRYPTO hero preset with enlarged cards and high-res sparklines."""
    w, h = 680, 520
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="CRYPTO")

    f_sec = get_font(10, bold=True)
    f_bold = get_font(11, bold=True)
    f_huge = get_font(16, bold=True)
    f_small = get_font(9, bold=False)

    curr_y = 74
    m = 12
    draw.text((m, curr_y), "─── [ FOCUS: CRYPTO MARKETS · REALTIME BINANCE FEED ] ", fill=C_GOLD, font=f_sec)
    draw.line([m + 320, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 24

    # Top row: 3 major coins (BTC, ETH, SOL) - larger cards
    card_w = (w - m * 2 - 16) // 3
    card_h = 185
    gap = 8

    pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = (card_w - 24) / (len(pts) - 1)

    # 1. BTC
    c1 = (m, curr_y)
    draw_card(draw, c1[0], c1[1], card_w, card_h, "₿ BITCOIN (BTC)", C_GOLD, "-0.9%", C_RED, is_active=True)
    draw.text((c1[0] + 12, c1[1] + 36), "$84,021", fill=C_GOLD, font=f_huge)
    draw.text((c1[0] + card_w - 65, c1[1] + 40), "-0.9%", fill=C_RED, font=f_bold)
    sp_pts = [(c1[0] + 12 + i * step, c1[1] + 130 - v * 55) for i, v in enumerate(pts)]
    for i in range(len(sp_pts) - 1):
        draw.line([sp_pts[i], sp_pts[i+1]], fill=C_GOLD, width=3)
    draw.text((c1[0] + 12, c1[1] + card_h - 22), "HIGH: $85,208  LOW: $83,230", fill=C_TEXT_DIM, font=f_small)

    # 2. ETH
    c2 = (m + card_w + gap, curr_y)
    draw_card(draw, c2[0], c2[1], card_w, card_h, "Ξ ETHEREUM (ETH)", C_ETH, "-0.2%", C_RED)
    draw.text((c2[0] + 12, c2[1] + 36), "$2,691.40", fill=C_ETH, font=f_huge)
    draw.text((c2[0] + card_w - 65, c2[1] + 40), "-0.2%", fill=C_RED, font=f_bold)
    eth_pts = [(c2[0] + 12 + i * step, c2[1] + 130 - v * 50) for i, v in enumerate(pts[::-1])]
    for i in range(len(eth_pts) - 1):
        draw.line([eth_pts[i], eth_pts[i+1]], fill=C_ETH, width=3)
    draw.text((c2[0] + 12, c2[1] + card_h - 22), "HIGH: $2,740  LOW: $2,667", fill=C_TEXT_DIM, font=f_small)

    # 3. SOL
    c3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, c3[0], c3[1], card_w, card_h, "◎ SOLANA (SOL)", C_SOLANA, "+3.3%", C_GREEN)
    draw.text((c3[0] + 12, c3[1] + 36), "$122.06", fill=C_SOLANA, font=f_huge)
    draw.text((c3[0] + card_w - 65, c3[1] + 40), "+3.3%", fill=C_GREEN, font=f_bold)
    sol_pts = [(c3[0] + 12 + i * step, c3[1] + 130 - (0.2 + 0.7 * (i/len(pts))) * 55) for i in range(len(pts))]
    for i in range(len(sol_pts) - 1):
        draw.line([sol_pts[i], sol_pts[i+1]], fill=C_SOLANA, width=3)
    draw.text((c3[0] + 12, c3[1] + card_h - 22), "HIGH: $122.75  LOW: $115.92", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 10

    # Bottom row: 2 alt/meme coins (DOGE, PEPE) - wide half-split cards
    card_w2 = (w - m * 2 - gap) // 2
    card_h2 = 175
    step2 = (card_w2 - 24) / (len(pts) - 1)

    # 4. DOGE
    d1 = (m, curr_y)
    draw_card(draw, d1[0], d1[1], card_w2, card_h2, "Ð DOGECOIN (DOGE)", C_DOGE, "+2.7%", C_GREEN)
    draw.text((d1[0] + 12, d1[1] + 36), "$0.09892", fill=C_DOGE, font=f_huge)
    draw.text((d1[0] + card_w2 - 70, d1[1] + 40), "+2.7%", fill=C_GREEN, font=f_bold)
    doge_pts = [(d1[0] + 12 + i * step2, d1[1] + 125 - (0.3 + 0.5 * (i/len(pts))) * 50) for i in range(len(pts))]
    for i in range(len(doge_pts) - 1):
        draw.line([doge_pts[i], doge_pts[i+1]], fill=C_DOGE, width=3)
    draw.text((d1[0] + 12, d1[1] + card_h2 - 20), "HIGH: $0.09971  LOW: $0.09460  VOL: 1.2B DOGE", fill=C_TEXT_DIM, font=f_small)

    # 5. PEPE
    d2 = (m + card_w2 + gap, curr_y)
    draw_card(draw, d2[0], d2[1], card_w2, card_h2, "🐸 PEPE (PEPE)", C_PEPE, "+0.7%", C_GREEN)
    draw.text((d2[0] + 12, d2[1] + 36), "$0.00000452", fill=C_PEPE, font=f_huge)
    draw.text((d2[0] + card_w2 - 70, d2[1] + 40), "+0.7%", fill=C_GREEN, font=f_bold)
    pepe_pts = [(d2[0] + 12 + i * step2, d2[1] + 125 - (0.2 + 0.6 * (i/len(pts))) * 50) for i in range(len(pts))]
    for i in range(len(pepe_pts) - 1):
        draw.line([pepe_pts[i], pepe_pts[i+1]], fill=C_PEPE, width=3)
    draw.text((d2[0] + 12, d2[1] + card_h2 - 20), "MICRO TOKEN  ·  $4.52u  ·  VOL: 8.4T PEPE", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 3. PRESET STOCKS SCREENSHOT (Top Volatile Stocks Scanner)
# ---------------------------------------------------------------------------
def render_preset_stocks_screenshot(out_path: str):
    """Renders STOCKS hero preset emphasizing price, day %, and volatility."""
    w, h = 680, 520
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="STOCKS")

    f_sec = get_font(10, bold=True)
    f_bold = get_font(11, bold=True)
    f_huge = get_font(13, bold=True)
    f_small = get_font(9, bold=False)

    curr_y = 74
    m = 12
    draw.text((m, curr_y), "─── [ FOCUS: US EQUITIES VOLATILITY SCANNER ] ", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.line([m + 300, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 24

    sw_w = w - m * 2
    sw_h = 390
    draw.rectangle([m, curr_y, m + sw_w, curr_y + sw_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN, width=2)

    # Title bar
    draw.text((m + 16, curr_y + 12), "TOP 10 MOST VOLATILE US EQUITIES (LIVE MARKET CRUMB FEED)", fill=C_ACTIVE_CYAN, font=f_huge)
    draw.rectangle([m + sw_w - 90, curr_y + 10, m + sw_w - 12, curr_y + 30], fill=(16, 24, 38), outline=C_GREEN)
    draw.ellipse([m + sw_w - 84, curr_y + 17, m + sw_w - 78, curr_y + 23], fill=C_GREEN)
    draw.text((m + sw_w - 72, curr_y + 13), "MARKET OPEN", fill=C_GREEN, font=f_small)

    draw.line([m + 8, curr_y + 40, m + sw_w - 8, curr_y + 40], fill=(28, 38, 56), width=1)

    stocks_data = [
        ("1", "DKNG", "DraftKings Inc", "$22.02", "+3.5%", "VOL: 8.3%", "$20.30 - $22.15"),
        ("2", "GME", "GameStop Corp", "$23.39", "-6.5%", "VOL: 7.6%", "$22.80 - $24.70"),
        ("3", "MARA", "MARA Holdings", "$12.55", "-2.9%", "VOL: 6.4%", "$12.10 - $12.90"),
        ("4", "RIOT", "Riot Platforms", "$23.00", "-2.0%", "VOL: 5.7%", "$22.40 - $23.70"),
        ("5", "TSLA", "Tesla Inc", "$372.11", "-1.5%", "VOL: 5.1%", "$364.50 - $383.20"),
        ("6", "ARM", "Arm Holdings", "$310.32", "+1.3%", "VOL: 5.0%", "$302.10 - $317.50"),
        ("7", "SMCI", "Super Micro", "$43.26", "+4.2%", "VOL: 4.5%", "$41.50 - $43.40"),
        ("8", "MSFT", "Microsoft Corp", "$516.17", "+3.7%", "VOL: 4.4%", "$505.00 - $527.10"),
        ("9", "MSTR", "MicroStrategy", "$158.61", "-1.9%", "VOL: 3.7%", "$153.20 - $159.00"),
        ("10", "COIN", "Coinbase Global", "$195.11", "-2.1%", "VOL: 3.6%", "$191.00 - $198.00"),
    ]

    # Table Header
    hy = curr_y + 48
    draw.text((m + 16, hy), "RANK", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + 65, hy), "TICKER", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + 140, hy), "NAME", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + 280, hy), "LAST PRICE", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + 380, hy), "DAY CHANGE", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + 480, hy), "INTRADAY RANGE", fill=C_TEXT_DIM, font=f_small)
    draw.text((m + sw_w - 90, hy), "VOLATILITY", fill=C_TEXT_DIM, font=f_small)

    draw.line([m + 12, hy + 18, m + sw_w - 12, hy + 18], fill=(24, 32, 48), width=1)

    for idx, (rk, sym, name, pr, chg, vol, rng) in enumerate(stocks_data):
        ry = hy + 26 + idx * 28
        row_bg = (19, 27, 42) if idx % 2 == 0 else (14, 19, 30)
        draw.rectangle([m + 10, ry - 4, m + sw_w - 10, ry + 22], fill=row_bg)

        draw.text((m + 22, ry + 2), rk, fill=C_TEXT_DIM, font=f_small)
        draw.text((m + 65, ry + 1), sym, fill=C_ACTIVE_CYAN, font=f_bold)
        draw.text((m + 140, ry + 2), name, fill=C_TEXT_MUTED, font=f_small)
        draw.text((m + 280, ry + 1), pr, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((m + 380, ry + 1), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((m + 480, ry + 2), rng, fill=C_TEXT_MUTED, font=f_small)
        draw.text((m + sw_w - 85, ry + 1), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((m + 16, curr_y + sw_h - 16), "CRUMB API: Authenticated Yahoo Finance Scraping · Refresh: 60s · Range = (H - L) / PrevClose", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 4. PRESET AI SCREENSHOT (Codex, Gemini, Claude + AI Activity)
# ---------------------------------------------------------------------------
def render_preset_ai_screenshot(out_path: str):
    """Renders AI hero preset emphasizing Quota LEFT %, Reset time, and Agent state."""
    w, h = 680, 520
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="AI")

    f_sec = get_font(10, bold=True)
    f_bold = get_font(11, bold=True)
    f_huge = get_font(18, bold=True)
    f_small = get_font(9, bold=False)

    curr_y = 74
    m = 12
    draw.text((m, curr_y), "─── [ FOCUS: AI SUBSCRIPTION QUOTAS & LOCAL AGENT ACTIVITY ] ", fill=C_CORAL, font=f_sec)
    draw.line([m + 370, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 24

    card_w = (w - m * 2 - 16) // 3
    card_h = 240
    gap = 8

    # 1. CODEX
    a1 = (m, curr_y)
    draw_card(draw, a1[0], a1[1], card_w, card_h, "CODEX CLI", C_GREEN, "READY", C_GREEN)
    draw.text((a1[0] + 12, a1[1] + 36), "100%", fill=C_GREEN, font=f_huge)
    draw.text((a1[0] + 80, a1[1] + 42), "LEFT", fill=C_GREEN, font=f_bold)
    draw.text((a1[0] + card_w - 75, a1[1] + 42), "5H ROLLING", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a1[0] + 12, a1[1] + 68, card_w - 24, 8, 100, C_GREEN)
    draw.text((a1[0] + 12, a1[1] + 84), "RESET IN: 5H 00M", fill=C_TEXT_MUTED, font=f_small)

    draw.line([a1[0] + 12, a1[1] + 104, a1[0] + card_w - 12, a1[1] + 104], fill=(24, 32, 48), width=1)

    draw.text((a1[0] + 12, a1[1] + 116), "29%", fill=C_AMBER, font=f_huge)
    draw.text((a1[0] + 65, a1[1] + 122), "LEFT", fill=C_AMBER, font=f_bold)
    draw.text((a1[0] + card_w - 75, a1[1] + 122), "WEEKLY CAP", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a1[0] + 12, a1[1] + 148, card_w - 24, 8, 29, C_AMBER)
    draw.text((a1[0] + 12, a1[1] + 164), "RESET IN: 1D 22H", fill=C_TEXT_MUTED, font=f_small)
    draw.text((a1[0] + 12, a1[1] + card_h - 22), "GPT-5.6 · CHATGPT PLUS TIER", fill=C_TEXT_DIM, font=f_small)

    # 2. GEMINI
    a2 = (m + card_w + gap, curr_y)
    draw_card(draw, a2[0], a2[1], card_w, card_h, "GEMINI CODE ASSIST", C_BLUE, "ACTIVE", C_GREEN)
    draw.text((a2[0] + 12, a2[1] + 36), "73%", fill=C_GREEN, font=f_huge)
    draw.text((a2[0] + 65, a2[1] + 42), "LEFT", fill=C_GREEN, font=f_bold)
    draw.text((a2[0] + card_w - 75, a2[1] + 42), "5H ROLLING", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a2[0] + 12, a2[1] + 68, card_w - 24, 8, 73, C_GREEN)
    draw.text((a2[0] + 12, a2[1] + 84), "RESET IN: 4H 16M", fill=C_TEXT_MUTED, font=f_small)

    draw.line([a2[0] + 12, a2[1] + 104, a2[0] + card_w - 12, a2[1] + 104], fill=(24, 32, 48), width=1)

    draw.text((a2[0] + 12, a2[1] + 116), "76%", fill=C_GREEN, font=f_huge)
    draw.text((a2[0] + 65, a2[1] + 122), "LEFT", fill=C_GREEN, font=f_bold)
    draw.text((a2[0] + card_w - 75, a2[1] + 122), "WEEKLY CAP", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a2[0] + 12, a2[1] + 148, card_w - 24, 8, 76, C_GREEN)
    draw.text((a2[0] + 12, a2[1] + 164), "RESET IN: 6D 01H", fill=C_TEXT_MUTED, font=f_small)
    draw.text((a2[0] + 12, a2[1] + card_h - 22), "GEMINI 3.8 · GOOGLE AI PRO", fill=C_TEXT_DIM, font=f_small)

    # 3. CLAUDE
    a3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, a3[0], a3[1], card_w, card_h, "CLAUDE PRO", C_CORAL, "STALE", C_AMBER)
    draw.text((a3[0] + 12, a3[1] + 36), "97%", fill=C_GREEN, font=f_huge)
    draw.text((a3[0] + 65, a3[1] + 42), "LEFT", fill=C_GREEN, font=f_bold)
    draw.text((a3[0] + card_w - 75, a3[1] + 42), "5H ROLLING", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a3[0] + 12, a3[1] + 68, card_w - 24, 8, 97, C_GREEN)
    draw.text((a3[0] + 12, a3[1] + 84), "RESET: NOW (CACHED)", fill=C_TEXT_MUTED, font=f_small)

    draw.line([a3[0] + 12, a3[1] + 104, a3[0] + card_w - 12, a3[1] + 104], fill=(24, 32, 48), width=1)

    draw.text((a3[0] + 12, a3[1] + 116), "62%", fill=C_GREEN, font=f_huge)
    draw.text((a3[0] + 65, a3[1] + 122), "LEFT", fill=C_GREEN, font=f_bold)
    draw.text((a3[0] + card_w - 75, a3[1] + 122), "WEEKLY CAP", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, a3[0] + 12, a3[1] + 148, card_w - 24, 8, 62, C_GREEN)
    draw.text((a3[0] + 12, a3[1] + 164), "RESET: NOW (CACHED)", fill=C_TEXT_MUTED, font=f_small)
    draw.text((a3[0] + 12, a3[1] + card_h - 22), "no***@gmail.com · ANTHROPIC", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 10

    # AI Activity Monitor Box below
    act_w = w - m * 2
    act_h = 135
    draw.rectangle([m, curr_y, m + act_w, curr_y + act_h], fill=C_CARD_BG, outline=C_PURPLE, width=2)
    draw.text((m + 16, curr_y + 12), "LOCAL AGENT ACTIVITY DAEMON (PROCESS MONITOR + CLI WAL)", fill=C_PURPLE, font=f_bold)
    draw.line([m + 12, curr_y + 36, m + act_w - 12, curr_y + 36], fill=(28, 38, 56), width=1)

    draw.ellipse([m + 18, curr_y + 54, m + 26, curr_y + 62], fill=C_GREEN)
    draw.text((m + 34, curr_y + 51), "CODEX CLI:", fill=C_TEXT_WHITE, font=f_bold)
    draw.text((m + 120, curr_y + 52), "WORKING  (Active 6h 52m · 24 tasks completed today · Subprocess PID 1492)", fill=C_GREEN, font=f_small)

    draw.ellipse([m + 18, curr_y + 80, m + 26, curr_y + 88], fill=C_TEXT_DIM)
    draw.text((m + 34, curr_y + 77), "CLAUDE PRO:", fill=C_TEXT_WHITE, font=f_bold)
    draw.text((m + 120, curr_y + 78), "IDLE     (Last prompt 42m ago · Web session active)", fill=C_TEXT_MUTED, font=f_small)

    draw.ellipse([m + 18, curr_y + 106, m + 26, curr_y + 114], fill=C_GREEN)
    draw.text((m + 34, curr_y + 103), "GEMINI CODE:", fill=C_TEXT_WHITE, font=f_bold)
    draw.text((m + 120, curr_y + 104), "WORKING  (Active 5h 45m · Background indexing sparkline tensors)", fill=C_GREEN, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 5. PRESET SYSTEM SCREENSHOT (RTX GPU, DGX Spark, Services, Coding)
# ---------------------------------------------------------------------------
def render_preset_system_screenshot(out_path: str):
    """Renders SYSTEM hero preset with Local RTX, DGX Spark, Services, Coding."""
    w, h = 680, 520
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="SYSTEM")

    f_sec = get_font(10, bold=True)
    f_bold = get_font(11, bold=True)
    f_huge = get_font(16, bold=True)
    f_small = get_font(9, bold=False)

    curr_y = 74
    m = 12
    draw.text((m, curr_y), "─── [ FOCUS: HARDWARE CLUSTER & WORKSTATION TELEMETRY ] ", fill=C_BLUE, font=f_sec)
    draw.line([m + 350, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 24

    card_w = (w - m * 2 - 8) // 2
    card_h = 185
    gap = 8

    # 1. LOCAL PC (RTX 5080)
    s1 = (m, curr_y)
    draw_card(draw, s1[0], s1[1], card_w, card_h, "LOCAL WORKSTATION", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((s1[0] + 12, s1[1] + 36), "RTX 5080 16GB", fill=C_TEXT_WHITE, font=f_huge)
    draw.text((s1[0] + card_w - 70, s1[1] + 40), "GPU 3%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, s1[0] + 12, s1[1] + 65, card_w - 24, 8, 3, C_GREEN)
    draw.text((s1[0] + 12, s1[1] + 82), "TEMP: 38°C  ·  POWER: 42W  ·  VRAM: 3.0 / 16.0 GB (18%)", fill=C_TEXT_MUTED, font=f_small)

    draw.line([s1[0] + 12, s1[1] + 104, s1[0] + card_w - 12, s1[1] + 104], fill=(24, 32, 48), width=1)

    draw.text((s1[0] + 12, s1[1] + 116), "SYSTEM RAM: 44%", fill=C_TEXT_WHITE, font=f_bold)
    draw.text((s1[0] + card_w - 110, s1[1] + 116), "28.1 / 64.0 GB", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, s1[0] + 12, s1[1] + 138, card_w - 24, 8, 44, (55, 195, 245))
    draw.text((s1[0] + 12, s1[1] + card_h - 20), "AMD RYZEN 9 9950X · 16 CORES / 32 THREADS · WINDOWS 11", fill=C_TEXT_DIM, font=f_small)

    # 2. DGX SPARK
    s2 = (m + card_w + gap, curr_y)
    draw_card(draw, s2[0], s2[1], card_w, card_h, "REMOTE DGX SPARK", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((s2[0] + 12, s2[1] + 36), "NVIDIA GB10 SPARK", fill=C_NVIDIA, font=f_huge)
    draw.text((s2[0] + card_w - 70, s2[1] + 40), "GPU 0%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, s2[0] + 12, s2[1] + 65, card_w - 24, 8, 0, C_GREEN)
    draw.text((s2[0] + 12, s2[1] + 82), "TEMP: 39°C  ·  SYS LOAD: 1.72  ·  VRAM: 1.2 / 128.0 GB", fill=C_TEXT_MUTED, font=f_small)

    draw.line([s2[0] + 12, s2[1] + 104, s2[0] + card_w - 12, s2[1] + 104], fill=(24, 32, 48), width=1)

    draw.text((s2[0] + 12, s2[1] + 116), "CLUSTER RAM: 40%", fill=C_TEXT_WHITE, font=f_bold)
    draw.text((s2[0] + card_w - 110, s2[1] + 116), "51.2 / 128.0 GB", fill=C_TEXT_DIM, font=f_small)
    draw_segmented_bar(draw, s2[0] + 12, s2[1] + 138, card_w - 24, 8, 40, C_NVIDIA)
    draw.text((s2[0] + 12, s2[1] + card_h - 20), "TAILSCALE MESH 100.x.x.x · ZERO CONSOLE FLASHING", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 10

    # Bottom Row: Services & Coding Activity
    card_h2 = 185

    # 3. SERVICES
    s3 = (m, curr_y)
    draw_card(draw, s3[0], s3[1], card_w, card_h2, "INTERNAL SERVICES", C_GREEN, "5/5 UP", C_GREEN)
    svcs = [
        ("TAILSCALE MESH NODE", "ONLINE (100.82.14.9)", True),
        ("OLLAMA LLM RUNTIME", "ONLINE (PORT 11434)", True),
        ("COMFYUI TENSOR SERVER", "ONLINE (PORT 8188)", True),
        ("FORGE3D SPATIAL ENGINE", "ONLINE (PORT 9000)", True),
        ("HERMES AGENT BRIDGE", "ONLINE (PORT 5005)", True),
    ]
    sy = s3[1] + 36
    for s_name, s_detail, s_up in svcs:
        draw.ellipse([s3[0] + 14, sy + 4, s3[0] + 20, sy + 10], fill=C_GREEN if s_up else C_RED)
        draw.text((s3[0] + 28, sy + 1), s_name, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((s3[0] + card_w - 150, sy + 2), s_detail, fill=C_GREEN, font=f_small)
        sy += 25
    draw.text((s3[0] + 12, s3[1] + card_h2 - 20), "TCP HEALTH PROBE · AUTOMATIC BACKGROUND RECOVERY", fill=C_TEXT_DIM, font=f_small)

    # 4. CODING & AI ACTIVITY
    s4 = (m + card_w + gap, curr_y)
    draw_card(draw, s4[0], s4[1], card_w, card_h2, "ACTIVE CODING REPOS", C_PURPLE, "LIVE", C_GREEN)
    repos = [
        ("claude-minitoo", "Milestone 13 UX & BT Coexistence", "ACTIVE"),
        ("ai-dev-skills", "Autonomous coding skills", "IDLE"),
        ("quant-codex", "Crypto trading engine", "IDLE"),
        ("flow88-mix-engine", "Spatial DSP pipeline", "IDLE"),
    ]
    ry = s4[1] + 36
    for r_name, r_desc, r_st in repos:
        draw.ellipse([s4[0] + 14, ry + 4, s4[0] + 20, ry + 10], fill=C_GREEN if r_st == "ACTIVE" else C_TEXT_DIM)
        draw.text((s4[0] + 28, ry + 1), r_name, fill=C_ACTIVE_CYAN if r_st == "ACTIVE" else C_TEXT_WHITE, font=f_bold)
        draw.text((s4[0] + 140, ry + 2), r_desc, fill=C_TEXT_MUTED, font=f_small)
        ry += 25
    draw.text((s4[0] + 12, s4[1] + card_h2 - 20), "WORKSPACE GIT PROBE · REALTIME DEV ACTIVITY", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 6. SETTINGS DASHBOARD TAB SCREENSHOT
# ---------------------------------------------------------------------------
def render_settings_dashboard_screenshot(out_path: str):
    """Renders redesigned 5-tab Settings UI on the DASHBOARD tab."""
    w, h = 720, 560
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_title = get_font(12, bold=True)
    f_tab = get_font(10, bold=True)
    f_h2 = get_font(11, bold=True)
    f_sub = get_font(9, bold=False)
    f_bold = get_font(10, bold=True)
    f_btn = get_font(9, bold=True)

    # Window title bar
    draw.rectangle([0, 0, w, 36], fill=(12, 17, 27), outline=(28, 38, 56))
    draw.text((16, 10), "⚙ SETTINGS · AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((w - 30, 10), "✕", fill=C_TEXT_MUTED, font=f_bold)

    # Left Navigation Sidebar (5 Tabs)
    sidebar_w = 160
    draw.rectangle([0, 36, sidebar_w, h], fill=(14, 19, 30), outline=(24, 32, 48))

    tabs = [
        ("GENERAL", False),
        ("DASHBOARD", True),
        ("MINITOO", False),
        ("INTEGRATIONS", False),
        ("ADVANCED", False),
    ]

    ty = 50
    for tab_name, is_sel in tabs:
        if is_sel:
            draw.rectangle([0, ty, sidebar_w, ty + 36], fill=(18, 38, 54), outline=C_ACTIVE_CYAN, width=1)
            draw.text((20, ty + 10), f"▶ {tab_name}", fill=C_ACTIVE_CYAN, font=f_tab)
        else:
            draw.text((24, ty + 10), tab_name, fill=C_TEXT_MUTED, font=f_tab)
        ty += 42

    # Right Content Area: DASHBOARD TAB
    rx = sidebar_w + 16
    draw.text((rx, 50), "DASHBOARD SECTIONS & INDEPENDENT CARD VISIBILITY", fill=C_ACTIVE_CYAN, font=f_h2)
    draw.text((rx, 70), "Configure which cards appear on the Desktop app vs the physical MiniToo display.", fill=C_TEXT_MUTED, font=f_sub)

    card_list = [
        ("AI USAGE", "SECTION", True, True, True),
        ("Codex CLI", "CARD", True, True, False),
        ("Gemini Code", "CARD", True, True, False),
        ("Claude Pro", "CARD", True, True, False),
        ("CRYPTO MARKETS", "SECTION", True, True, True),
        ("Bitcoin (BTC)", "CARD", True, True, False),
        ("Ethereum (ETH)", "CARD", True, True, False),
        ("Solana (SOL)", "CARD", True, True, False),
        ("Dogecoin (DOGE)", "CARD", True, True, False),
        ("Pepe (PEPE)", "CARD", True, True, False),
        ("STOCKS SCANNER", "SECTION", True, True, True),
        ("Volatile Stocks Today", "CARD", True, False, False),
        ("SYSTEM & HARDWARE", "SECTION", True, True, True),
        ("Local PC (RTX GPU)", "CARD", True, True, False),
        ("DGX Spark (GB10)", "CARD", True, True, False),
        ("Services Health", "CARD", True, True, False),
        ("Coding Activity", "CARD", True, False, False),
    ]

    # Tree container
    cy = 96
    ch_w = w - rx - 16
    draw.rectangle([rx, cy, rx + ch_w, cy + 390], fill=(14, 18, 28), outline=(28, 38, 56))

    # Header in list
    draw.rectangle([rx, cy, rx + ch_w, cy + 24], fill=(18, 24, 38))
    draw.text((rx + 12, cy + 5), "CARD / WIDGET NAME", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + ch_w - 240, cy + 5), "DESKTOP", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + ch_w - 140, cy + 5), "MINITOO", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + ch_w - 55, cy + 5), "ORDER", fill=C_TEXT_DIM, font=f_sub)

    ly = cy + 28
    for name, kind, d_on, m_on, is_sec in card_list[:13]:
        row_bg = (20, 28, 44) if is_sec else ((16, 22, 34) if (ly // 26) % 2 == 0 else (13, 17, 26))
        draw.rectangle([rx + 4, ly, rx + ch_w - 4, ly + 24], fill=row_bg)

        if is_sec:
            draw.text((rx + 10, ly + 4), f"▼ {name}", fill=C_GOLD, font=f_bold)
            draw.text((rx + ch_w - 235, ly + 4), "[x] Enabled", fill=C_GREEN, font=f_sub)
            draw.text((rx + ch_w - 135, ly + 4), "[x] Enabled", fill=C_GREEN, font=f_sub)
        else:
            draw.text((rx + 28, ly + 4), f"• {name}", fill=C_TEXT_WHITE, font=f_sub)
            draw.text((rx + ch_w - 235, ly + 4), "[x] Visible" if d_on else "[ ] Hidden", fill=C_GREEN if d_on else C_TEXT_DIM, font=f_sub)
            draw.text((rx + ch_w - 135, ly + 4), "[x] Visible" if m_on else "[ ] Hidden", fill=C_GREEN if m_on else C_TEXT_DIM, font=f_sub)
            # Arrow buttons
            draw.rectangle([rx + ch_w - 60, ly + 2, rx + ch_w - 40, ly + 20], fill=(22, 32, 48), outline=(38, 52, 76))
            draw.text((rx + ch_w - 54, ly + 4), "▲", fill=C_ACTIVE_CYAN, font=f_sub)
            draw.rectangle([rx + ch_w - 35, ly + 2, rx + ch_w - 15, ly + 20], fill=(22, 32, 48), outline=(38, 52, 76))
            draw.text((rx + ch_w - 29, ly + 4), "▼", fill=C_ACTIVE_CYAN, font=f_sub)

        ly += 26

    # Bottom action bar
    draw.rectangle([0, h - 48, w, h], fill=(12, 16, 26), outline=(24, 32, 48))
    draw.rectangle([w - 210, h - 38, w - 120, h - 10], fill=(22, 28, 42), outline=(38, 50, 72))
    draw.text((w - 190, h - 28), "CANCEL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([w - 110, h - 38, w - 16, h - 10], fill=(14, 48, 64), outline=C_ACTIVE_CYAN)
    draw.text((w - 95, h - 28), "SAVE CHANGES", fill=C_ACTIVE_CYAN, font=f_btn)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# 7. SETTINGS MINITOO TAB SCREENSHOT
# ---------------------------------------------------------------------------
def render_settings_minitoo_screenshot(out_path: str):
    """Renders redesigned Settings UI on the MINITOO tab with diagnostics & Low Interference mode."""
    w, h = 720, 560
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_title = get_font(12, bold=True)
    f_tab = get_font(10, bold=True)
    f_h2 = get_font(11, bold=True)
    f_sub = get_font(9, bold=False)
    f_bold = get_font(10, bold=True)
    f_btn = get_font(9, bold=True)

    # Window title bar
    draw.rectangle([0, 0, w, 36], fill=(12, 17, 27), outline=(28, 38, 56))
    draw.text((16, 10), "⚙ SETTINGS · AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((w - 30, 10), "✕", fill=C_TEXT_MUTED, font=f_bold)

    # Left Navigation Sidebar
    sidebar_w = 160
    draw.rectangle([0, 36, sidebar_w, h], fill=(14, 19, 30), outline=(24, 32, 48))

    tabs = [
        ("GENERAL", False),
        ("DASHBOARD", False),
        ("MINITOO", True),
        ("INTEGRATIONS", False),
        ("ADVANCED", False),
    ]

    ty = 50
    for tab_name, is_sel in tabs:
        if is_sel:
            draw.rectangle([0, ty, sidebar_w, ty + 36], fill=(18, 38, 54), outline=C_ACTIVE_CYAN, width=1)
            draw.text((20, ty + 10), f"▶ {tab_name}", fill=C_ACTIVE_CYAN, font=f_tab)
        else:
            draw.text((24, ty + 10), tab_name, fill=C_TEXT_MUTED, font=f_tab)
        ty += 42

    # Right Content Area: MINITOO TAB
    rx = sidebar_w + 16
    draw.text((rx, 50), "MINITOO HARDWARE & BLUETOOTH CONFIGURATION", fill=C_ACTIVE_CYAN, font=f_h2)
    draw.text((rx, 70), "Manage physical Bluetooth SPP transport, display rotation, and knob navigation.", fill=C_TEXT_MUTED, font=f_sub)

    # 1. GROUP: DEVICE
    gy = 96
    gw = w - rx - 16
    draw.rectangle([rx, gy, rx + gw, gy + 88], fill=(15, 20, 32), outline=(30, 42, 64))
    draw.text((rx + 12, gy + 8), "DEVICE STATUS & TRANSPORT MODE", fill=C_TEXT_WHITE, font=f_bold)
    draw.line([rx + 8, gy + 26, rx + gw - 8, gy + 26], fill=(24, 32, 48), width=1)

    draw.text((rx + 16, gy + 36), "Connection:", fill=C_TEXT_MUTED, font=f_sub)
    draw.ellipse([rx + 105, gy + 40, rx + 111, gy + 46], fill=C_GREEN)
    draw.text((rx + 118, gy + 36), "CONNECTED  (Port: COM13 · Divoom Pixoo-Max / MiniToo)", fill=C_GREEN, font=f_bold)

    draw.text((rx + 16, gy + 62), "Bluetooth Mode:", fill=C_TEXT_MUTED, font=f_sub)
    # Mode buttons
    draw.rectangle([rx + 115, gy + 56, rx + 185, gy + 78], fill=(18, 24, 36), outline=(38, 50, 72))
    draw.text((rx + 125, gy + 62), "NORMAL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([rx + 195, gy + 56, rx + 330, gy + 78], fill=(12, 42, 58), outline=C_ACTIVE_CYAN)
    draw.text((rx + 205, gy + 62), "● LOW INTERFERENCE", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((rx + 340, gy + 62), "(Optimized for Bluetooth Audio Coexistence)", fill=C_TEXT_DIM, font=f_sub)

    # 2. GROUP: DISPLAY & CONTROLS
    gy2 = gy + 98
    draw.rectangle([rx, gy2, rx + gw, gy2 + 82], fill=(15, 20, 32), outline=(30, 42, 64))
    draw.text((rx + 12, gy2 + 8), "DISPLAY & PHYSICAL CONTROLS", fill=C_TEXT_WHITE, font=f_bold)
    draw.line([rx + 8, gy2 + 26, rx + gw - 8, gy2 + 26], fill=(24, 32, 48), width=1)

    draw.text((rx + 16, gy2 + 36), "Auto Cycle Pages:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 125, gy2 + 36), "[x] Enabled", fill=C_GREEN, font=f_bold)
    draw.text((rx + 220, gy2 + 36), "Dwell Time:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 290, gy2 + 36), "4 seconds", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.text((rx + 380, gy2 + 36), "Current Page:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 465, gy2 + 36), "BTC (Page 1/7)", fill=C_GOLD, font=f_bold)

    draw.text((rx + 16, gy2 + 58), "Knob Navigation:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 125, gy2 + 58), "[x] Enabled", fill=C_GREEN, font=f_bold)
    draw.text((rx + 220, gy2 + 58), "Knob Poll Rate:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 320, gy2 + 58), "AUTO (~2.8 Hz in Low Interference)", fill=C_ACTIVE_CYAN, font=f_bold)

    # 3. GROUP: LIVE TELEMETRY & DIAGNOSTICS
    gy3 = gy2 + 92
    draw.rectangle([rx, gy3, rx + gw, gy3 + 125], fill=(15, 20, 32), outline=C_ACTIVE_CYAN, width=1)
    draw.text((rx + 12, gy3 + 8), "LIVE BLUETOOTH TRAFFIC TELEMETRY (ROLLING 60-SEC WINDOW)", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.line([rx + 8, gy3 + 26, rx + gw - 8, gy3 + 26], fill=(24, 32, 48), width=1)

    # Stats Grid (3 Clean Columns)
    c1_lbl = rx + 16
    c1_val = rx + 110
    c2_lbl = rx + 175
    c2_val = rx + 255
    c3_lbl = rx + 355
    c3_val = rx + 435

    # Row 1
    draw.text((c1_lbl, gy3 + 36), "SPP Writes/min:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c1_val, gy3 + 36), "134", fill=C_TEXT_WHITE, font=f_bold)

    draw.text((c2_lbl, gy3 + 36), "SPP Reads/min:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c2_val, gy3 + 36), "136", fill=C_TEXT_WHITE, font=f_bold)

    draw.text((c3_lbl, gy3 + 36), "Frames/min:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c3_val, gy3 + 36), "2", fill=C_GREEN, font=f_bold)

    # Row 2
    draw.text((c1_lbl, gy3 + 60), "Throughput:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c1_val - 20, gy3 + 60), "1.89 KB/min", fill=C_GREEN, font=f_bold)

    draw.text((c2_lbl, gy3 + 60), "Total Sent:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c2_val, gy3 + 60), "42.6 KB (14f)", fill=C_TEXT_WHITE, font=f_bold)

    draw.text((c3_lbl, gy3 + 60), "Redundant:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c3_val, gy3 + 60), "0 (Diff elided)", fill=C_ACTIVE_CYAN, font=f_bold)

    # Row 3
    draw.text((c1_lbl, gy3 + 84), "Knob Rate:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c1_val - 20, gy3 + 84), "2.85 Hz", fill=C_TEXT_WHITE, font=f_bold)

    draw.text((c2_lbl, gy3 + 84), "Channel Check:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c2_val, gy3 + 84), "1 / min", fill=C_GREEN, font=f_bold)

    draw.text((c3_lbl, gy3 + 84), "Errors/Recon:", fill=C_TEXT_DIM, font=f_sub)
    draw.text((c3_val, gy3 + 84), "0 / 0", fill=C_GREEN, font=f_bold)

    draw.text((rx + 16, gy3 + 106), "Coexistence Diagnostic: 25.1% radio contention reduction on MediaTek RZ616 Bluetooth adapter.", fill=C_TEXT_DIM, font=f_sub)

    # Action Buttons
    gy4 = gy3 + 135
    draw.rectangle([rx, gy4, rx + 120, gy4 + 26], fill=(18, 32, 48), outline=C_ACTIVE_CYAN)
    draw.text((rx + 14, gy4 + 7), "TEST DISPLAY", fill=C_ACTIVE_CYAN, font=f_btn)

    draw.rectangle([rx + 130, gy4, rx + 240, gy4 + 26], fill=(18, 32, 48), outline=(40, 56, 80))
    draw.text((rx + 150, gy4 + 7), "RECONNECT", fill=C_TEXT_WHITE, font=f_btn)

    draw.rectangle([rx + 250, gy4, rx + 380, gy4 + 26], fill=(18, 32, 48), outline=(40, 56, 80))
    draw.text((rx + 264, gy4 + 7), "COPY DIAGNOSTICS", fill=C_TEXT_WHITE, font=f_btn)

    # Bottom action bar
    draw.rectangle([0, h - 48, w, h], fill=(12, 16, 26), outline=(24, 32, 48))
    draw.rectangle([w - 210, h - 38, w - 120, h - 10], fill=(22, 28, 42), outline=(38, 50, 72))
    draw.text((w - 190, h - 28), "CANCEL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([w - 110, h - 38, w - 16, h - 10], fill=(14, 48, 64), outline=C_ACTIVE_CYAN)
    draw.text((w - 95, h - 28), "SAVE CHANGES", fill=C_ACTIVE_CYAN, font=f_btn)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

# ---------------------------------------------------------------------------
# MAIN SCRIPT RUNNER
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("assets/screenshots", exist_ok=True)

    # Milestone 13 Requested Screenshots
    render_preset_ai_screenshot("assets/screenshots/preset-ai.png")
    render_preset_crypto_screenshot("assets/screenshots/preset-crypto.png")
    render_preset_stocks_screenshot("assets/screenshots/preset-stocks.png")
    render_preset_system_screenshot("assets/screenshots/preset-system.png")
    render_preset_all_screenshot("assets/screenshots/preset-all.png")
    render_settings_dashboard_screenshot("assets/screenshots/settings-dashboard.png")
    render_settings_minitoo_screenshot("assets/screenshots/settings-minitoo.png")

    # Legacy numbered screenshots for backward compatibility
    render_preset_all_screenshot("assets/screenshots/01_desktop_overview.png")
    render_preset_all_screenshot("assets/screenshots/06_preset_all_dashboard.png")
    render_preset_ai_screenshot("assets/screenshots/08_preset_ai.png")
