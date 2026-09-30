#!/usr/bin/env python3
"""
Pixel-perfect 128x128 unified screen renderer for AI Desk Dashboard.
Renders all pages:
  1. CLAUDE
  2. CODEX
  3. GEMINI
  4. LOCAL PC
  5. DGX SPARK (online or offline)
  6. CODING
"""
from __future__ import annotations

import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from models import PageData, MetricItem


def get_fonts():
    """Load standard Segoe UI and Consolas fonts with fallback."""
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")

    try:
        f_header = ImageFont.truetype(os.path.join(fonts_dir, "segoeuib.ttf"), 13)
        f_header_sm = ImageFont.truetype(os.path.join(fonts_dir, "segoeuib.ttf"), 11)
        f_badge = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 9)
        f_label = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 10)
        f_value = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 11)
        f_large = ImageFont.truetype(os.path.join(fonts_dir, "segoeuib.ttf"), 15)
        f_reset = ImageFont.truetype(os.path.join(fonts_dir, "consolab.ttf"), 9)
    except Exception:
        f_header = ImageFont.load_default()
        f_header_sm = f_header
        f_badge = f_header
        f_label = f_header
        f_value = f_header
        f_large = f_header
        f_reset = f_header

    return {
        "header": f_header,
        "header_sm": f_header_sm,
        "badge": f_badge,
        "label": f_label,
        "value": f_value,
        "large": f_large,
        "reset": f_reset,
    }


def draw_progress_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
    percent: Optional[float],
    active_color: Tuple[int, int, int],
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


def get_color_for_pct(pct: Optional[float], is_stale: bool = False, is_remaining: bool = False) -> Tuple[int, int, int]:
    """
    Color mapping:
    - Standard (used/utilization): Emerald < 75%, Amber < 90%, Red >= 90%
    - Remaining (quota left): Emerald >= 30%, Amber >= 15%, Red < 15%
    """
    if pct is None:
        return (110, 125, 145)  # Muted gray
    if is_stale:
        return (245, 175, 50)   # Amber
    if is_remaining:
        if pct < 15:
            return (245, 75, 75)    # Red (critical quota)
        elif pct < 30:
            return (245, 175, 50)   # Amber (low quota)
        else:
            return (50, 230, 140)   # Emerald (healthy quota)
    else:
        if pct >= 90:
            return (245, 75, 75)    # Red
        elif pct >= 75:
            return (245, 175, 50)   # Amber
        else:
            return (50, 230, 140)   # Emerald


