import pytest
from PIL import Image

from src.renderers.ditoo_16 import (
    Btc16Renderer,
    Stock16Renderer,
    format_abbreviated_price,
    format_delta_pct,
    measure_text,
    draw_text,
    render_scrolling_text_strip,
    get_scroll_frame,
    FONT_3x5,
    COLOR_GREEN,
    COLOR_RED,
)
from src.devices.ditoo import (
    frame_spp,
    encode_16x16_frame,
    build_0x8b_packets,
    build_solid_color_packet,
)


def test_format_abbreviated_price():
    assert format_abbreviated_price(68420.50) == "$68K"
    assert format_abbreviated_price(4200.0) == "$4.2K"
    assert format_abbreviated_price(192.40) == "$192"
    assert format_abbreviated_price(25.67) == "$25.7"
    assert format_abbreviated_price(3.14) == "$3.14"
    assert format_abbreviated_price(0.421) == "$0.421"


def test_format_delta_pct():
    t_pos, c_pos = format_delta_pct(3.14)
    assert t_pos == "+3.1%"
    assert c_pos == COLOR_GREEN

    t_neg, c_neg = format_delta_pct(-2.45)
    assert t_neg == "-2.5%"
    assert c_neg == COLOR_RED


def test_measure_and_draw_text():
    # 4-character ticker: 4 * 3px + 3 * 1px spacing = 15px
    assert measure_text("NVDA", FONT_3x5) == 15
    assert measure_text("BTC", FONT_3x5) == 11
    
    img = Image.new("RGB", (16, 16), (0, 0, 0))
    drawn_w = draw_text(img, "BTC", x=1, y=1, color=(255, 255, 255))
    assert drawn_w == 11


def test_btc_renderer_dimensions():
    icon = Btc16Renderer.render_icon_frame()
    assert icon.size == (16, 16)

    price_frame = Btc16Renderer.render_price_frame(68420)
    assert price_frame.size == (16, 16)

    change_frame = Btc16Renderer.render_change_frame(2.5)
    assert change_frame.size == (16, 16)

    split_frame = Btc16Renderer.render_split_frame(68420, 2.5)
    assert split_frame.size == (16, 16)

    cycle = Btc16Renderer.render_cycle_frames(68420, 2.5)
    assert len(cycle) == 3
    for f in cycle:
        assert f.size == (16, 16)


def test_stock_renderer_dimensions():
    sym_frame = Stock16Renderer.render_symbol_frame("NVDA")
    assert sym_frame.size == (16, 16)

    price_frame = Stock16Renderer.render_price_frame("NVDA", 121.50)
    assert price_frame.size == (16, 16)

    change_frame = Stock16Renderer.render_change_frame(-1.4)
    assert change_frame.size == (16, 16)

    split_frame = Stock16Renderer.render_split_frame("NVDA", 121.50, -1.4)
    assert split_frame.size == (16, 16)

    cycle = Stock16Renderer.render_cycle_frames("TSLA", 214.20, 3.2)
    assert len(cycle) == 3


def test_horizontal_scroller():
    strip = render_scrolling_text_strip("NVDA $121.50")
    assert strip.size[1] == 16
    assert strip.size[0] > 16

    win = get_scroll_frame(strip, 5)
    assert win.size == (16, 16)


def test_ditoo_packet_framing():
    # Test SPP framing envelope
    payload = bytes([0x12, 0x34])
    pkt = frame_spp(0x45, payload)
    assert pkt[0] == 0x01
    assert pkt[-1] == 0x02
    assert pkt[3] == 0x45
    # Checksum verification
    decl = len(payload) + 3
    chk = sum(pkt[1 : len(pkt) - 3]) & 0xFFFF
    assert pkt[-3] == (chk & 0xFF)
    assert pkt[-2] == ((chk >> 8) & 0xFF)


def test_ditoo_16x16_encoding():
    img = Image.new("RGB", (16, 16), (255, 0, 0))
    raw = encode_16x16_frame(img)
    assert raw[0] == 0xAA  # Frame magic byte
    length = raw[1] | (raw[2] << 8)
    assert length == len(raw)

    packets = build_0x8b_packets(raw)
    assert len(packets) >= 2  # Start packet + at least 1 data chunk
    assert packets[0][0] == 0x01
    assert packets[0][3] == 0x8B


def test_ditoo_solid_color_packet():
    pkt = build_solid_color_packet(255, 0, 0, 100)
    assert pkt[0] == 0x01
    assert pkt[3] == 0x45
    assert pkt[4] == 0x01  # Channel 1 (Lightning)
    assert pkt[5] == 255   # R
    assert pkt[6] == 0     # G
    assert pkt[7] == 0     # B
    assert pkt[8] == 100   # Brightness


def test_crypto_16_all_supported_coins():
    from src.renderers.ditoo_16 import Crypto16Renderer, CRYPTO_ICONS

    coins = ["BTC", "ETH", "SOL", "DOGE", "PEPE"]
    for coin in coins:
        assert coin in CRYPTO_ICONS
        icon = Crypto16Renderer.render_icon_frame(coin)
        assert icon.size == (16, 16)

        # Check price frame
        p_frame = Crypto16Renderer.render_price_frame(coin, 123.45)
        assert p_frame.size == (16, 16)

        # Check cycle frames
        cycle = Crypto16Renderer.render_cycle_frames(coin, 123.45, 2.5)
        assert len(cycle) == 3
        for f in cycle:
            assert f.size == (16, 16)


def test_punctuation_kerning_fits_16px():
    # Crucial for 16x16: ensure $84K, $4.1K, +2.4%, -1.2%, $0.18, 9.8u fit <= 15px
    test_strings = ["$84K", "$4.1K", "+2.4%", "-1.2%", "$0.18", "9.8U", "$192", "$25.7"]
    for s in test_strings:
        w = measure_text(s, FONT_3x5)
        assert w <= 15, f"String '{s}' width {w} exceeds 15px limit on 16x16 screen!"


def test_stock_provider_batch_and_cache():
    from market_provider import YahooFinanceMarketDataProvider, StockQuote
    
    provider = YahooFinanceMarketDataProvider()
    sq1 = StockQuote(
        symbol="NVDA",
        name="NVIDIA Corporation",
        price=120.5,
        change_pct=2.1,
        volatility_pct=3.5,
        high=122.0,
        low=118.0,
        previous_close=118.0,
    )
    sq2 = StockQuote(
        symbol="TSLA",
        name="Tesla Inc",
        price=210.0,
        change_pct=-1.8,
        volatility_pct=4.2,
        high=215.0,
        low=208.0,
        previous_close=213.8,
    )
    provider._write_cache([sq1, sq2])
    
    quotes = provider.get_quotes_for_symbols(["NVDA", "TSLA"])
    assert "NVDA" in quotes
    assert quotes["NVDA"].price == 120.5
    assert "TSLA" in quotes
    assert quotes["TSLA"].price == 210.0


