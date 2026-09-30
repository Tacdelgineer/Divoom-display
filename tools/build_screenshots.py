#!/usr/bin/env python3
"""
Generate crisp, clean, high-resolution 1080p (1920x1080) and 9:16 Vertical Creator screenshots
for AI Desk Dashboard Milestone 15:
1. assets/screenshots/desktop-all-1080p.png (Command center hero: Crypto, AI, Stocks, Signals, System)
2. assets/screenshots/desktop-ai-1080p.png (AI hero preset: Codex, Gemini, Claude, Agent Activity)
3. assets/screenshots/desktop-crypto-1080p.png (CRYPTO hero preset: 5-asset layout with sparklines)
4. assets/screenshots/desktop-stocks-1080p.png (STOCKS hero preset: Top 10 US Equities by Market Cap 5x2 grid)
5. assets/screenshots/desktop-system-1080p.png (SYSTEM hero preset: Workstation, DGX Spark, Services)
6. assets/screenshots/desktop-signals-1080p.png (SIGNALS hero preset: Polymarket prediction odds & headlines)
7. assets/screenshots/creator-ai-vertical.png (1080x1920 9:16 vertical Shorts capture: AI quotas)
8. assets/screenshots/creator-crypto-vertical.png (1080x1920 9:16 vertical Shorts capture: Crypto assets)
9. assets/screenshots/creator-stocks-vertical.png (1080x1920 9:16 vertical Shorts capture: Top Equities)
10. assets/screenshots/device-setup.png (First-Run Device Onboarding Screen 1 Wizard)
11. assets/screenshots/settings-dashboard.png (High-DPI Settings UI: Dashboard Tab & UI Scale)
12. assets/screenshots/settings-device.png (Compact Device Status & Hardware Panel)

PRIVACY RULES STRICTLY ENFORCED:
- Zero real email addresses (use "CLAUDE PERSONAL")
- Zero Windows usernames
- Zero private IP addresses
- Zero tokens or machine-specific paths
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

# Theme Colors
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
C_EMERALD = (56, 239, 125)

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
    dev_x = 230
    draw.rectangle([dev_x, 16, dev_x + 130, 52], fill=(16, 24, 38), outline=C_ACTIVE_CYAN, width=1)
    draw.text((dev_x + 14, 25), "🖥 MiniToo ▼", fill=C_ACTIVE_CYAN, font=f_btn)

    # 3. Presets
    px = 380
    draw.text((px, 26), "PRESET:", fill=C_TEXT_DIM, font=f_meta)
    px += 65
    for p in ["ALL", "AI", "CRYPTO", "STOCKS", "SIGNALS", "SYSTEM"]:
        is_act = (p == active_preset)
        p_bg = (11, 56, 74) if is_act else (16, 22, 34)
        p_fg = C_ACTIVE_CYAN if is_act else C_TEXT_MUTED
        p_bd = C_ACTIVE_CYAN if is_act else (28, 37, 54)
        bw = 82 if p in ["CRYPTO", "STOCKS", "SIGNALS", "SYSTEM"] else 60
        draw.rectangle([px, 16, px + bw, 52], fill=p_bg, outline=p_bd, width=2 if is_act else 1)
        draw.text((px + bw // 2 - 18, 25), p, fill=p_fg, font=f_btn)
        px += bw + 8

    # 4. Right Controls
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

    # Status Pill
    pill_x2 = creat_x1 - 14
    pill_x1 = pill_x2 - 205
    draw.rectangle([pill_x1, 16, pill_x2, 52], fill=(13, 38, 27), outline=(27, 77, 54), width=1)
    draw.ellipse([pill_x1 + 12, 31, pill_x1 + 20, 39], fill=C_GREEN)
    draw.text((pill_x1 + 28, 26), "● MINITOO: CONNECTED", fill=C_GREEN, font=f_meta)

    draw.line([0, 68, w, 68], fill=(21, 29, 42), width=1)

def draw_stock_card_img(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, sym: str, name: str, pr: str, chg: str, chg_col: tuple, mcap: str, pts: list, state: str = "REG", src: str = "Yahoo · 1D"):
    draw.rectangle([x, y, x + w, y + h], fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)

    # Header: Symbol (cyan) and change % (green/red)
    draw.text((x + 14, y + 12), sym, fill=C_ACTIVE_CYAN, font=get_font(13, bold=True))
    chg_w = get_font(12, bold=True).getbbox(chg)[2]
    draw.text((x + w - 14 - chg_w, y + 12), chg, fill=chg_col, font=get_font(12, bold=True))

    # Subtitle: Name
    draw.text((x + 14, y + 28), name[:20], fill=C_TEXT_MUTED, font=get_font(9, bold=False))

    # Price and Market State badge
    draw.text((x + 14, y + 46), pr, fill=C_TEXT_WHITE, font=get_font(17, bold=True))
    draw.rectangle([x + w - 46, y + 46, x + w - 14, y + 62], fill=(16, 24, 38), outline=C_GREEN if state=="REG" else C_AMBER)
    draw.text((x + w - 41, y + 48), state, fill=C_GREEN if state=="REG" else C_AMBER, font=get_font(8, bold=True))

    # 1D Intraday Sparkline
    sp_x1 = x + 14
    sp_x2 = x + w - 14
    sp_y1 = y + 70
    sp_y2 = y + h - 26
    step = (sp_x2 - sp_x1) / max(1, len(pts) - 1)
    mn, mx = min(pts), max(pts)
    span = (mx - mn) if mx != mn else 1.0
    sp_pts = [(sp_x1 + i * step, sp_y2 - ((v - mn) / span) * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
    for i in range(len(sp_pts) - 1):
        draw.line([sp_pts[i], sp_pts[i+1]], fill=chg_col, width=2)
    draw.ellipse([sp_pts[-1][0] - 2, sp_pts[-1][1] - 2, sp_pts[-1][0] + 2, sp_pts[-1][1] + 2], fill=chg_col)

    # Footer
    draw.text((x + 14, y + h - 16), f"MARKET CAP  {mcap}", fill=C_AMBER, font=get_font(9, bold=True))
    src_w = get_font(9).getbbox(src)[2]
    draw.text((x + w - 14 - src_w, y + h - 16), src, fill=C_TEXT_DIM, font=get_font(9))

def draw_signal_card_img(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, question: str, cat: str, prob: str, delta: str, d_col: tuple, vol: str, liq: str, headlines: list):
    draw.rectangle([x, y, x + w, y + h], fill=C_CARD_BG, outline=(30, 48, 38), width=1)

    # Question
    draw.text((x + 14, y + 14), question[:42], fill=C_TEXT_WHITE, font=get_font(12, bold=True))

    # Probability (big cyan)
    prob_w = get_font(18, bold=True).getbbox(prob)[2]
    draw.text((x + w - 14 - prob_w, y + 14), prob, fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))

    # Category badge & Delta
    cat_w = get_font(8, bold=True).getbbox(cat)[2]
    draw.rectangle([x + 14, y + 34, x + 14 + cat_w + 10, y + 48], fill=(16, 38, 26), outline=(30, 80, 50))
    draw.text((x + 19, y + 36), cat, fill=(56, 239, 125), font=get_font(8, bold=True))
    del_w = get_font(11, bold=True).getbbox(delta)[2]
    draw.text((x + w - 14 - del_w, y + 36), delta, fill=d_col, font=get_font(11, bold=True))

    # Divider
    draw.line([x + 14, y + 54, x + w - 14, y + 54], fill=(22, 34, 28), width=1)

    # Meta
    draw.text((x + 14, y + 62), f"VOL: {vol}   LIQ: {liq}   Polymarket Odds", fill=C_TEXT_MUTED, font=get_font(9))

    # Related headlines
    draw.text((x + 14, y + 82), "Related Headlines & Market Context:", fill=(56, 239, 125), font=get_font(9, bold=True))
    hy = y + 100
    for hl, src, elapsed in headlines[:2]:
        draw.text((x + 14, hy), f"• {hl[:44]}", fill=C_TEXT_WHITE, font=get_font(9))
        s_txt = f"{src} · {elapsed}"
        s_w = get_font(9).getbbox(s_txt)[2]
        draw.text((x + w - 14 - s_w, hy), s_txt, fill=C_TEXT_DIM, font=get_font(9))
        hy += 18

    # Footer
    draw.text((x + 14, y + h - 14), "DISCLAIMER: Market-implied probability, not news fact", fill=C_TEXT_DIM, font=get_font(8))


# ---------------------------------------------------------------------------
# 1. 1920x1080 COMMAND CENTER SCREENSHOT (desktop-all-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_all_screenshot(out_path: str):
    """Renders 1080p full command center dashboard with all 5 responsive sections."""
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
    curr_y = 80
    gap = 12

    # 1. SECTION: CRYPTO MARKETS (5 cards fit across full 1920px screen in 1 row)
    draw.text((m, curr_y), "─── [ CRYPTO MARKETS ]", fill=C_GOLD, font=f_sec)
    draw.rectangle([m + 230, curr_y - 4, m + 325, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 242, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 340, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 28

    crypto_w = (w - 2 * m - 4 * gap) // 5
    crypto_h = 150
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
        draw.text((cx + 14, curr_y + 40), price, fill=col, font=f_hero)
        draw.text((cx + crypto_w - 75, curr_y + 44), chg, fill=chg_col, font=f_sec_metric)

        sp_x1 = cx + 14
        sp_x2 = cx + crypto_w - 14
        sp_y1 = curr_y + 68
        sp_y2 = curr_y + crypto_h - 26
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=2)
        draw.ellipse([sp_pts[-1][0] - 2, sp_pts[-1][1] - 2, sp_pts[-1][0] + 2, sp_pts[-1][1] + 2], fill=col)

        draw.text((cx + 14, curr_y + crypto_h - 16), "24H H $85.2K  L $83.2K", fill=C_TEXT_DIM, font=f_meta)
        draw.text((cx + crypto_w - 48, curr_y + crypto_h - 16), "SPOT", fill=C_TEXT_DIM, font=f_meta)

    curr_y += crypto_h + gap + 6

    # 2. SECTION: AI USAGE (3 spacious cards)
    draw.text((m, curr_y), "─── [ AI USAGE & SUBSCRIPTION QUOTAS ]", fill=C_CORAL, font=f_sec)
    draw.rectangle([m + 375, curr_y - 4, m + 470, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 387, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 485, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 28

    ai_w = (w - 2 * m - 2 * gap) // 3
    ai_h = 150
    ai_data = [
        ("CODEX CLI", C_GREEN, "READY", C_GREEN, "5H ROLLING", "100% LEFT", 100, "RESET: 5H 00M", "WEEKLY CAP", "29% LEFT", 29, "RESET: 1D 22H", "GPT-5.6 · CHATGPT PLUS TIER"),
        ("GEMINI CODE ASSIST", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING", "73% LEFT", 73, "RESET: 4H 16M", "WEEKLY CAP", "76% LEFT", 76, "RESET: 6D 01H", "GEMINI 3.8 · GOOGLE AI PRO"),
        ("CLAUDE PRO", C_CORAL, "ONLINE", C_GREEN, "5H ROLLING", "97% LEFT", 97, "RESET: NOW (CACHED)", "WEEKLY CAP", "62% LEFT", 62, "RESET: NOW (CACHED)", "CLAUDE PERSONAL · ANTHROPIC PRO"),
    ]

    for idx, (title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot) in enumerate(ai_data):
        ax = m + idx * (ai_w + gap)
        draw_card_frame(draw, ax, curr_y, ai_w, ai_h, title, col, bd, bd_col)

        draw.text((ax + 14, curr_y + 36), p_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 110, curr_y + 32), p_val, fill=col, font=get_font(16, bold=True))
        draw_segmented_bar(draw, ax + 14, curr_y + 56, ai_w - 28, 6, p_pct, col, segments=16)

        draw.text((ax + 14, curr_y + 82), s_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 90, curr_y + 80), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=f_sec_metric)
        draw_segmented_bar(draw, ax + 14, curr_y + 100, ai_w - 28, 5, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=16)

        draw.text((ax + 14, curr_y + ai_h - 16), foot, fill=C_TEXT_MUTED, font=f_meta)

    curr_y += ai_h + gap + 6

    # 3. SECTION: US EQUITIES (5 cards in 1 row in overview)
    draw.text((m, curr_y), "─── [ US EQUITIES ]", fill=C_ACTIVE_CYAN, font=f_sec)
    draw.rectangle([m + 195, curr_y - 4, m + 300, curr_y + 20], fill=(14, 53, 71), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 205, curr_y + 1), "[ MARKET CAP ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.rectangle([m + 308, curr_y - 4, m + 400, curr_y + 20], fill=(16, 22, 34), outline=(32, 46, 66), width=1)
    draw.text((m + 320, curr_y + 1), "[ VOLATILE ]", fill=C_TEXT_MUTED, font=f_btn)
    draw.rectangle([m + 412, curr_y - 4, m + 505, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 424, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 518, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 28

    stk_w = (w - 2 * m - 4 * gap) // 5
    stk_h = 145
    stocks_top = [
        ("NVDA", "NVIDIA Corporation", "$229.81", "+2.14%", C_GREEN, "$5.55T", [222, 224, 223, 225, 226, 225, 227, 228, 227, 229, 230]),
        ("AAPL", "Apple Inc.", "$254.23", "+0.85%", C_GREEN, "$3.82T", [251, 252, 252, 253, 253, 254, 253, 254, 254, 255, 254]),
        ("MSFT", "Microsoft Corp.", "$516.17", "-0.42%", C_RED, "$3.74T", [520, 519, 518, 519, 518, 517, 518, 517, 516, 516, 516]),
        ("AMZN", "Amazon.com Inc.", "$231.40", "+1.12%", C_GREEN, "$2.44T", [228, 229, 229, 230, 230, 231, 230, 231, 232, 231, 231]),
        ("GOOGL", "Alphabet Inc.", "$201.55", "-0.65%", C_RED, "$2.41T", [203, 203, 202, 202, 201, 202, 201, 201, 200, 201, 201]),
    ]

    for idx, (sym, name, pr, chg, chg_col, mcap, pts) in enumerate(stocks_top):
        sx = m + idx * (stk_w + gap)
        draw_stock_card_img(draw, sx, curr_y, stk_w, stk_h, sym, name, pr, chg, chg_col, mcap, pts)

    curr_y += stk_h + gap + 6

    # 4. SECTION: SIGNALS & PREDICTION MARKETS (3 columns across)
    draw.text((m, curr_y), "─── [ MARKET SIGNALS & PREDICTIONS ]", fill=C_EMERALD, font=f_sec)
    draw.rectangle([m + 375, curr_y - 4, m + 470, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 387, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 485, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 28

    sig_w = (w - 2 * m - 2 * gap) // 3
    sig_h = 160
    signals_data = [
        ("Fed Interest Rate Cut by Dec?", "FINANCE", "64%", "▲ +8.0 pts", C_GREEN, "$14.2M", "$2.8M", [
            ("Reuters: Fed Chair Powell signals easing cycle baseline...", "Reuters", "18m ago"),
            ("Bloomberg: Treasury yields steady following CPI print...", "Bloomberg", "42m ago")
        ]),
        ("Bitcoin Reaches $100K in 2026?", "CRYPTO", "71%", "▲ +5.2 pts", C_GREEN, "$28.5M", "$4.1M", [
            ("CoinDesk: ETF weekly net inflows surge to fresh high...", "CoinDesk", "24m ago"),
            ("CNBC: Digital asset market liquidity expands significantly...", "CNBC", "1h ago")
        ]),
        ("Next Frontier AI Model Release Q4?", "TECH / AI", "83%", "▲ +12.0 pts", C_GREEN, "$6.2M", "$1.5M", [
            ("TechCrunch: Anthropic / OpenAI speed up release schedules...", "TechCrunch", "31m ago"),
            ("TheVerge: Safety evaluation benchmarks completed...", "TheVerge", "2h ago")
        ]),
    ]

    for idx, (q, cat, prob, delta, d_col, vol, liq, hls) in enumerate(signals_data):
        sig_x = m + idx * (sig_w + gap)
        draw_signal_card_img(draw, sig_x, curr_y, sig_w, sig_h, q, cat, prob, delta, d_col, vol, liq, hls)

    curr_y += sig_h + gap + 6

    # 5. SECTION: SYSTEM & SERVICES
    draw.text((m, curr_y), "─── [ SYSTEM HARDWARE & SERVICES ]", fill=C_GREEN, font=f_sec)
    draw.rectangle([m + 350, curr_y - 4, m + 445, curr_y + 20], fill=(19, 27, 42), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 362, curr_y + 1), "[ 🔍 FOCUS ]", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.line([m + 460, curr_y + 8, w - m, curr_y + 8], fill=(24, 32, 48), width=1)
    curr_y += 28

    sys_w = (w - 2 * m - 2 * gap) // 3
    sys_h = 135

    s1 = m
    draw_card_frame(draw, s1, curr_y, sys_w, sys_h, "LOCAL WORKSTATION", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((s1 + 14, curr_y + 36), "GPU LOAD", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s1 + sys_w - 60, curr_y + 32), "3%", fill=C_GREEN, font=get_font(16, bold=True))
    draw_segmented_bar(draw, s1 + 14, curr_y + 56, sys_w - 28, 6, 3, C_GREEN, segments=16)
    draw.text((s1 + 14, curr_y + 76), "SYSTEM RAM: 44%  RTX 5080 16GB", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s1 + 14, curr_y + sys_h - 16), "WINDOWS 11 WORKSTATION · ACTIVE SESSION", fill=C_TEXT_DIM, font=f_meta)

    s2 = m + sys_w + gap
    draw_card_frame(draw, s2, curr_y, sys_w, sys_h, "NVIDIA DGX SPARK CLUSTER", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((s2 + 14, curr_y + 36), "CLUSTER GPU LOAD", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s2 + sys_w - 60, curr_y + 32), "0%", fill=C_GREEN, font=get_font(16, bold=True))
    draw_segmented_bar(draw, s2 + 14, curr_y + 56, sys_w - 28, 6, 0, C_GREEN, segments=16)
    draw.text((s2 + 14, curr_y + 76), "TEMP 39°C  LOAD AVG 1.72  RAM 40%", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((s2 + 14, curr_y + sys_h - 16), "dgx-spark · GB10 ARCHITECTURE", fill=C_TEXT_DIM, font=f_meta)

    s3 = m + 2 * (sys_w + gap)
    draw_card_frame(draw, s3, curr_y, sys_w, sys_h, "DEVELOPMENT SERVICES", C_GREEN, "HEALTHY", C_GREEN)
    services = [("OLLAMA DAEMON", True), ("DOCKER ENGINE", True), ("REDIS KV CACHE", True), ("POSTGRESQL DB", True)]
    for s_idx, (s_name, s_on) in enumerate(services):
        sy = curr_y + 36 + s_idx * 22
        draw.text((s3 + 14, sy), s_name, fill=C_TEXT_WHITE, font=f_meta)
        draw.ellipse([s3 + sys_w - 26, sy + 3, s3 + sys_w - 18, sy + 11], fill=C_GREEN)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 2. 1080p STOCKS HERO SCREENSHOT (desktop-stocks-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_stocks_screenshot(out_path: str):
    """Renders 1080p STOCKS hero preset: Top 10 US Equities by Market Cap 5x2 card grid."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="STOCKS")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    # Focus Header Banner
    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_ACTIVE_CYAN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_ACTIVE_CYAN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_ACTIVE_CYAN, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: TOP 10 US EQUITIES BY MARKET CAP", fill=C_ACTIVE_CYAN, font=f_title)

    # Mode Toggles in banner
    tx1 = w - m - 380
    draw.rectangle([tx1, curr_y + 10, tx1 + 115, curr_y + 38], fill=(14, 53, 71), outline=C_ACTIVE_CYAN, width=1)
    draw.text((tx1 + 10, curr_y + 16), "[ MARKET CAP ]", fill=C_ACTIVE_CYAN, font=f_btn)
    tx2 = tx1 + 125
    draw.rectangle([tx2, curr_y + 10, tx2 + 100, curr_y + 38], fill=(16, 22, 34), outline=(32, 46, 66), width=1)
    draw.text((tx2 + 12, curr_y + 16), "[ VOLATILE ]", fill=C_TEXT_MUTED, font=f_btn)

    curr_y += 68

    # 5 cards per row x 2 rows
    cols = 5
    rows = 2
    gap = 14
    card_w = (w - 2 * m - (cols - 1) * gap) // cols
    card_h = 410

    all_10_stocks = [
        ("NVDA", "NVIDIA Corporation", "$229.81", "+2.14%", C_GREEN, "$5.55T", [222, 223, 225, 224, 226, 227, 226, 228, 229, 228, 230]),
        ("AAPL", "Apple Inc.", "$254.23", "+0.85%", C_GREEN, "$3.82T", [251, 252, 252, 253, 253, 254, 253, 254, 254, 255, 254]),
        ("MSFT", "Microsoft Corp.", "$516.17", "-0.42%", C_RED, "$3.74T", [520, 519, 518, 519, 518, 517, 518, 517, 516, 516, 516]),
        ("AMZN", "Amazon.com Inc.", "$231.40", "+1.12%", C_GREEN, "$2.44T", [228, 229, 229, 230, 230, 231, 230, 231, 232, 231, 231]),
        ("GOOGL", "Alphabet Inc.", "$201.55", "-0.65%", C_RED, "$2.41T", [203, 203, 202, 202, 201, 202, 201, 201, 200, 201, 201]),
        ("META", "Meta Platforms Inc.", "$715.30", "+3.45%", C_GREEN, "$1.81T", [690, 695, 698, 702, 705, 708, 711, 712, 714, 715, 716]),
        ("TSLA", "Tesla Inc.", "$372.11", "-1.50%", C_RED, "$1.18T", [382, 380, 378, 376, 375, 374, 373, 372, 371, 372, 372]),
        ("BRK-B", "Berkshire Hathaway", "$492.80", "+0.32%", C_GREEN, "$1.08T", [490, 491, 491, 491, 492, 492, 492, 492, 493, 492, 493]),
        ("LLY", "Eli Lilly and Co.", "$895.40", "+1.78%", C_GREEN, "$850.2B", [878, 882, 885, 887, 889, 891, 892, 894, 895, 896, 895]),
        ("AVGO", "Broadcom Inc.", "$182.60", "+2.90%", C_GREEN, "$845.6B", [176, 177, 178, 179, 180, 181, 181, 182, 182, 183, 183]),
    ]

    for idx, (sym, name, pr, chg, chg_col, mcap, pts) in enumerate(all_10_stocks):
        col = idx % cols
        row = idx // cols
        cx = m + col * (card_w + gap)
        cy = curr_y + row * (card_h + gap)
        draw_stock_card_img(draw, cx, cy, card_w, card_h, sym, name, pr, chg, chg_col, mcap, pts)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 3. 1080p SIGNALS HERO SCREENSHOT (desktop-signals-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_signals_screenshot(out_path: str):
    """Renders 1080p SIGNALS hero preset: Polymarket prediction odds & related headlines."""
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="SIGNALS")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_meta = get_font(11, bold=False)

    m = 20
    curr_y = 86

    # Focus Header Banner
    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_EMERALD, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_EMERALD, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_EMERALD, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: MARKET SIGNALS & POLYMARKET ODDS", fill=C_EMERALD, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "MARKET-IMPLIED PROBABILITIES & CONTEXTUAL HEADLINES · ATTENTION RANKED", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 68

    cols = 3
    gap = 14
    card_w = (w - 2 * m - (cols - 1) * gap) // cols
    card_h = 420

    signals_all = [
        ("Fed Interest Rate Cut by Dec?", "FINANCE", "64%", "▲ +8.0 pts / 24H", C_GREEN, "$14.2M", "$2.8M", [
            ("Reuters: Fed Chair Powell signals easing cycle baseline...", "Reuters", "18m ago"),
            ("Bloomberg: Treasury yields steady following CPI print...", "Bloomberg", "42m ago"),
            ("WSJ: Market odds price in 25bps cut at next FOMC session...", "WSJ", "1h ago"),
        ]),
        ("Bitcoin Reaches $100K in 2026?", "CRYPTO", "71%", "▲ +5.2 pts / 24H", C_GREEN, "$28.5M", "$4.1M", [
            ("CoinDesk: ETF weekly net inflows surge to fresh high...", "CoinDesk", "24m ago"),
            ("CNBC: Digital asset market liquidity expands significantly...", "CNBC", "1h ago"),
            ("TheBlock: Exchange reserves hit multi-year lows as supply shrinks...", "TheBlock", "2h ago"),
        ]),
        ("Next Frontier AI Model Release Q4?", "TECH / AI", "83%", "▲ +12.0 pts / 24H", C_GREEN, "$6.2M", "$1.5M", [
            ("TechCrunch: Anthropic / OpenAI speed up release schedules...", "TechCrunch", "31m ago"),
            ("TheVerge: Safety evaluation benchmarks completed...", "TheVerge", "2h ago"),
            ("ArsTechnica: Developers report breakthrough reasoning gains...", "ArsTechnica", "3h ago"),
        ]),
        ("US Economic Soft Landing in 2026?", "MACRO", "58%", "▼ -3.1 pts / 24H", C_RED, "$9.4M", "$1.9M", [
            ("WSJ: Payrolls report shows labor market resilience...", "WSJ", "52m ago"),
            ("FT: Central banks coordinate gradual liquidity transition...", "FT", "2h ago"),
            ("Barron's: Consumer spending indexes stay in expansion territory...", "Barron's", "4h ago"),
        ]),
        ("SpaceX Starship Orbital Catch Success?", "AEROSPACE", "76%", "▲ +4.0 pts / 24H", C_GREEN, "$11.0M", "$2.3M", [
            ("ArsTechnica: Super Heavy booster caught on pad arms...", "ArsTechnica", "1h ago"),
            ("SpaceNews: FAA orbital license approved for next launch...", "SpaceNews", "3h ago"),
            ("AviationWeek: Reusability cadence reaches commercial milestone...", "AviationWeek", "5h ago"),
        ]),
        ("Crude Oil Below $70 by Year-End?", "COMMODITIES", "42%", "▼ -6.4 pts / 24H", C_RED, "$8.7M", "$1.6M", [
            ("Reuters: OPEC+ supply policy review meeting scheduled...", "Reuters", "1h ago"),
            ("Bloomberg: Global demand outlook revisions weigh on futures...", "Bloomberg", "3h ago"),
            ("S&P Global: Refining margins moderate across key shipping hubs...", "S&P Global", "4h ago"),
        ]),
    ]

    for idx, (q, cat, prob, delta, d_col, vol, liq, hls) in enumerate(signals_all):
        col = idx % cols
        row = idx // cols
        cx = m + col * (card_w + gap)
        cy = curr_y + row * (card_h + gap)
        draw_signal_card_img(draw, cx, cy, card_w, card_h, q, cat, prob, delta, d_col, vol, liq, hls)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 4. 1080p AI HERO SCREENSHOT (desktop-ai-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_ai_screenshot(out_path: str):
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="AI")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_hero = get_font(26, bold=True)
    f_sec_metric = get_font(16, bold=True)
    f_meta = get_font(12, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_CORAL, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_CORAL, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_CORAL, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: AI USAGE & SUBSCRIPTION QUOTAS", fill=C_CORAL, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "LIVE OAUTH TELEMETRY & MULTI-AGENT STATE MONITOR", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 68

    ai_w = (w - 2 * m - 2 * 16) // 3
    ai_h = 420
    ai_data = [
        ("CODEX CLI", C_GREEN, "READY", C_GREEN, "5H ROLLING USAGE", "100% LEFT", 100, "RESET IN: 5H 00M", "WEEKLY ROLLING CAP", "29% LEFT", 29, "RESET IN: 1D 22H", "GPT-5.6 · CHATGPT PLUS TIER", "16,420 TOKENS / SEC"),
        ("GEMINI CODE ASSIST", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING USAGE", "73% LEFT", 73, "RESET IN: 4H 16M", "WEEKLY ROLLING CAP", "76% LEFT", 76, "RESET IN: 6D 01H", "GEMINI 3.8 FLASH / PRO", "GOOGLE AI DEVELOPER WORKSPACE"),
        ("CLAUDE PRO", C_CORAL, "ONLINE", C_GREEN, "5H ROLLING USAGE", "97% LEFT", 97, "RESET IN: NOW (CACHED)", "WEEKLY ROLLING CAP", "62% LEFT", 62, "RESET IN: NOW (CACHED)", "CLAUDE PERSONAL · ANTHROPIC PRO", "CLAUDE 3.7 SONNET DUAL ENGINE"),
    ]

    for idx, (title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot1, foot2) in enumerate(ai_data):
        ax = m + idx * (ai_w + 16)
        draw_card_frame(draw, ax, curr_y, ai_w, ai_h, title, col, bd, bd_col)

        draw.text((ax + 20, curr_y + 50), p_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 180, curr_y + 44), p_val, fill=col, font=f_hero)
        draw_segmented_bar(draw, ax + 20, curr_y + 90, ai_w - 40, 16, p_pct, col, segments=18)
        draw.text((ax + 20, curr_y + 115), p_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.line([ax + 20, curr_y + 160, ax + ai_w - 20, curr_y + 160], fill=(26, 36, 54), width=1)

        draw.text((ax + 20, curr_y + 185), s_lbl, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((ax + ai_w - 160, curr_y + 180), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=f_sec_metric)
        draw_segmented_bar(draw, ax + 20, curr_y + 225, ai_w - 40, 14, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=18)
        draw.text((ax + 20, curr_y + 248), s_rst, fill=C_TEXT_DIM, font=f_meta)

        draw.line([ax + 20, curr_y + 300, ax + ai_w - 20, curr_y + 300], fill=(26, 36, 54), width=1)
        draw.text((ax + 20, curr_y + 330), foot1, fill=C_TEXT_WHITE, font=f_meta)
        draw.text((ax + 20, curr_y + 360), foot2, fill=C_TEXT_MUTED, font=f_meta)

    # Agent Activity Bar
    curr_y += ai_h + 20
    draw.rectangle([m, curr_y, w - m, curr_y + 420], fill=C_CARD_BG, outline=C_PURPLE, width=1)
    draw.text((m + 20, curr_y + 20), "─── [ LIVE AGENTIC CODING TELEMETRY ] ─── ACTIVE SUBPROCESS SESSIONS", fill=C_PURPLE, font=f_title)
    
    agent_rows = [
        ("CODEX CLOUD RUNNER", "WORKING", C_GREEN, "Running verification test suite: tests/test_milestone15.py", "Active 3m 42s", "14 Tool Calls"),
        ("GEMINI ASSISTANT", "WORKING", C_GREEN, "Optimizing 1D intraday sparkline math & polygon smoothing", "Active 1m 15s", "8 Tool Calls"),
        ("CLAUDE PRO SUITE", "IDLE", C_TEXT_DIM, "Awaiting next user instruction or task schedule trigger", "Last active 6m ago", "Session Healthy"),
    ]
    for r_idx, (a_name, a_st, a_st_col, a_desc, a_elap, a_tools) in enumerate(agent_rows):
        ry = curr_y + 65 + r_idx * 105
        draw.rectangle([m + 16, ry, w - m - 16, ry + 90], fill=(14, 19, 30), outline=(28, 38, 56), width=1)
        draw.text((m + 35, ry + 16), a_name, fill=C_TEXT_WHITE, font=f_title)
        draw.rectangle([m + 280, ry + 14, m + 370, ry + 38], fill=(16, 38, 26) if a_st=="WORKING" else (24, 28, 38), outline=a_st_col)
        draw.text((m + 295, ry + 18), a_st, fill=a_st_col, font=get_font(10, bold=True))
        draw.text((m + 35, ry + 50), a_desc, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((w - m - 180, ry + 18), a_elap, fill=C_ACTIVE_CYAN, font=f_meta)
        draw.text((w - m - 180, ry + 50), a_tools, fill=C_TEXT_DIM, font=f_meta)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 5. 1080p CRYPTO HERO SCREENSHOT (desktop-crypto-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_crypto_screenshot(out_path: str):
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="CRYPTO")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_hero = get_font(28, bold=True)
    f_sec_metric = get_font(18, bold=True)
    f_meta = get_font(12, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_GOLD, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_GOLD, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_GOLD, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: CRYPTO SPOT MARKETS & LIVE CHARTS", fill=C_GOLD, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "HIGH-FREQUENCY WEBSOCKET TELEMETRY · 1D INTRADAY SPARKLINE", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 68

    # Row 1: BTC & ETH (Large Hero Cards)
    top_w = (w - 2 * m - 16) // 2
    top_h = 420
    top_assets = [
        ("btc", "₿ BITCOIN SPOT (BTC/USDT)", "$84,021.50", "-0.88%", C_GOLD, C_RED, [0.35, 0.32, 0.40, 0.45, 0.38, 0.50, 0.58, 0.54, 0.65, 0.70, 0.68, 0.75, 0.82, 0.78, 0.85, 0.90, 0.86, 0.92, 0.95], "$85,210.00", "$83,180.00", "$1.66T", "$34.2B"),
        ("eth", "Ξ ETHEREUM SPOT (ETH/USDT)", "$2,691.80", "-0.24%", C_ETH, C_RED, [0.85, 0.80, 0.78, 0.72, 0.75, 0.68, 0.62, 0.65, 0.58, 0.52, 0.55, 0.48, 0.42, 0.45, 0.38, 0.35, 0.32, 0.28, 0.25], "$2,740.00", "$2,670.00", "$324.5B", "$16.8B"),
    ]

    for idx, (cid, title, price, chg, col, chg_col, pts, hi, lo, mcap, vol) in enumerate(top_assets):
        cx = m + idx * (top_w + 16)
        draw_card_frame(draw, cx, curr_y, top_w, top_h, title, col, chg, chg_col, is_active=(idx==0))

        draw.text((cx + 20, curr_y + 50), price, fill=col, font=f_hero)
        draw.text((cx + top_w - 120, curr_y + 56), chg, fill=chg_col, font=f_sec_metric)

        sp_x1 = cx + 20
        sp_x2 = cx + top_w - 20
        sp_y1 = curr_y + 110
        sp_y2 = curr_y + top_h - 60
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=3)
        draw.ellipse([sp_pts[-1][0] - 4, sp_pts[-1][1] - 4, sp_pts[-1][0] + 4, sp_pts[-1][1] + 4], fill=col)

        draw.text((cx + 20, curr_y + top_h - 30), f"24H HIGH: {hi}   LOW: {lo}   |   MCAP: {mcap}   VOL: {vol}", fill=C_TEXT_DIM, font=f_meta)

    # Row 2: SOL, DOGE, PEPE
    curr_y += top_h + 16
    bot_w = (w - 2 * m - 2 * 16) // 3
    bot_h = 420
    bot_assets = [
        ("sol", "◎ SOLANA SPOT", "$122.06", "+3.34%", C_SOLANA, C_GREEN, [0.2, 0.25, 0.35, 0.45, 0.55, 0.65, 0.72, 0.85, 0.94], "$124.50", "$117.80", "$59.2B"),
        ("doge", "Ð DOGECOIN SPOT", "$0.0989", "+2.71%", C_DOGE, C_GREEN, [0.3, 0.35, 0.42, 0.50, 0.62, 0.75, 0.82, 0.88, 0.91], "$0.1020", "$0.0950", "$14.4B"),
        ("pepe", "🐸 PEPE SPOT", "$0.0000045", "+0.70%", C_PEPE, C_GREEN, [0.4, 0.45, 0.52, 0.58, 0.64, 0.70, 0.76, 0.79, 0.82], "$0.0000048", "$0.0000043", "$1.89B"),
    ]

    for idx, (cid, title, price, chg, col, chg_col, pts, hi, lo, mcap) in enumerate(bot_assets):
        cx = m + idx * (bot_w + 16)
        draw_card_frame(draw, cx, curr_y, bot_w, bot_h, title, col, chg, chg_col)

        draw.text((cx + 20, curr_y + 50), price, fill=col, font=f_hero)
        draw.text((cx + bot_w - 110, curr_y + 56), chg, fill=chg_col, font=f_sec_metric)

        sp_x1 = cx + 20
        sp_x2 = cx + bot_w - 20
        sp_y1 = curr_y + 110
        sp_y2 = curr_y + bot_h - 60
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=3)
        draw.ellipse([sp_pts[-1][0] - 4, sp_pts[-1][1] - 4, sp_pts[-1][0] + 4, sp_pts[-1][1] + 4], fill=col)

        draw.text((cx + 20, curr_y + bot_h - 30), f"24H HIGH: {hi}   LOW: {lo}   |   MCAP: {mcap}", fill=C_TEXT_DIM, font=f_meta)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 6. 1080p SYSTEM HERO SCREENSHOT (desktop-system-1080p.png)
# ---------------------------------------------------------------------------
def render_preset_system_screenshot(out_path: str):
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)
    draw_command_center_header(draw, w, active_preset="SYSTEM")

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_hero = get_font(26, bold=True)
    f_sec_metric = get_font(16, bold=True)
    f_meta = get_font(12, bold=False)

    m = 20
    curr_y = 86

    draw.rectangle([m, curr_y, w - m, curr_y + 48], fill=(14, 22, 36), outline=C_GREEN, width=1)
    draw.rectangle([m + 8, curr_y + 8, m + 175, curr_y + 40], fill=(21, 38, 59), outline=C_GREEN, width=1)
    draw.text((m + 22, curr_y + 14), "◀ BACK TO ALL (Esc)", fill=C_GREEN, font=f_btn)
    draw.text((m + 195, curr_y + 14), "FOCUS PRESENTATION MODE: SYSTEM HARDWARE & LOCAL DAEMONS", fill=C_GREEN, font=f_title)
    draw.text((w - m - 20, curr_y + 16), "NVML ACCELERATION MONITOR · LINUX CLUSTER NODES", fill=C_TEXT_DIM, font=f_meta, anchor="ra")

    curr_y += 68

    col_w = (w - 2 * m - 16) // 2
    col_h = 420

    # Local RTX 5080 Card
    c1 = m
    draw_card_frame(draw, c1, curr_y, col_w, col_h, "LOCAL WORKSTATION GPU & CORES", (55, 195, 245), "ONLINE", C_GREEN)
    draw.text((c1 + 20, curr_y + 50), "NVIDIA GEFORCE RTX 5080 (16GB GDDR7)", fill=C_TEXT_WHITE, font=f_title)
    draw.text((c1 + 20, curr_y + 85), "GPU UTILIZATION", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((c1 + col_w - 100, curr_y + 78), "3%", fill=C_GREEN, font=f_hero)
    draw_segmented_bar(draw, c1 + 20, curr_y + 120, col_w - 40, 16, 3, C_GREEN, segments=24)
    draw.text((c1 + 20, curr_y + 148), "VRAM ALLOCATED: 3.2 GB / 16.0 GB (20%)", fill=C_TEXT_DIM, font=f_meta)

    draw.line([c1 + 20, curr_y + 185, c1 + col_w - 20, curr_y + 185], fill=(26, 36, 54), width=1)
    draw.text((c1 + 20, curr_y + 205), "HOST RAM USAGE", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((c1 + col_w - 100, curr_y + 200), "44%", fill=C_BLUE, font=f_sec_metric)
    draw_segmented_bar(draw, c1 + 20, curr_y + 235, col_w - 40, 14, 44, C_BLUE, segments=24)
    draw.text((c1 + 20, curr_y + 260), "COMMITTED: 28.1 GB / 64.0 GB DDR5 · 16 CORES ACTIVE", fill=C_TEXT_DIM, font=f_meta)

    draw.line([c1 + 20, curr_y + 300, c1 + col_w - 20, curr_y + 300], fill=(26, 36, 54), width=1)
    draw.text((c1 + 20, curr_y + 330), "GPU TEMP: 41°C   FAN: 0 RPM (QUIET)   POWER: 28W", fill=C_TEXT_WHITE, font=f_meta)
    draw.text((c1 + 20, curr_y + 365), "NVML DRIVER 572.70 · CUDA 12.8 ACTIVE", fill=C_TEXT_DIM, font=f_meta)

    # DGX Spark Cluster Card
    c2 = m + col_w + 16
    draw_card_frame(draw, c2, curr_y, col_w, col_h, "NVIDIA DGX SPARK SUPERCOMPUTER CLUSTER", C_NVIDIA, "ONLINE", C_GREEN)
    draw.text((c2 + 20, curr_y + 50), "CLUSTER NODE 01 (GB10 DUAL ARCHITECTURE)", fill=C_TEXT_WHITE, font=f_title)
    draw.text((c2 + 20, curr_y + 85), "AGGREGATE GPU LOAD", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((c2 + col_w - 100, curr_y + 78), "0%", fill=C_GREEN, font=f_hero)
    draw_segmented_bar(draw, c2 + 20, curr_y + 120, col_w - 40, 16, 0, C_GREEN, segments=24)
    draw.text((c2 + 20, curr_y + 148), "CLUSTER VRAM: 0.0 GB / 256.0 GB POOL (IDLE)", fill=C_TEXT_DIM, font=f_meta)

    draw.line([c2 + 20, curr_y + 185, c2 + col_w - 20, curr_y + 185], fill=(26, 36, 54), width=1)
    draw.text((c2 + 20, curr_y + 205), "CLUSTER NODE SYSTEM RAM", fill=C_TEXT_MUTED, font=f_meta)
    draw.text((c2 + col_w - 100, curr_y + 200), "40%", fill=C_GREEN, font=f_sec_metric)
    draw_segmented_bar(draw, c2 + 20, curr_y + 235, col_w - 40, 14, 40, C_GREEN, segments=24)
    draw.text((c2 + 20, curr_y + 260), "LOAD AVERAGE: 1.72, 1.45, 1.30 (64 CORES)", fill=C_TEXT_DIM, font=f_meta)

    draw.line([c2 + 20, curr_y + 300, c2 + col_w - 20, curr_y + 300], fill=(26, 36, 54), width=1)
    draw.text((c2 + 20, curr_y + 330), "CLUSTER TEMP: 39°C   INFNBAND: 400 Gbps   STATUS: STABLE", fill=C_TEXT_WHITE, font=f_meta)
    draw.text((c2 + 20, curr_y + 365), "dgx-spark · UBUNTU 24.04 LTS ENTERPRISE", fill=C_TEXT_DIM, font=f_meta)

    curr_y += col_h + 16
    draw.rectangle([m, curr_y, w - m, curr_y + 420], fill=C_CARD_BG, outline=C_GREEN, width=1)
    draw.text((m + 20, curr_y + 20), "─── [ BACKGROUND SERVICES HEALTH ] ─── WORKSTATION LOCAL INFRASTRUCTURE", fill=C_GREEN, font=f_title)
    
    svc_items = [
        ("OLLAMA DAEMON", "ONLINE", "REST API :11434 · Llama 3.3 70B loaded", "0.2% CPU", "18.4 GB RAM"),
        ("DOCKER ENGINE", "ONLINE", "12 Containers running (Postgres, Redis, Chroma, Nginx)", "1.1% CPU", "4.2 GB RAM"),
        ("REDIS KV CACHE", "ONLINE", "Memory footprint: 142 MB · 1,280 keys/sec throughput", "0.0% CPU", "142 MB RAM"),
        ("POSTGRESQL 17", "ONLINE", "Active connections: 8 · WAL archiving normal", "0.1% CPU", "512 MB RAM"),
    ]
    for s_idx, (s_name, s_st, s_desc, s_cpu, s_ram) in enumerate(svc_items):
        sy = curr_y + 60 + s_idx * 80
        draw.rectangle([m + 16, sy, w - m - 16, sy + 65], fill=(14, 19, 30), outline=(28, 38, 56), width=1)
        draw.text((m + 35, sy + 14), s_name, fill=C_TEXT_WHITE, font=f_title)
        draw.ellipse([m + 260, sy + 18, m + 270, sy + 28], fill=C_GREEN)
        draw.text((m + 280, sy + 14), s_st, fill=C_GREEN, font=get_font(11, bold=True))
        draw.text((m + 35, sy + 38), s_desc, fill=C_TEXT_MUTED, font=f_meta)
        draw.text((w - m - 280, sy + 22), s_cpu, fill=C_ACTIVE_CYAN, font=f_meta)
        draw.text((w - m - 140, sy + 22), s_ram, fill=C_TEXT_WHITE, font=f_meta)

    img.save(out_path, "PNG")
    print(f"Generated 1080p: {out_path}")


# ---------------------------------------------------------------------------
# 7. 9:16 VERTICAL CREATOR SCREENSHOTS (1080x1920)
# ---------------------------------------------------------------------------
def render_creator_ai_vertical_screenshot(out_path: str):
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 90], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.text((30, 30), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))
    draw.text((w - 240, 34), "CREATOR 9:16 · AI HERO", fill=C_PURPLE, font=get_font(13, bold=True))

    m = 30
    curr_y = 120
    card_w = w - 2 * m
    card_h = 370

    ai_data = [
        ("CODEX CLI", C_GREEN, "READY", C_GREEN, "5H ROLLING", "100% LEFT", 100, "RESET IN: 5H 00M", "WEEKLY CAP", "29% LEFT", 29, "RESET IN: 1D 22H", "GPT-5.6 · CHATGPT PLUS TIER"),
        ("GEMINI CODE ASSIST", C_BLUE, "ACTIVE", C_GREEN, "5H ROLLING", "73% LEFT", 73, "RESET IN: 4H 16M", "WEEKLY CAP", "76% LEFT", 76, "RESET IN: 6D 01H", "GEMINI 3.8 FLASH / PRO TIER"),
        ("CLAUDE PRO", C_CORAL, "ONLINE", C_GREEN, "5H ROLLING", "97% LEFT", 97, "RESET IN: NOW (CACHED)", "WEEKLY CAP", "62% LEFT", 62, "RESET IN: NOW (CACHED)", "CLAUDE PERSONAL · ANTHROPIC PRO"),
    ]

    for title, col, bd, bd_col, p_lbl, p_val, p_pct, p_rst, s_lbl, s_val, s_pct, s_rst, foot in ai_data:
        draw_card_frame(draw, m, curr_y, card_w, card_h, title, col, bd, bd_col)
        draw.text((m + 25, curr_y + 50), p_lbl, fill=C_TEXT_MUTED, font=get_font(13))
        draw.text((m + card_w - 210, curr_y + 44), p_val, fill=col, font=get_font(26, bold=True))
        draw_segmented_bar(draw, m + 25, curr_y + 95, card_w - 50, 16, p_pct, col, segments=20)
        draw.text((m + 25, curr_y + 125), p_rst, fill=C_TEXT_DIM, font=get_font(13))

        draw.line([m + 25, curr_y + 165, m + card_w - 25, curr_y + 165], fill=(26, 36, 54), width=1)

        draw.text((m + 25, curr_y + 190), s_lbl, fill=C_TEXT_MUTED, font=get_font(13))
        draw.text((m + card_w - 180, curr_y + 184), s_val, fill=C_GREEN if s_pct >= 30 else C_AMBER, font=get_font(20, bold=True))
        draw_segmented_bar(draw, m + 25, curr_y + 230, card_w - 50, 14, s_pct, C_GREEN if s_pct >= 30 else C_AMBER, segments=20)
        draw.text((m + 25, curr_y + 258), s_rst, fill=C_TEXT_DIM, font=get_font(13))

        draw.line([m + 25, curr_y + 300, m + card_w - 25, curr_y + 300], fill=(26, 36, 54), width=1)
        draw.text((m + 25, curr_y + 325), foot, fill=C_TEXT_WHITE, font=get_font(13))
        curr_y += card_h + 25

    # 4th Card: Agent Activity
    draw_card_frame(draw, m, curr_y, card_w, 420, "LIVE CODING AGENT TELEMETRY", C_PURPLE, "ACTIVE", C_GREEN)
    act_rows = [
        ("CODEX CLI", "WORKING", C_GREEN, "Active 3m 42s · Running tests"),
        ("GEMINI ASSIST", "WORKING", C_GREEN, "Active 1m 15s · Generating sparklines"),
        ("CLAUDE PRO", "IDLE", C_TEXT_DIM, "Idle 6m · Ready for instruction"),
    ]
    for idx, (aname, ast, ast_col, adesc) in enumerate(act_rows):
        ay = curr_y + 60 + idx * 110
        draw.rectangle([m + 20, ay, m + card_w - 20, ay + 90], fill=(14, 19, 30), outline=(28, 38, 56), width=1)
        draw.text((m + 40, ay + 18), aname, fill=C_TEXT_WHITE, font=get_font(16, bold=True))
        draw.text((m + card_w - 150, ay + 18), ast, fill=ast_col, font=get_font(14, bold=True))
        draw.text((m + 40, ay + 52), adesc, fill=C_TEXT_MUTED, font=get_font(13))

    img.save(out_path, "PNG")
    print(f"Generated 9:16 Vertical: {out_path}")


def render_creator_crypto_vertical_screenshot(out_path: str):
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 90], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.text((30, 30), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))
    draw.text((w - 280, 34), "CREATOR 9:16 · CRYPTO HERO", fill=C_GOLD, font=get_font(13, bold=True))

    m = 30
    curr_y = 120
    card_w = w - 2 * m
    card_h = 325

    coins = [
        ("₿ BTC · BITCOIN SPOT", "$84,021.50", "-0.88%", C_GOLD, C_RED, [0.35, 0.40, 0.45, 0.55, 0.65, 0.70, 0.82, 0.90, 0.95], "$85.2K", "$83.2K"),
        ("Ξ ETH · ETHEREUM SPOT", "$2,691.80", "-0.24%", C_ETH, C_RED, [0.85, 0.78, 0.72, 0.65, 0.58, 0.52, 0.45, 0.35, 0.25], "$2,740", "$2,670"),
        ("◎ SOL · SOLANA SPOT", "$122.06", "+3.34%", C_SOLANA, C_GREEN, [0.2, 0.30, 0.40, 0.55, 0.68, 0.75, 0.85, 0.94], "$124.50", "$117.80"),
        ("Ð DOGE · DOGECOIN SPOT", "$0.0989", "+2.71%", C_DOGE, C_GREEN, [0.3, 0.40, 0.50, 0.62, 0.75, 0.82, 0.88, 0.91], "$0.1020", "$0.0950"),
        ("🐸 PEPE · PEPE SPOT", "$0.0000045", "+0.70%", C_PEPE, C_GREEN, [0.4, 0.48, 0.55, 0.62, 0.70, 0.76, 0.79, 0.82], "$0.0000048", "$0.0000043"),
    ]

    for title, price, chg, col, chg_col, pts, hi, lo in coins:
        draw_card_frame(draw, m, curr_y, card_w, card_h, title, col, chg, chg_col)
        draw.text((m + 25, curr_y + 50), price, fill=col, font=get_font(32, bold=True))
        chg_w = get_font(20, bold=True).getbbox(chg)[2]
        draw.text((m + card_w - 25 - chg_w, curr_y + 56), chg, fill=chg_col, font=get_font(20, bold=True))

        sp_x1 = m + 25
        sp_x2 = m + card_w - 25
        sp_y1 = curr_y + 110
        sp_y2 = curr_y + card_h - 60
        step = (sp_x2 - sp_x1) / (len(pts) - 1)
        sp_pts = [(sp_x1 + i * step, sp_y2 - v * (sp_y2 - sp_y1)) for i, v in enumerate(pts)]
        for i in range(len(sp_pts) - 1):
            draw.line([sp_pts[i], sp_pts[i+1]], fill=col, width=4)
        draw.ellipse([sp_pts[-1][0] - 5, sp_pts[-1][1] - 5, sp_pts[-1][0] + 5, sp_pts[-1][1] + 5], fill=col)

        draw.text((m + 25, curr_y + card_h - 30), f"24H HIGH: {hi}   LOW: {lo}   ·   SPOT FEED", fill=C_TEXT_DIM, font=get_font(13))
        curr_y += card_h + 20

    img.save(out_path, "PNG")
    print(f"Generated 9:16 Vertical: {out_path}")


def render_creator_stocks_vertical_screenshot(out_path: str):
    """Renders 1080x1920 9:16 vertical Shorts capture: Top 5 US equities."""
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 90], fill=C_HEADER_BG, outline=(24, 32, 48), width=1)
    draw.text((30, 30), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))
    draw.text((w - 280, 34), "CREATOR 9:16 · US EQUITIES", fill=C_ACTIVE_CYAN, font=get_font(13, bold=True))

    m = 30
    curr_y = 120
    card_w = w - 2 * m
    card_h = 325

    top_5_equities = [
        ("NVDA", "NVIDIA Corporation", "$229.81", "+2.14%", C_GREEN, "$5.55T", [222, 224, 223, 225, 226, 227, 228, 229, 230]),
        ("AAPL", "Apple Inc.", "$254.23", "+0.85%", C_GREEN, "$3.82T", [251, 252, 252, 253, 253, 254, 254, 255, 254]),
        ("MSFT", "Microsoft Corp.", "$516.17", "-0.42%", C_RED, "$3.74T", [520, 519, 518, 519, 518, 517, 518, 517, 516]),
        ("AMZN", "Amazon.com Inc.", "$231.40", "+1.12%", C_GREEN, "$2.44T", [228, 229, 229, 230, 230, 231, 230, 231, 231]),
        ("GOOGL", "Alphabet Inc.", "$201.55", "-0.65%", C_RED, "$2.41T", [203, 203, 202, 202, 201, 202, 201, 201, 201]),
    ]

    for sym, name, pr, chg, chg_col, mcap, pts in top_5_equities:
        draw_stock_card_img(draw, m, curr_y, card_w, card_h, sym, name, pr, chg, chg_col, mcap, pts)
        curr_y += card_h + 20

    img.save(out_path, "PNG")
    print(f"Generated 9:16 Vertical: {out_path}")


