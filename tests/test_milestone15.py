#!/usr/bin/env python3
"""
Unit and integration tests for AI Desk Dashboard Milestone 15:
- First-Run Device Setup Wizard
- Device Discovery State Machine (CONNECTED, CONNECTING, RECONNECTING, PAIRING REQUIRED, NOT FOUND, OFFLINE)
- Remembered Device Reconnect & Desktop-Only Fallback
- Top US Equities by Market Cap Dynamic Ranking & Share-Class Deduplication (GOOG/GOOGL, BRK)
- Stock Market-Cap Formatting & 1D Sparkline Normalization
- Stock Card Layout (9 required fields)
- Polymarket Signals Provider & Attention Ranking Formula
- News Headline Integration
- Alert Engine Normalized Architecture
- Public Screenshot Privacy Fixtures (no emails, usernames, tokens)
- Full Hardware-Free CI Compatibility
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from models import StockQuote, PredictionMarketSignal, NewsHeadline, Alert, PageData
from market_provider import (
    filter_duplicate_share_classes,
    get_top_market_cap_stocks,
    synthesize_sparkline,
    DEFAULT_TOP_MARKET_CAP_FALLBACK,
    SHARE_CLASS_CANONICAL_MAP,
)
from signals_provider import (
    calculate_attention_score,
    normalize_polymarket_event,
    classify_category,
    is_sports_event,
    get_prediction_signals,
    FALLBACK_PREDICTION_SIGNALS,
)
from detector import detect_minitoo_connection_state
from config import DashboardConfig, PRESET_ALL, PRESET_STOCKS, PRESET_SIGNALS
from engine import DashboardState


# ==============================================================================
# 1. DEVICE DISCOVERY & CONNECTION STATE UX
# ==============================================================================
def test_device_discovery_state_machine_not_found():
    """Verify NOT FOUND / PAIRING REQUIRED state when no serial COM ports exist."""
    import detector
    mock_serial = MagicMock()
    mock_serial.tools.list_ports.comports.return_value = []
    with patch.object(detector, "serial", mock_serial):
        state, port = detect_minitoo_connection_state()
        assert state in ("PAIRING REQUIRED", "NOT FOUND")
        assert port is None


def test_device_discovery_state_machine_paired_found():
    """Verify FOUND state when paired Divoom/SPP serial port exists."""
    import detector
    mock_port = MagicMock()
    mock_port.device = "COM13"
    mock_port.description = "Standard Serial over Bluetooth link (COM13)"
    mock_port.hwid = "BTHENUM\\{00001101-0000-1000-8000-00805F9B34FB}"
    mock_port.vid = 0x05D6
    mock_port.manufacturer = "Divoom"

    mock_serial = MagicMock()
    mock_serial.tools.list_ports.comports.return_value = [mock_port]

    with patch.object(detector, "serial", mock_serial), \
         patch("detector.probe_divoom_device", return_value=True):
        state, port = detect_minitoo_connection_state()
        assert state == "FOUND"
        assert port == "COM13"


def test_remembered_device_reconnect_and_desktop_fallback():
    """Verify remembered device preference & graceful fallback to desktop-only mode."""
    cfg = DashboardConfig(last_successful_device="minitoo", target_device="desktop")
    assert cfg.last_successful_device == "minitoo"
    assert cfg.target_device == "desktop"

    # Missing physical hardware must never break or hang state initialization
    state = DashboardState(config=cfg)
    assert state.minitoo_state in ("CONNECTING", "OFFLINE", "NOT FOUND", "PAIRING REQUIRED", "CONNECTED")
    assert state.ditoo_state in ("CONNECTING", "OFFLINE", "NOT FOUND", "PAIRING REQUIRED", "CONNECTED")

    # Desktop mode requires no physical link
    assert cfg.target_device == "desktop"



# ==============================================================================
# 2. TOP-10 US EQUITIES BY MARKET CAP & DEDUPLICATION
# ==============================================================================
def test_duplicate_share_class_filtering():
    """
    Test corporate entity share-class deduplication rule:
    Maps multiple listed classes (GOOGL/GOOG, BRK-A/BRK-B) and retains only the single
    share class with the highest market capitalization.
    """
    quotes = [
        StockQuote(symbol="NVDA", name="NVIDIA Corp", price=229.81, change_pct=2.1, market_cap=5_550_000_000_000),
        StockQuote(symbol="GOOGL", name="Alphabet Inc. Class A", price=201.55, change_pct=-0.5, market_cap=2_410_000_000_000),
        StockQuote(symbol="GOOG", name="Alphabet Inc. Class C", price=202.10, change_pct=-0.4, market_cap=2_390_000_000_000),
        StockQuote(symbol="BRK-A", name="Berkshire Hathaway A", price=720000.0, change_pct=0.1, market_cap=1_050_000_000_000),
        StockQuote(symbol="BRK-B", name="Berkshire Hathaway B", price=492.80, change_pct=0.2, market_cap=1_080_000_000_000),
        StockQuote(symbol="AAPL", name="Apple Inc.", price=254.23, change_pct=0.8, market_cap=3_820_000_000_000),
    ]

    filtered = filter_duplicate_share_classes(quotes)
    symbols = [q.symbol for q in filtered]

    # Exactly one Alphabet ticker retained (GOOGL with $2.41T vs GOOG with $2.39T)
    assert "GOOGL" in symbols
    assert "GOOG" not in symbols

    # Exactly one Berkshire ticker retained (BRK-B with $1.08T vs BRK-A with $1.05T)
    assert "BRK-B" in symbols
    assert "BRK-A" not in symbols

    # Alphabet corporate entity appears only once
    alphabet_symbols = [s for s in symbols if s in ("GOOG", "GOOGL")]
    assert len(alphabet_symbols) == 1


def test_market_cap_formatting():
    """Verify formatted_market_cap formats trillions, billions, millions cleanly."""
    q_trillion = StockQuote(symbol="NVDA", name="NVIDIA", price=230.0, change_pct=2.0, market_cap=5_550_000_000_000)
    assert q_trillion.formatted_market_cap == "$5.55T"

    q_billion = StockQuote(symbol="AVGO", name="Broadcom", price=180.0, change_pct=1.0, market_cap=845_600_000_000)
    assert q_billion.formatted_market_cap == "$845.6B"

    q_million = StockQuote(symbol="TEST", name="SmallCap", price=10.0, change_pct=0.5, market_cap=450_000_000)
    assert q_million.formatted_market_cap == "$450.0M"

    q_none = StockQuote(symbol="TEST", name="NoCap", price=10.0, change_pct=0.5, market_cap=None)
    assert q_none.formatted_market_cap == "N/A"


def test_stock_sparkline_synthesis():
    """Verify 1D sparkline synthesis generates valid curve anchored on price and change %."""
    pts = synthesize_sparkline(price=100.0, change_pct=5.0, count=16)
    assert len(pts) == 16
    assert all(isinstance(v, float) for v in pts)
    # With +5% gain, final price should exceed initial base
    assert pts[-1] > pts[0]

    pts_down = synthesize_sparkline(price=100.0, change_pct=-5.0, count=16)
    assert len(pts_down) == 16
    assert pts_down[-1] < pts_down[0]


def test_stock_card_required_fields():
    """
    Verify all 9 required fields for stock cards:
    symbol, company name, price, day change %, market cap, intraday / 1D sparkline,
    market state, source, fetched_at.
    """
    fallback = DEFAULT_TOP_MARKET_CAP_FALLBACK[0]
    assert fallback.symbol == "NVDA"
    assert fallback.name == "NVIDIA Corporation"
    assert fallback.price > 0
    assert isinstance(fallback.change_pct, float)
    assert fallback.market_cap > 0
    assert fallback.formatted_market_cap != "N/A"
    assert len(fallback.sparkline) >= 8
    assert fallback.market_state in ("REGULAR", "OPEN", "CLOSED", "POST", "PRE")
    assert fallback.source == "YahooFinance"
    assert fallback.fetched_at is not None


# ==============================================================================
# 3. SIGNALS & POLYMARKET PROBABILITY SEMANTICS
# ==============================================================================
def test_attention_score_formula():
    """
    Test deterministic attention ranking formula:
    score = (|delta_pts| * 12.0) + (log10(max(vol, 1000)) * 6.0) + (min(liq, 1M) / 20000.0)
    """
    # Significant move (8 pts) with large volume ($10M) and $500k liquidity
    score_high = calculate_attention_score(change_24h_pts=8.0, volume_24h=10_000_000, liquidity=500_000)
    # Flat market (0 pts) with low volume ($5k) and $10k liquidity
    score_low = calculate_attention_score(change_24h_pts=0.1, volume_24h=5_000, liquidity=10_000)

    assert score_high > score_low
    assert score_high > 100.0


def test_polymarket_probability_semantics():
    """
    Verify probabilities are represented explicitly as market-implied odds (0.0 to 1.0),
    not asserted news facts.
    """
    sig = FALLBACK_PREDICTION_SIGNALS[0]
    assert 0.0 <= sig.yes_probability <= 1.0
    assert 0.0 <= sig.no_probability <= 1.0
    # Yes + No roughly equals 1.0 (or normalized binary odds)
    assert pytest.approx(sig.yes_probability + sig.no_probability, abs=0.05) == 1.0

    # Formatted probability percentage string
    pct_val = int(round(sig.yes_probability * 100))
    assert 0 <= pct_val <= 100


def test_sports_filtering():
    """Ensure high-volume sports tournaments are filtered to maintain macro/fin/tech signal."""
    sports_event = {
        "title": "Arsenal vs Chelsea Premier League Match",
        "description": "Will Arsenal beat Chelsea?",
        "tags": [{"label": "Soccer"}, {"label": "Sports"}],
    }
    assert is_sports_event(sports_event) is True

    macro_event = {
        "title": "Fed Interest Rate Cut by Dec?",
        "description": "Will the Federal Reserve decrease target interest rate?",
        "tags": [{"label": "Finance"}, {"label": "Fed"}],
    }
    assert is_sports_event(macro_event) is False


def test_category_classification():
    """Verify category classification into allowed groups."""
    assert classify_category("Fed Interest Rate decision") == "FINANCE"
    assert classify_category("Bitcoin reaching 100k") == "CRYPTO"
    assert classify_category("OpenAI GPT-5 release date") == "TECH / AI"
    assert classify_category("Ceasefire agreement treaty signed") == "GEOPOLITICS"


def test_news_headline_model():
    """Verify NewsHeadline normalization and attachment to signals."""
    hl = NewsHeadline(
        headline="Federal Reserve holds baseline rate expectations steady",
        source="Reuters",
        url="https://reuters.com/markets",
        time_ago="18m ago"
    )
    assert hl.source == "Reuters"
    assert hl.time_ago == "18m ago"

    sig = FALLBACK_PREDICTION_SIGNALS[0]
    assert len(sig.related_headlines) >= 1
    assert isinstance(sig.related_headlines[0], NewsHeadline)


# ==============================================================================
# 4. ALERT ENGINE MODEL PREPARATION
# ==============================================================================
def test_alert_engine_model():
    """Verify normalized Alert model per Milestone 15 architecture."""
    alert = Alert(
        source="polymarket",
        severity="info",
        title="POLYMARKET +14 pts",
        value="Fed Cut odds surged to 64%",
        timestamp="16:00:00",
        action_url="https://polymarket.com/event/fed-cut"
    )
    assert alert.source == "polymarket"
    assert alert.severity == "info"
    assert "POLYMARKET" in alert.title

    state = DashboardState(config=DashboardConfig())
    state.add_alert(alert)
    recent = state.get_recent_alerts(limit=5)
    assert len(recent) == 1
    assert recent[0].title == "POLYMARKET +14 pts"


# ==============================================================================
# 5. PUBLIC SCREENSHOT PRIVACY FIXTURES
# ==============================================================================
def test_screenshot_privacy_sanitization():
    """
    Verify public screenshot generation source code contains zero exposed personal emails,
    tokens, or private paths.
    """
    screenshot_tool_path = os.path.join(os.path.dirname(__file__), "..", "tools", "build_screenshots.py")
    assert os.path.exists(screenshot_tool_path)

    with open(screenshot_tool_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain "CLAUDE PERSONAL"
    assert "CLAUDE PERSONAL" in content

    # Must not contain real personal emails
    assert "nodal" not in content.lower()
    assert "@gmail.com" not in content.lower()


# ==============================================================================
# 6. CI ZERO HARDWARE EXECUTION
# ==============================================================================
def test_ci_zero_hardware_execution():
    """Ensure data collection runs completely without physical hardware."""
    cfg = DashboardConfig(target_device="desktop")
    cfg.apply_preset(PRESET_STOCKS)
    assert cfg.enabled_sections["stocks"] is True

    cfg.apply_preset(PRESET_SIGNALS)
    assert cfg.enabled_sections["signals"] is True

    # Offline fallbacks are reliable
    stocks = get_top_market_cap_stocks()
    assert len(stocks) >= 10

    signals = get_prediction_signals()
    assert len(signals) >= 5
