"""
Divoom Ditoo / Ditoo Plus 16x16 Dedicated Pixel Renderer.
Designed specifically for the physical 16x16 RGB LED matrix.
No downscaling from 128x128. Built with custom 3x5 bitmap font,
crisp 16x16 icons for Crypto (BTC, ETH, SOL, DOGE, PEPE) and US Equities (NVDA, TSLA, AAPL, etc.),
multi-frame flip sequences (Icon -> Price -> 24h Change), and nearest-neighbor scaling.
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

# Crypto Brand Accent Colors
CRYPTO_BRAND_COLORS = {
    "BTC": COLOR_GOLD,
    "ETH": (98, 126, 234),        # Ethereum Blue #627EEA
    "SOL": (20, 241, 149),        # Solana Teal #14F195
    "DOGE": (194, 166, 51),       # Dogecoin Gold #C2A633
    "PEPE": (72, 199, 116),       # Pepe Green #48C774
}

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
# 16x16 FULL-CANVAS CRYPTO ICONS
# ==============================================================================
# BTC: Bitcoin Gold Coin with 'B'
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

# ETH: Ethereum Crystal Diamond
ETH_ICON_16x16 = [
    ".......WW.......",
    "......WLLW......",
    ".....WLLLDW.....",
    "....WLLLLDDW....",
    "...WLLLLLDDDW...",
    "..WLLLLLLDDDDW..",
    ".WLLLLLLLDDDDDW.",
    "WWWWWWWWWWWWWWWW",
    ".WLLLLLLLDDDDDW.",
    "..WLLLLLLDDDDW..",
    "...WLLLLLDDDW...",
    "....WLLLLDDW....",
    ".....WLLLDW.....",
    "......WLLW......",
    ".......WW.......",
    "................",
]
COLOR_MAP_ETH = {
    '.': COLOR_BLACK,
    'W': COLOR_WHITE,
    'L': (160, 195, 255),       # Light facet
    'D': (98, 126, 234),        # Dark facet (Ethereum blue)
}

# SOL: Solana 3 Slanted Gradient Bars
SOL_ICON_16x16 = [
    "................",
    "................",
    "...TTTTTTTTMM...",
    "....TTTTTTTTMM..",
    "................",
    "....MMTTTTTTTT..",
    "...MMTTTTTTTT...",
    "................",
    "...TTTTTTTTMM...",
    "....TTTTTTTTMM..",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
COLOR_MAP_SOL = {
    '.': COLOR_BLACK,
    'T': (20, 241, 149),     # Solana Teal
    'M': (220, 31, 255),     # Solana Magenta
}

# DOGE: Golden Dogecoin with 'Ð'
DOGE_ICON_16x16 = [
    "....BBBBBBBB....",
    "..BBGGGGGGGGBB..",
    ".BGGGGGGGGGGGGB.",
    ".BGGGLWWWWLLGGB.",
    "BGGGLWWLLWWLGGBB",
    "BGGGLWWLLLLLGGBB",
    "BGGGLWWWWWWLGGBB",
    "BGGGLWWWWWWLGGBB",
    "BGGGLWWLLLLLGGBB",
    "BGGGLWWLLWWLGGBB",
    "BGGGLWWWWLLLGGBB",
    ".BGGGGLLLLGGGGB.",
    ".BGGGGGGGGGGGGB.",
    "..BBGGGGGGGGBB..",
    "....BBBBBBBB....",
    "................",
]
COLOR_MAP_DOGE = {
    '.': COLOR_BLACK,
    'B': (140, 115, 25),
    'G': (194, 166, 51),     # Doge Gold
    'L': (255, 225, 110),
    'W': COLOR_WHITE,
}

# PEPE: Pepe the Frog Face
PEPE_ICON_16x16 = [
    "................",
    "...GG......GG...",
    "..GWWG....GWWG..",
    "..GWKG....GWKG..",
    ".GGWWGGGGGGWWGG.",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    ".GLLLLLLLLLLLLG.",
    ".GLRRRRRRRRRRLG.",
    "..GLLLLLLLLLLG..",
    "...GGGGGGGGGG...",
    ".....GGGGGG.....",
    "................",
    "................",
    "................",
]
COLOR_MAP_PEPE = {
    '.': COLOR_BLACK,
    'G': (72, 199, 116),     # Pepe Green
    'W': COLOR_WHITE,
    'K': COLOR_BLACK,
    'L': (45, 130, 75),      # Lips
    'R': (245, 80, 80),      # Mouth
}

CRYPTO_ICONS = {
    "BTC": (BTC_ICON_16x16, COLOR_MAP_BTC),
    "ETH": (ETH_ICON_16x16, COLOR_MAP_ETH),
    "SOL": (SOL_ICON_16x16, COLOR_MAP_SOL),
    "DOGE": (DOGE_ICON_16x16, COLOR_MAP_DOGE),
    "PEPE": (PEPE_ICON_16x16, COLOR_MAP_PEPE),
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
    """Draw text onto an image using bitmap font with tight punctuation spacing. Returns total width drawn."""
    pixels = img.load()
    cur_x = x
    w, h = img.size
    t = text.upper()

    for i, ch in enumerate(t):
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
        sp = spacing
        if ch in ('.', ',') or (i + 1 < len(t) and t[i + 1] in ('.', ',')):
            sp = 0
        cur_x += char_w + sp

    last_sp = 0 if (t and t[-1] in ('.', ',')) else spacing
    return cur_x - x - last_sp


def measure_text(text: str, font: Dict[str, Tuple[str, ...]] = FONT_3x5, spacing: int = 1) -> int:
    """Calculate pixel width of rendered text with punctuation kerning."""
    if not text:
        return 0
    total = 0
    t = text.upper()
    for i, ch in enumerate(t):
        glyph = font.get(ch, font.get(' ', (" ", " ", " ", " ", " ")))
        char_w = len(glyph[0])
        sp = spacing
        if ch in ('.', ',') or (i + 1 < len(t) and t[i + 1] in ('.', ',')):
            sp = 0
        total += char_w + sp
    last_sp = 0 if (t and t[-1] in ('.', ',')) else spacing
    return max(0, total - last_sp)


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
    elif val >= 0.01:
        return f"${val:.3f}"
    elif val >= 0.0001:
        return f"$.{int(val*10000):04d}"
    elif val > 0:
        # Micro-pricing for meme tokens (e.g. PEPE $0.0000098 -> 9.8u)
        return f"{val*1e6:.1f}u"
    else:
        return "$0.00"


def format_delta_pct(pct: float) -> Tuple[str, Tuple[int, int, int]]:
    """Format price change percentage and return text with bull/bear color."""
    sign = "+" if pct >= 0 else ""
    text = f"{sign}{pct:.1f}%"
    color = COLOR_GREEN if pct >= 0 else COLOR_RED
    return text, color


# ==============================================================================
# CRYPTO RENDERERS (16x16: BTC, ETH, SOL, DOGE, PEPE)
# ==============================================================================
class Crypto16Renderer:
    """Generates 16x16 frame sequences for supported cryptocurrencies."""

    @staticmethod
    def render_icon_frame(symbol: str = "BTC") -> Image.Image:
        """Frame 1: Recognizable 16x16 pixel-art coin/icon."""
        sym = symbol.upper().strip()
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        if sym in CRYPTO_ICONS:
            lines, cmap = CRYPTO_ICONS[sym]
            draw_bitmap_16x16(img, lines, cmap)
        else:
            # Fallback ticker badge
            color = CRYPTO_BRAND_COLORS.get(sym, COLOR_CYAN)
            draw = ImageDraw.Draw(img)
            draw.line([(2, 2), (13, 2)], fill=color)
            w = measure_text(sym)
            draw_text(img, sym, x=max(0, (16 - w) // 2), y=5, color=COLOR_WHITE)
            draw.line([(2, 13), (13, 13)], fill=color)
        return img

    @staticmethod
    def render_price_frame(symbol: str, price: float) -> Image.Image:
        """Frame 2: Abbreviated current USD price with ticker banner."""
        sym = symbol.upper().strip()
        color = CRYPTO_BRAND_COLORS.get(sym, COLOR_GOLD)
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        # Top banner: Ticker (e.g. "BTC", "ETH", "SOL")
        w_sym = measure_text(sym)
        draw_text(img, sym, x=max(0, (16 - w_sym) // 2), y=1, color=color)
        # Divider line
        draw = ImageDraw.Draw(img)
        draw.line([(1, 7), (14, 7)], fill=COLOR_DARK_GRAY)
        # Bottom: Abbreviated price
        price_str = format_abbreviated_price(price)
        w_p = measure_text(price_str)
        draw_text(img, price_str, x=max(0, (16 - w_p) // 2), y=9, color=COLOR_WHITE)
        return img

    @staticmethod
    def render_change_frame(pct: float) -> Image.Image:
        """Frame 3: 24h percentage change with up/down indication."""
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        delta_str, col = format_delta_pct(pct)
        # Direction arrow on top
        arrow_char = '▲' if pct >= 0 else '▼'
        arrow_y = 2 if pct >= 0 else 3
        draw_text(img, arrow_char, x=6, y=arrow_y, color=col)
        # Percentage below
        w = measure_text(delta_str)
        draw_text(img, delta_str, x=max(0, (16 - w) // 2), y=9, color=col)
        return img

    @staticmethod
    def render_split_frame(symbol: str, price: float, pct: float) -> Image.Image:
        """Compact single-frame view: mini crypto badge + price + delta dot."""
        sym = symbol.upper().strip()
        color = CRYPTO_BRAND_COLORS.get(sym, COLOR_GOLD)
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        draw_text(img, sym[:4], x=1, y=1, color=color)
        col = COLOR_GREEN if pct >= 0 else COLOR_RED
        img.putpixel((14, 2), col)
        img.putpixel((13, 3), col)
        img.putpixel((14, 3), col)
        price_str = format_abbreviated_price(price)
        w = measure_text(price_str)
        draw_text(img, price_str, x=max(0, (16 - w) // 2), y=9, color=COLOR_WHITE)
        return img

    @classmethod
    def render_cycle_frames(cls, symbol: str, price: float, pct: float) -> List[Image.Image]:
        """Returns the full 3-frame flip sequence for a cryptocurrency."""
        return [
            cls.render_icon_frame(symbol),
            cls.render_price_frame(symbol, price),
            cls.render_change_frame(pct),
        ]


# Backward-compatible class
class Btc16Renderer:
    @staticmethod
    def render_icon_frame() -> Image.Image:
        return Crypto16Renderer.render_icon_frame("BTC")

    @staticmethod
    def render_price_frame(price: float) -> Image.Image:
        return Crypto16Renderer.render_price_frame("BTC", price)

    @staticmethod
    def render_change_frame(pct: float) -> Image.Image:
        return Crypto16Renderer.render_change_frame(pct)

    @staticmethod
    def render_split_frame(price: float, pct: float) -> Image.Image:
        return Crypto16Renderer.render_split_frame("BTC", price, pct)

    @staticmethod
    def render_cycle_frames(price: float, pct: float) -> List[Image.Image]:
        return [
            Crypto16Renderer.render_icon_frame("BTC"),
            Crypto16Renderer.render_price_frame("BTC", price),
            Crypto16Renderer.render_change_frame(pct),
        ]


# ==============================================================================
# STOCK RENDERERS (16x16: Configurable Tickers NVDA, TSLA, AAPL, MSFT, META, etc.)
# ==============================================================================
class Stock16Renderer:
    """Generates 16x16 frame sequences for configurable stock tickers."""

    @staticmethod
    def render_symbol_frame(symbol: str) -> Image.Image:
        """Frame 1: Ticker badge with brand color accent."""
        sym = symbol.upper().strip()
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(sym, COLOR_CYAN)
        # Top accent bar
        draw = ImageDraw.Draw(img)
        draw.line([(2, 2), (13, 2)], fill=brand_col)
        # Centered symbol
        w = measure_text(sym)
        x = max(0, (16 - w) // 2)
        draw_text(img, sym, x=x, y=5, color=COLOR_WHITE)
        # Bottom accent bar
        draw.line([(2, 13), (13, 13)], fill=brand_col)
        return img

    @staticmethod
    def render_price_frame(symbol: str, price: float) -> Image.Image:
        """Frame 2: Stock price frame."""
        sym = symbol.upper().strip()
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(sym, COLOR_CYAN)
        # Mini ticker on top
        w_sym = measure_text(sym)
        draw_text(img, sym, x=max(0, (16 - w_sym) // 2), y=1, color=brand_col)
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
        sym = symbol.upper().strip()
        img = Image.new("RGB", (16, 16), COLOR_BLACK)
        brand_col = BRAND_COLORS.get(sym, COLOR_CYAN)
        draw_text(img, sym[:4], x=1, y=1, color=brand_col)
        col = COLOR_GREEN if pct >= 0 else COLOR_RED
        img.putpixel((14, 2), col)
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
    total_w = text_w + 32  # 16px lead-in + 16px trail
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
