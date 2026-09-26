import pytest
from models import CryptoAsset
from collectors import MultiCryptoCollector, CRYPTO_METADATA


def test_crypto_asset_formatted_price_large():
    btc = CryptoAsset(
        symbol="BTC",
        name="Bitcoin",
        price=84520.0,
        change_24h_pct=-0.5,
        high_24h=85200.0,
        low_24h=83400.0,
    )
    assert btc.formatted_price == "$84,520"
    assert btc.formatted_compact_price == "$84.5K"


def test_crypto_asset_formatted_price_medium():
    sol = CryptoAsset(
        symbol="SOL",
        name="Solana",
        price=122.45,
        change_24h_pct=3.2,
    )
    assert sol.formatted_price == "$122.45"
    assert sol.formatted_compact_price == "$122.5"

    doge = CryptoAsset(
        symbol="DOGE",
        name="Dogecoin",
        price=0.0987,
        change_24h_pct=2.1,
    )
    assert doge.formatted_price == "$0.0987"
    assert doge.formatted_compact_price == "$0.099"


def test_pepe_micro_price_formatting():
    """Verify micro-decimal tokens like PEPE format intelligently without unreadable long strings."""
    pepe = CryptoAsset(
        symbol="PEPE",
        name="Pepe",
        price=0.00000452,
        change_24h_pct=1.2,
    )
    # Formatted price should retain precision cleanly up to 7 decimal places
    assert pepe.formatted_price == "$0.0000045"
    # MiniToo 128px display compact notation
    assert pepe.formatted_compact_price == "$4.5u"


def test_multi_crypto_overview_mock():
    collector = MultiCryptoCollector(cache_file=".nonexistent_test_cache.json")
    mock_assets = {
        "btc": CryptoAsset(symbol="BTC", name="Bitcoin", price=84000.0, change_24h_pct=1.0),
        "eth": CryptoAsset(symbol="ETH", name="Ethereum", price=2700.0, change_24h_pct=2.0),
        "sol": CryptoAsset(symbol="SOL", name="Solana", price=120.0, change_24h_pct=-1.0),
        "doge": CryptoAsset(symbol="DOGE", name="Dogecoin", price=0.10, change_24h_pct=0.5),
        "pepe": CryptoAsset(symbol="PEPE", name="Pepe", price=0.0000045, change_24h_pct=0.8),
    }
    # Mock get_all_assets
    collector.get_all_assets = lambda: mock_assets

    overview_page = collector.collect_overview()
    assert overview_page.title == "CRYPTO"
    assert len(overview_page.crypto_assets) == 5
    assert overview_page.primary_metric.label == "BTC"
    assert overview_page.secondary_metric.label == "ETH"


def test_individual_crypto_asset_page_mock():
    collector = MultiCryptoCollector(cache_file=".nonexistent_test_cache.json")
    mock_assets = {
        "pepe": CryptoAsset(
            symbol="PEPE",
            name="Pepe",
            price=0.0000045,
            change_24h_pct=1.5,
            sparkline=[0.0000040 + i * 0.0000001 for i in range(24)],
            icon_char="🐸",
        )
    }
    collector.get_all_assets = lambda: mock_assets

    pepe_page = collector.collect_asset("pepe")
    assert "PEPE" in pepe_page.title
    assert pepe_page.primary_metric.value == "$0.0000045"
    assert len(pepe_page.sparkline_data) == 24