# ---------------------------------------------------------------------------
# 8. FIRST-RUN DEVICE SETUP SCREENSHOT (device-setup.png)
# ---------------------------------------------------------------------------
def render_device_setup_screenshot(out_path: str):
    """Renders Screen 1: Choose Your Display Onboarding Wizard."""
    w, h = 900, 720
    img = Image.new("RGBA", (w, h), (8, 11, 18))
    draw = ImageDraw.Draw(img)

    # Dialog Window Container
    cx, cy, cw, ch = 70, 40, 760, 640
    draw.rectangle([cx, cy, cx + cw, cy + ch], fill=C_BG, outline=C_ACTIVE_CYAN, width=2)

    # Header
    draw.text((cx + 30, cy + 30), "AI DESK DASHBOARD", fill=C_ACTIVE_CYAN, font=get_font(18, bold=True))
    draw.text((cx + 30, cy + 60), "FIRST-RUN DEVICE ONBOARDING", fill=C_TEXT_WHITE, font=get_font(12, bold=True))
    draw.text((cx + 30, cy + 85), "Choose your display hardware to begin:", fill=C_TEXT_MUTED, font=get_font(11))

    # 4 Option Cards
    cards_y = cy + 120
    opt_w = cw - 60
    opt_h = 95
    gap = 14

    options = [
        ("MiniToo", "Bluetooth Classic / SPP (160x128 16-bit color LCD)", "Divoom MiniToo with hardware rotary knob & live AI quotas", C_ACTIVE_CYAN, True),
        ("Ditoo", "Bluetooth LE (16x16 Pixel Matrix)", "Divoom Ditoo / Ditoo-Pro retro pixel speaker display", C_PURPLE, False),
        ("No physical display", "Desktop dashboard only (Monitor Command Center)", "Full high-DPI desktop experience with no hardware required", C_GREEN, False),
        ("Detect automatically", "Probe active COM ports and BLE radios", "Scans Windows serial ports and Bluetooth adapters for supported devices", C_AMBER, False),
    ]

    for idx, (title, sub, det, col, is_selected) in enumerate(options):
        oy = cards_y + idx * (opt_h + gap)
        bg = (16, 26, 42) if is_selected else (14, 18, 28)
        bd = col if is_selected else (30, 40, 60)
        draw.rectangle([cx + 30, oy, cx + 30 + opt_w, oy + opt_h], fill=bg, outline=bd, width=2 if is_selected else 1)

        draw.text((cx + 50, oy + 14), title, fill=col, font=get_font(14, bold=True))
        draw.text((cx + 50, oy + 38), sub, fill=C_TEXT_WHITE, font=get_font(11, bold=True))
        draw.text((cx + 50, oy + 62), det, fill=C_TEXT_MUTED, font=get_font(10))

        # Checkmark / Radio dot
        rx = cx + 30 + opt_w - 40
        ry = oy + opt_h // 2
        draw.ellipse([rx - 10, ry - 10, rx + 10, ry + 10], outline=col, width=2)
        if is_selected:
            draw.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=col)

    # Footer note & continue button
    draw.text((cx + 30, cy + ch - 50), "Note: MiniToo requires Windows Bluetooth pairing first before SPP activation.", fill=C_TEXT_DIM, font=get_font(9))
    btn_w = 200
    btn_x = cx + cw - 30 - btn_w
    btn_y = cy + ch - 60
    draw.rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + 40], fill=(14, 56, 76), outline=C_ACTIVE_CYAN, width=1)
    draw.text((btn_x + 35, btn_y + 12), "[ CONTINUE ]", fill=C_ACTIVE_CYAN, font=get_font(11, bold=True))

    img.save(out_path, "PNG")
    print(f"Generated Device Setup: {out_path}")


