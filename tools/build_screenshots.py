#!/usr/bin/env python3
"""
Generate crisp, clean, high-resolution screenshots for AI Desk Dashboard documentation:
1. assets/screenshots/01_desktop_overview.png (Complete desktop companion app with sections & presets)
2. assets/screenshots/02_quota_remaining_cards.png (Codex, Gemini & Claude remaining quota)
3. assets/screenshots/03_btc_sparkline.png (Multi-crypto sparklines & pricing)
4. assets/screenshots/04_gpu_and_dgx_monitoring.png (Local RTX & Remote DGX Spark)
5. assets/screenshots/05_ai_activity_and_services.png (AI Activity & Services health)
6. assets/screenshots/06_preset_all_dashboard.png (ALL preset with all 4 sections)
7. assets/screenshots/07_preset_markets.png (MARKETS preset: Crypto + Stocks Scanner)
8. assets/screenshots/08_preset_ai.png (AI preset: Codex, Gemini, Claude + Activity)
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

    f_title = get_font(11, bold=True)
    f_badge = get_font(9, bold=True)

    draw.text((x + 8, y + 6), title, fill=title_color, font=f_title)

    if is_active:
        draw.rectangle([x + w - 74, y + 4, x + w - 6, y + 18], fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
        draw.text((x + w - 66, y + 5), "ON MINITOO", fill=C_ACTIVE_CYAN, font=f_badge)
    else:
        draw.rectangle([x + w - 64, y + 4, x + w - 6, y + 18], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.ellipse([x + w - 58, y + 9, x + w - 53, y + 14], fill=badge_color)
        draw.text((x + w - 48, y + 5), badge_text, fill=C_TEXT_WHITE, font=f_badge)

    draw.line([x + 6, y + 23, x + w - 6, y + 23], fill=(27, 35, 53), width=1)


def draw_header(draw: ImageDraw.ImageDraw, w: int, active_preset: str = "ALL"):
    f_ui = get_font(11, bold=True)
    f_sub = get_font(9, bold=False)
    f_btn = get_font(8, bold=True)

    draw.rectangle([0, 0, w, 64], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.text((12, 10), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_ui)
    draw.text((160, 13), "v0.2.0", fill=C_TEXT_DIM, font=f_sub)

    # MiniToo status pill
    draw.rectangle([w - 280, 8, w - 165, 28], fill=(16, 24, 38), outline=C_ACTIVE_CYAN)
    draw.ellipse([w - 274, 15, w - 268, 21], fill=C_GREEN)
    draw.text((w - 262, 11), "MINITOO ● COM7", fill=C_ACTIVE_CYAN, font=f_sub)

    # Autostart
    draw.rectangle([w - 158, 8, w - 74, 28], fill=(14, 36, 25), outline=C_GREEN)
    draw.text((w - 150, 11), "AUTOSTART: ON", fill=C_GREEN, font=f_btn)

    # Settings
    draw.rectangle([w - 68, 8, w - 12, 28], fill=(20, 28, 44), outline=(40, 52, 75))
    draw.text((w - 60, 11), "⚙ SETTINGS", fill=C_ACTIVE_CYAN, font=f_btn)

    # Line 2: Presets
    draw.text((12, 42), "PRESETS:", fill=C_TEXT_DIM, font=f_btn)
    px = 78
    for p in ["ALL", "AI", "MARKETS", "SYSTEM"]:
        is_act = (p == active_preset)
        p_bg = (11, 38, 56) if is_act else (16, 22, 34)
        p_fg = C_ACTIVE_CYAN if is_act else C_TEXT_MUTED
        p_bd = C_ACTIVE_CYAN if is_act else (28, 37, 54)
        draw.rectangle([px, 34, px + 70, 54], fill=p_bg, outline=p_bd, width=1)
        draw.text((px + 14, 38), f"[ {p} ]", fill=p_fg, font=f_btn)
        px += 76


def render_preset_all_screenshot(out_path: str):
    """Renders the comprehensive ALL preset dashboard with all 4 sections."""
    w, h = 640, 680
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="ALL")

    f_sec = get_font(9, bold=True)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)

    curr_y = 74
    card_w = 200
    card_h = 120
    gap = 8
    m = 10

    # 1. SECTION: CRYPTO MARKETS
    draw.text((m, curr_y), "─── [ CRYPTO MARKETS ] ", fill=C_GOLD, font=f_sec)
    draw.line([m + 130, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # BTC, ETH, SOL
    c1 = (m, curr_y)
    draw_card(draw, c1[0], c1[1], card_w, card_h, "₿ BTC", C_GOLD, "-0.9%", C_RED, is_active=True)
    draw.text((c1[0] + 8, c1[1] + 32), "$84,021", fill=C_GOLD, font=get_font(13, bold=True))
    draw.text((c1[0] + card_w - 55, c1[1] + 32), "-0.9%", fill=C_RED, font=f_bold)
    # Sparkline
    pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = (card_w - 20) / (len(pts) - 1)
    sp_pts = [(c1[0] + 10 + i * step, c1[1] + 85 - v * 35) for i, v in enumerate(pts)]
    for i in range(len(sp_pts) - 1):
        draw.line([sp_pts[i], sp_pts[i+1]], fill=C_GOLD, width=2)
    draw.text((c1[0] + 8, c1[1] + card_h - 14), "H $85,208  L $83,230", fill=C_TEXT_DIM, font=f_small)

    c2 = (m + card_w + gap, curr_y)
    draw_card(draw, c2[0], c2[1], card_w, card_h, "Ξ ETH", (98, 126, 234), "-0.2%", C_RED)
    draw.text((c2[0] + 8, c2[1] + 32), "$2,691", fill=(98, 126, 234), font=get_font(13, bold=True))
    draw.text((c2[0] + card_w - 55, c2[1] + 32), "-0.2%", fill=C_RED, font=f_bold)
    eth_pts = [(c2[0] + 10 + i * step, c2[1] + 85 - v * 30) for i, v in enumerate(pts[::-1])]
    for i in range(len(eth_pts) - 1):
        draw.line([eth_pts[i], eth_pts[i+1]], fill=(98, 126, 234), width=2)
    draw.text((c2[0] + 8, c2[1] + card_h - 14), "H $2,740  L $2,667", fill=C_TEXT_DIM, font=f_small)

    c3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, c3[0], c3[1], card_w, card_h, "◎ SOL", (20, 241, 149), "+3.3%", C_GREEN)
    draw.text((c3[0] + 8, c3[1] + 32), "$122.06", fill=(20, 241, 149), font=get_font(13, bold=True))
    draw.text((c3[0] + card_w - 55, c3[1] + 32), "+3.3%", fill=C_GREEN, font=f_bold)
    sol_pts = [(c3[0] + 10 + i * step, c3[1] + 85 - (0.3 + 0.6 * (i/len(pts))) * 35) for i in range(len(pts))]
    for i in range(len(sol_pts) - 1):
        draw.line([sol_pts[i], sol_pts[i+1]], fill=(20, 241, 149), width=2)
    draw.text((c3[0] + 8, c3[1] + card_h - 14), "H $122.75  L $115.92", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 8

    # 2. SECTION: AI USAGE
    draw.text((m, curr_y), "─── [ AI USAGE ] ", fill=C_CORAL, font=f_sec)
    draw.line([m + 100, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
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
    draw.line([m + 175, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
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
        draw.text((m + 80, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((m + 160, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((mid_x - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.line([mid_x, curr_y + 24, mid_x, curr_y + sw_h - 16], fill=(24, 32, 48), width=1)

    for idx, (rk, sym, pr, chg, vol) in enumerate(stocks_sample[5:]):
        ry = curr_y + 28 + idx * 18
        draw.text((mid_x + 12, ry), rk, fill=C_TEXT_DIM, font=f_small)
        draw.text((mid_x + 30, ry), sym, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((mid_x + 85, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((mid_x + 165, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((m + sw_w - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((m + 10, curr_y + sw_h - 12), "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance Public Crumb API", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_preset_markets_screenshot(out_path: str):
    """Renders MARKETS preset: Crypto multi-assets + Top 10 Volatile Stocks."""
    w, h = 640, 520
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="MARKETS")

    f_sec = get_font(9, bold=True)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)

    curr_y = 74
    card_w = 200
    card_h = 120
    gap = 8
    m = 10

    # SECTION: CRYPTO MARKETS
    draw.text((m, curr_y), "─── [ CRYPTO MARKETS ] ", fill=C_GOLD, font=f_sec)
    draw.line([m + 130, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # BTC, DOGE, PEPE
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
    draw_card(draw, c2[0], c2[1], card_w, card_h, "Ð DOGE", (194, 166, 51), "+2.7%", C_GREEN)
    draw.text((c2[0] + 8, c2[1] + 32), "$0.0989", fill=(194, 166, 51), font=get_font(13, bold=True))
    draw.text((c2[0] + card_w - 55, c2[1] + 32), "+2.7%", fill=C_GREEN, font=f_bold)
    doge_pts = [(c2[0] + 10 + i * step, c2[1] + 85 - (0.4 + 0.5 * (i/len(pts))) * 35) for i in range(len(pts))]
    for i in range(len(doge_pts) - 1):
        draw.line([doge_pts[i], doge_pts[i+1]], fill=(194, 166, 51), width=2)
    draw.text((c2[0] + 8, c2[1] + card_h - 14), "H $0.0997  L $0.0946", fill=C_TEXT_DIM, font=f_small)

    c3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, c3[0], c3[1], card_w, card_h, "🐸 PEPE", (72, 199, 116), "+0.7%", C_GREEN)
    draw.text((c3[0] + 8, c3[1] + 32), "$0.0000045", fill=(72, 199, 116), font=get_font(11, bold=True))
    draw.text((c3[0] + card_w - 55, c3[1] + 32), "+0.7%", fill=C_GREEN, font=f_bold)
    pepe_pts = [(c3[0] + 10 + i * step, c3[1] + 85 - (0.3 + 0.4 * (i/len(pts))) * 35) for i in range(len(pts))]
    for i in range(len(pepe_pts) - 1):
        draw.line([pepe_pts[i], pepe_pts[i+1]], fill=(72, 199, 116), width=2)
    draw.text((c3[0] + 8, c3[1] + card_h - 14), "MICRO TOKEN · $4.5u", fill=C_TEXT_DIM, font=f_small)

    curr_y += card_h + gap + 14

    # SECTION: VOLATILE STOCKS SCANNER
    draw.text((m, curr_y), "─── [ VOLATILE STOCKS SCANNER ] ", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.line([m + 175, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

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
        draw.text((m + 80, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((m + 160, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((mid_x - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.line([mid_x, curr_y + 24, mid_x, curr_y + sw_h - 16], fill=(24, 32, 48), width=1)

    for idx, (rk, sym, pr, chg, vol) in enumerate(stocks_sample[5:]):
        ry = curr_y + 28 + idx * 18
        draw.text((mid_x + 12, ry), rk, fill=C_TEXT_DIM, font=f_small)
        draw.text((mid_x + 30, ry), sym, fill=C_TEXT_WHITE, font=f_bold)
        draw.text((mid_x + 85, ry), pr, fill=C_TEXT_MUTED, font=f_small)
        draw.text((mid_x + 165, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_bold)
        draw.text((m + sw_w - 14, ry), vol, fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((m + 10, curr_y + sw_h - 12), "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance Public Crumb API", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_preset_ai_screenshot(out_path: str):
    """Renders AI preset: Codex, Gemini, Claude (with diagnostics) + AI Activity."""
    w, h = 640, 420
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, w, active_preset="AI")

    f_sec = get_font(9, bold=True)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)

    curr_y = 74
    card_w = 200
    card_h = 135
    gap = 8
    m = 10

    draw.text((m, curr_y), "─── [ AI USAGE & ACTIVITY ] ", fill=C_CORAL, font=f_sec)
    draw.line([m + 160, curr_y + 6, w - m, curr_y + 6], fill=(24, 32, 48), width=1)
    curr_y += 18

    # Codex
    a1 = (m, curr_y)
    draw_card(draw, a1[0], a1[1], card_w, card_h, "CODEX", C_GREEN, "READY", C_GREEN)
    draw.text((a1[0] + 8, a1[1] + 32), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a1[0] + card_w - 65, a1[1] + 32), "100% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a1[0] + 8, a1[1] + 45, card_w - 16, 5, 100, C_GREEN)
    draw.text((a1[0] + 8, a1[1] + 57), "RESET 5H 0M", fill=C_TEXT_DIM, font=f_small)

    draw.text((a1[0] + 8, a1[1] + 72), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a1[0] + card_w - 65, a1[1] + 72), "29% LEFT", fill=C_AMBER, font=f_bold)
    draw_segmented_bar(draw, a1[0] + 8, a1[1] + 85, card_w - 16, 5, 29, C_AMBER)
    draw.text((a1[0] + 8, a1[1] + 97), "RESET 1D 22H", fill=C_TEXT_DIM, font=f_small)
    draw.text((a1[0] + 8, a1[1] + card_h - 14), "GPT-5.6 · CHATGPT PLUS", fill=C_TEXT_DIM, font=f_small)

    # Gemini
    a2 = (m + card_w + gap, curr_y)
    draw_card(draw, a2[0], a2[1], card_w, card_h, "GEMINI", C_BLUE, "ACTIVE", C_GREEN)
    draw.text((a2[0] + 8, a2[1] + 32), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a2[0] + card_w - 65, a2[1] + 32), "73% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a2[0] + 8, a2[1] + 45, card_w - 16, 5, 73, C_GREEN)
    draw.text((a2[0] + 8, a2[1] + 57), "RESET 4H 16M", fill=C_TEXT_DIM, font=f_small)

    draw.text((a2[0] + 8, a2[1] + 72), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a2[0] + card_w - 65, a2[1] + 72), "76% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a2[0] + 8, a2[1] + 85, card_w - 16, 5, 76, C_GREEN)
    draw.text((a2[0] + 8, a2[1] + 97), "RESET 6D 1H", fill=C_TEXT_DIM, font=f_small)
    draw.text((a2[0] + 8, a2[1] + card_h - 14), "GEMINI 3.8 · GOOGLE AI PRO", fill=C_TEXT_DIM, font=f_small)

    # Claude
    a3 = (m + (card_w + gap) * 2, curr_y)
    draw_card(draw, a3[0], a3[1], card_w, card_h, "CLAUDE", C_CORAL, "STALE", C_AMBER)
    draw.text((a3[0] + 8, a3[1] + 32), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a3[0] + card_w - 65, a3[1] + 32), "97% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a3[0] + 8, a3[1] + 45, card_w - 16, 5, 97, C_GREEN)
    draw.text((a3[0] + 8, a3[1] + 57), "RESET NOW (CACHED)", fill=C_TEXT_DIM, font=f_small)

    draw.text((a3[0] + 8, a3[1] + 72), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((a3[0] + card_w - 65, a3[1] + 72), "62% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, a3[0] + 8, a3[1] + 85, card_w - 16, 5, 62, C_GREEN)
    draw.text((a3[0] + 8, a3[1] + 97), "RESET NOW (CACHED)", fill=C_TEXT_DIM, font=f_small)
    draw.text((a3[0] + 8, a3[1] + card_h - 14), "no***@gmail.com · CLAUDE PRO", fill=C_TEXT_DIM, font=f_small)

    # AI Activity below
    curr_y += card_h + gap + 14
    act_w = w - m * 2
    act_h = 75
    draw.rectangle([m, curr_y, m + act_w, curr_y + act_h], fill=C_CARD_BG, outline=C_PURPLE, width=1)
    draw.text((m + 10, curr_y + 8), "AI ACTIVITY MONITOR (LOCAL PROCESS TABLE & RECENT DB WAL)", fill=C_PURPLE, font=f_bold)

    draw.ellipse([m + 12, curr_y + 36, m + 18, curr_y + 42], fill=C_GREEN)
    draw.text((m + 24, curr_y + 34), "CODEX: WORKING (active 6h 52m)", fill=C_TEXT_WHITE, font=f_small)

    draw.ellipse([m + 220, curr_y + 36, m + 226, curr_y + 42], fill=C_TEXT_DIM)
    draw.text((m + 232, curr_y + 34), "CLAUDE: IDLE", fill=C_TEXT_MUTED, font=f_small)

    draw.ellipse([m + 380, curr_y + 36, m + 386, curr_y + 42], fill=C_GREEN)
    draw.text((m + 392, curr_y + 34), "GEMINI: WORKING (active 5h 45m)", fill=C_TEXT_WHITE, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_quota_cards_screenshot(out_path: str):
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)
    card_w = 196
    card_h = 144

    # Card 1: CODEX
    draw_card(draw, 8, 8, card_w, card_h, "CODEX", C_GREEN, "READY", C_GREEN)
    draw.text((16, 40), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((card_w - 65, 40), "100% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, 16, 54, card_w - 16, 6, 100, C_GREEN)
    draw.text((16, 66), "RESET 5H 0M", fill=C_TEXT_DIM, font=f_small)
    draw.text((16, 82), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((card_w - 65, 82), "29% LEFT", fill=C_AMBER, font=f_bold)
    draw_segmented_bar(draw, 16, 96, card_w - 16, 6, 29, C_AMBER)
    draw.text((16, 108), "RESET 1D 22H", fill=C_TEXT_DIM, font=f_small)
    draw.text((16, card_h - 8), "GPT-5.6 · PLUS", fill=C_TEXT_DIM, font=f_small)

    # Card 2: GEMINI
    draw_card(draw, 8 + card_w + 8, 8, card_w, card_h, "GEMINI", C_BLUE, "ACTIVE", C_GREEN)
    c2 = 8 + card_w + 8
    draw.text((c2 + 8, 40), "5H", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2 + card_w - 65, 40), "73% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2 + 8, 54, card_w - 16, 6, 73, C_GREEN)
    draw.text((c2 + 8, 66), "RESET 4H 16M", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2 + 8, 82), "WEEK", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2 + card_w - 65, 82), "76% LEFT", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2 + 8, 96, card_w - 16, 6, 76, C_GREEN)
    draw.text((c2 + 8, 108), "RESET 6D 1H", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2 + 8, card_h - 8), "GEMINI 3.8 · ULTRA", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_btc_sparkline_screenshot(out_path: str):
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)
    card_w = 196
    card_h = 144

    # BTC Card
    draw_card(draw, 8, 8, card_w, card_h, "₿ BTC", C_GOLD, "-0.9%", C_RED)
    draw.text((16, 40), "$84,021", fill=C_GOLD, font=get_font(13, bold=True))
    draw.text((card_w - 55, 40), "-0.9%", fill=C_RED, font=f_bold)
    pts = [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95]
    step = (card_w - 20) / (len(pts) - 1)
    sp_pts = [(18 + i * step, 105 - v * 40) for i, v in enumerate(pts)]
    for i in range(len(sp_pts) - 1):
        draw.line([sp_pts[i], sp_pts[i+1]], fill=C_GOLD, width=2)
    draw.text((16, card_h - 8), "H $85,208  L $83,230", fill=C_TEXT_DIM, font=f_small)

    # PEPE Card
    c2 = 8 + card_w + 8
    draw_card(draw, c2, 8, card_w, card_h, "🐸 PEPE", (72, 199, 116), "+0.7%", C_GREEN)
    draw.text((c2 + 8, 40), "$0.0000045", fill=(72, 199, 116), font=get_font(11, bold=True))
    draw.text((c2 + card_w - 55, 40), "+0.7%", fill=C_GREEN, font=f_bold)
    pepe_pts = [(c2 + 10 + i * step, 105 - (0.3 + 0.5 * (i/len(pts))) * 40) for i in range(len(pts))]
    for i in range(len(pepe_pts) - 1):
        draw.line([pepe_pts[i], pepe_pts[i+1]], fill=(72, 199, 116), width=2)
    draw.text((c2 + 8, card_h - 8), "MICRO TOKEN · $4.5u", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_gpu_dgx_screenshot(out_path: str):
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)
    card_w = 196
    card_h = 144

    draw_card(draw, 8, 8, card_w, card_h, "LOCAL PC", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((16, 40), "GPU", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((card_w - 50, 40), "3%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, 16, 54, card_w - 16, 6, 3, C_GREEN)
    draw.text((16, 66), "TEMP 38C  VRAM 3.0G", fill=C_TEXT_DIM, font=f_small)
    draw.text((16, 82), "RAM", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((card_w - 50, 82), "44%", fill=(55, 195, 245), font=f_bold)
    draw_segmented_bar(draw, 16, 96, card_w - 16, 6, 44, (55, 195, 245))
    draw.text((16, card_h - 8), "RTX 5080 · 16G", fill=C_TEXT_DIM, font=f_small)

    c2 = 8 + card_w + 8
    draw_card(draw, c2, 8, card_w, card_h, "DGX SPARK", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((c2 + 8, 40), "GPU", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2 + card_w - 50, 40), "0%", fill=C_GREEN, font=f_bold)
    draw_segmented_bar(draw, c2 + 8, 54, card_w - 16, 6, 0, C_GREEN)
    draw.text((c2 + 8, 66), "TEMP 39C  LOAD 1.72", fill=C_TEXT_DIM, font=f_small)
    draw.text((c2 + 8, 82), "RAM", fill=C_TEXT_MUTED, font=f_bold)
    draw.text((c2 + card_w - 50, 82), "40%", fill=C_NVIDIA, font=f_bold)
    draw_segmented_bar(draw, c2 + 8, 96, card_w - 16, 6, 40, C_NVIDIA)
    draw.text((c2 + 8, card_h - 8), "GB10 · SPARK LIVE", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def render_activity_services_screenshot(out_path: str):
    w, h = 420, 160
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    f_bold = get_font(10, bold=True)
    f_small = get_font(8, bold=False)
    card_w = 196
    card_h = 144

    draw_card(draw, 8, 8, card_w, card_h, "AI ACTIVITY", C_PURPLE, "2/3 ACT", C_GREEN)
    draw.ellipse([16, 43, 22, 49], fill=C_GREEN)
    draw.text((28, 40), "CODEX: WORKING", fill=C_TEXT_WHITE, font=f_small)
    draw.ellipse([16, 65, 22, 71], fill=C_TEXT_DIM)
    draw.text((28, 62), "CLAUDE: IDLE", fill=C_TEXT_MUTED, font=f_small)
    draw.ellipse([16, 87, 22, 93], fill=C_GREEN)
    draw.text((28, 84), "GEMINI: WORKING", fill=C_TEXT_WHITE, font=f_small)
    draw.text((16, card_h - 8), "AGENT DAEMON POOL", fill=C_TEXT_DIM, font=f_small)

    c2 = 8 + card_w + 8
    draw_card(draw, c2, 8, card_w, card_h, "SERVICES", C_GREEN, "ONLINE", C_GREEN)
    svcs = [("DGX (SSH)", True), ("OLLAMA", True), ("COMFYUI", True), ("FORGE3D", True), ("HERMES", True)]
    sy = 36
    for s_name, s_up in svcs:
        draw.ellipse([c2 + 10, sy + 3, c2 + 16, sy + 9], fill=C_GREEN if s_up else C_RED)
        draw.text((c2 + 22, sy), s_name, fill=C_TEXT_WHITE, font=f_small)
        sy += 18
    draw.text((c2 + 8, card_h - 8), "TAILSCALE WORKSTATION", fill=C_TEXT_DIM, font=f_small)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    os.makedirs("assets/screenshots", exist_ok=True)
    render_preset_all_screenshot("assets/screenshots/01_desktop_overview.png")
    render_preset_all_screenshot("assets/screenshots/06_preset_all_dashboard.png")
    render_preset_markets_screenshot("assets/screenshots/07_preset_markets.png")
    render_preset_ai_screenshot("assets/screenshots/08_preset_ai.png")
    render_quota_cards_screenshot("assets/screenshots/02_quota_remaining_cards.png")
    render_btc_sparkline_screenshot("assets/screenshots/03_btc_sparkline.png")
    render_gpu_dgx_screenshot("assets/screenshots/04_gpu_and_dgx_monitoring.png")
    render_activity_services_screenshot("assets/screenshots/05_ai_activity_and_services.png")