def render_dashboard_page(
    page: PageData,
    page_num: int = 1,
    total_pages: int = 6,
) -> Image.Image:
    """Render a 128x128 pixel-perfect dashboard frame for any normalized PageData."""
    img = Image.new("RGB", (128, 128), (11, 15, 25))  # Deep slate night blue
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Outer 1px frame
    draw.rectangle([0, 0, 127, 127], outline=(25, 35, 55))

    # --- Header Colors by Page ---
    p_id = page.page_id.lower()
    if p_id == "claude":
        c_title = (245, 140, 60)      # Anthropic coral
        c_badge_border = (80, 50, 30)
    elif p_id == "codex":
        c_title = (50, 215, 145)      # OpenAI emerald
        c_badge_border = (30, 80, 60)
    elif p_id == "gemini":
        c_title = (90, 165, 255)      # Google azure
        c_badge_border = (40, 70, 115)
    elif p_id == "local_pc":
        c_title = (55, 185, 245)      # Workstation cyan
        c_badge_border = (30, 75, 105)
    elif p_id == "dgx_spark":
        c_title = (118, 185, 0)       # NVIDIA green
        c_badge_border = (50, 80, 25)
    elif p_id == "coding":
        c_title = (185, 135, 255)     # Studio purple
        c_badge_border = (70, 45, 110)
    elif p_id in ("btc", "eth", "sol", "doge", "pepe", "crypto"):
        c_title = (247, 147, 26)      # Bitcoin / Crypto gold
        c_badge_border = (120, 75, 15)
    elif p_id in ("stocks_market_cap", "stocks_volatile", "stocks"):
        c_title = (0, 229, 255)       # Cyan stocks scanner
        c_badge_border = (0, 90, 110)
    elif p_id == "signals":
        c_title = (56, 239, 125)      # Emerald prediction markets
        c_badge_border = (30, 90, 60)
    elif p_id == "ai_activity":
        c_title = (185, 140, 255)     # Agent purple
        c_badge_border = (70, 45, 110)
    elif p_id == "services":
        c_title = (50, 215, 145)      # Services emerald
        c_badge_border = (30, 80, 60)
    else:
        c_title = (200, 200, 220)
        c_badge_border = (50, 60, 80)

    # Header Title
    title_font = fonts["header_sm"] if len(page.title) > 8 else fonts["header"]
    draw.text((8, 6), page.title, fill=c_title, font=title_font)

    # Header Top-Right Pill Badge (Model, Plan, or Status)
    # Prefer compact label in top right so it never crowds title
    if page.is_offline:
        b_text = "OFFLINE"
    elif p_id in ("claude", "codex", "gemini"):
        b_text = (page.footer_right or page.badge).upper()
    elif p_id == "local_pc":
        b_text = (page.footer_left or "ONLINE").upper()
    elif p_id == "dgx_spark":
        b_text = (page.footer_left or "ONLINE").upper()
    elif p_id == "coding":
        b_text = (page.secondary_metric.value if page.secondary_metric else "MAIN").upper()
    elif p_id in ("btc", "eth", "sol", "doge", "pepe", "crypto", "stocks_market_cap", "stocks_volatile", "stocks"):
        b_text = (page.badge or "").upper()
    elif p_id == "signals":
        b_text = (page.badge or "ODDS").upper()
    elif p_id in ("ai_activity", "services"):
        b_text = page.badge.upper()
    else:
        b_text = page.badge.upper()

    # Truncate badge if too long
    if len(b_text) > 10:
        b_text = b_text[:10]

    bbox = fonts["badge"].getbbox(b_text)
    bw = bbox[2] - bbox[0] + 12
    bx = 120 - bw
    by = 8
    draw.rectangle([bx, by, 120, by + 12], fill=(20, 26, 38), outline=c_badge_border)

    # Dot in badge
    if page.badge_color == "green":
        dot_c = (50, 230, 140)
    elif page.badge_color == "amber":
        dot_c = (245, 175, 50)
    elif page.badge_color == "blue":
        dot_c = (90, 165, 255)
    elif page.badge_color == "red":
        dot_c = (245, 75, 75)
    else:
        dot_c = (110, 125, 145)

    draw.ellipse([bx + 3, by + 4, bx + 7, by + 8], fill=dot_c)
    draw.text((bx + 9, by), b_text, fill=(210, 220, 235), font=fonts["badge"])
    badge_dot_c = dot_c

    # Header divider
    draw.line([(8, 22), (120, 22)], fill=(25, 38, 60), width=1)

    # =========================================================================
    # BODY CONTENT
    # =========================================================================

    # PATH A: OFFLINE VIEW (e.g. DGX Spark unreachable or BTC API down)
    if page.is_offline:
        off_text = page.offline_msg or "OFFLINE"
        off_font = fonts["large"] if len(off_text) <= 9 else fonts["header_sm"]
        obbox = off_font.getbbox(off_text)
        ow = obbox[2] - obbox[0]
        draw.text(((128 - ow) // 2, 40), off_text, fill=(245, 80, 80), font=off_font)

        lbl_text = "STATUS / LAST SEEN"
        lbbox = fonts["badge"].getbbox(lbl_text)
        lw = lbbox[2] - lbbox[0]
        draw.text(((128 - lw) // 2, 63), lbl_text, fill=(120, 135, 160), font=fonts["badge"])

        ago_text = page.offline_sub or "N/A"
        if len(ago_text) <= 12:
            ago_font = fonts["header"]
        elif len(ago_text) <= 18:
            ago_font = fonts["label"]
        else:
            ago_font = fonts["reset"]
        abbox = ago_font.getbbox(ago_text)
        aw = abbox[2] - abbox[0]
        draw.text(((128 - aw) // 2, 77), ago_text, fill=(245, 175, 50), font=ago_font)

    # PATH B: CODING STATUS PAGE
    elif p_id == "coding":
        draw.text((8, 25), "REPO", fill=(130, 145, 170), font=fonts["label"])
        repo_val = page.primary_metric.value if page.primary_metric else "hedgefly"
        draw.text((8, 36), repo_val[:16], fill=(55, 195, 245), font=fonts["value"])

        draw.text((8, 52), "BRANCH", fill=(130, 145, 170), font=fonts["label"])
        draw.text((68, 52), "STATE", fill=(130, 145, 170), font=fonts["label"])

        branch_val = page.secondary_metric.value if page.secondary_metric else "main"
        state_val = page.secondary_metric.reset if (page.secondary_metric and page.secondary_metric.reset) else "CLEAN"
        draw.text((8, 63), branch_val[:8], fill=(220, 230, 245), font=fonts["value"])

        state_color = (50, 230, 140) if "CLEAN" in state_val else (245, 175, 50)
        draw.text((68, 63), state_val[:8], fill=state_color, font=fonts["value"])

        draw.text((8, 79), "MODEL", fill=(130, 145, 170), font=fonts["label"])
        model_val = page.extra_metrics[0].value if page.extra_metrics else "GPT-5.6"
        draw.text((8, 90), model_val[:16], fill=(185, 140, 255), font=fonts["value"])

    # PATH C: LOCAL PC PAGE
    elif p_id == "local_pc":
        pm = page.primary_metric
        draw.text((8, 25), "GPU", fill=(140, 155, 175), font=fonts["label"])
        gpu_str = pm.value if pm else "N/A"
        c_gpu = get_color_for_pct(pm.pct if pm else None)
        vbox = fonts["value"].getbbox(gpu_str)
        vw = vbox[2] - vbox[0]
        draw.text((120 - vw, 24), gpu_str, fill=c_gpu, font=fonts["value"])
        draw_progress_bar(draw, 8, 38, 112, 6, pm.pct if pm else None, active_color=c_gpu)

        reset_str = pm.reset if (pm and pm.reset) else "TEMP N/A  VRAM N/A"
        draw.text((8, 48), reset_str, fill=(100, 125, 155), font=fonts["reset"])
        draw.line([(8, 61), (120, 61)], fill=(20, 30, 48), width=1)

        sm = page.secondary_metric
        draw.text((8, 65), "RAM", fill=(140, 155, 175), font=fonts["label"])
        ram_str = sm.value if sm else "N/A"
        c_ram = get_color_for_pct(sm.pct if sm else None)
        rvbox = fonts["value"].getbbox(ram_str)
        rvw = rvbox[2] - rvbox[0]
        draw.text((120 - rvw, 64), ram_str, fill=c_ram, font=fonts["value"])
        draw_progress_bar(draw, 8, 77, 112, 6, sm.pct if sm else None, active_color=c_ram)

        em = page.extra_metrics[0] if page.extra_metrics else None
        draw.text((8, 87), "CPU", fill=(140, 155, 175), font=fonts["label"])
        cpu_str = em.value if em else "N/A"
        c_cpu = get_color_for_pct(em.pct if em else None)
        cvbox = fonts["value"].getbbox(cpu_str)
        cvw = cvbox[2] - cvbox[0]
        draw.text((120 - cvw, 86), cpu_str, fill=c_cpu, font=fonts["value"])
        draw_progress_bar(draw, 8, 98, 112, 5, em.pct if em else None, active_color=c_cpu)

    # PATH D: DGX SPARK PAGE (ONLINE)
    elif p_id == "dgx_spark":
        pm = page.primary_metric
        draw.text((8, 25), "GPU", fill=(140, 155, 175), font=fonts["label"])
        gpu_str = pm.value if pm else "N/A"
        c_gpu = get_color_for_pct(pm.pct if pm else None)
        vbox = fonts["value"].getbbox(gpu_str)
        vw = vbox[2] - vbox[0]
        draw.text((120 - vw, 24), gpu_str, fill=c_gpu, font=fonts["value"])
        draw_progress_bar(draw, 8, 38, 112, 6, pm.pct if pm else None, active_color=c_gpu)
        reset_str = pm.reset if (pm and pm.reset) else "TEMP N/A  LOAD N/A"
        draw.text((8, 48), reset_str, fill=(100, 125, 155), font=fonts["reset"])
        draw.line([(8, 61), (120, 61)], fill=(20, 30, 48), width=1)

        sm = page.secondary_metric
        draw.text((8, 65), "RAM", fill=(140, 155, 175), font=fonts["label"])
        ram_str = sm.value if sm else "N/A"
        c_ram = get_color_for_pct(sm.pct if sm else None)
        rvbox = fonts["value"].getbbox(ram_str)
        rvw = rvbox[2] - rvbox[0]
        draw.text((120 - rvw, 64), ram_str, fill=c_ram, font=fonts["value"])
        draw_progress_bar(draw, 8, 77, 112, 6, sm.pct if sm else None, active_color=c_ram)

        mem_up_str = sm.reset if (sm and sm.reset) else "UPTIME N/A"
        draw.text((8, 89), mem_up_str, fill=(100, 125, 155), font=fonts["reset"])

    # PATH E: INDIVIDUAL CRYPTO ASSET (PRICE + 24H HIGH-CONTRAST SPARKLINE)
    elif p_id in ("btc", "eth", "sol", "doge", "pepe"):
        pm = page.primary_metric
        price_str = pm.value if pm else "$0"
        price_font = fonts["large"] if len(price_str) <= 8 else fonts["value"]
        draw.text((8, 25), price_str, fill=(245, 250, 255), font=price_font)

        # Sparkline area (x: 8..120, y: 46..84)
        closes = page.sparkline_data or []
        if len(closes) >= 2:
            min_c = min(closes)
            max_c = max(closes)
            rng = max_c - min_c if max_c != min_c else 1.0

            sx, sy, sw, sh = 8, 48, 112, 36
            points = []
            for i, c in enumerate(closes):
                px = sx + int(round(i * (sw / (len(closes) - 1))))
                norm_y = (c - min_c) / rng
                py = sy + sh - int(round(norm_y * sh))
                points.append((px, py))

            is_up = closes[-1] >= closes[0]
            c_line = (50, 230, 140) if is_up else (245, 80, 80)
            c_fill = (20, 50, 35) if is_up else (50, 22, 25)

            # Draw shaded area below sparkline
            poly = [(sx, sy + sh)] + points + [(sx + sw, sy + sh)]
            draw.polygon(poly, fill=c_fill)

            # Draw sparkline polyline
            for i in range(len(points) - 1):
                draw.line([points[i], points[i+1]], fill=c_line, width=2)

            # Highlight current rightmost price point
            last_pt = points[-1]
            draw.ellipse([last_pt[0]-2, last_pt[1]-2, last_pt[0]+2, last_pt[1]+2], fill=(255, 255, 255), outline=c_line)

        # 24H High & Low
        h_val = page.sparkline_high or "N/A"
        l_val = page.sparkline_low or "N/A"
        draw.text((8, 91), f"24H H {h_val}  L {l_val}", fill=(130, 150, 175), font=fonts["reset"])

    # PATH E2: CRYPTO OVERVIEW TABLE (5 ASSETS ON 128px DISPLAY)
    elif p_id == "crypto":
        assets = page.crypto_assets or []
        for idx, a in enumerate(assets[:5]):
            ry = 26 + idx * 15
            # Symbol
            draw.text((8, ry), a.symbol, fill=(245, 250, 255), font=fonts["label"])
            # Compact Price
            p_str = a.formatted_compact_price
            draw.text((44, ry), p_str, fill=(200, 215, 230), font=fonts["label"])
            # 24H Change
            chg_c = (50, 230, 140) if a.change_24h_pct >= 0 else (245, 80, 80)
            chg_str = f"{a.change_24h_pct:+.1f}%"
            cbox = fonts["label"].getbbox(chg_str)
            cw = cbox[2] - cbox[0]
            draw.text((120 - cw, ry), chg_str, fill=chg_c, font=fonts["label"])
            if idx < 4:
                draw.line([(8, ry + 14), (120, ry + 14)], fill=(18, 26, 40), width=1)

    # PATH E3: US EQUITIES (TOP 5 ON 128px DISPLAY)
    elif p_id in ("stocks_market_cap", "stocks_volatile", "stocks"):
        quotes = page.stocks_data or []
        for idx, q in enumerate(quotes[:5]):
            ry = 26 + idx * 15
            rank_str = f"{idx+1}"
            draw.text((8, ry), rank_str, fill=(100, 120, 145), font=fonts["reset"])
            draw.text((18, ry), q.symbol, fill=(245, 250, 255), font=fonts["label"])
            
            p_str = f"${q.price:.1f}" if q.price < 1000 else f"${q.price:.0f}"
            draw.text((54, ry), p_str, fill=(190, 205, 220), font=fonts["reset"])
            
            if p_id == "stocks_market_cap" or q.market_cap > 0:
                right_str = q.formatted_market_cap.replace("$", "").replace(" ", "")
                r_col = (245, 175, 50)
            else:
                right_str = f"{q.volatility_pct:.1f}%"
                r_col = (0, 229, 255)

            rbox = fonts["label"].getbbox(right_str)
            rw = rbox[2] - rbox[0]
            draw.text((120 - rw, ry), right_str, fill=r_col, font=fonts["label"])
            if idx < 4:
                draw.line([(8, ry + 14), (120, ry + 14)], fill=(18, 26, 40), width=1)

    # PATH E4: SIGNALS / POLYMARKET PREDICTION ODDS
    elif p_id == "signals":
        signals = page.signals_data or []
        if signals:
            sig = signals[0]
            q_short = sig.question
            if len(q_short) > 18:
                q_short = q_short[:17] + "…"
            draw.text((8, 26), q_short.upper(), fill=(210, 225, 245), font=fonts["label"])

            prob_pct = int(round(sig.yes_probability * 100))
            prob_str = f"{prob_pct}%"
            draw.text((8, 40), prob_str, fill=(56, 239, 125), font=fonts["large"])

            delta = sig.change_24h_pts
            d_arrow = "▲" if delta >= 0 else "▼"
            d_col = (50, 230, 140) if delta >= 0 else (245, 80, 80)
            d_str = f"{d_arrow} {abs(delta):.1f} pts"
            draw.text((62, 44), d_str, fill=d_col, font=fonts["value"])

            draw.line([(8, 64), (120, 64)], fill=(20, 32, 48), width=1)

            draw.text((8, 70), f"VOL: {sig.formatted_volume}", fill=(130, 145, 170), font=fonts["reset"])
            draw.text((8, 84), f"LIQ: {sig.formatted_liquidity}", fill=(130, 145, 170), font=fonts["reset"])

            if len(signals) > 1:
                sig2 = signals[1]
                p2 = int(round(sig2.yes_probability * 100))
                draw.text((8, 100), f"2. {sig2.question[:11]}…", fill=(100, 120, 145), font=fonts["reset"])
                bbox2 = fonts["reset"].getbbox(f"{p2}%")
                w2 = bbox2[2] - bbox2[0]
                draw.text((120 - w2, 100), f"{p2}%", fill=(0, 229, 255), font=fonts["reset"])
        else:
            draw.text((18, 50), "NO SIGNAL DATA", fill=(120, 135, 155), font=fonts["label"])

    # PATH F: AI ACTIVITY PAGE (CODEX, CLAUDE, GEMINI REAL-TIME STATUS)
    elif p_id == "ai_activity":
        items = page.items_list or []
        for idx, it in enumerate(items[:3]):
            ry = 27 + idx * 26
            name = it.get("name", "AGENT")
            working = it.get("working", False)
            elapsed = it.get("elapsed", "")

            # Agent Name
            draw.text((8, ry + 1), name, fill=(215, 225, 240), font=fonts["label"])

            # Working status
            if working:
                dot_c = (50, 230, 140)
                stat_c = (50, 230, 140)
                stat_text = "WORKING"
            else:
                dot_c = (100, 115, 135)
                stat_c = (100, 115, 135)
                stat_text = "IDLE"

            sbox = fonts["label"].getbbox(stat_text)
            sw = sbox[2] - sbox[0]
            draw.ellipse([118 - sw - 7, ry + 5, 118 - sw - 3, ry + 9], fill=dot_c)
            draw.text((120 - sw, ry + 1), stat_text, fill=stat_c, font=fonts["label"])

            # Sub-text on line 2 (elapsed active time)
            if working and elapsed:
                sub_text = f"active {elapsed.lower()}"
                ssbox = fonts["reset"].getbbox(sub_text)
                ssw = ssbox[2] - ssbox[0]
                draw.text((120 - ssw, ry + 13), sub_text, fill=(85, 110, 140), font=fonts["reset"])

            if idx < 2:
                draw.line([(8, ry + 25), (120, ry + 25)], fill=(20, 30, 48), width=1)

    # PATH G: SERVICES PAGE (COMPACT WORKSTATION HEALTH)
    elif p_id == "services":
        items = page.items_list or []
        for idx, it in enumerate(items[:5]):
            ry = 26 + idx * 16
            name = it.get("name", "SERVICE")
            online = it.get("online", False)

            draw.text((8, ry), name, fill=(210, 220, 235), font=fonts["value"])

            # Dot indicator
            if online:
                dot_c = (50, 230, 140)  # Green live
                draw.ellipse([113, ry + 3, 119, ry + 9], fill=dot_c)
            else:
                dot_c = (100, 115, 135) # Gray offline outline
                draw.ellipse([113, ry + 3, 119, ry + 9], fill=(20, 26, 38), outline=dot_c)

    # PATH H: AI PROVIDERS (CLAUDE, CODEX, GEMINI)
    else:
        pm = page.primary_metric
        sm = page.secondary_metric

        # Primary Block (5H, USAGE)
        p_label = pm.label.upper() if pm else "5H"
        draw.text((8, 26), p_label, fill=(140, 155, 175), font=fonts["label"])

        p_val_str = pm.value if pm else "N/A"
        c_pval = get_color_for_pct(pm.pct if pm else None, is_remaining=True)
        pv_bbox = fonts["value"].getbbox(p_val_str)
        pvw = pv_bbox[2] - pv_bbox[0]
        draw.text((120 - pvw, 25), p_val_str, fill=c_pval, font=fonts["value"])

        # Primary Bar
        draw_progress_bar(draw, 8, 41, 112, 7, pm.pct if pm else None, active_color=c_pval)
        p_reset = pm.reset or "RESET N/A"
        draw.text((8, 52), p_reset, fill=(90, 115, 145), font=fonts["reset"])

        # Divider
        draw.line([(8, 66), (120, 66)], fill=(20, 30, 48), width=1)

        # Secondary Block (WEEK)
        s_label = sm.label.upper() if sm else "WEEK"
        draw.text((8, 70), s_label, fill=(140, 155, 175), font=fonts["label"])

        s_val_str = sm.value if sm else "N/A"
        is_stale = "STALE" in page.badge
        c_sval = get_color_for_pct(sm.pct if sm else None, is_stale=is_stale, is_remaining=True)
        sv_bbox = fonts["value"].getbbox(s_val_str)
        svw = sv_bbox[2] - sv_bbox[0]
        draw.text((120 - svw, 69), s_val_str, fill=c_sval, font=fonts["value"])

        # Secondary Bar
        draw_progress_bar(draw, 8, 85, 112, 7, sm.pct if sm else None, active_color=c_sval)
        s_reset = sm.reset or "RESET N/A"
        draw.text((8, 96), s_reset, fill=(90, 115, 145), font=fonts["reset"])

    # =========================================================================
    # FOOTER BAR & PAGINATION
    # =========================================================================
    draw.line([(8, 107), (120, 107)], fill=(20, 30, 48), width=1)

    # Footer Left
    f_left = page.footer_left or page.badge
    draw.ellipse([8, 114, 13, 119], fill=badge_dot_c)
    draw.text((17, 111), f_left[:14], fill=(90, 110, 135), font=fonts["reset"])

    # Footer Right (Pagination)
    if total_pages > 1:
        page_str = f"{page_num}/{total_pages}"
        pb_bbox = fonts["reset"].getbbox(page_str)
        pbw = pb_bbox[2] - pb_bbox[0]
        draw.text((120 - pbw, 111), page_str, fill=(75, 95, 125), font=fonts["reset"])

    return img