# ---------------------------------------------------------------------------
# 9. SETTINGS DASHBOARD SCREENSHOT (settings-dashboard.png)
# ---------------------------------------------------------------------------
def render_settings_dashboard_screenshot(out_path: str):
    """Renders 900x660 High-DPI Settings dialog."""
    w, h = 900, 660
    img = Image.new("RGBA", (w, h), C_BG)
    draw = ImageDraw.Draw(img)

    f_title = get_font(15, bold=True)
    f_btn = get_font(11, bold=True)
    f_bold = get_font(12, bold=True)
    f_sub = get_font(11, bold=False)

    # Window Header
    draw.rectangle([0, 0, w, 55], fill=(12, 17, 26), outline=(24, 32, 48), width=1)
    draw.text((20, 18), "⚙ AI DESK DASHBOARD SETTINGS", fill=C_ACTIVE_CYAN, font=f_title)

    # Tabs
    tabs = [("DASHBOARD", True), ("MINITOO (128x128)", False), ("DITOO (16x16)", False), ("CLAUDE ACCOUNTS", False)]
    tx = 20
    ty = 65
    for t_name, is_sel in tabs:
        t_w = 160 if len(t_name) > 12 else 120
        t_bg = (16, 48, 64) if is_sel else (14, 18, 28)
        t_fg = C_ACTIVE_CYAN if is_sel else C_TEXT_MUTED
        t_bd = C_ACTIVE_CYAN if is_sel else (28, 38, 54)
        draw.rectangle([tx, ty, tx + t_w, ty + 36], fill=t_bg, outline=t_bd, width=2 if is_sel else 1)
        draw.text((tx + 18, ty + 10), t_name, fill=t_fg, font=f_btn)
        tx += t_w + 10

    # Content Area
    rx, ry, rw, rh = 20, 115, w - 40, h - 180
    draw.rectangle([rx, ry, rx + rw, ry + rh], fill=(13, 17, 26), outline=(24, 34, 50), width=1)

    # Group 1: UI Scale
    gy = ry + 20
    draw.text((rx + 18, gy), "DISPLAY SCALE & HIGH-DPI ENGINE", fill=C_ACTIVE_CYAN, font=f_bold)
    scales = ["100% (Native)", "125% (Balanced)", "150% (Recommended 1080p)", "175%", "200% (4K)"]
    sx = rx + 18
    for s_idx, s_txt in enumerate(scales):
        is_cur = (s_idx == 2)
        s_bg = (14, 53, 71) if is_cur else (16, 22, 34)
        s_fg = C_ACTIVE_CYAN if is_cur else C_TEXT_MUTED
        s_bd = C_ACTIVE_CYAN if is_cur else (28, 38, 54)
        sw = 155 if s_idx == 2 else (115 if s_idx < 2 else 75)
        draw.rectangle([sx, gy + 28, sx + sw, gy + 58], fill=s_bg, outline=s_bd, width=2 if is_cur else 1)
        draw.text((sx + 10, gy + 37), s_txt, fill=s_fg, font=get_font(10, bold=is_cur))
        sx += sw + 10

    # Group 2: Sections
    gy2 = gy + 85
    draw.text((rx + 18, gy2), "ENABLED DASHBOARD SECTIONS", fill=C_ACTIVE_CYAN, font=f_bold)
    sections = [("CRYPTO MARKETS", True), ("AI USAGE & QUOTAS", True), ("US EQUITIES (MARKET CAP)", True), ("MARKET SIGNALS & PREDICTIONS", True), ("SYSTEM HARDWARE & SERVICES", True)]
    for idx, (sec_name, on) in enumerate(sections):
        s_y = gy2 + 30 + idx * 30
        draw.rectangle([rx + 18, s_y, rx + 34, s_y + 16], fill=(14, 46, 32) if on else (20, 26, 38), outline=C_GREEN if on else C_TEXT_DIM)
        if on:
            draw.text((rx + 22, s_y + 1), "✓", fill=C_GREEN, font=get_font(11, bold=True))
        draw.text((rx + 44, s_y + 2), sec_name, fill=C_TEXT_WHITE if on else C_TEXT_DIM, font=f_sub)

    # Footer
    draw.rectangle([0, h - 55, w, h], fill=(10, 14, 22), outline=(24, 32, 48), width=1)
    draw.rectangle([w - 240, h - 45, w - 130, h - 12], fill=(22, 28, 42), outline=(38, 50, 72))
    draw.text((w - 205, h - 34), "CANCEL", fill=C_TEXT_MUTED, font=f_btn)
    draw.rectangle([w - 120, h - 45, w - 18, h - 12], fill=(14, 56, 76), outline=C_ACTIVE_CYAN)
    draw.text((w - 95, h - 34), "SAVE CONFIG", fill=C_ACTIVE_CYAN, font=f_btn)

    img.save(out_path, "PNG")
    print(f"Generated High-DPI Settings: {out_path}")


