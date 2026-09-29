"""
Divoom Ditoo / Ditoo Plus 16x16 Dedicated Pixel Renderer.
Designed specifically for the physical 16x16 RGB LED matrix.
No downscaling from 128x128. Built with custom 3x5 and 4x7 bitmap fonts,
crisp 16x16 icons, multi-frame flip sequences, and smooth scrolling buffers.
"""
from __future__ import annotations

import math
from typing import Dict, Tuple, List, Optional
from PIL import Image, ImageDraw

# ==============================================================================
# COLOR PALETTE TOKENS
# ==============================================================================
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GOLD = (247, 147, 26)       # Bitcoin Brand Gold #F7931A
COLOR_GOLD_DARK = (184, 101, 4)   # Bitcoin Border
COLOR_GOLD_LIGHT = (255, 206, 120)
COLOR_GREEN = (0, 230, 118)       # Electric Bullish Green #00E676
COLOR_RED = (255, 61, 87)         # Vivid Bearish Red #FF3D57
COLOR_CYAN = (0, 229, 255)        # Clean Tech Cyan #00E5FF
COLOR_GRAY = (110, 118, 129)      # Muted Gray
COLOR_DARK_GRAY = (33, 38, 45)

# Brand Accent Colors for US Equities
BRAND_COLORS = {
    "NVDA": (118, 185, 0),     # NVIDIA Lime Green #76B900
    "TSLA": (232, 33, 39),     # Tesla Red #E82127
    "AAPL": (162, 170, 173),   # Apple Silver #A2AAAD
    "MSFT": (0, 164, 239),     # Microsoft Sky Blue #00A4EF
    "META": (6, 104, 225),     # Meta Blue #0668E1
    "AMD": (237, 28, 36),
    "COIN": (0, 82, 255),
    "AMZN": (255, 153, 0),
    "GOOGL": (66, 133, 244),
}

# ==============================================================================
# FONT_3x5: 3x5 Bitmap Font (Numbers, Letters, Symbols)
# ==============================================================================
FONT_3x5: Dict[str, Tuple[str, ...]] = {
    '0': ("###", "# #", "# #", "# #", "###"),
    '1': (" # ", "## ", " # ", " # ", "###"),
    '2': ("###", "  #", "###", "#  ", "###"),
    '3': ("###", "  #", "###", "  #", "###"),
    '4': ("# #", "# #", "###", "  #", "  #"),
    '5': ("###", "#  ", "###", "  #", "###"),
    '6': ("###", "#  ", "###", "# #", "###"),
    '7': ("###", "  #", "  #", "  #", "  #"),
    '8': ("###", "# #", "###", "# #", "###"),
    '9': ("###", "# #", "###", "  #", "###"),
    'A': ("###", "# #", "###", "# #", "# #"),
    'B': ("## ", "# #", "## ", "# #", "## "),
    'C': ("###", "#  ", "#  ", "#  ", "###"),
    'D': ("## ", "# #", "# #", "# #", "## "),
    'E': ("###", "#  ", "## ", "#  ", "###"),
    'F': ("###", "#  ", "## ", "#  ", "#  "),
    'G': ("###", "#  ", "# #", "# #", "###"),
    'H': ("# #", "# #", "###", "# #", "# #"),
    'I': ("###", " # ", " # ", " # ", "###"),
    'J': ("  #", "  #", "  #", "# #", "###"),
    'K': ("# #", "## ", "#  ", "## ", "# #"),
    'L': ("#  ", "#  ", "#  ", "#  ", "###"),
    'M': ("# #", "###", "# #", "# #", "# #"),
    'N': ("###", "# #", "# #", "# #", "# #"),
    'O': ("###", "# #", "# #", "# #", "###"),
    'P': ("###", "# #", "###", "#  ", "#  "),
    'Q': ("###", "# #", "# #", "###", "  #"),
    'R': ("###", "# #", "## ", "# #", "# #"),
    'S': ("###", "#  ", "###", "  #", "###"),
    'T': ("###", " # ", " # ", " # ", " # "),
    'U': ("# #", "# #", "# #", "# #", "###"),
    'V': ("# #", "# #", "# #", " # ", " # "),
    'W': ("# #", "# #", "# #", "###", "# #"),
    'X': ("# #", "# #", " # ", "# #", "# #"),
    'Y': ("# #", "# #", "###", "  #", "###"),
    'Z': ("###", "  #", " # ", "#  ", "###"),
    '.': (" ", " ", " ", " ", "#"),
    ',': (" ", " ", " ", "#", "#"),
    '$': ("###", "#  ", "###", "  #", "###"),
    '%': ("# #", "  #", " # ", "#  ", "# #"),
    '+': ("   ", " # ", "###", " # ", "   "),
    '-': ("   ", "   ", "###", "   ", "   "),
    '▲': (" # ", "###", "   ", "   ", "   "),
    '▼': ("   ", "   ", "###", " # ", "   "),
    ' ': (" ", " ", " ", " ", " "),
}

