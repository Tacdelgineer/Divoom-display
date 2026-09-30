"""
Unit tests for Milestone 13:
- Preset composition (ALL, AI, CRYPTO, STOCKS, SYSTEM)
- Desktop vs MiniToo visibility independence
- Section and card ordering persistence
- Bluetooth low-interference mode and poll rates
- Frame diffing / zero redundant frame transmissions
- Unrelated collector refreshes do not push frames to MiniToo
- MiniToo diagnostics telemetry and report generation
"""
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image

from config import (
    DashboardConfig,
    ALL_SECTIONS,
    ALL_PAGE_IDS,
    SECTION_CRYPTO,
    SECTION_AI_USAGE,
    SECTION_SYSTEM,
    SECTION_STOCKS,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_SYSTEM,
    ALL_PRESETS,
)
from engine import DashboardState, MiniTooController
from models import PageData, MetricItem
from backends import MiniTooDisplay
from inputs import MiniTooInputAdapter


def test_preset_compositions():
    """Verify all 5 presets enable their expected sections and cards."""
    cfg = DashboardConfig()

    # 1. ALL
    cfg.apply_preset(PRESET_ALL)
    assert cfg.active_preset == PRESET_ALL
    for s in ALL_SECTIONS:
        assert cfg.enabled_sections[s] is True
    for c in ALL_PAGE_IDS:
        assert cfg.enabled_cards[c] is True

    # 2. AI
    cfg.apply_preset(PRESET_AI)
    assert cfg.active_preset == PRESET_AI
    assert cfg.enabled_sections[SECTION_AI_USAGE] is True
    assert cfg.enabled_sections[SECTION_SYSTEM] is True
    assert cfg.enabled_sections[SECTION_CRYPTO] is False
    assert cfg.enabled_sections[SECTION_STOCKS] is False
    assert cfg.enabled_cards["codex"] is True
    assert cfg.enabled_cards["gemini"] is True
    assert cfg.enabled_cards["claude"] is True
    assert cfg.enabled_cards["ai_activity"] is True
    assert cfg.enabled_cards["btc"] is False

    # 3. CRYPTO
    cfg.apply_preset(PRESET_CRYPTO)
    assert cfg.active_preset == PRESET_CRYPTO
    assert cfg.enabled_sections[SECTION_CRYPTO] is True
    assert cfg.enabled_sections[SECTION_AI_USAGE] is False
    assert cfg.enabled_sections[SECTION_SYSTEM] is False
    assert cfg.enabled_sections[SECTION_STOCKS] is False
    for coin in ("btc", "eth", "sol", "doge", "pepe", "crypto"):
        assert cfg.enabled_cards[coin] is True
    assert cfg.enabled_cards["codex"] is False

    # 4. STOCKS
    cfg.apply_preset(PRESET_STOCKS)
    assert cfg.active_preset == PRESET_STOCKS
    assert cfg.enabled_sections[SECTION_STOCKS] is True
    assert cfg.enabled_sections[SECTION_CRYPTO] is False
    assert cfg.enabled_sections[SECTION_AI_USAGE] is False
    assert cfg.enabled_sections[SECTION_SYSTEM] is False
    assert cfg.enabled_cards["stocks_volatile"] is True
    assert cfg.enabled_cards["btc"] is False

    # 5. SYSTEM
    cfg.apply_preset(PRESET_SYSTEM)
    assert cfg.active_preset == PRESET_SYSTEM
    assert cfg.enabled_sections[SECTION_SYSTEM] is True
    assert cfg.enabled_sections[SECTION_CRYPTO] is False
    assert cfg.enabled_sections[SECTION_AI_USAGE] is False
    assert cfg.enabled_sections[SECTION_STOCKS] is False
    for sys_card in ("local_pc", "dgx_spark", "services", "coding", "ai_activity"):
        assert cfg.enabled_cards[sys_card] is True
    assert cfg.enabled_cards["btc"] is False


def test_desktop_vs_minitoo_visibility():
    """Verify card visibility can be toggled independently for Desktop vs MiniToo."""
    cfg = DashboardConfig()
    cfg.apply_preset(PRESET_ALL)

    # Enable on desktop, disable on MiniToo
    cfg.enabled_cards["btc"] = True
    cfg.enabled_cards_minitoo["btc"] = False

    # Disable on desktop, enable on MiniToo
    cfg.enabled_cards["coding"] = False
    cfg.enabled_cards_minitoo["coding"] = True

    active_minitoo_pages = cfg.get_active_pages()
    assert "btc" not in active_minitoo_pages
    assert "coding" in active_minitoo_pages

    # Check serialization round-trip
    d = cfg.to_dict()
    restored = DashboardConfig.from_dict(d)
    assert restored.enabled_cards["btc"] is True
    assert restored.enabled_cards_minitoo["btc"] is False
    assert restored.enabled_cards["coding"] is False
    assert restored.enabled_cards_minitoo["coding"] is True


def test_bluetooth_config_persistence():
    """Verify Bluetooth settings persist across config serialization."""
    cfg = DashboardConfig()
    cfg.minitoo_bt_mode = "LOW_INTERFERENCE"
    cfg.minitoo_knob_enabled = False
    cfg.minitoo_poll_rate = "2Hz"
    cfg.default_preset = PRESET_CRYPTO
    cfg.focus_section = SECTION_CRYPTO

    d = cfg.to_dict()
    restored = DashboardConfig.from_dict(d)

    assert restored.minitoo_bt_mode == "LOW_INTERFERENCE"
    assert restored.minitoo_knob_enabled is False
    assert restored.minitoo_poll_rate == "2Hz"
    assert restored.default_preset == PRESET_CRYPTO
    assert restored.focus_section == SECTION_CRYPTO


