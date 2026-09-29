import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from src.renderers.ditoo_16 import (
    Btc16Renderer,
    Stock16Renderer,
    upscale_preview,
    render_scrolling_text_strip,
    get_scroll_frame,
)
from collectors import MultiCryptoCollector
from market_provider import YahooFinanceMarketDataProvider

def generate_all_previews():
    out_dir = os.path.abspath("previews_ditoo_16")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Fetch live or cached data
    print("Fetching market data...")
    crypto_col = MultiCryptoCollector()
    assets = crypto_col.get_all_assets()
    
    btc_price = 68420.0
    btc_pct = 2.45
    if assets and "btc" in assets:
        btc_price = assets["btc"].price
        btc_pct = assets["btc"].change_24h_pct

    stocks_provider = YahooFinanceMarketDataProvider()
    stock_universe = ["NVDA", "TSLA", "AAPL", "MSFT", "META"]
    quotes_list = stocks_provider.get_top_volatile_stocks(universe=stock_universe)
    quotes = {q.symbol: q for q in quotes_list}

    fallback_prices = {
        "NVDA": (121.40, 3.12),
        "TSLA": (214.25, -1.84),
        "AAPL": (225.80, 0.95),
        "MSFT": (428.15, -0.42),
        "META": (568.30, 2.10),
    }

    # 2. Render Bitcoin frames
    btc_f1 = Btc16Renderer.render_icon_frame()
    btc_f2 = Btc16Renderer.render_price_frame(btc_price)
    btc_f3 = Btc16Renderer.render_change_frame(btc_pct)
    btc_split = Btc16Renderer.render_split_frame(btc_price, btc_pct)

    upscale_preview(btc_f1).save(os.path.join(out_dir, "btc_frame1_logo.png"))
    upscale_preview(btc_f2).save(os.path.join(out_dir, "btc_frame2_price.png"))
    upscale_preview(btc_f3).save(os.path.join(out_dir, "btc_frame3_change.png"))
    upscale_preview(btc_split).save(os.path.join(out_dir, "btc_split_layout.png"))

    # 3. Render Stock frames
    stock_frames = {}
    for sym in stock_universe:
        if sym in quotes:
            p = quotes[sym].price
            ch = quotes[sym].change_pct
        else:
            p, ch = fallback_prices[sym]

        f1 = Stock16Renderer.render_symbol_frame(sym)
        f2 = Stock16Renderer.render_price_frame(sym, p)
        f3 = Stock16Renderer.render_change_frame(ch)
        f_split = Stock16Renderer.render_split_frame(sym, p, ch)

        upscale_preview(f1).save(os.path.join(out_dir, f"{sym.lower()}_frame1_symbol.png"))
        upscale_preview(f2).save(os.path.join(out_dir, f"{sym.lower()}_frame2_price.png"))
        upscale_preview(f3).save(os.path.join(out_dir, f"{sym.lower()}_frame3_change.png"))
        upscale_preview(f_split).save(os.path.join(out_dir, f"{sym.lower()}_split_layout.png"))
        stock_frames[sym] = (f1, f2, f3, f_split)

    # 4. Generate Composite Overview Image (Clean 4x4 or 3x6 grid)
    # 6 columns x 4 rows of 256x256 tiles with 8px margin
    cols = 6
    rows = 4
    tile_size = 128
    margin = 8
    canvas_w = cols * tile_size + (cols + 1) * margin
    canvas_h = rows * tile_size + (rows + 1) * margin
    comp = Image.new("RGB", (canvas_w, canvas_h), (20, 24, 33))

    tiles_to_place = [
        # Row 1: BTC
        ("BTC Logo", btc_f1),
        ("BTC Price", btc_f2),
        ("BTC Change", btc_f3),
        ("BTC Split", btc_split),
        # Row 2: NVDA
        ("NVDA Sym", stock_frames["NVDA"][0]),
        ("NVDA Price", stock_frames["NVDA"][1]),
        ("NVDA Change", stock_frames["NVDA"][2]),
        ("NVDA Split", stock_frames["NVDA"][3]),
        # Row 3: TSLA
        ("TSLA Sym", stock_frames["TSLA"][0]),
        ("TSLA Price", stock_frames["TSLA"][1]),
        ("TSLA Change", stock_frames["TSLA"][2]),
        ("TSLA Split", stock_frames["TSLA"][3]),
        # Row 4: AAPL & META
        ("AAPL Price", stock_frames["AAPL"][1]),
        ("AAPL Split", stock_frames["AAPL"][3]),
        ("MSFT Price", stock_frames["MSFT"][1]),
        ("MSFT Split", stock_frames["MSFT"][3]),
        ("META Price", stock_frames["META"][1]),
        ("META Split", stock_frames["META"][3]),
    ]

    for idx, (title, img16) in enumerate(tiles_to_place[:24]):
        r = idx // cols
        c = idx % cols
        x = margin + c * (tile_size + margin)
        y = margin + r * (tile_size + margin)
        scaled = upscale_preview(img16, scale=tile_size // 16)
        comp.paste(scaled, (x, y))

    comp_path = os.path.join(out_dir, "composite_overview.png")
    comp.save(comp_path)
    print(f"Composite overview saved -> {comp_path}")
    print(f"All previews generated in {out_dir}")

if __name__ == "__main__":
    generate_all_previews()