# ==============================================================================
# 16x16 FULL-CANVAS BITCOIN ICON
# ==============================================================================
# Distinct 16x16 pixel art Bitcoin coin:
# . = background (black)
# B = dark gold border
# G = bright gold face
# W = white 'B' letter
# L = gold highlight
BTC_ICON_16x16 = [
    "....BBBBBBBB....",
    "..BBGGGGGGGGBB..",
    ".BGGGGGGGGGGGGB.",
    ".BGGGLWLLWLLGGB.",
    "BGGGLWWWWWWLGGBB",
    "BGGGLWLLLLWLGGBB",
    "BGGGLWWWWWLLGGBB",
    "BGGGLWLLLLWLGGBB",
    "BGGGLWWWWWWLGGBB",
    "BGGGLWLLWLLGGBBB",
    "BGGGGLLLLLLLGGBB",
    ".BGGGGGGGGGGGGB.",
    ".BGGGGGGGGGGGGB.",
    "..BBGGGGGGGGBB..",
    "....BBBBBBBB....",
    "................",
]

COLOR_MAP_BTC = {
    '.': COLOR_BLACK,
    'B': COLOR_GOLD_DARK,
    'G': COLOR_GOLD,
    'L': COLOR_GOLD_LIGHT,
    'W': COLOR_WHITE,
}


def draw_bitmap_16x16(img: Image.Image, lines: List[str], color_map: Dict[str, Tuple[int, int, int]]) -> None:
    """Draw a 16x16 ASCII art template onto a PIL image."""
    pixels = img.load()
    for y, line in enumerate(lines[:16]):
        for x, ch in enumerate(line[:16]):
            if ch in color_map:
                pixels[x, y] = color_map[ch]


def draw_text(
    img: Image.Image,
    text: str,
    x: int,
    y: int,
    color: Tuple[int, int, int] = COLOR_WHITE,
    font: Dict[str, Tuple[str, ...]] = FONT_3x5,
    spacing: int = 1,
) -> int:
    """Draw text onto an image using bitmap font. Returns total width drawn."""
    pixels = img.load()
    cur_x = x
    w, h = img.size

    for ch in text.upper():
        glyph = font.get(ch, font.get(' ', (" ", " ", " ", " ", " ")))
        char_w = len(glyph[0])
        char_h = len(glyph)
        for row_idx, row in enumerate(glyph):
            draw_y = y + row_idx
            if 0 <= draw_y < h:
                for col_idx, col in enumerate(row):
                    draw_x = cur_x + col_idx
                    if col == '#' and 0 <= draw_x < w:
                        pixels[draw_x, draw_y] = color
        cur_x += char_w + spacing

    return cur_x - x - spacing


def measure_text(text: str, font: Dict[str, Tuple[str, ...]] = FONT_3x5, spacing: int = 1) -> int:
    """Calculate pixel width of rendered text."""
    if not text:
        return 0
    total_w = 0
    for ch in text.upper():
        glyph = font.get(ch, font.get(' ', (" ", " ", " ", " ", " ")))
        total_w += len(glyph[0]) + spacing
    return max(0, total_w - spacing)