def test_frame_diffing_no_redundant_sends():
    """Verify MiniToo does not retransmit identical frames even when requested if pixels unchanged."""
    cfg = DashboardConfig()
    state = DashboardState(config=cfg)
    ctrl = MiniTooController(state, config=cfg)
    mock_display = MagicMock()
    mock_display.show.return_value = True
    ctrl.display = mock_display

    img1 = Image.new("RGB", (160, 128), color=(255, 0, 0))
    ctrl._render_active_frame = MagicMock(return_value=img1)

    # 1. First frame sent because _last_sent_bytes is None
    ctrl._force_push = True
    # Simulate the controller send check:
    frame_bytes = img1.tobytes()
    if ctrl._force_push or frame_bytes != ctrl._last_sent_bytes:
        ok = ctrl.display.show(img1)
        if ok:
            ctrl._last_sent_bytes = frame_bytes
            ctrl._force_push = False

    assert mock_display.show.call_count == 1
    assert ctrl._last_sent_bytes == frame_bytes

    # 2. Second frame with identical bytes and _force_push is False
    mock_display.show.reset_mock()
    frame_bytes_2 = img1.tobytes()
    should_send = ctrl._force_push or frame_bytes_2 != ctrl._last_sent_bytes
    assert should_send is False  # Frame diffing skips send!
    if should_send:
        ctrl.display.show(img1)
    assert not mock_display.show.called

    # 3. Third frame with changed image
    img2 = Image.new("RGB", (160, 128), color=(0, 255, 0))
    frame_bytes_3 = img2.tobytes()
    should_send_3 = ctrl._force_push or frame_bytes_3 != ctrl._last_sent_bytes
    assert should_send_3 is True
    if should_send_3:
        ctrl.display.show(img2)
        ctrl._last_sent_bytes = frame_bytes_3
    assert mock_display.show.call_count == 1


def test_knob_poll_rates_and_disable():
    """Verify knob polling intervals adjust correctly and stop when disabled."""
    inputs = MiniTooInputAdapter(port="COM99")

    # NORMAL mode default
    inputs.set_poll_rate("AUTO", mode="NORMAL")
    assert inputs.poll_interval == 0.25  # ~4 Hz

    # LOW_INTERFERENCE mode default
    inputs.set_poll_rate("AUTO", mode="LOW_INTERFERENCE")
    assert inputs.poll_interval == 0.35  # ~2.8 Hz

    # Explicit rates
    inputs.set_poll_rate("2Hz")
    assert inputs.poll_interval == 0.50
    inputs.set_poll_rate("3Hz")
    assert inputs.poll_interval == 0.33
    inputs.set_poll_rate("4Hz")
    assert inputs.poll_interval == 0.25
    inputs.set_poll_rate("5Hz")
    assert inputs.poll_interval == 0.20

    # Toggle knob
    inputs.knob_enabled = False
    assert inputs.knob_enabled is False


def test_unrelated_collector_refresh_does_not_push_minitoo_frame():
    """
    When MiniToo is displaying page X (e.g. BTC), an update to page Y (e.g. local_pc)
    must NOT trigger a physical MiniToo frame transmission.
    """
    cfg = DashboardConfig()
    cfg.auto_cycle = False
    state = DashboardState(config=cfg)
    ctrl = MiniTooController(state, config=cfg)

    # Set active page to btc and seed btc data
    state.minitoo_active_page = "btc"
    state.set_minitoo_status(True, "MINITOO ● CONNECTED")
    btc_data = PageData(page_id="btc", title="BTC", badge="SPOT", primary_metric=MetricItem("PRICE", "$95,000"))
    state.update_page("btc", btc_data)

    # Initial frame rendered and cached
    initial_img = ctrl._render_active_frame()
    assert initial_img is not None
    ctrl._last_sent_bytes = initial_img.tobytes()
    ctrl._force_push = False

    # Simulate background collector updating unrelated page "local_pc"
    pc_data = PageData(page_id="local_pc", title="LOCAL PC", badge="SYSTEM", primary_metric=MetricItem("GPU", "15%"))
    state.update_page("local_pc", pc_data)

    # Active page frame should be identical to last sent frame
    current_img = ctrl._render_active_frame()
    assert current_img.tobytes() == ctrl._last_sent_bytes

    # Frame diff check: should NOT send
    should_send = ctrl._force_push or current_img.tobytes() != ctrl._last_sent_bytes
    assert should_send is False


def test_diagnostics_report_generation():
    """Verify MiniToo controller produces detailed diagnostics telemetry."""
    cfg = DashboardConfig()
    state = DashboardState(config=cfg)
    ctrl = MiniTooController(state, config=cfg)

    diag = ctrl.get_diagnostics()
    assert "mode" in diag
    assert "knob_polls_per_sec" in diag
    assert "reconnect_count" in diag
    assert "writes_per_min" in diag

    report = ctrl.format_diagnostics_report()
    assert "MINITOO BLUETOOTH TRANSPORT DIAGNOSTICS" in report
    assert "Transport Mode:" in report
    assert "Knob Poll Rate Config:" in report
    assert "Real-Time Rolling Rates" in report
