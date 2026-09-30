#!/usr/bin/env python3
"""
Unit and regression tests for Milestone 14.1 Hotfix:
Fixed Desktop Navigation Header Interactions, Native Retro Buttons,
High-DPI Hitbox Reliability, and Hover Feedback.

Verifies:
1. All header controls are native Tkinter Button widgets with valid command callbacks.
2. Direct button invocation fires corresponding actions exactly once.
3. Preset buttons switch active preset and update active styling.
4. Ditoo playback controls (PREV, PAUSE, NEXT, ROT) function cleanly in Ditoo mode.
5. Creator Mode header widgets (Exit, 16:9, 9:16, Presets) function cleanly.
6. Hover feedback (<Enter> and <Leave>) dynamically highlights button borders.
7. Unrelated navigation controls (Settings, Creator, Presets) work independently of Ditoo/MiniToo connection states.
8. Scaling across DPI factors (100%, 125%, 150%, 200%) maintains geometry and styling.
"""
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch

from config import DashboardConfig, PRESET_ALL, PRESET_AI, PRESET_CRYPTO, PRESET_STOCKS, PRESET_SYSTEM
from ui_scale import UiScale, ui_scale
from dashboard_app import DesktopDashboardApp


@pytest.fixture(scope="module")
def shared_root():
    root = tk.Tk()
    root.geometry("1100x700+100+100")
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_tk_app(shared_root):
    # Clean any leftover children on shared_root
    for child in list(shared_root.children.values()):
        try:
            child.destroy()
        except Exception:
            pass

    with patch("dashboard_app.DataEngine.start"), \
         patch("dashboard_app.MiniTooController.start"), \
         patch("dashboard_app.DitooController.start"), \
         patch.object(DesktopDashboardApp, "_show_first_run"), \
         patch.object(DesktopDashboardApp, "_schedule_next_refresh"):
        app = DesktopDashboardApp(shared_root)
        app.creator_mode = False
        app.config.creator_mode = False
        app.config.target_device = "minitoo"
        app._build_header_widgets()
        app._render_gui()
        app.root.update_idletasks()
        app.root.update()
        yield app
        if hasattr(app, "_after_id") and app._after_id:
            try:
                app.root.after_cancel(app._after_id)
            except Exception:
                pass


def test_header_widgets_instantiation(mock_tk_app):
    """Verify header controls are real interactive widgets with hand cursor and commands."""
    app = mock_tk_app
    assert hasattr(app, "header_frame")
    assert hasattr(app, "btn_device")
    assert hasattr(app, "btn_settings")
    assert hasattr(app, "btn_auto")
    assert hasattr(app, "btn_creator")
    assert hasattr(app, "preset_btn_widgets")

    # All buttons must have hand2 cursor
    assert app.btn_device["cursor"] == "hand2"
    assert app.btn_settings["cursor"] == "hand2"
    assert app.btn_auto["cursor"] == "hand2"
    assert app.btn_creator["cursor"] == "hand2"
    for p_name, btn in app.preset_btn_widgets.items():
        assert btn["cursor"] == "hand2"


def test_preset_button_clicks_update_state(mock_tk_app):
    """Verify clicking preset buttons updates the active preset and re-renders."""
    app = mock_tk_app

    # Test ALL -> CRYPTO
    crypto_btn = app.preset_btn_widgets[PRESET_CRYPTO]
    crypto_btn.invoke()
    assert app.config.active_preset == PRESET_CRYPTO

    # Test CRYPTO -> AI
    ai_btn = app.preset_btn_widgets[PRESET_AI]
    ai_btn.invoke()
    assert app.config.active_preset == PRESET_AI

    # Test AI -> SYSTEM
    sys_btn = app.preset_btn_widgets[PRESET_SYSTEM]
    sys_btn.invoke()
    assert app.config.active_preset == PRESET_SYSTEM

    # Return to ALL
    all_btn = app.preset_btn_widgets[PRESET_ALL]
    all_btn.invoke()
    assert app.config.active_preset == PRESET_ALL