# ==============================================================================
# PRICE FORMATTERS
# ==============================================================================
def format_abbreviated_price(val: float) -> str:
    """Compact price formatting for 16x16 display."""
    if val >= 10000:
        return f"${int(round(val / 1000))}K"
    elif val >= 1000:
        return f"${val/1000:.1f}K"
    elif val >= 100:
        return f"${int(round(val))}"
    elif val >= 10:
        return f"${val:.1f}"
    elif val >= 1:
        return f"${val:.2f}"
    else:
        return f"${val:.3f}"


def format_delta_pct(pct: float) -> Tuple[str, Tuple[int, int, int]]:
    """Format price change percentage and return text with bull/bear color."""
    sign = "+" if pct >= 0 else ""
    text = f"{sign}{pct:.1f}%"
    color = COLOR_GREEN if pct >= 0 else COLOR_RED
    return text, color


# ==============================================================================
# BITCOIN RENDERERS (16x16)
# ==============================================================================
class Btc16Renderer:
    """Generates 16x16 frame sequences for Bitcoin."""

    @staticmethod
    def render_icon_frame() -> Image.Image:
        """Frame 1: Crisp 16x16 Bitcoin coin pixel art."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        draw_bitmap_16x16(img, BTC_ICON_16x16, COLOR_MAP_BTC)
        return img

    @staticmethod
    def render_price_frame(price: float) -> Image.Image:
        """Frame 2: Price frame (e.g. '$68K' or '$68.4K')."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        # Top banner: "BTC" (gold)
        draw_text(img, "BTC", x=2, y=2, color=COLOR_GOLD)
        # Horizontal divider line (dark gold)
        draw = ImageDraw.Draw(img)
        draw.line([(1, 8), (14, 8)], fill=COLOR_GOLD_DARK)
        # Bottom: Abbreviated price (cyan/white)
        price_str = format_abbreviated_price(price)
        w = measure_text(price_str)
        x = max(0, (16 - w) // 2)
        draw_text(img, price_str, x=x, y=10, color=COLOR_WHITE)
        return img

    @staticmethod
    def render_change_frame(pct: float) -> Image.Image:
        """Frame 3: 24H Price Change with direction arrow (▲ +2.4% / ▼ -1.8%)."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        delta_str, col = format_delta_pct(pct)
        # Big Arrow in top center
        arrow_char = '▲' if pct >= 0 else '▼'
        arrow_y = 2 if pct >= 0 else 3
        draw_text(img, arrow_char, x=6, y=arrow_y, color=col)
        # Percentage below
        w = measure_text(delta_str)
        x = max(0, (16 - w) // 2)
        draw_text(img, delta_str, x=x, y=9, color=col)
        return img

    @staticmethod
    def render_split_frame(price: float, pct: float) -> Image.Image:
        """Compact single-frame view: mini BTC badge + price + delta indicator."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        # Top line: "BTC" in gold
        draw_text(img, "BTC", x=1, y=1, color=COLOR_GOLD)
        # Top right: mini direction dot/arrow
        col = COLOR_GREEN if pct >= 0 else COLOR_RED
        img.putpixel((14, 2), col)
        img.putpixel((13, 3), col)
        img.putpixel((14, 3), col)
        # Bottom price
        price_str = format_abbreviated_price(price)
        w = measure_text(price_str)
        draw_text(img, price_str, x=max(0, (16 - w) // 2), y=9, color=COLOR_WHITE)
        return img

    @classmethod
    def render_cycle_frames(cls, price: float, pct: float) -> List[Image.Image]:
        """Returns the full 3-frame flip sequence for Bitcoin."""
        return [
            cls.render_icon_frame(),
            cls.render_price_frame(price),
            cls.render_change_frame(pct),
        ]


# ==============================================================================
# STOCK RENDERERS (16x16)
# ==============================================================================
class Stock16Renderer:
    """Generates 16x16 frame sequences for configurable stock tickers."""

    @staticmethod
    def render_symbol_frame(symbol: str) -> Image.Image:
        """Frame 1: Ticker badge with brand color accent."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(symbol.upper(), COLOR_CYAN)
        # Top accent bar
        draw = ImageDraw.Draw(img)
        draw.line([(2, 2), (13, 2)], fill=brand_col)
        # Centered symbol
        w = measure_text(symbol)
        x = max(0, (16 - w) // 2)
        draw_text(img, symbol, x=x, y=5, color=COLOR_WHITE)
        # Bottom accent bar
        draw.line([(2, 13), (13, 13)], fill=brand_col)
        return img

    @staticmethod
    def render_price_frame(symbol: str, price: float) -> Image.Image:
        """Frame 2: Stock price frame."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(symbol.upper(), COLOR_CYAN)
        # Mini ticker on top
        w_sym = measure_text(symbol)
        draw_text(img, symbol, x=max(0, (16 - w_sym) // 2), y=1, color=brand_col)
        # Divider line
        draw = ImageDraw.Draw(img)
        draw.line([(1, 7), (14, 7)], fill=COLOR_DARK_GRAY)
        # Price on bottom
        price_str = format_abbreviated_price(price)
        w_p = measure_text(price_str)
        draw_text(img, price_str, x=max(0, (16 - w_p) // 2), y=9, color=COLOR_WHITE)
        return img

    @staticmethod
    def render_change_frame(pct: float) -> Image.Image:
        """Frame 3: Daily delta with arrow."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        delta_str, col = format_delta_pct(pct)
        arrow_char = '▲' if pct >= 0 else '▼'
        arrow_y = 2 if pct >= 0 else 3
        draw_text(img, arrow_char, x=6, y=arrow_y, color=col)
        w = measure_text(delta_str)
        draw_text(img, delta_str, x=max(0, (16 - w) // 2), y=9, color=col)
        return img

    @staticmethod
    def render_split_frame(symbol: str, price: float, pct: float) -> Image.Image:
        """Split view: Ticker on top, price on bottom with colored trend dot."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(symbol.upper(), COLOR_CYAN)
        # Top symbol
        draw_text(img, symbol, x=1, y=1, color=brand_col)
        # Trend dot in top right
        col = COLOR_GREEN if pct >= 0 else COLOR_RED
        img.putpixel((14, 2), col)
        # Bottom price
        price_str = format_abbreviated_price(price)
        w_p = measure_text(price_str)
        draw_text(img, price_str, x=max(0, (16 - w_p) // 2), y=9, color=COLOR_WHITE)
        return img

    @classmethod
    def render_cycle_frames(cls, symbol: str, price: float, pct: float) -> List[Image.Image]:
        """Returns the full 3-frame flip sequence for a stock."""
        return [
            cls.render_symbol_frame(symbol),
            cls.render_price_frame(symbol, price),
            cls.render_change_frame(pct),
        ]


# ==============================================================================
# HORIZONTAL SCROLLER
# ==============================================================================
def render_scrolling_text_strip(
    text: str,
    color: Tuple[int, int, int] = COLOR_WHITE,
    bg_color: Tuple[int, int, int] = COLOR_BLACK,
    y: int = 5,
) -> Image.Image:
    """Render a wide image containing text for horizontal marquee scrolling."""
    text_w = measure_text(text)
    total_w = text_w + 32 # 16px lead-in + 16px trail
    img = Image.new("RGB", (total_w, 16), bg_color)
    draw_text(img, text, x=16, y=y, color=color)
    return img


def get_scroll_frame(strip: Image.Image, offset_x: int) -> Image.Image:
    """Extract a 16x16 window from the scroll strip at offset_x."""
    w, _ = strip.size
    ox = offset_x % max(1, w - 16)
    return strip.crop((ox, 0, ox + 16, 16))


# ==============================================================================
# UPSCALE PREVIEWS (Nearest Neighbor for Sharp Pixel Display)
# ==============================================================================
def upscale_preview(img: Image.Image, scale: int = 16) -> Image.Image:
    """Upscale 16x16 image to high-DPI crisp pixel art preview (e.g. 256x256)."""
    return img.resize((16 * scale, 16 * scale), Image.Resampling.NEAREST)
