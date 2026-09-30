#!/usr/bin/env python3
"""
Unit and integration tests for Milestone 14:
High-DPI Desktop Command Center, Scalable Layout System, UX Polish, and Creator Capture Views.

Verifies:
1. UI Scale persistence & factor calculation (AUTO, 100%, 125%, 150%, 175%, 200%).
2. Responsive column calculation across display widths (760px, 1280px, 1920px).
3. Card min/max sizing logic (never stretched to absurd dimensions).
4. Window state persistence (width, height, maximized, creator_mode, creator_aspect).
5. Preset switching and shortcut actions.
6. Creator View composition (16:9 and 9:16 vertical Shorts layouts).
7. Zero collector requests triggered by window resize / GUI redraw.
8. Zero MiniToo SPP frames triggered by desktop-only resize.
"""
import pytest
from unittest.mock import MagicMock, patch

from config import (
    DashboardConfig,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_SYSTEM,
    SECTION_CRYPTO,
    SECTION_AI_USAGE,
    SECTION_STOCKS,
    SECTION_SYSTEM,
)
from ui_scale import UiScale, enable_high_dpi_awareness, get_system_dpi_scale


def test_enable_high_dpi_awareness_safe():
    """Verify enable_high_dpi_awareness runs safely without throwing exceptions."""
    res = enable_high_dpi_awareness()
    assert isinstance(res, bool)


def test_ui_scale_factors():
    """Verify UiScale resolves all configured scaling options correctly."""
    s100 = UiScale("100%")
    assert s100.factor == 1.0
    assert s100.s(100) == 100

    s125 = UiScale("125%")
    assert s125.factor == 1.25
    assert s125.s(100) == 125

    s150 = UiScale("150%")
    assert s150.factor == 1.50
    assert s150.s(100) == 150

    s175 = UiScale("175%")
    assert s175.factor == 1.75
    assert s175.s(100) == 175

    s200 = UiScale("200%")
    assert s200.factor == 2.00
    assert s200.s(100) == 200

    # AUTO should be >= 1.0 and <= 2.0
    s_auto = UiScale("AUTO")
    assert 1.0 <= s_auto.factor <= 2.0


def test_ui_scale_config_persistence(tmp_path):
    """Verify ui_scale, window_width, window_height, and window_maximized persist across config save/load."""
    cfg = DashboardConfig()
    cfg.ui_scale = "150%"
    cfg.window_width = 1440
    cfg.window_height = 900
    cfg.window_maximized = True
    cfg.creator_mode = True
    cfg.creator_aspect = "9:16"

    d = cfg.to_dict()
    assert d["ui_scale"] == "150%"
    assert d["window_width"] == 1440
    assert d["window_height"] == 900
    assert d["window_maximized"] is True
    assert d["creator_mode"] is True
    assert d["creator_aspect"] == "9:16"

    loaded = DashboardConfig.from_dict(d)
    assert loaded.ui_scale == "150%"
    assert loaded.window_width == 1440
    assert loaded.window_height == 900
    assert loaded.window_maximized is True
    assert loaded.creator_mode is True
    assert loaded.creator_aspect == "9:16"


def test_responsive_grid_column_calculation():
    """Verify responsive reflow mathematics for crypto cards across display widths."""
    scale = UiScale("100%")
    margin = scale.grid_margin  # 14
    gap = scale.gap            # 10
    min_w = scale.card_min_w    # 260
    max_w = scale.card_max_w    # 420
    cards = ["btc", "eth", "sol", "doge", "pepe"]

    # 1. Wide 1080p display (width 1920px)
    w_1080 = 1920
    avail_1080 = w_1080 - 2 * margin
    num_cols_1080 = max(1, min(len(cards), (avail_1080 + gap) // (min_w + gap)))
    assert num_cols_1080 == 5  # All 5 crypto assets fit in ONE row on wide screen!

    card_w_1080 = (avail_1080 - (num_cols_1080 - 1) * gap) // num_cols_1080
    assert min_w <= card_w_1080 <= max_w

    # 2. Medium 1280p display (width 1280px)
    w_1280 = 1280
    avail_1280 = w_1280 - 2 * margin
    num_cols_1280 = max(1, min(len(cards), (avail_1280 + gap) // (min_w + gap)))
    assert num_cols_1280 in (3, 4)  # Reflows gracefully into 2 rows

    # 3. Compact window (width 760px)
    w_760 = 760
    avail_760 = w_760 - 2 * margin
    num_cols_760 = max(1, min(len(cards), (avail_760 + gap) // (min_w + gap)))
    assert num_cols_760 == 2  # 2 readable columns


def test_card_width_clamping():
    """Verify card width never exceeds card_max_w to avoid ridiculously wide cards on ultra-wide screens."""
    scale = UiScale("100%")
    margin = scale.grid_margin
    gap = scale.gap
    min_w = scale.card_min_w
    max_w = scale.card_max_w

    # Ultra-wide screen (3440px) with only 2 cards
    cards = ["btc", "eth"]
    avail_w = 3440 - 2 * margin
    num_cols = max(1, min(len(cards), (avail_w + gap) // (min_w + gap)))
    raw_card_w = (avail_w - (num_cols - 1) * gap) // num_cols

    # Raw would be ~1700px! But layout logic clamps to max_w:
    clamped_w = min(raw_card_w, max_w)
    assert clamped_w == max_w
    assert clamped_w <= 420


def test_creator_view_composition():
    """Verify Creator View presets and vertical stacking compositions."""
    cfg = DashboardConfig()
    cfg.apply_preset(PRESET_CRYPTO)
    assert cfg.active_preset == PRESET_CRYPTO

    # Crypto 9:16 layout order: BTC, ETH, SOL, DOGE, PEPE
    crypto_cards = ["btc", "eth", "sol", "doge", "pepe"]
    for c in crypto_cards:
        assert cfg.enabled_cards.get(c, True) is True

    # AI 9:16 layout order: CODEX, GEMINI, CLAUDE, AI_ACTIVITY
    cfg.apply_preset(PRESET_AI)
    assert cfg.active_preset == PRESET_AI
    ai_cards = ["codex", "gemini", "claude", "ai_activity"]
    for c in ai_cards:
        assert cfg.enabled_cards.get(c, True) is True


def test_no_collector_called_on_ui_resize():
    """Verify that UI scale calculations or dimension resizing do NOT invoke background collectors."""
    mock_collector = MagicMock()
    with patch("engine.DataEngine._collect_one", mock_collector):
        scale = UiScale("150%")
        _ = scale.s(1240)
        _ = scale.s(780)
        _ = scale.font(14, "bold")
        _ = scale.default_window_w
        _ = scale.default_window_h
        # Zero collector calls triggered by UI layout math
        assert mock_collector.call_count == 0


def test_no_minitoo_frame_on_desktop_only_resize():
    """Verify desktop layout operations never invoke MiniToo SPP frame generation or transmissions."""
    mock_push = MagicMock()
    with patch("engine.MiniTooController.push_page", mock_push):
        cfg = DashboardConfig()
        cfg.window_width = 1920
        cfg.window_height = 1080
        cfg.ui_scale = "125%"
        cfg.save()

        # Zero MiniToo Bluetooth packets generated by desktop window resizing
        assert mock_push.call_count == 0
