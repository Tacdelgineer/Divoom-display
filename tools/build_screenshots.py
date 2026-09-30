#!/usr/bin/env python3
"""
Generate crisp, clean, high-resolution 1080p (1920x1080) and 9:16 Vertical Creator screenshots
for AI Desk Dashboard Milestone 14 documentation:
1. assets/screenshots/preset-all.png (1920x1080 command center hero: Crypto, AI, Stocks, System)
2. assets/screenshots/preset-ai.png (1920x1080 AI hero preset: Codex, Gemini, Claude quotas + Agent Activity)
3. assets/screenshots/preset-crypto.png (1920x1080 CRYPTO hero preset: 5-asset layout with high-res sparklines)
4. assets/screenshots/preset-stocks.png (1920x1080 STOCKS hero preset: Top 10 Volatile Stocks Scanner terminal)
5. assets/screenshots/preset-system.png (1920x1080 SYSTEM hero preset: Local RTX 5080, DGX Spark, Services, Coding)
6. assets/screenshots/settings-dashboard.png (900x660 High-DPI Settings UI: DASHBOARD tab & UI Scale system)
7. assets/screenshots/settings-minitoo.png (900x660 High-DPI Settings UI: MINITOO tab with Bluetooth Low Interference)
8. assets/screenshots/creator-crypto-vertical.png (1080x1920 9:16 vertical Shorts capture: BTC, ETH, SOL, DOGE, PEPE)
9. assets/screenshots/creator-ai-vertical.png (1080x1920 9:16 vertical Shorts capture: Codex, Gemini, Claude, Activity)
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

def draw_segmented_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float | None, color: tuple, segments: int = 16):
    gap = 2
    seg_w = (w - (segments - 1) * gap) / segments
    active_count = int(round((pct / 100.0) * segments)) if pct is not None else 0

    for i in range(segments):
        sx = x + i * (seg_w + gap)
        fill = color if i < active_count else (24, 32, 46)
        draw.rectangle([sx, y, sx + seg_w, y + h], fill=fill)

def draw_card_frame(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    title: str,
    title_color: tuple,
    badge_text: str,
    badge_color: tuple,
    is_active: bool = False,
    is_hover: bool = False,
):
    border_col = C_ACTIVE_CYAN if is_active else ((45, 59, 84) if is_hover else C_CARD_BORDER)
    border_w = 2 if is_active else 1
    bg_col = (18, 26, 43) if is_active else C_CARD_BG

    draw.rectangle([x, y, x + w, y + h], fill=bg_col, outline=border_col, width=border_w)

    f_title = get_font(13, bold=True)
    f_badge = get_font(10, bold=True)

    draw.text((x + 14, y + 12), title, fill=title_color, font=f_title)

    if is_active:
        tag_w = 90
        draw.rectangle([x + w - tag_w - 12, y + 10, x + w - 12, y + 28], fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
        draw.text((x + w - tag_w - 4, y + 12), "ON MINITOO", fill=C_ACTIVE_CYAN, font=f_badge)
    else:
        tag_w = 80
        draw.rectangle([x + w - tag_w - 12, y + 10, x + w - 12, y + 28], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.ellipse([x + w - tag_w - 4, y + 16, x + w - tag_w + 2, y + 22], fill=badge_color)
        draw.text((x + w - tag_w + 8, y + 12), badge_text, fill=C_TEXT_WHITE, font=f_badge)

def draw_command_center_header(draw: ImageDraw.ImageDraw, w: int, active_preset: str = "ALL"):
    f_title = get_font(14, bold=True)
    f_btn = get_font(11, bold=True)
    f_meta = get_font(10, bold=False)

    draw.rectangle([0, 0, w, 68], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)

    # 1. App Title
    draw.text((20, 24), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=f_title)

    # 2. Device Selector
    dev_x = 240
    draw.rectangle([dev_x, 16, dev_x + 135, 52], fill=(16, 24, 38), outline=C_ACTIVE_CYAN, width=1)
    draw.text((dev_x + 14, 25), "🖥 MiniToo ▼", fill=C_ACTIVE_CYAN, font=f_btn)

    # 3. Presets
    px = 405
    draw.text((px, 26), "PRESET:", fill=C_TEXT_DIM, font=f_meta)
    px += 65
    for p in ["ALL", "AI", "CRYPTO", "STOCKS", "SYSTEM"]:
        is_act = (p == active_preset)
        p_bg = (11, 56, 74) if is_act else (16, 22, 34)
        p_fg = C_ACTIVE_CYAN if is_act else C_TEXT_MUTED
        p_bd = C_ACTIVE_CYAN if is_act else (28, 37, 54)
        bw = 80 if p in ["CRYPTO", "STOCKS", "SYSTEM"] else 60
        draw.rectangle([px, 16, px + bw, 52], fill=p_bg, outline=p_bd, width=2 if is_act else 1)
        draw.text((px + bw // 2 - 16, 25), p, fill=p_fg, font=f_btn)
        px += bw + 8

    # 4. Right Utility Bar
    # Settings
    set_x2 = w - 20
    set_x1 = set_x2 - 120
    draw.rectangle([set_x1, 16, set_x2, 52], fill=(19, 27, 42), outline=(37, 53, 79), width=1)
    draw.text((set_x1 + 16, 25), "⚙ SETTINGS", fill=C_ACTIVE_CYAN, font=f_btn)

    # Autostart
    auto_x2 = set_x1 - 12
    auto_x1 = auto_x2 - 130
    draw.rectangle([auto_x1, 16, auto_x2, 52], fill=(14, 36, 25), outline=C_GREEN, width=1)
    draw.text((auto_x1 + 18, 25), "⚡ AUTO: ON", fill=C_GREEN, font=f_btn)

    # Creator View
    creat_x2 = auto_x1 - 12
    creat_x1 = creat_x2 - 125
    draw.rectangle([creat_x1, 16, creat_x2, 52], fill=(27, 20, 40), outline=(64, 37, 95), width=1)
    draw.text((creat_x1 + 14, 25), "🎬 CREATOR", fill=C_PURPLE, font=f_btn)

    # Connection Status Pill
    pill_x2 = creat_x1 - 14
    pill_x1 = pill_x2 - 180
    draw.rectangle([pill_x1, 16, pill_x2, 52], fill=(13, 38, 27), outline=(27, 77, 54), width=1)
    draw.ellipse([pill_x1 + 12, 31, pill_x1 + 20, 39], fill=C_GREEN)
    draw.text((pill_x1 + 28, 26), "MINITOO ● COM13", fill=C_GREEN, font=f_meta)

    draw.line([0, 68, w, 68], fill=(21, 29, 42), width=1)

# ---------------------------------------------------------------------------
# 1. 1920x1080 COMMAND CENTER SCREENSHOT (PRESET ALL)
# ---------------------------------------------------------------------------
def render_preset_all_screenshot(out_path: str):
    """Renders 1080p full command center dashboard with all 4 responsive sections."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="ALL")

    f_sec = get_font(13, bold=True)
    f_btn = get_font(11, bold=True)
    f_hero = get_font(20, bold=True)
    f_sec_metric = get_font(13, bold=True)
    f_meta = get_font(10, bold=False)

    m = 20
    curr_y = 82
    gap = 14

    # 1. SECTION: CRYPTO MARKETS (5 cards fit across full 1920px screen in 1 row!)
    draw.text((m, curr_y), "─── [ CRYPTO MARKETS ]", fill=C_GOLD, font=f_sec)
    draw.rectangle([m + 230, curr_y - 4, m + 325, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 242, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 340, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 30

    crypto_w = (w - 2 * m - 4 * gap) // 5
    crypto_h = 165
    coins_data = [
        ("btc", "₿ BTC · BITCOIN", "$84,021", "-0.9%", C_GOLD, C_RED, [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95], True),
        ("eth", "Ξ ETH · ETHEREUM", "$2,691", "-0.2%", C_ETH, C_RED, [0.8, 0.72, 0.75, 0.62, 0.65, 0.55, 0.58, 0.48, 0.52, 0.42, 0.45, 0.35, 0.38, 0.28, 0.30, 0.22], False),
        ("sol", "◎ SOL · SOLANA", "$122.06", "+3.3%", C_SOLANA, C_GREEN, [0.3, 0.35, 0.32, 0.45, 0.48, 0.58, 0.55, 0.68, 0.72, 0.82, 0.78, 0.88, 0.85, 0.94, 0.91, 0.97], False),
        ("doge", "Ð DOGE · DOGECOIN", "$0.0989", "+2.7%", C_DOGE, C_GREEN, [0.4, 0.42, 0.38, 0.50, 0.52, 0.60, 0.58, 0.68, 0.65, 0.75, 0.72, 0.82, 0.80, 0.88, 0.85, 0.91], False),
        ("pepe", "🐸 PEPE · PEPE", "$0.0000045", "+0.7%", C_PEPE, C_GREEN, [0.5, 0.48, 0.52, 0.55, 0.53, 0.62, 0.60, 0.68, 0.65, 0.72, 0.70, 0.76, 0.74, 0.79, 0.77, 0.82], False),
    ]

    for idx, (cid, title, price, chg, col, chg_col, pts, is_act) in enumerate(coins_data):
        cx = m + idx * (crypto_w + gap)
        draw_card_frame(draw, cx, curr_y, crypto_w, crypto_h, title, col, chg, chg_col, is_active=is_act)
        draw.text((cx + 14, curr_y + 44), price, fill=col, font=f_hero)
        draw.text((cx + crypto_w - 75, curr_y + 48), chg, fill=chg_col, font=f_sec_metric)

        # High-res Sparkline
        sp_x1 = cx + 14
        sp_x2 = cx + crypto_w - 14
        sp_y1 = curr_y + 76
        sp_y2 = curr_y + crypto_h - 32
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=2)
        draw.ellipse([sp_pts[-1][0] - 3, sp_pts[-1][1] - 3, sp_pts[-1][0] + 3, sp_pts[-1][1] + 3], fill=col)

        draw.text((cx + 14, curr_y + crypto_h - 20), "24H H $85.2K  L $83.2K", fill=C_TEXT_DIM, font=f_meta)
        draw.text((cx + crypto_w - 48, curr_y + crypto_h - 20), "SPOT", fill=C_TEXT_DIM, font=f_meta)

    curr_y += crypto_h + gap + 10

    # 2. SECTION: AI USAGE (3 spacious cards)
    draw.text((m, curr_y), "─── [ AI USAGE & SUBSCRIPTION QUOTAS ]", fill=C_CORAL, font=f_sec)
    draw.rectangle([m + 375, curr_y - 4, m + 470, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 387, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 485, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 30

    ai_w = (w - 2 * m - 2 * gap) // 3
    ai_h = 175
    ai_data = [
        ("CODEX CLI", C_GREEN, "READY", C_GREEN, "5H ROLLING", "100% LEFT", 100, "RESET: 5H 00M", "WEEKLY CAP", "29% LEFT", 29, "RESET: 1D 22H", "GPT-5.6 · CHATGPT PLUS TIER"),
        ("GEMINI CODE ASSIST", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING", "73% LEFT", 73, "RESET: 4H 16M", "WEEKLY CAP", "76% LEFT", 76, "RESET: 6D 01H", "GEMINI 3.8 · GOOGLE AI PRO"),
        ("CLAUDE PRO", C_CORAL, "ONLINE", C_GREEN, "5H ROLLING", "97% LEFT", 97, "RESET: NOW (CACHED)", "WEEKLY CAP", "62% LEFT", 62, "RESET: NOW (CACHED)", "no***@gmail.com · ANTHROPIC PRO"),
    ]

    for idx, (title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot) in enumerate(ai_data):
        ax = m + idx * (ai_w + gap)
        draw_card_frame(draw, ax, curr_y, ai_w, ai_h, title, col, bd, bd_col)

        # Primary Metric
        draw.text((ax + 14, curr_y + 42), p_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 120, curr_y + 38), p_val, fill=col, font=f_hero)
        draw_segmented_bar(draw, ax + 14, curr_y + 68, ai_w - 28, 8, p_pct, col, segments=16)
        draw.text((ax + 14, curr_y + 82), p_rst, fill=C_TEXT_DIM, font=f_meta)

        # Secondary Metric
        draw.text((ax + 14, curr_y + 106), s_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 95, curr_y + 104), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=f_sec_metric)
        draw_segmented_bar(draw, ax + 14, curr_y + 124, ai_w - 28, 6, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=16)
        draw.text((ax + 14, curr_y + 136), s_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.text((ax + 14, curr_y + ai_h - 18), foot, fill=C_TEXT_MUTED, font=f_meta)

    curr_y += ai_h + gap + 10

    # 3. SECTION: VOLATILE STOCKS SCANNER (Full Width Responsive Card)
    draw.text((m, curr_y), "─── [ VOLATILE US EQUITIES SCANNER ]", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.rectangle([m + 355, curr_y - 4, m + 450, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 367, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 465, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 30

    stocks_w = w - 2 * m
    stocks_h = 175
    draw.rectangle([m, curr_y, m + stocks_w, curr_y + stocks_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN, width=1)

    draw.text((m + 16, curr_y + 14), "TOP 10 MOST VOLATILE US EQUITIES (LIVE MARKET CRUMB FEED)", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.rectangle([m + stocks_w - 100, curr_y + 10, m + stocks_w - 14, curr_y + 30], fill=(16, 24, 38), outline=C_GREEN)
    draw.text((m + stocks_w - 86, curr_y + 13), "MARKET OPEN", fill=C_GREEN, font=f_meta)

    stocks_sample = [
        ("1", "DKNG", "DraftKings Inc", "$22.02", "+3.5%", "VOL 8.3%"),
        ("2", "GME", "GameStop Corp", "$23.39", "-6.5%", "VOL 7.6%"),
        ("3", "MARA", "MARA Holdings", "$12.55", "-2.9%", "VOL 6.4%"),
        ("4", "RIOT", "Riot Platforms", "$23.00", "-2.0%", "VOL 5.7%"),
        ("5", "TSLA", "Tesla Inc", "$372.11", "-1.5%", "VOL 5.1%"),
        ("6", "ARM", "Arm Holdings", "$310.32", "+1.3%", "VOL 5.0%"),
        ("7", "SMCI", "Super Micro", "$43.26", "+4.2%", "VOL 4.5%"),
        ("8", "MSFT", "Microsoft Corp", "$516.17", "+3.7%", "VOL 4.4%"),
        ("9", "MSTR", "MicroStrategy", "$158.61", "-1.9%", "VOL 3.7%"),
        ("10", "COIN", "Coinbase Global", "$195.11", "-2.1%", "VOL 3.6%"),
    ]

    mid_x = m + stocks_w // 2
    row_h = 24
    for idx, (rk, sym, name, pr, chg, vol) in enumerate(stocks_sample[:5]):
        ry = curr_y + 44 + idx * row_h
        draw.text((m + 20, ry), f"#{rk}", fill=C_TEXT_DIM, font=f_meta)
        draw.text((m + 65, ry), sym, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((m + 160, ry), name, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((m + 320, ry), pr, fill=C_TEXT_WHITE, font=f_meta)
        draw.text((m + 420, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_sec_metric)
        draw.text((mid_x - 30, ry), vol, fill=C_ACTIVE_CYAN, font=f_sec_metric)

    draw.line([mid_x, curr_y + 40, mid_x, curr_y + stocks_h - 30], fill=(24, 32, 48), width=1)

    for idx, (rk, sym, name, pr, chg, vol) in enumerate(stocks_sample[5:]):
        ry = curr_y + 44 + idx * row_h
        draw.text((mid_x + 30, ry), f"#{rk}", fill=C_TEXT_DIM, font=f_meta)
        draw.text((mid_x + 75, ry), sym, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((mid_x + 170, ry), name, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((mid_x + 330, ry), pr, fill=C_TEXT_WHITE, font=f_meta)
        draw.text((mid_x + 430, ry), chg, fill=C_GREEN if "+" in chg else C_RED, font=f_sec_metric)
        draw.text((m + stocks_w - 30, ry), vol, fill=C_ACTIVE_CYAN, font=f_sec_metric)

    draw.text((m + 16, curr_y + stocks_h - 18), "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance High-Frequency Poller", fill=C_TEXT_DIM, font=f_meta)

    curr_y += stocks_h + gap + 10

    # 4. SECTION: SYSTEM & SERVICES (3 Cards)
    draw.text((m, curr_y), "─── [ LOCAL HARDWARE & SYSTEM SERVICES ]", fill=C_GREEN, font=f_sec)
    draw.rectangle([m + 375, curr_y - 4, m + 470, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 387, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 485, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 30

    sys_w = (w - 2 * m - 2 * gap) // 3
    sys_h = 160

    # Local PC
    s1 = m
    draw_card_frame(draw, s1, curr_y, sys_w, sys_h, "LOCAL WORKSTATION", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((s1 + 14, curr_y + 40), "GPU LOAD", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s1 + sys_w - 60, curr_y + 36), "3%", fill=C_GREEN, font=f_hero)
    draw_segmented_bar(draw, s1 + 14, curr_y + 64, sys_w - 28, 8, 3, C_GREEN, segments=16)
    draw.text((s1 + 14, curr_y + 80), "SYSTEM RAM", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s1 + sys_w - 60, curr_y + 78), "44%", fill=C_BLUE, font=f_sec_metric)
    draw_segmented_bar(draw, s1 + 14, curr_y + 98, sys_w - 28, 6, 44, C_BLUE, segments=16)
    draw.text((s1 + 14, curr_y + sys_h - 20), "RTX 5080 · 16GB VRAM · 16 CORES ACTIVE", fill=C_TEXT_DIM, font=f_meta)

    # DGX Spark
    s2 = m + sys_w + gap
    draw_card_frame(draw, s2, curr_y, sys_w, sys_h, "NVIDIA DGX SPARK CLUSTER", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((s2 + 14, curr_y + 40), "CLUSTER GPU LOAD", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s2 + sys_w - 60, curr_y + 36), "0%", fill=C_GREEN, font=f_hero)
    draw_segmented_bar(draw, s2 + 14, curr_y + 64, sys_w - 28, 8, 0, C_GREEN, segments=16)
    draw.text((s2 + 14, curr_y + 80), "TEMP 39°C  LOAD AVG 1.72  RAM 40%", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s2 + 14, curr_y + sys_h - 20), "ssh://dgx-spark · GB10 ARCHITECTURE", fill=C_TEXT_DIM, font=f_meta)

    # Services
    s3 = m + 2 * (sys_w + gap)
    draw_card_frame(draw, s3, curr_y, sys_w, sys_h, "CORE SYSTEM DAEMONS", C_GREEN, "HEALTHY", C_GREEN)
    svcs = [("DGX CLUSTER (SSH)", True), ("OLLAMA SERVER", True), ("COMFYUI DAEMON", True), ("FORGE3D SERVICE", True)]
    for s_idx, (s_name, s_up) in enumerate(svcs):
        sy = curr_y + 42 + s_idx * 24
        draw.ellipse([s3 + 14, sy + 3, s3 + 22, sy + 11], fill=C_GREEN if s_up else C_RED)
        draw.text((s3 + 28, sy), s_name, fill=C_TEXT_WHITE, font=f_meta)
        draw.text((s3 + sys_w - 45, sy), "OK" if s_up else "DOWN", fill=C_GREEN if s_up else C_RED, font=f_btn)
    draw.text((s3 + 14, curr_y + sys_h - 20), "TAILSCALE WORKSTATION MESH", fill=C_TEXT_DIM, font=f_meta)

    # Footer Bar
    draw.line([0, h - 36, w, h - 36], fill=(21, 29, 42), width=1)
    draw.text((20, h - 24), "TARGET: [ MINITOO ]  |  ACTIVE PAGE: [ BTC ]  |  AUTO-CYCLE: ON", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((w - 20, h - 24), "HIGH-DPI SCALE: AUTO (100%)  |  Ctrl+, Settings  |  1..5 Presets  |  F11 Fullscreen  |  Esc Exit", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")

# ---------------------------------------------------------------------------
# 2. 1920x1080 FOCUS PRESENTATION SCREENSHOTS
# ---------------------------------------------------------------------------
def render_preset_crypto_screenshot(out_path: str):
    """Renders 1080p CRYPTO hero focus mode with giant sparklines and high visual hierarchy."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="CRYPTO")

    f_huge_price = get_font(30, bold=True)
    f_sec_metric = get_font(16, bold=True)
    f_title = get_font(15, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    # Focus Banner
    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_ACTIVE_CYAN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_ACTIVE_CYAN, font=get_font(11, bold=True))
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: CRYPTO MARKETS · REALTIME SPOT ASSETS", fill=C_GOLD, font=get_font(13, bold=True))
    draw.text((w - m - 20, curr_y + 16), "FILMING & CREATOR MODE · 1080p COMMAND CENTER", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 62
    gap = 16

    # Top Row: 3 Major Assets (BTC, ETH, SOL)
    top_w = (w - 2 * m - 2 * gap) // 3
    top_h = 420
    top_coins = [
        ("₿ BITCOIN (BTC)", "$84,021.50", "-0.9%", C_GOLD, C_RED, [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95], True, "$85,208", "$83,230", "ON MINITOO"),
        ("Ξ ETHEREUM (ETH)", "$2,691.40", "-0.2%", C_ETH, C_RED, [0.8, 0.72, 0.75, 0.62, 0.65, 0.55, 0.58, 0.48, 0.52, 0.42, 0.45, 0.35, 0.38, 0.28, 0.30, 0.22], False, "$2,740", "$2,667", "SPOT 24H"),
        ("◎ SOLANA (SOL)", "$122.06", "+3.3%", C_SOLANA, C_GREEN, [0.3, 0.35, 0.32, 0.45, 0.48, 0.58, 0.55, 0.68, 0.72, 0.82, 0.78, 0.88, 0.85, 0.94, 0.91, 0.97], False, "$122.75", "$115.92", "SPOT 24H"),
    ]

    for idx, (title, price, chg, col, chg_col, pts, is_act, hi, lo, tag) in enumerate(top_coins):
        cx = m + idx * (top_w + gap)
        draw.rectangle([cx, curr_y, cx + top_w, curr_y + top_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN if is_act else C_CARD_BORDER, width=2 if is_act else 1)
        draw.text((cx + 18, curr_y + 18), title, fill=col, font=f_title)

        draw.rectangle([cx + top_w - 105, curr_y + 14, cx + top_w - 14, curr_y + 36], fill=C_ACTIVE_TAG_BG if is_act else (22, 29, 43), outline=C_ACTIVE_CYAN if is_act else (37, 50, 73))
        draw.text((cx + top_w - 95, curr_y + 18), tag, fill=C_ACTIVE_CYAN if is_act else C_TEXT_MUTED, font=get_font(10, bold=True))

        draw.text((cx + 18, curr_y + 58), price, fill=col, font=f_huge_price)
        draw.text((cx + top_w - 90, curr_y + 68), chg, fill=chg_col, font=f_sec_metric)

        # Giant 180px Sparkline
        sp_x1 = cx + 18
        sp_x2 = cx + top_w - 18
        sp_y1 = curr_y + 115
        sp_y2 = curr_y + top_h - 55
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=3)
        draw.ellipse([sp_pts[-1][0] - 4, sp_pts[-1][1] - 4, sp_pts[-1][0] + 4, sp_pts[-1][1] + 4], fill=col)

        draw.text((cx + 18, curr_y + top_h - 26), f"24H HIGH: {hi}   LOW: {lo}", fill=C_TEXT_DIM, font=f_meta)
        draw.text((cx + top_w - 18, curr_y + top_h - 26), "COINGECKO SPOT", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += top_h + gap

    # Bottom Row: 2 Alt/Meme Assets (DOGE, PEPE)
    bot_w = (w - 2 * m - gap) // 2
    bot_h = 420
    bot_coins = [
        ("Ð DOGECOIN (DOGE)", "$0.09892", "+2.7%", C_DOGE, C_GREEN, [0.4, 0.42, 0.38, 0.50, 0.52, 0.60, 0.58, 0.68, 0.65, 0.75, 0.72, 0.82, 0.80, 0.88, 0.85, 0.91], "$0.09971", "$0.09460", "VOL: 1.2B DOGE"),
        ("🐸 PEPE (PEPE)", "$0.00000452", "+0.7%", C_PEPE, C_GREEN, [0.5, 0.48, 0.52, 0.55, 0.53, 0.62, 0.60, 0.68, 0.65, 0.72, 0.70, 0.76, 0.74, 0.79, 0.77, 0.82], "$0.00000468", "$0.00000438", "VOL: 8.4T PEPE"),
    ]

    for idx, (title, price, chg, col, chg_col, pts, hi, lo, vol) in enumerate(bot_coins):
        cx = m + idx * (bot_w + gap)
        draw.rectangle([cx, curr_y, cx + bot_w, curr_y + bot_h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        draw.text((cx + 18, curr_y + 18), title, fill=col, font=f_title)
        draw.text((cx + 18, curr_y + 58), price, fill=col, font=f_huge_price)
        draw.text((cx + bot_w - 90, curr_y + 68), chg, fill=chg_col, font=f_sec_metric)

        sp_x1 = cx + 18
        sp_x2 = cx + bot_w - 18
        sp_y1 = curr_y + 115
        sp_y2 = curr_y + bot_h - 55
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=3)
        draw.ellipse([sp_pts[-1][0] - 4, sp_pts[-1][1] - 4, sp_pts[-1][0] + 4, sp_pts[-1][1] + 4], fill=col)

        draw.text((cx + 18, curr_y + bot_h - 26), f"24H HIGH: {hi}   LOW: {lo}   |   {vol}", fill=C_TEXT_DIM, font=f_meta)
        draw.text((cx + bot_w - 18, curr_y + bot_h - 26), "BINANCE API SPOT FEED", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")

def render_preset_stocks_screenshot(out_path: str):
    """Renders 1080p STOCKS hero preset scanner terminal."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="STOCKS")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_sec_metric = get_font(14, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_ACTIVE_CYAN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: TOP 10 VOLATILE US STOCKS SCANNER", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "OBJECTIVE INTRADAY HIGH-LOW RANGE RANKING · YAHOO CRUMB API", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 62
    stocks_w = w - 2 * m
    stocks_h = 880

    draw.rectangle([m, curr_y, m + stocks_w, curr_y + stocks_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN, width=2)

    # Table Header
    hy = curr_y + 24
    draw.text((m + 30, hy), "RANK", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 110, hy), "TICKER", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 230, hy), "COMPANY NAME", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 530, hy), "LAST PRICE", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 720, hy), "DAY CHANGE", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 920, hy), "INTRADAY RANGE (HIGH - LOW)", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + 1320, hy), "VOLATILITY METER", fill=C_TEXT_DIM, font=f_meta)
    draw.text((m + stocks_w - 180, hy), "INTRADAY VOLATILITY", fill=C_TEXT_DIM, font=f_meta)

    draw.line([m + 20, hy + 28, m + stocks_w - 20, hy + 28], fill=(28, 38, 56), width=1)

    stocks_data = [
        ("1", "DKNG", "DraftKings Inc", "$22.02", "+3.5%", "$20.30 - $22.15", 8.3),
        ("2", "GME", "GameStop Corp", "$23.39", "-6.5%", "$22.80 - $24.70", 7.6),
        ("3", "MARA", "MARA Holdings", "$12.55", "-2.9%", "$12.10 - $12.90", 6.4),
        ("4", "RIOT", "Riot Platforms", "$23.00", "-2.0%", "$22.40 - $23.70", 5.7),
        ("5", "TSLA", "Tesla Inc", "$372.11", "-1.5%", "$364.50 - $383.20", 5.1),
        ("6", "ARM", "Arm Holdings", "$310.32", "+1.3%", "$302.10 - $317.50", 5.0),
        ("7", "SMCI", "Super Micro Computer", "$43.26", "+4.2%", "$41.50 - $43.40", 4.5),
        ("8", "MSFT", "Microsoft Corp", "$516.17", "+3.7%", "$505.00 - $527.10", 4.4),
        ("9", "MSTR", "MicroStrategy Inc", "$158.61", "-1.9%", "$153.20 - $159.00", 3.7),
        ("10", "COIN", "Coinbase Global", "$195.11", "-2.1%", "$191.00 - $198.00", 3.6),
    ]

    for idx, (rk, sym, name, pr, chg, rng, vol) in enumerate(stocks_data):
        ry = hy + 45 + idx * 72
        row_bg = (19, 27, 42) if idx % 2 == 0 else (14, 19, 30)
        draw.rectangle([m + 16, ry - 10, m + stocks_w - 16, ry + 50], fill=row_bg, outline=(24, 34, 52), width=1)

        draw.text((m + 35, ry + 12), f"#{rk}", fill=C_TEXT_DIM, font=f_sec_metric)
        draw.text((m + 110, ry + 10), sym, fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))
        draw.text((m + 230, ry + 12), name, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((m + 530, ry + 10), pr, fill=C_TEXT_WHITE, font=get_font(16, bold=True))
        draw.text((m + 720, ry + 10), chg, fill=C_GREEN if "+" in chg else C_RED, font=get_font(16, bold=True))
        draw.text((m + 920, ry + 12), rng, fill=C_TEXT_MUTED, font=f_meta)

        # Range bar
        bar_w = 260
        meter_x = m + 1320
        meter_pct = min(100.0, (vol / 10.0) * 100.0)
        draw_segmented_bar(draw, meter_x, ry + 15, bar_w, 12, meter_pct, C_ACTIVE_CYAN, segments=18)

        draw.text((m + stocks_w - 170, ry + 10), f"VOL {vol:.1f}%", fill=C_ACTIVE_CYAN, font=get_font(16, bold=True))

    draw.text((m + 30, curr_y + stocks_h - 25), "METRIC FORMULA: Intraday Range % = (High - Low) / PrevClose · Yahoo Finance Authenticated Crumb API (60s Cadence)", fill=C_TEXT_DIM, font=f_meta)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")

def render_preset_ai_screenshot(out_path: str):
    """Renders 1080p AI hero focus mode with giant gauges and local agent activity."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="AI")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_huge = get_font(28, bold=True)
    f_sec_metric = get_font(15, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_ACTIVE_CYAN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: AI SUBSCRIPTION QUOTAS & AGENT RUNTIME", fill=C_CORAL, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "AUTHORITATIVE % LEFT QUOTAS · ZERO GUESSTIMATION", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 62
    gap = 16

    # 3 Giant Cards for OpenAI Codex, Google Gemini, Anthropic Claude
    card_w = (w - 2 * m - 2 * gap) // 3
    card_h = 520

    ai_focus_data = [
        ("CODEX CLI (OPENAI)", C_GREEN, "READY", C_GREEN, "5H ROLLING LIMIT", "100% LEFT", 100, "RESET: 5H 00M", "WEEKLY CAP", "29% LEFT", 29, "RESET: 1D 22H", "GPT-5.6 · CHATGPT PLUS SUBSCRIPTION"),
        ("GEMINI CODE ASSIST (GOOGLE)", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING LIMIT", "73% LEFT", 73, "RESET: 4H 16M", "WEEKLY CAP", "76% LEFT", 76, "RESET: 6D 01H", "GEMINI 3.8 · GOOGLE AI PRO WORKSPACE"),
        ("CLAUDE PRO (ANTHROPIC)", C_CORAL, "STALE", C_AMBER, "5H ROLLING LIMIT", "97% LEFT", 97, "RESET: NOW (CACHED)", "WEEKLY CAP", "62% LEFT", 62, "RESET: NOW (CACHED)", "no***@gmail.com · ANTHROPIC PRO"),
    ]

    for idx, (title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot) in enumerate(ai_focus_data):
        ax = m + idx * (card_w + gap)
        draw.rectangle([ax, curr_y, ax + card_w, curr_y + card_h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        draw.text((ax + 20, curr_y + 20), title, fill=col, font=f_title)

        draw.rectangle([ax + card_w - 95, curr_y + 16, ax + card_w - 18, curr_y + 38], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.text((ax + card_w - 85, curr_y + 20), bd, fill=bd_col, font=f_btn)

        # Primary Gauge
        draw.text((ax + 20, curr_y + 75), p_lbl, fill=C_TEXT_MUTED, font=f_sec_metric)
        draw.text((ax + card_w - 180, curr_y + 68), p_val, fill=col, font=f_huge)
        draw_segmented_bar(draw, ax + 20, curr_y + 120, card_w - 40, 16, p_pct, col, segments=20)
        draw.text((ax + 20, curr_y + 148), p_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.line([ax + 20, curr_y + 195, ax + card_w - 20, curr_y + 195], fill=(24, 32, 48), width=1)

        # Secondary Gauge
        draw.text((ax + 20, curr_y + 225), s_lbl, fill=C_TEXT_MUTED, font=f_sec_metric)
        draw.text((ax + card_w - 160, curr_y + 218), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=f_huge)
        draw_segmented_bar(draw, ax + 20, curr_y + 270, card_w - 40, 14, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=20)
        draw.text((ax + 20, curr_y + 298), s_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.line([ax + 20, curr_y + 345, ax + card_w - 20, curr_y + 345], fill=(24, 32, 48), width=1)

        # Telemetry & Diagnostics
        draw.text((ax + 20, curr_y + 375), "DIAGNOSTIC TELEMETRY:", fill=C_TEXT_DIM, font=f_meta)
        draw.text((ax + 20, curr_y + 400), "• Poller: High-Frequency Local Daemon", fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + 20, curr_y + 424), "• State: Authenticated Session Cached", fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + 20, curr_y + 448), "• MiniToo Page: Linked to Physical Display", fill=C_ACTIVE_CYAN, font=f_meta)

        draw.text((ax + 20, curr_y + card_h - 26), foot, fill=C_TEXT_MUTED, font=f_meta)

    curr_y += card_h + gap

    # Agent Activity Box below
    act_w = w - 2 * m
    act_h = 320
    draw.rectangle([m, curr_y, m + act_w, curr_y + act_h], fill=C_CARD_BG, outline=C_PURPLE, width=2)
    draw.text((m + 20, curr_y + 20), "LOCAL AGENT ACTIVITY DAEMON (ACTIVE REPOSITORIES & PROCESS MONITOR)", fill=C_PURPLE, font=f_title)
    draw.line([m + 20, curr_y + 55, m + act_w - 20, curr_y + 55], fill=(28, 38, 56), width=1)

    agents = [
        ("CODEX CLI DAEMON", "WORKING", C_GREEN, "Active 6h 52m · 24 tasks completed today · Subprocess PID 1492 (Silent execution)", "Repository: claude-minitoo · Branch: main"),
        ("ANTHROPIC CLAUDE PRO", "IDLE", C_TEXT_DIM, "Last prompt evaluated 42m ago · Web session active · No pending queued turns", "Diagnostics: no***@gmail.com (PRO)"),
        ("GEMINI CODE ENGINE", "WORKING", C_GREEN, "Active 5h 45m · Background indexing sparkline tensors & repo embeddings", "Target: Desktop Command Center UI"),
    ]

    for idx, (aname, astat, acol, adetail, arepo) in enumerate(agents):
        ay = curr_y + 75 + idx * 75
        draw.ellipse([m + 25, ay + 12, m + 37, ay + 24], fill=acol)
        draw.text((m + 50, ay + 8), aname, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((m + 320, ay + 8), astat, fill=acol, font=f_btn)
        draw.text((m + 420, ay + 10), adetail, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((m + act_w - 380, ay + 10), arepo, fill=C_ACTIVE_CYAN, font=f_meta)
        draw.line([m + 25, ay + 48, m + act_w - 25, ay + 48], fill=(20, 28, 42), width=1)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")

def render_preset_system_screenshot(out_path: str):
    """Renders 1080p SYSTEM hero preset."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="SYSTEM")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_huge = get_font(28, bold=True)
    f_sec_metric = get_font(15, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_ACTIVE_CYAN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: WORKSTATION HARDWARE, DGX SPARK, AND CLUSTER DAEMONS", fill=C_GREEN, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "REALTIME HARDWARE TELEMETRY · 1080p COMMAND CENTER", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 62
    gap = 16
    card_w = (w - 2 * m - gap) // 2
    card_h = 420

    # 1. Local PC
    draw.rectangle([m, curr_y, m + card_w, curr_y + card_h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
    draw.text((m + 20, curr_y + 20), "LOCAL WORKSTATION HARDWARE (RTX 5080)", fill=(55, 195, 245), font=f_title)
    draw.text((m + 20, curr_y + 70), "GPU LOAD (RTX 5080)", fill=C_TEXT_MUTED, font=f_sec_metric)
    draw.text((m + card_w - 120, curr_y + 65), "3%", fill=C_GREEN, font=f_huge)
    draw_segmented_bar(draw, m + 20, curr_y + 115, card_w - 40, 16, 3, C_GREEN, segments=20)
    draw.text((m + 20, curr_y + 145), "TEMP: 38°C   VRAM USAGE: 3.0 GB / 16.0 GB   FAN: 32%", fill=C_TEXT_DIM, font=f_meta)

    draw.line([m + 20, curr_y + 190, m + card_w - 20, curr_y + 190], fill=(24, 32, 48), width=1)

    draw.text((m + 20, curr_y + 215), "SYSTEM RAM (DDR5)", fill=C_TEXT_MUTED, font=f_sec_metric)
    draw.text((m + card_w - 140, curr_y + 210), "44%", fill=C_BLUE, font=f_huge)
    draw_segmented_bar(draw, m + 20, curr_y + 260, card_w - 40, 14, 44, C_BLUE, segments=20)
    draw.text((m + 20, curr_y + 290), "USED: 28.1 GB / 64.0 GB   COMMITTED: 34.2 GB", fill=C_TEXT_DIM, font=f_meta)

    draw.text((m + 20, curr_y + card_h - 26), "WINDOWS 11 PRO WORKSTATION · AMD RYZEN 9 7950X", fill=C_TEXT_DIM, font=f_meta)

    # 2. DGX Spark Cluster
    dx = m + card_w + gap
    draw.rectangle([dx, curr_y, dx + card_w, curr_y + card_h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
    draw.text((dx + 20, curr_y + 20), "NVIDIA DGX SPARK · REMOTE ACCELERATOR", fill=C_NVIDIA, font=f_title)
    draw.text((dx + 20, curr_y + 70), "CLUSTER GPU LOAD", fill=C_TEXT_MUTED, font=f_sec_metric)
    draw.text((dx + card_w - 120, curr_y + 65), "0%", fill=C_GREEN, font=f_huge)
    draw_segmented_bar(draw, dx + 20, curr_y + 115, card_w - 40, 16, 0, C_GREEN, segments=20)
    draw.text((dx + 20, curr_y + 145), "TEMP: 39°C   LOAD AVERAGE: 1.72, 1.48, 1.55", fill=C_TEXT_DIM, font=f_meta)

    draw.line([dx + 20, curr_y + 190, dx + card_w - 20, curr_y + 190], fill=(24, 32, 48), width=1)

    draw.text((dx + 20, curr_y + 215), "CLUSTER RAM (UNIFIED)", fill=C_TEXT_MUTED, font=f_sec_metric)
    draw.text((dx + card_w - 140, curr_y + 210), "40%", fill=C_NVIDIA, font=f_huge)
    draw_segmented_bar(draw, dx + 20, curr_y + 260, card_w - 40, 14, 40, C_NVIDIA, segments=20)
    draw.text((dx + 20, curr_y + 290), "USED: 51.2 GB / 128.0 GB   NVLINK HEALTH: OK", fill=C_TEXT_DIM, font=f_meta)

    draw.text((dx + 20, curr_y + card_h - 26), "ssh://dgx-spark · NVIDIA BLACKWELL GB10 CLUSTER", fill=C_TEXT_DIM, font=f_meta)

    curr_y += card_h + gap

    # Services Box below
    srv_w = w - 2 * m
    srv_h = 420
    draw.rectangle([m, curr_y, m + srv_w, curr_y + srv_h], fill=C_CARD_BG, outline=C_GREEN, width=1)
    draw.text((m + 20, curr_y + 20), "CORE SYSTEM DAEMONS & TAILSCALE WORKSTATION HEALTH", fill=C_GREEN, font=f_title)
    draw.line([m + 20, curr_y + 55, m + srv_w - 20, curr_y + 55], fill=(28, 38, 56), width=1)

    services_list = [
        ("DGX CLUSTER SSH DAEMON", "ONLINE", C_GREEN, "ssh://dgx-spark:22 · Keepalive Ping 24ms · Non-blocking healthcheck"),
        ("OLLAMA LLM RUNTIME", "ONLINE", C_GREEN, "http://localhost:11434 · Local deepseek-r1:8b loaded in GPU VRAM"),
        ("COMFYUI GENERATION SERVER", "ONLINE", C_GREEN, "http://127.0.0.1:8188 · SDXL Turbo Workflow Ready"),
        ("FORGE3D PIXEL SHADER SERVICE", "ONLINE", C_GREEN, "http://localhost:7860 · Nearest-Neighbor 160x128 Streamer"),
        ("TAILSCALE WORKSTATION MESH", "HEALTHY", C_GREEN, "100.x.y.z · 10 nodes interconnected securely (Tailscale Mesh)"),
    ]

    for idx, (sname, sstat, scol, sdesc) in enumerate(services_list):
        sy = curr_y + 75 + idx * 65
        draw.ellipse([m + 25, sy + 10, m + 37, sy + 22], fill=scol)
        draw.text((m + 50, sy + 6), sname, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((m + 420, sy + 8), sdesc, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((m + srv_w - 120, sy + 6), sstat, fill=scol, font=f_btn)
        draw.line([m + 25, sy + 44, m + srv_w - 25, sy + 44], fill=(20, 28, 42), width=1)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")

# ---------------------------------------------------------------------------
# 3. 9:16 VERTICAL CREATOR CAPTURE SCREENSHOTS (Shorts / OBS Filming)
# ---------------------------------------------------------------------------
def render_creator_crypto_vertical_screenshot(out_path: str):
    """Renders 1080x1920 9:16 vertical Shorts capture view for Crypto (BTC, ETH, SOL, DOGE, PEPE)."""
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_huge_price = get_font(38, bold=True)
    f_sec_metric = get_font(20, bold=True)
    f_title = get_font(18, bold=True)
    f_meta = get_font(13, bold=False)

    # Clean Creator Top Bar
    draw.rectangle([0, 0, w, 84], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.rectangle([24, 18, 240, 64], fill=(43, 20, 20), outline=C_RED, width=1)
    draw.text((45, 30), "✕ EXIT CREATOR (Esc)", fill=C_RED, font=get_font(14, bold=True))

    draw.text((270, 32), "CAPTURE RATIO:", fill=C_TEXT_DIM, font=f_meta)
    draw.rectangle([385, 20, 480, 62], fill=(16, 22, 34), outline=(28, 37, 54))
    draw.text((410, 32), "16:9", fill=C_TEXT_MUTED, font=get_font(13, bold=True))

    draw.rectangle([495, 20, 645, 62], fill=(11, 56, 74), outline=C_ACTIVE_CYAN, width=2)
    draw.text((515, 32), "9:16 SHORTS", fill=C_ACTIVE_CYAN, font=get_font(13, bold=True))

    draw.text((w - 280, 32), "PRESET: [ CRYPTO ]", fill=C_GOLD, font=get_font(15, bold=True))

    draw.line([0, 84, w, 84], fill=(28, 37, 54), width=1)

    # 5 Vertically Stacked Hero Cards
    curr_y = 110
    card_w = w - 60
    card_h = 330
    gap = 24
    m = 30

    coins_data = [
        ("₿ BITCOIN (BTC)", "$84,021.50", "-0.9%", C_GOLD, C_RED, [0.2, 0.28, 0.24, 0.42, 0.38, 0.52, 0.48, 0.65, 0.58, 0.72, 0.68, 0.85, 0.78, 0.92, 0.88, 0.95], True, "$85,208", "$83,230"),
        ("Ξ ETHEREUM (ETH)", "$2,691.40", "-0.2%", C_ETH, C_RED, [0.8, 0.72, 0.75, 0.62, 0.65, 0.55, 0.58, 0.48, 0.52, 0.42, 0.45, 0.35, 0.38, 0.28, 0.30, 0.22], False, "$2,740", "$2,667"),
        ("◎ SOLANA (SOL)", "$122.06", "+3.3%", C_SOLANA, C_GREEN, [0.3, 0.35, 0.32, 0.45, 0.48, 0.58, 0.55, 0.68, 0.72, 0.82, 0.78, 0.88, 0.85, 0.94, 0.91, 0.97], False, "$122.75", "$115.92"),
        ("Ð DOGECOIN (DOGE)", "$0.09892", "+2.7%", C_DOGE, C_GREEN, [0.4, 0.42, 0.38, 0.50, 0.52, 0.60, 0.58, 0.68, 0.65, 0.75, 0.72, 0.82, 0.80, 0.88, 0.85, 0.91], False, "$0.09971", "$0.09460"),
        ("🐸 PEPE (PEPE)", "$0.00000452", "+0.7%", C_PEPE, C_GREEN, [0.5, 0.48, 0.52, 0.55, 0.53, 0.62, 0.60, 0.68, 0.65, 0.72, 0.70, 0.76, 0.74, 0.79, 0.77, 0.82], False, "$0.00000468", "$0.00000438"),
    ]

    for idx, (title, price, chg, col, chg_col, pts, is_act, hi, lo) in enumerate(coins_data):
        draw.rectangle([m, curr_y, m + card_w, curr_y + card_h], fill=C_CARD_BG, outline=C_ACTIVE_CYAN if is_act else C_CARD_BORDER, width=2 if is_act else 1)
        draw.text((m + 24, curr_y + 20), title, fill=col, font=f_title)

        if is_act:
            draw.rectangle([m + card_w - 130, curr_y + 16, m + card_w - 20, curr_y + 44], fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
            draw.text((m + card_w - 118, curr_y + 22), "ON MINITOO", fill=C_ACTIVE_CYAN, font=get_font(12, bold=True))
        else:
            draw.rectangle([m + card_w - 110, curr_y + 16, m + card_w - 20, curr_y + 44], fill=(22, 29, 43), outline=(37, 50, 73))
            draw.text((m + card_w - 95, curr_y + 22), "SPOT 24H", fill=C_TEXT_MUTED, font=get_font(12, bold=True))

        draw.text((m + 24, curr_y + 60), price, fill=col, font=f_huge_price)
        draw.text((m + card_w - 120, curr_y + 72), chg, fill=chg_col, font=f_sec_metric)

        # High-res Sparkline
        sp_x1 = m + 24
        sp_x2 = m + card_w - 24
        sp_y1 = curr_y + 125
        sp_y2 = curr_y + card_h - 55
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=3)
        draw.ellipse([sp_pts[-1][0] - 5, sp_pts[-1][1] - 5, sp_pts[-1][0] + 5, sp_pts[-1][1] + 5], fill=col)

        draw.text((m + 24, curr_y + card_h - 30), f"24H HIGH: {hi}   LOW: {lo}", fill=C_TEXT_DIM, font=f_meta)
        draw.text((m + card_w - 24, curr_y + card_h - 30), "COINGECKO SPOT FEED", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

        curr_y += card_h + gap

    img.save(out_path, "PNG")
    print(f"Generated 9:16 Shorts: {out_path}")

def render_creator_ai_vertical_screenshot(out_path: str):
    """Renders 1080x1920 9:16 vertical Shorts capture view for AI (Codex, Gemini, Claude, Agent Activity)."""
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_huge = get_font(34, bold=True)
    f_sec_metric = get_font(20, bold=True)
    f_title = get_font(18, bold=True)
    f_meta = get_font(13, bold=False)

    # Top Bar
    draw.rectangle([0, 0, w, 84], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.rectangle([24, 18, 240, 64], fill=(43, 20, 20), outline=C_RED, width=1)
    draw.text((45, 30), "✕ EXIT CREATOR (Esc)", fill=C_RED, font=get_font(14, bold=True))

    draw.text((270, 32), "CAPTURE RATIO:", fill=C_TEXT_DIM, font=f_meta)
    draw.rectangle([385, 20, 480, 62], fill=(16, 22, 34), outline=(28, 37, 54))
    draw.text((410, 32), "16:9", fill=C_TEXT_MUTED, font=get_font(13, bold=True))

    draw.rectangle([495, 20, 645, 62], fill=(11, 56, 74), outline=C_ACTIVE_CYAN, width=2)
    draw.text((515, 32), "9:16 SHORTS", fill=C_ACTIVE_CYAN, font=get_font(13, bold=True))

    draw.text((w - 230, 32), "PRESET: [ AI ]", fill=C_CORAL, font=get_font(15, bold=True))

    draw.line([0, 84, w, 84], fill=(28, 37, 54), width=1)

    curr_y = 110
    card_w = w - 60
    card_h = 390
    gap = 26
    m = 30

    ai_data = [
        ("CODEX CLI (OPENAI)", C_GREEN, "READY", C_GREEN, "5H ROLLING LIMIT", "100% LEFT", 100, "RESET: 5H 00M", "WEEKLY CAP", "29% LEFT", 29, "RESET: 1D 22H", "GPT-5.6 · CHATGPT PLUS SUBSCRIPTION"),
        ("GEMINI CODE ASSIST (GOOGLE)", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING LIMIT", "73% LEFT", 73, "RESET: 4H 16M", "WEEKLY CAP", "76% LEFT", 76, "RESET: 6D 01H", "GEMINI 3.8 · GOOGLE AI PRO WORKSPACE"),
        ("CLAUDE PRO (ANTHROPIC)", C_CORAL, "ONLINE", C_GREEN, "5H ROLLING LIMIT", "97% LEFT", 97, "RESET: NOW (CACHED)", "WEEKLY CAP", "62% LEFT", 62, "RESET: NOW (CACHED)", "no***@gmail.com · ANTHROPIC PRO"),
    ]

    for idx, (title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot) in enumerate(ai_data):
        draw.rectangle([m, curr_y, m + card_w, curr_y + card_h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        draw.text((m + 24, curr_y + 20), title, fill=col, font=f_title)

        draw.rectangle([m + card_w - 110, curr_y + 16, m + card_w - 20, curr_y + 44], fill=(22, 29, 43), outline=(37, 50, 73))
        draw.text((m + card_w - 95, curr_y + 22), bd, fill=bd_col, font=get_font(12, bold=True))

        # Primary Gauge
        draw.text((m + 24, curr_y + 65), p_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((m + card_w - 180, curr_y + 55), p_val, fill=col, font=f_huge)
        draw_segmented_bar(draw, m + 24, curr_y + 105, card_w - 48, 14, p_pct, col, segments=20)
        draw.text((m + 24, curr_y + 128), p_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.line([m + 24, curr_y + 165, m + card_w - 24, curr_y + 165], fill=(24, 32, 48), width=1)

        # Secondary Gauge
        draw.text((m + 24, curr_y + 190), s_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((m + card_w - 170, curr_y + 180), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=f_huge)
        draw_segmented_bar(draw, m + 24, curr_y + 230, card_w - 48, 12, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=20)
        draw.text((m + 24, curr_y + 252), s_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.text((m + 24, curr_y + card_h - 30), foot, fill=C_TEXT_MUTED, font=f_meta)

        curr_y += card_h + gap

    # AI Activity Card
    act_h = 420
    draw.rectangle([m, curr_y, m + card_w, curr_y + act_h], fill=C_CARD_BG, outline=C_PURPLE, width=2)
    draw.text((m + 24, curr_y + 20), "LOCAL AGENT ACTIVITY DAEMON", fill=C_PURPLE, font=f_title)
    draw.line([m + 24, curr_y + 55, m + card_w - 24, curr_y + 55], fill=(28, 38, 56), width=1)

    agents = [
        ("CODEX CLI DAEMON", "WORKING", C_GREEN, "Active 6h 52m · Subprocess PID 1492"),
        ("ANTHROPIC CLAUDE PRO", "IDLE", C_TEXT_DIM, "Web session active · Ready for prompts"),
        ("GEMINI CODE ENGINE", "WORKING", C_GREEN, "Active 5h 45m · Indexing sparkline tensors"),
    ]
    for idx, (aname, astat, acol, adetail) in enumerate(agents):
        ay = curr_y + 80 + idx * 85
        draw.ellipse([m + 28, ay + 10, m + 42, ay + 24], fill=acol)
        draw.text((m + 56, ay + 6), aname, fill=C_TEXT_WHITE, font=f_sec_metric)
        draw.text((m + card_w - 140, ay + 6), astat, fill=acol, font=get_font(14, bold=True))
        draw.text((m + 56, ay + 38), adetail, fill=C_TEXT_MUTED, font=f_meta)

    img.save(out_path, "PNG")
    print(f"Generated 9:16 Shorts: {out_path}")

# ---------------------------------------------------------------------------
# 4. SETTINGS DIALOG HIGH-DPI SCREENSHOTS (900x660)
# ---------------------------------------------------------------------------
def render_settings_dashboard_screenshot(out_path: str):
    """Renders 900x660 High-DPI Settings dialog on DASHBOARD tab with UI Scale system."""
    w, h = 900, 660
    img = Image.new("RGBA", (w, h), (13, 17, 26))
    draw = ImageDraw.Draw(img)

    f_title = get_font(13, bold=True)
    f_tab = get_font(11, bold=True)
    f_bold = get_font(11, bold=True)
    f_sub = get_font(10, bold=False)
    f_btn = get_font(10, bold=True)

    # Dialog Title Bar
    draw.rectangle([0, 0, w, 44], fill=(10, 14, 22), outline=(24, 32, 48), width=1)
    draw.text((16, 12), "AI DESK DASHBOARD — CONFIGURATION & SETTINGS", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((w - 32, 12), "✕", fill=C_TEXT_MUTED, font=f_title)

    # Left Navigation Sidebar (5 Tabs)
    sidebar_w = 200
    draw.rectangle([0, 44, sidebar_w, h - 55], fill=(15, 20, 32), outline=(24, 34, 52), width=1)

    tabs = [
        ("GENERAL", False),
        ("DASHBOARD", True),
        ("MINITOO", False),
        ("INTEGRATIONS", False),
        ("ADVANCED", False),
    ]

    ty = 60
    for t_name, is_sel in tabs:
        if is_sel:
            draw.rectangle([0, ty, sidebar_w, ty + 42], fill=(19, 45, 62), outline=C_ACTIVE_CYAN, width=1)
            draw.text((22, ty + 12), f"▶  {t_name}", fill=C_ACTIVE_CYAN, font=f_tab)
        else:
            draw.rectangle([0, ty, sidebar_w, ty + 42], fill=(15, 20, 32), outline=(20, 26, 40))
            draw.text((22, ty + 12), f"   {t_name}", fill=C_TEXT_MUTED, font=f_tab)
        ty += 48

    # Right Content Area (DASHBOARD tab)
    rx = sidebar_w + 24
    rw = w - sidebar_w - 48
    cy = 60

    draw.text((rx, cy), "DASHBOARD SECTIONS & INDEPENDENT CARD VISIBILITY", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((rx, cy + 24), "Configure which cards appear on your desktop command center vs physical MiniToo display.", fill=C_TEXT_DIM, font=f_sub)
    draw.line([rx, cy + 46, rx + rw, cy + 46], fill=(26, 36, 54), width=1)

    # UI Scale Setting Box
    sy = cy + 58
    draw.rectangle([rx, sy, rx + rw, sy + 74], fill=(18, 24, 38), outline=C_ACTIVE_CYAN, width=1)
    draw.text((rx + 16, sy + 14), "DESKTOP UI SCALE & HIGH-DPI SYSTEM:", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.text((rx + 16, sy + 38), "Selected: AUTO (Per-Monitor-V2 DPI Awareness)", fill=C_TEXT_WHITE, font=f_sub)

    # Scale choices
    scale_x = rx + rw - 340
    for s_opt, s_act in [("AUTO", True), ("100%", False), ("125%", False), ("150%", False), ("200%", False)]:
        draw.rectangle([scale_x, sy + 22, scale_x + 58, sy + 52], fill=(11, 56, 74) if s_act else (14, 18, 28), outline=C_ACTIVE_CYAN if s_act else (32, 44, 68))
        draw.text((scale_x + 12, sy + 30), s_opt, fill=C_ACTIVE_CYAN if s_act else C_TEXT_MUTED, font=f_btn)
        scale_x += 66

    # Section Grid
    gy = sy + 90
    draw.text((rx, gy), "ACTIVE PRESET COMPOSITION:", fill=C_TEXT_WHITE, font=f_bold)
    gy += 28

    cards_table = [
        ("CRYPTO MARKETS", "Bitcoin (BTC)", True, True),
        ("CRYPTO MARKETS", "Ethereum (ETH)", True, True),
        ("CRYPTO MARKETS", "Solana (SOL)", True, True),
        ("CRYPTO MARKETS", "Dogecoin (DOGE)", True, False),
        ("CRYPTO MARKETS", "Pepe (PEPE)", True, False),
        ("AI SUBSCRIPTIONS", "Codex CLI (% LEFT)", True, True),
        ("AI SUBSCRIPTIONS", "Gemini Code Assist", True, True),
        ("AI SUBSCRIPTIONS", "Claude Pro Account", True, True),
        ("VOLATILE STOCKS", "Top 10 Stocks Scanner", True, False),
        ("LOCAL SYSTEM", "Workstation PC Hardware", True, True),
        ("LOCAL SYSTEM", "DGX Spark Cluster", True, True),
    ]

    draw.rectangle([rx, gy, rx + rw, gy + 320], fill=(16, 21, 34), outline=(30, 42, 64), width=1)
    # Header
    draw.text((rx + 18, gy + 10), "SECTION", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + 180, gy + 10), "CARD / METRIC ITEM", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + rw - 220, gy + 10), "DESKTOP APP", fill=C_TEXT_DIM, font=f_sub)
    draw.text((rx + rw - 90, gy + 10), "MINITOO", fill=C_TEXT_DIM, font=f_sub)
    draw.line([rx + 10, gy + 30, rx + rw - 10, gy + 30], fill=(26, 36, 54), width=1)

    for idx, (sec, item, d_on, m_on) in enumerate(cards_table[:9]):
        ry = gy + 36 + idx * 30
        row_bg = (19, 27, 42) if idx % 2 == 0 else (16, 21, 34)
        draw.rectangle([rx + 10, ry - 4, rx + rw - 10, ry + 24], fill=row_bg)

        draw.text((rx + 18, ry + 2), sec, fill=C_TEXT_MUTED, font=f_sub)
        draw.text((rx + 180, ry + 2), item, fill=C_TEXT_WHITE, font=f_sub)

        # Desktop checkbox
        draw.rectangle([rx + rw - 210, ry, rx + rw - 192, ry + 18], fill=(14, 38, 25) if d_on else (20, 26, 40), outline=C_GREEN if d_on else (40, 52, 75))
        if d_on:
            draw.text((rx + rw - 206, ry + 1), "✓", fill=C_GREEN, font=f_btn)

        # MiniToo checkbox
        draw.rectangle([rx + rw - 80, ry, rx + rw - 62, ry + 18], fill=(14, 38, 25) if m_on else (20, 26, 40), outline=C_GREEN if m_on else (40, 52, 75))
        if m_on:
            draw.text((rx + rw - 76, ry + 1), "✓", fill=C_GREEN, font=f_btn)

    # Dialog Footer Action Bar
    draw.rectangle([0, h - 55, w, h], fill=(10, 14, 22), outline=(24, 32, 48), width=1)
    draw.rectangle([w - 240, h - 45, w - 130, h - 12], fill=(22, 28, 42), outline=(38, 50, 72))
    draw.text((w - 205, h - 34), "CANCEL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([w - 120, h - 45, w - 18, h - 12], fill=(14, 56, 76), outline=C_ACTIVE_CYAN)
    draw.text((w - 95, h - 34), "SAVE CONFIG", fill=C_ACTIVE_CYAN, font=f_btn)

    img.save(out_path, "PNG")
    print(f"Generated High-DPI Settings: {out_path}")

def render_settings_minitoo_screenshot(out_path: str):
    """Renders 900x660 High-DPI Settings dialog on MINITOO tab with Bluetooth Low Interference mode."""
    w, h = 900, 660
    img = Image.new("RGBA", (w, h), (13, 17, 26))
    draw = ImageDraw.Draw(img)

    f_title = get_font(13, bold=True)
    f_tab = get_font(11, bold=True)
    f_bold = get_font(11, bold=True)
    f_sub = get_font(10, bold=False)
    f_btn = get_font(10, bold=True)

    # Dialog Title Bar
    draw.rectangle([0, 0, w, 44], fill=(10, 14, 22), outline=(24, 32, 48), width=1)
    draw.text((16, 12), "AI DESK DASHBOARD — CONFIGURATION & SETTINGS", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((w - 32, 12), "✕", fill=C_TEXT_MUTED, font=f_title)

    # Left Navigation Sidebar (5 Tabs)
    sidebar_w = 200
    draw.rectangle([0, 44, sidebar_w, h - 55], fill=(15, 20, 32), outline=(24, 34, 52), width=1)

    tabs = [
        ("GENERAL", False),
        ("DASHBOARD", False),
        ("MINITOO", True),
        ("INTEGRATIONS", False),
        ("ADVANCED", False),
    ]

    ty = 60
    for t_name, is_sel in tabs:
        if is_sel:
            draw.rectangle([0, ty, sidebar_w, ty + 42], fill=(19, 45, 62), outline=C_ACTIVE_CYAN, width=1)
            draw.text((22, ty + 12), f"▶  {t_name}", fill=C_ACTIVE_CYAN, font=f_tab)
        else:
            draw.rectangle([0, ty, sidebar_w, ty + 42], fill=(15, 20, 32), outline=(20, 26, 40))
            draw.text((22, ty + 12), f"   {t_name}", fill=C_TEXT_MUTED, font=f_tab)
        ty += 48

    # Right Content Area (MINITOO tab)
    rx = sidebar_w + 24
    rw = w - sidebar_w - 48
    cy = 60

    draw.text((rx, cy), "MINITOO BLUETOOTH COEXISTENCE & HARDWARE CONFIG", fill=C_ACTIVE_CYAN, font=f_title)
    draw.text((rx, cy + 24), "Configure SPP serial transport, audio coexistence, knob polling, and live telemetry.", fill=C_TEXT_DIM, font=f_sub)
    draw.line([rx, cy + 46, rx + rw, cy + 46], fill=(26, 36, 54), width=1)

    # 1. GROUP: BLUETOOTH COEXISTENCE
    gy = cy + 58
    draw.rectangle([rx, gy, rx + rw, gy + 105], fill=(18, 24, 38), outline=C_ACTIVE_CYAN, width=1)
    draw.text((rx + 16, gy + 12), "BLUETOOTH SERIAL SPP & AUDIO COEXISTENCE", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.line([rx + 12, gy + 32, rx + rw - 12, gy + 32], fill=(28, 38, 56), width=1)

    draw.text((rx + 18, gy + 45), "Connection:", fill=C_TEXT_MUTED, font=f_sub)
    draw.ellipse([rx + 115, gy + 49, rx + 123, gy + 57], fill=C_GREEN)
    draw.text((rx + 130, gy + 45), "CONNECTED  (Port: COM13 · Divoom Pixoo-Max / MiniToo SPP)", fill=C_GREEN, font=f_bold)

    draw.text((rx + 18, gy + 74), "Radio Mode:", fill=C_TEXT_MUTED, font=f_sub)
    draw.rectangle([rx + 115, gy + 66, rx + 205, gy + 94], fill=(18, 24, 36), outline=(38, 50, 72))
    draw.text((rx + 135, gy + 74), "NORMAL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([rx + 215, gy + 66, rx + 400, gy + 94], fill=(12, 52, 70), outline=C_ACTIVE_CYAN, width=2)
    draw.text((rx + 230, gy + 74), "● LOW INTERFERENCE", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((rx + 415, gy + 74), "(Prevents Bluetooth headphone stuttering)", fill=C_TEXT_DIM, font=f_sub)

    # 2. GROUP: DISPLAY & PHYSICAL CONTROLS
    gy2 = gy + 118
    draw.rectangle([rx, gy2, rx + rw, gy2 + 88], fill=(18, 24, 38), outline=(30, 42, 64))
    draw.text((rx + 16, gy2 + 12), "DISPLAY DWELL & PHYSICAL KNOB NAVIGATION", fill=C_TEXT_WHITE, font=f_bold)
    draw.line([rx + 12, gy2 + 32, rx + rw - 12, gy2 + 32], fill=(28, 38, 56), width=1)

    draw.text((rx + 18, gy2 + 45), "Auto Cycle:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 115, gy2 + 45), "[✓] Enabled", fill=C_GREEN, font=f_bold)
    draw.text((rx + 230, gy2 + 45), "Dwell Interval:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 330, gy2 + 45), "4 seconds / page", fill=C_ACTIVE_CYAN, font=f_bold)

    draw.text((rx + 18, gy2 + 68), "Knob Control:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 115, gy2 + 68), "[✓] Enabled", fill=C_GREEN, font=f_bold)
    draw.text((rx + 230, gy2 + 68), "Knob Poller Rate:", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((rx + 350, gy2 + 68), "AUTO (2.85 Hz in Low Interference)", fill=C_ACTIVE_CYAN, font=f_bold)

    # 3. GROUP: ROLLING TELEMETRY
    gy3 = gy2 + 102
    draw.rectangle([rx, gy3, rx + rw, gy3 + 140], fill=(16, 21, 34), outline=C_ACTIVE_CYAN, width=1)
    draw.text((rx + 16, gy3 + 12), "LIVE BLUETOOTH TRAFFIC TELEMETRY (ROLLING 60-SEC WINDOW)", fill=C_ACTIVE_CYAN, font=f_bold)
    draw.line([rx + 12, gy3 + 32, rx + rw - 12, gy3 + 32], fill=(28, 38, 56), width=1)

    c1_x = rx + 24
    c2_x = rx + rw // 3 + 10
    c3_x = rx + 2 * (rw // 3) + 10

    # Row 1
    draw.text((c1_x, gy3 + 45), "SPP Writes/min: 134", fill=C_TEXT_WHITE, font=f_sub)
    draw.text((c2_x, gy3 + 45), "SPP Reads/min: 136", fill=C_TEXT_WHITE, font=f_sub)
    draw.text((c3_x, gy3 + 45), "Frames/min: 2 (Low Load)", fill=C_GREEN, font=f_bold)

    # Row 2
    draw.text((c1_x, gy3 + 70), "Throughput: 1.89 KB/min", fill=C_GREEN, font=f_bold)
    draw.text((c2_x, gy3 + 70), "Total Sent: 42.6 KB (14f)", fill=C_TEXT_WHITE, font=f_sub)
    draw.text((c3_x, gy3 + 70), "Redundant Frames: 0 (Diff elided)", fill=C_ACTIVE_CYAN, font=f_bold)

    # Row 3
    draw.text((c1_x, gy3 + 95), "Knob Rate: 2.85 Hz (Relaxed)", fill=C_TEXT_MUTED, font=f_sub)
    draw.text((c2_x, gy3 + 95), "Channel Check: 1 / min", fill=C_GREEN, font=f_sub)
    draw.text((c3_x, gy3 + 95), "Errors / Reconnects: 0 / 0", fill=C_GREEN, font=f_bold)

    draw.text((rx + 18, gy3 + 120), "Diagnostic: 25.1% radio contention reduction on MediaTek RZ616 Bluetooth adapter.", fill=C_TEXT_DIM, font=f_sub)

    # Footer Action Bar
    draw.rectangle([0, h - 55, w, h], fill=(10, 14, 22), outline=(24, 32, 48), width=1)
    draw.rectangle([w - 240, h - 45, w - 130, h - 12], fill=(22, 28, 42), outline=(38, 50, 72))
    draw.text((w - 205, h - 34), "CANCEL", fill=C_TEXT_MUTED, font=f_btn)

    draw.rectangle([w - 120, h - 45, w - 18, h - 12], fill=(14, 56, 76), outline=C_ACTIVE_CYAN)
    draw.text((w - 95, h - 34), "SAVE CONFIG", fill=C_ACTIVE_CYAN, font=f_btn)

    img.save(out_path, "PNG")
    print(f"Generated High-DPI Settings: {out_path}")

# ---------------------------------------------------------------------------
# MAIN SCRIPT RUNNER
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("assets/screenshots", exist_ok=True)

    # 1. High-DPI 1080p (1920x1080) Dashboard Screenshots
    render_preset_all_screenshot("assets/screenshots/preset-all.png")
    render_preset_ai_screenshot("assets/screenshots/preset-ai.png")
    render_preset_crypto_screenshot("assets/screenshots/preset-crypto.png")
    render_preset_stocks_screenshot("assets/screenshots/preset-stocks.png")
    render_preset_system_screenshot("assets/screenshots/preset-system.png")

    # 2. Scaled High-DPI Settings Dialog Screenshots (900x660)
    render_settings_dashboard_screenshot("assets/screenshots/settings-dashboard.png")
    render_settings_minitoo_screenshot("assets/screenshots/settings-minitoo.png")

    # 3. 9:16 Vertical Creator Capture Screenshots (1080x1920)
    render_creator_crypto_vertical_screenshot("assets/screenshots/creator-crypto-vertical.png")
    render_creator_ai_vertical_screenshot("assets/screenshots/creator-ai-vertical.png")

    # 4. Legacy numbered screenshots updated to 1080p hero view
    render_preset_all_screenshot("assets/screenshots/01_desktop_overview.png")
    render_preset_all_screenshot("assets/screenshots/06_preset_all_dashboard.png")
    render_preset_ai_screenshot("assets/screenshots/08_preset_ai.png")

    print("\nAll Milestone 14 screenshots generated successfully!")
