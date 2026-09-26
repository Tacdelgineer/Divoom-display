#!/usr/bin/env python3
"""
Generate professional retro-styled brand assets for AI Desk Dashboard:
- assets/icon.png (512x512)
- assets/logo.png (800x260)
- assets/banner.png (1280x420)

Design Aesthetic:
- Dark retro terminal / pixel dashboard motif
- MiniToo-inspired monitor with screen bezel and physical knob
- Glowing cyan (#00F5D4) + phosphor green (#10B981 / #32E68C)
- Subtle CRT scanlines and clean geometric pixel layout
- Readable at small GitHub avatar / icon sizes
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    # Try Windows system fonts for clean geometric/monospace rendering
    font_paths = [
        "C:\\Windows\\Fonts\\consola.ttf" if not bold else "C:\\Windows\\Fonts\\consolab.ttf",
        "C:\\Windows\\Fonts\\seguiemj.ttf",
        "C:\\Windows\\Fonts\\arial.ttf" if not bold else "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_retro_monitor(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, scale: float = 1.0):
    """Draws a crisp retro CRT/MiniToo-style monitor with screen, glowing widgets, and knob."""
    # Outer bezel / casing
    bezel_radius = int(14 * scale)
    c_casing = (18, 24, 38)
    c_casing_hi = (38, 50, 75)
    c_casing_shadow = (10, 14, 22)

    # Base stand / feet
    stand_w = int(w * 0.45)
    stand_h = int(12 * scale)
    stand_x = x + (w - stand_w) // 2
    stand_y = y + h - int(2 * scale)
    draw.rounded_rectangle(
        [stand_x, stand_y, stand_x + stand_w, stand_y + stand_h],
        radius=int(4 * scale),
        fill=(14, 18, 28),
        outline=c_casing_hi,
        width=max(1, int(1.5 * scale))
    )

    # Main monitor body
    body_h = h - int(10 * scale)
    draw.rounded_rectangle(
        [x, y, x + w, y + body_h],
        radius=bezel_radius,
        fill=c_casing,
        outline=c_casing_hi,
        width=max(1, int(2 * scale))
    )

    # Inner bezel inset
    inset_m = int(10 * scale)
    inner_w = w - (inset_m * 2)
    inner_h = body_h - (inset_m * 2)
    inner_x = x + inset_m
    inner_y = y + inset_m

    # Right control strip (knob area, MiniToo motif)
    strip_w = int(28 * scale)
    screen_w = inner_w - strip_w - int(6 * scale)
    screen_h = inner_h
    screen_x = inner_x
    screen_y = inner_y

    # Screen background (dark phosphor black)
    c_screen_bg = (6, 10, 18)
    draw.rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=int(8 * scale),
        fill=c_screen_bg,
        outline=(24, 34, 52),
        width=max(1, int(1.5 * scale))
    )

    # MiniToo physical knob on right panel
    knob_cx = inner_x + inner_w - (strip_w // 2)
    knob_cy = inner_y + int(screen_h * 0.35)
    knob_r = int(10 * scale)
    draw.ellipse(
        [knob_cx - knob_r, knob_cy - knob_r, knob_cx + knob_r, knob_cy + knob_r],
        fill=(28, 38, 58),
        outline=(0, 245, 212, 180),
        width=max(1, int(1.5 * scale))
    )
    # Knob notch
    draw.line(
        [knob_cx, knob_cy - knob_r + int(2 * scale), knob_cx, knob_cy - int(2 * scale)],
        fill=(0, 245, 212),
        width=max(1, int(2 * scale))
    )

    # Side button 1 (channel / power)
    btn_r = int(5 * scale)
    btn_cy = inner_y + int(screen_h * 0.7)
    draw.ellipse(
        [knob_cx - btn_r, btn_cy - btn_r, knob_cx + btn_r, btn_cy + btn_r],
        fill=(24, 32, 48),
        outline=(50, 230, 140),
        width=max(1, int(1.5 * scale))
    )

    # Status LED on casing
    led_x = screen_x + int(8 * scale)
    led_y = y + body_h - int(6 * scale)
    draw.ellipse(
        [led_x - int(2 * scale), led_y - int(2 * scale), led_x + int(2 * scale), led_y + int(2 * scale)],
        fill=(0, 245, 212)
    )

    # --- Screen Graphics (Dashboard Widgets) ---
    pad = int(8 * scale)
    sx = screen_x + pad
    sy = screen_y + pad
    sw = screen_w - (pad * 2)
    sh = screen_h - (pad * 2)

    # Header bar on screen
    header_h = int(12 * scale)
    draw.rectangle([sx, sy, sx + sw, sy + header_h], fill=(12, 20, 34))
    # Glowing dots (cyan, green)
    draw.rectangle([sx + int(3*scale), sy + int(3*scale), sx + int(7*scale), sy + int(7*scale)], fill=(0, 245, 212))
    draw.rectangle([sx + int(10*scale), sy + int(3*scale), sx + int(14*scale), sy + int(7*scale)], fill=(50, 230, 140))
    # Mini title bar text line
    draw.rectangle([sx + int(18*scale), sy + int(4*scale), sx + int(45*scale), sy + int(7*scale)], fill=(120, 140, 170))

    # Top Metric Box (AI Quota % Left)
    m_top = sy + header_h + int(6 * scale)
    m_h = int(32 * scale)
    draw.rectangle([sx, m_top, sx + sw, m_top + m_h], fill=(10, 16, 28), outline=(22, 34, 52), width=1)
    # Value bar (78% left)
    bar_w = int(sw * 0.78)
    draw.rectangle([sx + int(4*scale), m_top + int(18*scale), sx + int(4*scale) + bar_w, m_top + int(24*scale)], fill=(0, 245, 212))
    # Subdued label block
    draw.rectangle([sx + int(4*scale), m_top + int(5*scale), sx + int(35*scale), m_top + int(10*scale)], fill=(50, 230, 140))
    draw.rectangle([sx + sw - int(32*scale), m_top + int(5*scale), sx + sw - int(4*scale), m_top + int(11*scale)], fill=(0, 245, 212))

    # Sparkline Waveform (BTC / GPU graph)
    g_top = m_top + m_h + int(6 * scale)
    g_h = sh - (g_top - sy) - int(2 * scale)
    draw.rectangle([sx, g_top, sx + sw, g_top + g_h], fill=(8, 14, 24), outline=(20, 30, 48), width=1)

    # Plot wave points
    pts = [
        0.3, 0.45, 0.38, 0.55, 0.50, 0.68, 0.62, 0.75,
        0.70, 0.82, 0.65, 0.88, 0.78, 0.92, 0.85, 0.95
    ]
    step_w = sw / (len(pts) - 1)
    line_coords = []
    for i, val in enumerate(pts):
        px = sx + (i * step_w)
        py = g_top + g_h - (val * (g_h - int(6 * scale))) - int(3 * scale)
        line_coords.append((px, py))

    # Sparkline glow & stroke
    for i in range(len(line_coords) - 1):
        x1, y1 = line_coords[i]
        x2, y2 = line_coords[i+1]
        draw.line([x1, y1, x2, y2], fill=(50, 230, 140), width=max(1, int(2 * scale)))
        # Fill under graph lightly
        draw.line([x2, y2, x2, g_top + g_h - 1], fill=(16, 40, 36), width=max(1, int(1 * scale)))

    # CRT Scanline effect (subtle horizontal lines across screen)
    for scan_y in range(screen_y + 1, screen_y + screen_h, max(2, int(3 * scale))):
        draw.line([screen_x + 1, scan_y, screen_x + screen_w - 1, scan_y], fill=(0, 0, 0, 60))


def generate_icon(out_path: str):
    """512x512 App & GitHub avatar icon."""
    size = 512
    img = Image.new("RGBA", (size, size), (10, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Subtle background radial-style glow
    center = size // 2
    for r in range(240, 120, -15):
        alpha = int((1.0 - (r / 240.0)) * 35)
        draw.ellipse([center - r, center - r, center + r, center + r], fill=(0, 245, 212, alpha))

    # Outer retro container border
    draw.rounded_rectangle([16, 16, size - 16, size - 16], radius=32, outline=(30, 42, 64), width=3)

    # Draw Monitor in center
    mw = 380
    mh = 320
    mx = (size - mw) // 2
    my = (size - mh) // 2 - 10
    draw_retro_monitor(draw, mx, my, mw, mh, scale=2.3)

    # Bottom badge / title text
    f_badge = get_font(24, bold=True)
    text = "AI DESK DASHBOARD"
    bbox = f_badge.getbbox(text)
    tw = bbox[2] - bbox[0]
    tx = (size - tw) // 2
    draw.text((tx, size - 58), text, fill=(0, 245, 212), font=f_badge)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def generate_logo(out_path: str):
    """800x260 Horizontal brand logo."""
    w, h = 800, 260
    img = Image.new("RGBA", (w, h), (10, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # Left: Monitor icon
    mw, mh = 220, 185
    mx, my = 35, (h - mh) // 2
    draw_retro_monitor(draw, mx, my, mw, mh, scale=1.35)

    # Right: Text Branding
    f_title = get_font(38, bold=True)
    f_sub = get_font(16, bold=False)
    f_tag = get_font(13, bold=True)

    text_x = 290
    text_y = 52

    # Status tag
    tag_text = "RETRO PHYSICAL + DESKTOP AGENT MONITOR"
    draw.rounded_rectangle([text_x, text_y, text_x + 360, text_y + 24], radius=4, fill=(16, 32, 48), outline=(0, 245, 212, 120))
    draw.text((text_x + 10, text_y + 4), tag_text, fill=(0, 245, 212), font=f_tag)

    # Main Title
    draw.text((text_x, text_y + 36), "AI Desk Dashboard", fill=(240, 245, 252), font=f_title)

    # Subtitle / description
    desc = "AI Quotas · System Stats · Agents · Markets · Remote Nodes"
    draw.text((text_x, text_y + 92), desc, fill=(130, 150, 175), font=f_sub)

    # Badges line
    badges = [("CODEX", (50, 230, 140)), ("GEMINI", (0, 245, 212)), ("DGX", (118, 185, 0)), ("MINITOO", (0, 229, 255))]
    bx = text_x
    by = text_y + 130
    for b_label, b_color in badges:
        draw.rounded_rectangle([bx, by, bx + 70, by + 22], radius=4, fill=(18, 24, 36), outline=b_color, width=1)
        draw.text((bx + 8, by + 3), b_label, fill=b_color, font=f_tag)
        bx += 78

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


def generate_banner(out_path: str):
    """1280x420 Rich README Header Banner."""
    w, h = 1280, 420
    img = Image.new("RGBA", (w, h), (8, 12, 20, 255))
    draw = ImageDraw.Draw(img)

    # Background subtle terminal grid lines
    grid_spacing = 32
    for gx in range(0, w, grid_spacing):
        draw.line([gx, 0, gx, h], fill=(14, 20, 32, 100), width=1)
    for gy in range(0, h, grid_spacing):
        draw.line([0, gy, w, gy], fill=(14, 20, 32, 100), width=1)

    # Left: Hero Monitor Display
    mw, mh = 360, 300
    mx, my = 60, (h - mh) // 2
    draw_retro_monitor(draw, mx, my, mw, mh, scale=2.15)

    # Right: Hero Title, Pitch, & Status Badges
    f_badge = get_font(14, bold=True)
    f_hero = get_font(52, bold=True)
    f_pitch = get_font(20, bold=False)
    f_chip = get_font(13, bold=True)

    tx = 470
    ty = 60

    # Glowing terminal tag
    draw.rounded_rectangle([tx, ty, tx + 310, ty + 28], radius=6, fill=(12, 34, 46), outline=(0, 245, 212), width=1)
    draw.text((tx + 12, ty + 5), "● OPEN SOURCE HARDWARE & DESKTOP TELEMETRY", fill=(0, 245, 212), font=f_badge)

    # Main Hero Title
    draw.text((tx, ty + 42), "AI Desk Dashboard", fill=(245, 250, 255), font=f_hero)

    # One-line Pitch per milestone requirements
    pitch_line1 = "A retro desktop + physical desk dashboard for AI usage, system stats,"
    pitch_line2 = "agents, markets, and remote machines."
    draw.text((tx, ty + 115), pitch_line1, fill=(160, 180, 205), font=f_pitch)
    draw.text((tx, ty + 145), pitch_line2, fill=(160, 180, 205), font=f_pitch)

    # Status / Feature Badges
    chips = [
        ("CODEX % LEFT", (50, 230, 140)),
        ("GEMINI QUOTA", (90, 165, 255)),
        ("RTX & DGX GPU", (118, 185, 0)),
        ("BTC SPARKLINE", (247, 147, 26)),
        ("MINITOO HARDWARE", (0, 229, 255)),
        ("KNOB CONTROL", (185, 140, 255)),
    ]
    cx = tx
    cy = ty + 195
    row_count = 0
    for chip_text, chip_color in chips:
        c_w = int(len(chip_text) * 8.2) + 20
        if cx + c_w > w - 40:
            cx = tx
            cy += 34
        draw.rounded_rectangle([cx, cy, cx + c_w, cy + 24], radius=4, fill=(16, 24, 38), outline=chip_color, width=1)
        draw.text((cx + 10, cy + 4), chip_text, fill=chip_color, font=f_chip)
        cx += c_w + 10

    # Bottom Terminal Prompt Footer
    draw.line([tx, h - 60, w - 60, h - 60], fill=(24, 36, 56), width=1)
    draw.text((tx, h - 45), "> python dashboard_app.py --detect-hardware", fill=(0, 245, 212), font=f_badge)
    draw.text((w - 240, h - 45), "v0.1.0 PREVIEW", fill=(100, 120, 150), font=f_badge)

    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    generate_icon("assets/icon.png")
    generate_logo("assets/logo.png")
    generate_banner("assets/banner.png")
