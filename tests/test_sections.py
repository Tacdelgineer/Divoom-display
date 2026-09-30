import pytest
from config import (
    DashboardConfig,
    SECTION_CRYPTO,
    SECTION_AI_USAGE,
    SECTION_SYSTEM,
    SECTION_STOCKS,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_MARKETS,
    PRESET_SYSTEM,
)


def test_section_defaults():
    cfg = DashboardConfig()
    cfg.validate()

    assert SECTION_CRYPTO in cfg.sections_order
    assert SECTION_AI_USAGE in cfg.sections_order
    assert SECTION_SYSTEM in cfg.sections_order
    assert SECTION_STOCKS in cfg.sections_order

    for s in cfg.sections_order:
        assert cfg.enabled_sections[s] is True
        assert len(cfg.section_cards[s]) > 0


def test_presets_behavior():
    cfg = DashboardConfig()

    # Apply MARKETS preset
    cfg.apply_preset(PRESET_MARKETS)
    assert cfg.enabled_sections[SECTION_CRYPTO] is True
    assert cfg.enabled_sections[SECTION_STOCKS] is True
    assert cfg.enabled_sections[SECTION_AI_USAGE] is False
    assert cfg.enabled_sections[SECTION_SYSTEM] is False
    assert cfg.enabled_cards["btc"] is True
    assert cfg.enabled_cards["stocks_volatile"] is True
    assert cfg.enabled_cards["codex"] is False

    # Apply AI preset
    cfg.apply_preset(PRESET_AI)
    assert cfg.enabled_sections[SECTION_AI_USAGE] is True
    assert cfg.enabled_sections[SECTION_CRYPTO] is False
    assert cfg.enabled_cards["codex"] is True
    assert cfg.enabled_cards["gemini"] is True
    assert cfg.enabled_cards["claude"] is True
    assert cfg.enabled_cards["btc"] is False

    # Apply CRYPTO preset
    cfg.apply_preset(PRESET_CRYPTO)
    assert cfg.enabled_sections[SECTION_CRYPTO] is True
    assert cfg.enabled_sections[SECTION_STOCKS] is False
    assert cfg.enabled_sections[SECTION_AI_USAGE] is False
    assert cfg.enabled_cards["btc"] is True
    assert cfg.enabled_cards["eth"] is True
    assert cfg.enabled_cards["codex"] is False

    # Apply STOCKS preset
    cfg.apply_preset(PRESET_STOCKS)
    assert cfg.enabled_sections[SECTION_STOCKS] is True
    assert cfg.enabled_sections[SECTION_CRYPTO] is False
    assert cfg.enabled_cards["stocks_volatile"] is True
    assert cfg.enabled_cards["btc"] is False

    # Apply ALL preset
    cfg.apply_preset(PRESET_ALL)
    for s in cfg.sections_order:
        assert cfg.enabled_sections[s] is True


def test_minitoo_active_pages_respects_sections_and_cards():
    cfg = DashboardConfig()
    cfg.apply_preset(PRESET_ALL)

    active = cfg.get_active_pages()
    assert "btc" in active
    assert "codex" in active

    # Disabling CRYPTO section must remove all crypto cards from active pages
    cfg.enabled_sections[SECTION_CRYPTO] = False
    active_no_crypto = cfg.get_active_pages()
    assert "btc" not in active_no_crypto
    assert "eth" not in active_no_crypto
    assert "codex" in active_no_crypto

    # Disabling individual card for MiniToo independently from Desktop
    cfg.enabled_cards_minitoo["codex"] = False
    active_no_codex = cfg.get_active_pages()
    assert "codex" not in active_no_codex
    # Desktop remains enabled
    assert cfg.enabled_cards["codex"] is True


def test_desktop_and_minitoo_visibility_coexistence():
    cfg = DashboardConfig()
    # Card can be visible on desktop but disabled on MiniToo
    cfg.enabled_cards["coding"] = True
    cfg.enabled_cards_minitoo["coding"] = False
    assert cfg.enabled_cards["coding"] is True
    assert "coding" not in cfg.get_active_pages()

    # Card can be disabled on desktop but active on MiniToo
    cfg.enabled_cards["claude"] = False
    cfg.enabled_cards_minitoo["claude"] = True
    assert cfg.enabled_cards["claude"] is False
    assert "claude" in cfg.get_active_pages()


def test_section_ordering():
    cfg = DashboardConfig()
    # Move STOCKS to top
    cfg.sections_order = [SECTION_STOCKS, SECTION_CRYPTO, SECTION_AI_USAGE, SECTION_SYSTEM]
    cfg.validate()

    assert cfg.sections_order[0] == SECTION_STOCKS