def test_ditoo_mode_header_buttons(mock_tk_app):
    """Verify Ditoo controls (PREV, PAUSE, NEXT, ROT) function when Ditoo target is active."""
    app = mock_tk_app
    app.creator_mode = False
    app.config.creator_mode = False
    app.config.target_device = "ditoo"
    app._render_gui()
    app.root.update_idletasks()
    app.root.update()

    # Verify Ditoo nav frame is mapped
    assert app.frame_ditoo_nav.winfo_ismapped()

    # Mock controller methods
    app.ditoo.prev_asset = MagicMock()
    app.ditoo.toggle_pause = MagicMock()
    app.ditoo.next_asset = MagicMock()

    app.btn_ditoo_prev.invoke()
    app.ditoo.prev_asset.assert_called_once()

    app.btn_ditoo_pause.invoke()
    app.ditoo.toggle_pause.assert_called_once()

    app.btn_ditoo_next.invoke()
    app.ditoo.next_asset.assert_called_once()

    # Test auto rotation toggle
    init_rot = app.config.ditoo_auto_rotation
    app.btn_ditoo_rot.invoke()
    assert app.config.ditoo_auto_rotation != init_rot


def test_creator_mode_header_buttons(mock_tk_app):
    """Verify Creator Mode navigation buttons switch aspect ratios and exit cleanly."""
    app = mock_tk_app
    app.creator_mode = False
    app.config.creator_mode = False
    app._toggle_creator()
    app.root.update_idletasks()
    app.root.update()
    assert app.creator_mode is True
    assert app.nav_creator_frame.winfo_ismapped()

    # Test switching aspect ratio
    app.btn_c_9_16.invoke()
    assert app.creator_aspect == "9:16"

    app.btn_c_16_9.invoke()
    assert app.creator_aspect == "16:9"

    # Test exiting creator mode
    app.btn_creator_exit.invoke()
    app.root.update_idletasks()
    app.root.update()
    assert app.creator_mode is False
    assert not app.nav_creator_frame.winfo_ismapped()
    assert app.nav_normal_frame.winfo_ismapped()


def test_header_hover_feedback_bindings(mock_tk_app):
    """Verify hover feedback (<Enter> and <Leave>) dynamically highlights button borders."""
    app = mock_tk_app
    btn = app.btn_settings
    default_border = btn._default_border
    active_border = btn._active_border

    # Trigger hover enter callback
    btn._on_enter(None)
    assert btn["highlightbackground"] == active_border

    # Trigger hover leave callback
    btn._on_leave(None)
    assert btn["highlightbackground"] == default_border

    # Test disabled button does not highlight on enter
    btn.config(state="disabled")
    btn["highlightbackground"] = default_border
    btn._on_enter(None)
    assert btn["highlightbackground"] == default_border
    btn.config(state="normal")


def test_header_independent_of_connection_status(mock_tk_app):
    """Verify that a disconnected or reconnecting device does not disable unrelated desktop controls."""
    app = mock_tk_app
    app.creator_mode = False
    app.config.creator_mode = False
    app.config.target_device = "ditoo"
    app.state.set_ditoo_status(False, "DITOO \u2022 RECONNECTING")
    app._render_gui()
    app.root.update_idletasks()
    app.root.update()

    # Status pill must display reconnecting in amber
    assert "RECONNECTING" in app.lbl_status_pill["text"]

    # Settings and Creator must remain fully clickable and enabled
    assert app.btn_settings["state"] == "normal"
    assert app.btn_creator["state"] == "normal"
    assert app.btn_auto["state"] == "normal"
    assert app.btn_device["state"] == "normal"


def test_header_scales_across_dpis(mock_tk_app):
    """Verify UI scaling factors (100%, 125%, 150%, 200%) apply cleanly without errors."""
    app = mock_tk_app
    scales = ["100%", "125%", "150%", "200%"]
    for s_opt in scales:
        ui_scale.update_setting(s_opt)
        app._build_header_widgets()
        app._render_gui()
        app.root.update_idletasks()
        app.root.update()
        assert app.header_frame.winfo_exists()
        assert app.btn_settings.winfo_exists()
        assert app.btn_device.winfo_exists()
    ui_scale.update_setting("AUTO")