# ---------------------------------------------------------------------------
# 10. COMPACT DEVICE STATUS & HARDWARE PANEL (settings-device.png)
# ---------------------------------------------------------------------------
def render_settings_device_screenshot(out_path: str):
    """Renders 500x520 Compact Device Status & Hardware Panel."""
    w, h = 500, 520
    img = Image.new("RGBA", (w, h), (8, 11, 18))
    draw = ImageDraw.Draw(img)

    cx, cy, cw, ch = 30, 20, 440, 480
    draw.rectangle([cx, cy, cx + cw, cy + ch], fill=C_BG, outline=C_ACTIVE_CYAN, width=2)

    # Header
    draw.text((cx + 20, cy + 20), "DEVICE STATUS & HARDWARE", fill=C_ACTIVE_CYAN, font=get_font(15, bold=True))
    draw.text((cx + 20, cy + 46), "Physical Display Link & Connection Management", fill=C_TEXT_MUTED, font=get_font(10))
    draw.line([cx + 20, cy + 68, cx + cw - 20, cy + 68], fill=(24, 34, 52), width=1)

    # Info Grid
    items = [
        ("Device:", "Divoom MiniToo (160x128 16-bit Color LCD)"),
        ("Transport:", "Bluetooth Classic SPP (Serial Port Profile)"),
        ("Connection:", "CONNECTED"),
        ("Active Port:", "COM13 (Divoom SPP Serial Link)"),
        ("Last Seen:", "Just now (Active frame broadcast feed)"),
        ("Signal RSSI:", "-64 dBm (Strong Radio Link)"),
        ("Frame Rate:", "2.85 Hz (Relaxed Low-Interference Mode)"),
    ]

    iy = cy + 85
    for lbl, val in items:
        draw.text((cx + 20, iy), lbl, fill=C_TEXT_MUTED, font=get_font(11, bold=True))
        if val == "CONNECTED":
            draw.rectangle([cx + 140, iy - 2, cx + 250, iy + 18], fill=(13, 38, 27), outline=(27, 77, 54))
            draw.ellipse([cx + 148, iy + 4, cx + 156, iy + 12], fill=C_GREEN)
            draw.text((cx + 162, iy), val, fill=C_GREEN, font=get_font(10, bold=True))
        else:
            draw.text((cx + 140, iy), val, fill=C_TEXT_WHITE if "dBm" in val or "COM" in val else (200, 210, 225), font=get_font(10))
        iy += 32

    draw.line([cx + 20, cy + 325, cx + cw - 20, cy + 325], fill=(24, 34, 52), width=1)

    # Actions
    btn_y = cy + 345
    btn_w = cw - 40
    btn_h = 32

    # Reconnect
    draw.rectangle([cx + 20, btn_y, cx + 20 + btn_w, btn_y + btn_h], fill=(14, 53, 71), outline=C_ACTIVE_CYAN, width=1)
    draw.text((cx + 20 + btn_w // 2 - 60, btn_y + 8), "[ RECONNECT DEVICE ]", fill=C_ACTIVE_CYAN, font=get_font(10, bold=True))

    # Diagnostics
    btn_y += 40
    draw.rectangle([cx + 20, btn_y, cx + 20 + btn_w, btn_y + btn_h], fill=(16, 22, 34), outline=(32, 46, 66), width=1)
    draw.text((cx + 20 + btn_w // 2 - 80, btn_y + 8), "[ RUN HARDWARE DIAGNOSTICS ]", fill=C_TEXT_WHITE, font=get_font(10, bold=True))

    # Bluetooth Settings
    btn_y += 40
    draw.rectangle([cx + 20, btn_y, cx + 20 + btn_w, btn_y + btn_h], fill=(24, 18, 12), outline=C_AMBER, width=1)
    draw.text((cx + 20 + btn_w // 2 - 110, btn_y + 8), "[ OPEN WINDOWS BLUETOOTH SETTINGS ]", fill=C_AMBER, font=get_font(10, bold=True))

    img.save(out_path, "PNG")
    print(f"Generated Device Panel: {out_path}")


# ---------------------------------------------------------------------------
# MAIN EXECUTOR
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("assets/screenshots", exist_ok=True)

    # Milestone 15 Standard Named Screenshots
    render_preset_all_screenshot("assets/screenshots/desktop-all-1080p.png")
    render_preset_ai_screenshot("assets/screenshots/desktop-ai-1080p.png")
    render_preset_crypto_screenshot("assets/screenshots/desktop-crypto-1080p.png")
    render_preset_stocks_screenshot("assets/screenshots/desktop-stocks-1080p.png")
    render_preset_system_screenshot("assets/screenshots/desktop-system-1080p.png")
    render_preset_signals_screenshot("assets/screenshots/desktop-signals-1080p.png")
    render_creator_ai_vertical_screenshot("assets/screenshots/creator-ai-vertical.png")
    render_creator_crypto_vertical_screenshot("assets/screenshots/creator-crypto-vertical.png")
    render_creator_stocks_vertical_screenshot("assets/screenshots/creator-stocks-vertical.png")
    render_device_setup_screenshot("assets/screenshots/device-setup.png")
    render_settings_dashboard_screenshot("assets/screenshots/settings-dashboard.png")
    render_settings_device_screenshot("assets/screenshots/settings-device.png")

    # Backward-compatible aliases
    render_preset_all_screenshot("assets/screenshots/preset-all.png")
    render_preset_ai_screenshot("assets/screenshots/preset-ai.png")
    render_preset_crypto_screenshot("assets/screenshots/preset-crypto.png")
    render_preset_stocks_screenshot("assets/screenshots/preset-stocks.png")
    render_preset_system_screenshot("assets/screenshots/preset-system.png")
    render_settings_device_screenshot("assets/screenshots/settings-minitoo.png")

    print("\nAll Milestone 15 screenshots successfully rendered with full privacy sanitization!")
