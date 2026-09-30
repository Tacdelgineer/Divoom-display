#!/usr/bin/env python3
"""
AI Desk Dashboard — Desktop Companion App & MiniToo Controller.
Milestone 14: High-DPI Desktop Command Center, Scalable Layout System,
Professional UX Polish, and Creator Capture Views (16:9 / 9:16 Shorts).

Features:
- Windows Per-Monitor-V2 High-DPI awareness (100%, 125%, 150%, 175%, 200%).
- Centralized UI Scale Engine & shared design tokens (ui_scale.py).
- Modern default window geometry (1240x780) with full state persistence (w, h, x, y, maximized).
- Fully responsive card reflow grid: min/max card widths, dynamic column counts, centered grid.
- Bold typography hierarchy (App Title, Section Title, Card Title, Primary Metric, Secondary, Detail).
- Upgraded Focus Mode: presentation cards with 80px sparklines and large gauges.
- Creator Capture Mode: zero-clutter 16:9 and 9:16 vertical layouts for filming YouTube Shorts and OBS.
- Keyboard shortcuts: Ctrl+, (Settings), 1..5 (Presets), F11 (Fullscreen), Esc (Exit Focus/Creator).
- Clean Navigation Bar: sleek device selector dropdown, prominent preset buttons, connection pill.
- Bluetooth Coexistence & zero collector/Bluetooth re-fetches on desktop resize.
"""
from __future__ import annotations

import os
import sys
import time
import tkinter as tk
from tkinter import simpledialog
from typing import Optional, Dict, Tuple, Any, List
from PIL import Image, ImageTk

# 1. Enable High-DPI awareness on Windows BEFORE creating any Tk root handle
from ui_scale import enable_high_dpi_awareness, ui_scale, UI_SCALE_OPTIONS

enable_high_dpi_awareness()

from config import (
    DashboardConfig,
    get_log_path,
    ALL_PAGE_IDS,
    ALL_SECTIONS,
    SECTION_TITLES,
    SECTION_CRYPTO,
    SECTION_AI_USAGE,
    SECTION_SYSTEM,
    SECTION_STOCKS,
    ALL_PRESETS,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_MARKETS,
    PRESET_SYSTEM,
)
from ui_components import FirstRunDialog, SettingsDialog, ClaudeAccountsDialog
from engine import (
    DashboardState,
    DataEngine,
    MiniTooController,
    DitooController,
    WindowsAutostart,
)
from models import PageData, MetricItem
from src.renderers.ditoo_16 import (
    Crypto16Renderer,
    Stock16Renderer,
    format_abbreviated_price,
    format_delta_pct,
    upscale_preview,
    BRAND_COLORS,
    CRYPTO_BRAND_COLORS,
)


def rgb_to_hex(color: Any, default: str = "#00F5D4") -> str:
    """Convert RGB tuple or string to valid Tkinter hex color string."""
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
    if isinstance(color, str):
        return color
    return default


# Setup launch-time logging
def setup_logging():
    log_file = get_log_path()
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{ts}] === AI Desk Dashboard Launch (Milestone 14 High-DPI) ===\n")
            f.write(f"[{ts}] Python: {sys.version.split()[0]} | Frozen: {getattr(sys, 'frozen', False)}\n")
            f.write(f"[{ts}] Executable: {sys.executable}\n")
    except Exception:
        pass

    def excepthook(exc_type, exc_val, exc_tb):
        import traceback
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{ts}] UNCAUGHT EXCEPTION:\n")
                traceback.print_exception(exc_type, exc_val, exc_tb, file=f)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_val, exc_tb)

    sys.excepthook = excepthook


# ==============================================================================
# RETRO COLOR PALETTE & DESIGN SYSTEM
# ==============================================================================
C_BG = "#0A0E17"           # Near-black deep space background
C_CARD_BG = "#111622"      # Dark slate card background
C_CARD_BORDER = "#1E273A"  # Subdued card border
C_CARD_HOVER = "#2D3B54"   # Card hover border
C_ACTIVE_CYAN = "#00E5FF"  # Bright cyan glow for active MiniToo card
C_ACTIVE_TAG_BG = "#082B38"# Dark cyan tag background

C_TEXT_WHITE = "#E6EDF5"   # Primary text
C_TEXT_MUTED = "#7D8C9F"   # Secondary label text
C_TEXT_DIM = "#505E73"     # Reset / metadata text

C_GREEN = "#32E68C"        # Emerald / Healthy quota / Online
C_AMBER = "#F5AF32"        # Amber / Warning / Low quota / Stale
C_RED = "#F54B4B"          # Red / Critical quota / Offline
C_BLUE = "#5AA5FF"         # Google Azure
C_CORAL = "#F58C3C"        # Anthropic Coral
C_PURPLE = "#B98CFF"       # Studio Purple
C_GOLD = "#F7931A"         # Bitcoin Gold

# Title colors per card
CARD_COLORS = {
    "btc": C_GOLD,
    "eth": "#627EEA",
    "sol": "#14F195",
    "doge": "#C2A633",
    "pepe": "#48C774",
    "crypto": C_GOLD,
    "codex": C_GREEN,
    "gemini": C_BLUE,
    "claude": C_CORAL,
    "local_pc": "#37C3F5",
    "dgx_spark": "#76B900",
    "services": C_GREEN,
    "coding": C_PURPLE,
    "ai_activity": C_PURPLE,
    "stocks_volatile": C_ACTIVE_CYAN,
}

SECTION_COLORS = {
    SECTION_CRYPTO: C_GOLD,
    SECTION_AI_USAGE: C_CORAL,
    SECTION_SYSTEM: C_GREEN,
    SECTION_STOCKS: C_ACTIVE_CYAN,
}


class DesktopDashboardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI Desk Dashboard")
        self.root.configure(bg=C_BG)

        # 1. Load Persistent Configuration & Initialize UI Scale
        self.config = DashboardConfig.load()
        ui_scale.update_setting(self.config.ui_scale)

        self.focus_section: Optional[str] = getattr(self.config, "focus_section", None)
        self.creator_mode: bool = getattr(self.config, "creator_mode", False)
        self.creator_aspect: str = getattr(self.config, "creator_aspect", "16:9")
        self.is_fullscreen: bool = False

        # Compute initial window geometry
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        win_w = self.config.window_width if (self.config.window_width and self.config.window_width >= 640) else ui_scale.default_window_w
        win_h = self.config.window_height if (self.config.window_height and self.config.window_height >= 480) else ui_scale.default_window_h

        # Clamp to available screen work area
        win_w = min(win_w, max(640, screen_w - 40))
        win_h = min(win_h, max(480, screen_h - 80))

        if self.config.window_x is not None and self.config.window_y is not None:
            wx = max(0, min(self.config.window_x, screen_w - 120))
            wy = max(0, min(self.config.window_y, screen_h - 120))
            self.root.geometry(f"{win_w}x{win_h}+{wx}+{wy}")
        else:
            cx = max(0, (screen_w - win_w) // 2)
            cy = max(0, (screen_h - win_h) // 2)
            self.root.geometry(f"{win_w}x{win_h}+{cx}+{cy}")

        self.root.minsize(ui_scale.min_window_w, ui_scale.min_window_h)
        self.root.resizable(True, True)

        if self.config.window_maximized:
            try:
                self.root.state("zoomed")
            except Exception:
                pass

        if self.config.launch_minimized or "--minimized" in sys.argv:
            self.root.iconify()

        # 2. Initialize Shared State & Background Workers
        self.state = DashboardState(config=self.config)
        self.engine = DataEngine(self.state, config=self.config)
        self.minitoo = MiniTooController(self.state, config=self.config)
        self.ditoo = DitooController(self.state, config=self.config)

        self.autostart_enabled = WindowsAutostart.is_enabled()
        self.hovered_card: Optional[str] = None
        self.card_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.preset_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.focus_btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.device_btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.creator_btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_crypto_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_stock_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self._ditoo_photo = None
        self._minitoo_photo = None
        self._last_win_size: Optional[Tuple[int, int]] = None
        self._resize_job = None

        # 3. Build GUI Canvas with smooth scroll support
        self.canvas = tk.Canvas(
            self.root,
            width=win_w,
            height=win_h,
            bg=C_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.root.bind("<Configure>", self._on_window_configure)

        # 4. Keyboard Shortcuts (Milestone 14)
        self.root.bind("<Control-comma>", lambda e: self._open_settings())
        self.root.bind("<Control-p>", lambda e: self._open_settings())
        self.root.bind("1", lambda e: self._apply_preset_shortcut(PRESET_ALL))
        self.root.bind("2", lambda e: self._apply_preset_shortcut(PRESET_AI))
        self.root.bind("3", lambda e: self._apply_preset_shortcut(PRESET_CRYPTO))
        self.root.bind("4", lambda e: self._apply_preset_shortcut(PRESET_STOCKS))
        self.root.bind("5", lambda e: self._apply_preset_shortcut(PRESET_SYSTEM))
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self._on_escape())

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.state.add_listener(self._on_state_event)
        self.engine.start()
        self.minitoo.start()
        self.ditoo.start()

        if not self.config.first_run_completed:
            self.root.after(150, self._show_first_run)

        self._render_gui()

    def _show_first_run(self):
        FirstRunDialog(self.root, self.config, on_open_dashboard=self._render_gui)

    def _on_state_event(self, event_type: str, data: Any):
        if event_type in (
            "page_updated",
            "minitoo_status_changed",
            "minitoo_page_changed",
            "ditoo_status_changed",
            "ditoo_frame_updated",
            "device_target_changed",
        ):
            self.root.after_idle(self._render_gui)

    def _on_window_configure(self, event):
        if event.widget == self.root:
            cur_size = (event.width, event.height)
            if hasattr(self, "_last_win_size") and self._last_win_size == cur_size:
                return
            self._last_win_size = cur_size
            if self._resize_job:
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(40, self._render_gui)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _apply_preset_shortcut(self, preset_name: str):
        print(f"[APP] Shortcut applied Preset: {preset_name}")
        self.config.apply_preset(preset_name)
        self.focus_section = None
        self.config.focus_section = None
        self.config.save()
        self._render_gui()

    def _toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        try:
            self.root.attributes("-fullscreen", self.is_fullscreen)
        except Exception:
            pass
        self._render_gui()

    def _on_escape(self):
        if self.is_fullscreen:
            self.is_fullscreen = False
            try:
                self.root.attributes("-fullscreen", False)
            except Exception:
                pass
            self._render_gui()
            return
        if getattr(self, "creator_mode", False):
            self.creator_mode = False
            self.config.creator_mode = False
            self.config.save()
            self._render_gui()
            return
        if self.focus_section:
            self.focus_section = None
            self.config.focus_section = None
            self.config.save()
            self._render_gui()

    def _on_mouse_move(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        prev_hover = self.hovered_card
        self.hovered_card = None

        for p_id, (x1, y1, x2, y2) in self.card_bounds.items():
            if x1 <= canvas_x <= x2 and y1 <= canvas_y <= y2:
                self.hovered_card = p_id
                break

        # Check all clickable elements for hand cursor
        has_hand = False
        clickable_bounds = [
            self.card_bounds,
            self.preset_bounds,
            self.btn_bounds,
            self.focus_btn_bounds,
            self.device_btn_bounds,
            self.creator_btn_bounds,
            self.ditoo_btn_bounds,
            self.ditoo_crypto_bounds,
            self.ditoo_stock_bounds,
        ]
        for b_dict in clickable_bounds:
            for b_name, (bx1, by1, bx2, by2) in b_dict.items():
                if bx1 <= event.x <= bx2 and by1 <= event.y <= by2:
                    has_hand = True
                    break
                if bx1 <= canvas_x <= bx2 and by1 <= canvas_y <= by2:
                    has_hand = True
                    break
            if has_hand:
                break

        self.canvas.config(cursor="hand2" if has_hand else "")

        if self.hovered_card != prev_hover:
            self._render_gui()

    def _show_device_menu(self, event_x: int, event_y: int):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#111622",
            fg=C_TEXT_WHITE,
            activebackground="#1A273D",
            activeforeground=C_ACTIVE_CYAN,
            font=ui_scale.f_btn,
        )
        menu.add_command(label="🖥 MiniToo (160x128 LCD)", command=lambda: self._select_device("minitoo"))
        menu.add_command(label="👾 Ditoo (16x16 Matrix)", command=lambda: self._select_device("ditoo"))
        menu.add_command(label="👁 Dual Preview (Both Displays)", command=lambda: self._select_device("preview"))
        root_x = self.root.winfo_rootx() + event_x
        root_y = self.root.winfo_rooty() + event_y
        menu.tk_popup(root_x, root_y)

    def _select_device(self, dev_name: str):
        if self.config.target_device != dev_name:
            print(f"[APP] Switching target device -> {dev_name.upper()}")
            self.config.target_device = dev_name
            self.config.save()
            self._render_gui()

    def _on_mouse_click(self, event):
        x, y = event.x, event.y
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)

        # 0. Creator Mode Buttons
        if self.creator_mode:
            for c_key, (cx1, cy1, cx2, cy2) in self.creator_btn_bounds.items():
                if cx1 <= x <= cx2 and cy1 <= y <= cy2:
                    if c_key == "exit":
                        self.creator_mode = False
                        self.config.creator_mode = False
                        self.config.save()
                        self._render_gui()
                    elif c_key == "aspect_16_9":
                        self.creator_aspect = "16:9"
                        self.config.creator_aspect = "16:9"
                        self.config.save()
                        self._render_gui()
                    elif c_key == "aspect_9_16":
                        self.creator_aspect = "9:16"
                        self.config.creator_aspect = "9:16"
                        self.config.save()
                        self._render_gui()
                    elif c_key.startswith("preset_"):
                        p_name = c_key.replace("preset_", "")
                        self.config.apply_preset(p_name)
                        self.config.save()
                        self._render_gui()
                    return

        # 1. Focus Mode buttons
        if "back_all" in self.focus_btn_bounds:
            bx1, by1, bx2, by2 = self.focus_btn_bounds["back_all"]
            if (bx1 <= canvas_x <= bx2 and by1 <= canvas_y <= by2) or (bx1 <= x <= bx2 and by1 <= y <= by2):
                self.focus_section = None
                self.config.focus_section = None
                self.config.save()
                self._render_gui()
                return

        for sec_id, (fx1, fy1, fx2, fy2) in self.focus_btn_bounds.items():
            if sec_id != "back_all":
                if (fx1 <= canvas_x <= fx2 and fy1 <= canvas_y <= fy2) or (fx1 <= x <= fx2 and fy1 <= y <= fy2):
                    if self.focus_section == sec_id:
                        self.focus_section = None
                        self.config.focus_section = None
                    else:
                        self.focus_section = sec_id
                        self.config.focus_section = sec_id
                    self.config.save()
                    self._render_gui()
                    return

        # 2. Device Selector Dropdown Button
        if "device_selector" in self.device_btn_bounds:
            dx1, dy1, dx2, dy2 = self.device_btn_bounds["device_selector"]
            if dx1 <= x <= dx2 and dy1 <= y <= dy2:
                self._show_device_menu(dx1, dy2 + 2)
                return

        # 3. Creator Mode Toggle
        if "creator_toggle" in self.btn_bounds:
            cx1, cy1, cx2, cy2 = self.btn_bounds["creator_toggle"]
            if cx1 <= x <= cx2 and cy1 <= y <= cy2:
                self.creator_mode = not self.creator_mode
                self.config.creator_mode = self.creator_mode
                self.config.save()
                self._render_gui()
                return

        # 4. Autostart button
        if "autostart" in self.btn_bounds:
            ax1, ay1, ax2, ay2 = self.btn_bounds["autostart"]
            if ax1 <= x <= ax2 and ay1 <= y <= ay2:
                new_val = not self.autostart_enabled
                if WindowsAutostart.set_enabled(new_val):
                    self.autostart_enabled = new_val
                    self.config.start_with_windows = new_val
                    self.config.save()
                    self._render_gui()
                return

        # 5. Settings button
        if "settings" in self.btn_bounds:
            sx1, sy1, sx2, sy2 = self.btn_bounds["settings"]
            if sx1 <= x <= sx2 and sy1 <= y <= sy2:
                self._open_settings()
                return

        # 6. Preset buttons (in MiniToo mode)
        for p_name, (bx1, by1, bx2, by2) in self.preset_bounds.items():
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                print(f"[APP] Applying Preset: {p_name}")
                self.config.apply_preset(p_name)
                self.focus_section = None
                self.config.focus_section = None
                self.config.save()
                self._render_gui()
                return

        # 7. Ditoo Controls (when in Ditoo mode)
        if self.config.target_device == "ditoo":
            for btn_key, (bx1, by1, bx2, by2) in self.ditoo_btn_bounds.items():
                if (bx1 <= canvas_x <= bx2 and by1 <= canvas_y <= by2) or (bx1 <= x <= bx2 and by1 <= y <= by2):
                    if btn_key == "pause":
                        self.ditoo.toggle_pause()
                    elif btn_key == "prev":
                        self.ditoo.prev_asset()
                    elif btn_key == "next":
                        self.ditoo.next_asset()
                    elif btn_key == "rot_toggle":
                        self.config.ditoo_auto_rotation = not self.config.ditoo_auto_rotation
                        self.config.save()
                    elif btn_key == "bright_down":
                        b = max(10, self.config.ditoo_brightness - 10)
                        self.ditoo.set_brightness(b)
                    elif btn_key == "bright_up":
                        b = min(100, self.config.ditoo_brightness + 10)
                        self.ditoo.set_brightness(b)
                    elif btn_key == "crypto_master":
                        self.config.ditoo_enabled_crypto_page = not self.config.ditoo_enabled_crypto_page
                        self.config.save()
                        self.ditoo.update_config(self.config)
                    elif btn_key == "stock_master":
                        self.config.ditoo_enabled_stock_page = not self.config.ditoo_enabled_stock_page
                        self.config.save()
                        self.ditoo.update_config(self.config)
                    elif btn_key == "dwell_logo_down":
                        self.config.ditoo_frame_logo_dwell = max(0.5, round(self.config.ditoo_frame_logo_dwell - 0.5, 1))
                        self.config.save()
                    elif btn_key == "dwell_logo_up":
                        self.config.ditoo_frame_logo_dwell = min(10.0, round(self.config.ditoo_frame_logo_dwell + 0.5, 1))
                        self.config.save()
                    elif btn_key == "dwell_price_down":
                        self.config.ditoo_frame_price_dwell = max(0.5, round(self.config.ditoo_frame_price_dwell - 0.5, 1))
                        self.config.save()
                    elif btn_key == "dwell_price_up":
                        self.config.ditoo_frame_price_dwell = min(10.0, round(self.config.ditoo_frame_price_dwell + 0.5, 1))
                        self.config.save()
                    elif btn_key == "dwell_change_down":
                        self.config.ditoo_frame_change_dwell = max(0.5, round(self.config.ditoo_frame_change_dwell - 0.5, 1))
                        self.config.save()
                    elif btn_key == "dwell_change_up":
                        self.config.ditoo_frame_change_dwell = min(10.0, round(self.config.ditoo_frame_change_dwell + 0.5, 1))
                        self.config.save()
                    elif btn_key == "add_stock":
                        new_sym = simpledialog.askstring("Add Stock Ticker", "Enter US Stock Symbol (e.g. AMZN, COIN, AMD):", parent=self.root)
                        if new_sym:
                            s_clean = new_sym.strip().upper()
                            if s_clean and s_clean not in self.config.ditoo_stock_tickers:
                                self.config.ditoo_stock_tickers.append(s_clean)
                                self.config.save()
                                self.ditoo.update_config(self.config)
                    self._render_gui()
                    return

            for c_id, (cx1, cy1, cx2, cy2) in self.ditoo_crypto_bounds.items():
                if cx1 <= canvas_x <= cx2 and cy1 <= canvas_y <= cy2:
                    if c_id in self.config.ditoo_enabled_cryptos:
                        if len(self.config.ditoo_enabled_cryptos) > 1 or self.config.ditoo_stock_tickers:
                            self.config.ditoo_enabled_cryptos.remove(c_id)
                    else:
                        self.config.ditoo_enabled_cryptos.append(c_id)
                    self.config.save()
                    self.ditoo.update_config(self.config)
                    self._render_gui()
                    return

            for action, (sx1, sy1, sx2, sy2) in self.ditoo_stock_bounds.items():
                if sx1 <= canvas_x <= sx2 and sy1 <= canvas_y <= sy2:
                    act_type, idx_str = action.split("_", 1)
                    idx = int(idx_str)
                    tickers = self.config.ditoo_stock_tickers
                    if act_type == "up" and idx > 0:
                        tickers[idx - 1], tickers[idx] = tickers[idx], tickers[idx - 1]
                    elif act_type == "down" and idx < len(tickers) - 1:
                        tickers[idx + 1], tickers[idx] = tickers[idx], tickers[idx + 1]
                    elif act_type == "del":
                        if len(tickers) > 1 or self.config.ditoo_enabled_cryptos:
                            tickers.pop(idx)
                    self.config.save()
                    self.ditoo.update_config(self.config)
                    self._render_gui()
                    return

        # 8. Card clicked -> route to MiniToo
        if self.config.target_device == "minitoo":
            for p_id, (cx1, cy1, cx2, cy2) in self.card_bounds.items():
                if cx1 <= canvas_x <= cx2 and cy1 <= canvas_y <= cy2:
                    if self.config.enabled_cards.get(p_id, True):
                        print(f"[APP] Card clicked: {p_id.upper()} -> Routing to MiniToo")
                        self.minitoo.push_page(p_id)
                        self._render_gui()
                    break

    def _open_settings(self):
        SettingsDialog(
            self.root,
            self.config,
            on_save_callback=self._on_settings_saved,
            minitoo=self.minitoo,
            state=self.state,
        )

    def _on_settings_saved(self, new_config: DashboardConfig):
        self.config = new_config
        self.focus_section = new_config.focus_section
        self.creator_mode = getattr(new_config, "creator_mode", False)
        self.creator_aspect = getattr(new_config, "creator_aspect", "16:9")
        self.autostart_enabled = WindowsAutostart.is_enabled()
        ui_scale.update_setting(new_config.ui_scale)
        self.engine.update_config(new_config)
        self.minitoo.update_config(new_config)
        self.ditoo.update_config(new_config)
        self._render_gui()

    def _on_close(self):
        try:
            is_zoomed = (self.root.state() == "zoomed")
            self.config.window_maximized = is_zoomed
            if not is_zoomed and not self.is_fullscreen:
                self.config.window_width = self.root.winfo_width()
                self.config.window_height = self.root.winfo_height()
                wx = self.root.winfo_x()
                wy = self.root.winfo_y()
                if wx >= 0 and wy >= 0:
                    self.config.window_x = wx
                    self.config.window_y = wy
            self.config.creator_mode = self.creator_mode
            self.config.creator_aspect = self.creator_aspect
            self.config.save()
        except Exception:
            pass

        if hasattr(self, "_after_id") and self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self.engine.stop()
        self.minitoo.stop()
        self.ditoo.stop()
        self.root.destroy()
        sys.exit(0)

    # ==========================================================================
    # RENDERING METHODS
    # ==========================================================================
    def _render_gui(self):
        cur_w = self.canvas.winfo_width()
        min_w = ui_scale.min_window_w
        if cur_w < min_w:
            cur_w = self.root.winfo_width()
        if cur_w < min_w:
            cur_w = min_w

        self.canvas.delete("all")
        self.card_bounds.clear()
        self.preset_bounds.clear()
        self.btn_bounds.clear()
        self.focus_btn_bounds.clear()
        self.device_btn_bounds.clear()
        self.creator_btn_bounds.clear()
        self.ditoo_btn_bounds.clear()
        self.ditoo_crypto_bounds.clear()
        self.ditoo_stock_bounds.clear()

        # Handle Creator Capture Mode
        if self.creator_mode:
            curr_y = self._draw_creator_header(cur_w)
            curr_y = self._draw_creator_view(curr_y, cur_w)
            max_scroll_y = max(ui_scale.default_window_h, curr_y + ui_scale.s(30))
            self.canvas.configure(scrollregion=(0, 0, cur_w, max_scroll_y))
            self._schedule_next_refresh()
            return

        # 1. Clean Navigation Bar with Device Selector & Presets
        self._draw_header(cur_w)

        # 2. Main Content View based on Selected Device
        curr_y = ui_scale.header_height + ui_scale.s(10)
        target = getattr(self.config, "target_device", "minitoo").lower()

        if target == "ditoo":
            curr_y = self._draw_ditoo_panel(curr_y, cur_w)
        elif target == "preview":
            curr_y = self._draw_dual_preview_panel(curr_y, cur_w)
        else:
            curr_y = self._draw_minitoo_sections(curr_y, cur_w)

        # 3. Scaled Footer Bar
        self._draw_footer(curr_y, cur_w)

        # Update scrollregion
        max_scroll_y = max(ui_scale.default_window_h, curr_y + ui_scale.footer_height + ui_scale.s(15))
        self.canvas.configure(scrollregion=(0, 0, cur_w, max_scroll_y))
        self._schedule_next_refresh()

    def _schedule_next_refresh(self):
        if hasattr(self, "_after_id") and self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.root.after(350, self._render_gui)

    # --------------------------------------------------------------------------
    # HEADER & CONTROLS (Milestone 14 Polish)
    # --------------------------------------------------------------------------
    def _draw_header(self, cur_w: int):
        target = getattr(self.config, "target_device", "minitoo").lower()
        margin = ui_scale.grid_margin
        btn_h = ui_scale.btn_h
        y_top = ui_scale.s(14)

        # 1. Brand App Title (Consolas 13 bold)
        self.canvas.create_text(
            margin,
            y_top + btn_h // 2,
            text="AI DESK DASHBOARD",
            font=ui_scale.f_app_title,
            fill=C_ACTIVE_CYAN,
            anchor="w",
        )

        title_w = ui_scale.s(170)
        curr_x = margin + title_w + ui_scale.s(12)

        # 2. Sleek Device Selector Dropdown Button
        dev_labels = {
            "minitoo": "🖥 MiniToo ▼",
            "ditoo": "👾 Ditoo ▼",
            "preview": "👁 Dual ▼",
        }
        dev_text = dev_labels.get(target, "🖥 MiniToo ▼")
        dev_w = ui_scale.s(116)
        dev_x1 = curr_x
        dev_y1 = y_top
        dev_x2 = dev_x1 + dev_w
        dev_y2 = dev_y1 + btn_h

        self.canvas.create_rectangle(dev_x1, dev_y1, dev_x2, dev_y2, fill="#101826", outline=C_ACTIVE_CYAN, width=1)
        self.canvas.create_text(
            (dev_x1 + dev_x2) // 2,
            (dev_y1 + dev_y2) // 2,
            text=dev_text,
            font=ui_scale.f_btn,
            fill=C_ACTIVE_CYAN,
            anchor="center",
        )
        self.device_btn_bounds["device_selector"] = (dev_x1, dev_y1, dev_x2, dev_y2)
        curr_x = dev_x2 + ui_scale.s(16)

        # 3. Clean Preset Buttons (Prominent, High Hit Target)
        if target != "ditoo":
            self.canvas.create_text(
                curr_x,
                y_top + btn_h // 2,
                text="PRESET:",
                font=ui_scale.f_meta,
                fill=C_TEXT_DIM,
                anchor="w",
            )
            curr_x += ui_scale.s(52)

            preset_labels = ["ALL", "AI", "CRYPTO", "STOCKS", "SYSTEM"]
            pw = ui_scale.s(56)

            for p_name in preset_labels:
                is_active = (self.config.active_preset == p_name and not self.focus_section)
                p_bg = "#0B384A" if is_active else "#101622"
                p_fg = C_ACTIVE_CYAN if is_active else C_TEXT_MUTED
                p_border = C_ACTIVE_CYAN if is_active else "#1C2536"

                bx1 = curr_x
                by1 = y_top
                bx2 = bx1 + pw
                by2 = by1 + btn_h

                self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=p_bg, outline=p_border, width=2 if is_active else 1)
                self.canvas.create_text(
                    (bx1 + bx2) // 2,
                    (by1 + by2) // 2,
                    text=p_name,
                    font=ui_scale.f_btn,
                    fill=p_fg,
                    anchor="center",
                )
                self.preset_bounds[p_name] = (bx1, by1, bx2, by2)
                curr_x += pw + ui_scale.s(6)

            if self.focus_section:
                ex_w = ui_scale.s(82)
                ex_x1 = curr_x + ui_scale.s(4)
                ex_x2 = ex_x1 + ex_w
                self.canvas.create_rectangle(ex_x1, y_top, ex_x2, y_top + btn_h, fill="#2A1717", outline=C_RED, width=1)
                self.canvas.create_text(
                    (ex_x1 + ex_x2) // 2,
                    y_top + btn_h // 2,
                    text="✕ FOCUS",
                    font=ui_scale.f_btn,
                    fill=C_RED,
                    anchor="center",
                )
                self.focus_btn_bounds["back_all"] = (ex_x1, y_top, ex_x2, y_top + btn_h)

        elif target == "ditoo":
            # Ditoo Playback Quick Controls on Navigation Bar
            d_btns = [
                ("prev", "◀ PREV", ui_scale.s(60), "#121A28", C_TEXT_WHITE),
                ("pause", "▶ RESUME" if self.config.ditoo_is_paused else "⏸ PAUSE", ui_scale.s(78), "#261D0D" if self.config.ditoo_is_paused else "#0D261B", C_AMBER if self.config.ditoo_is_paused else C_GREEN),
                ("next", "NEXT ▶", ui_scale.s(60), "#121A28", C_TEXT_WHITE),
                ("rot_toggle", "ROT: ON" if self.config.ditoo_auto_rotation else "ROT: OFF", ui_scale.s(68), "#121A28", C_GREEN if self.config.ditoo_auto_rotation else C_TEXT_MUTED),
            ]
            for b_key, b_label, b_w, b_bg, b_fg in d_btns:
                bx1 = curr_x
                bx2 = bx1 + b_w
                self.canvas.create_rectangle(bx1, y_top, bx2, y_top + btn_h, fill=b_bg, outline="#202A3C")
                self.canvas.create_text((bx1 + bx2) // 2, y_top + btn_h // 2, text=b_label, font=ui_scale.f_btn, fill=b_fg, anchor="center")
                self.ditoo_btn_bounds[b_key] = (bx1, y_top, bx2, y_top + btn_h)
                curr_x += b_w + ui_scale.s(6)

        # 4. Right-Side Utility Bar: Settings, Autostart, Creator View, Status Pill
        set_w = ui_scale.s(96)
        set_x2 = cur_w - margin
        set_x1 = set_x2 - set_w
        self.canvas.create_rectangle(set_x1, y_top, set_x2, y_top + btn_h, fill="#131B2A", outline="#25354F", width=1)
        self.canvas.create_text(
            (set_x1 + set_x2) // 2,
            y_top + btn_h // 2,
            text="⚙ SETTINGS",
            font=ui_scale.f_btn,
            fill=C_ACTIVE_CYAN,
            anchor="center",
        )
        self.btn_bounds["settings"] = (set_x1, y_top, set_x2, y_top + btn_h)

        # Autostart Toggle
        auto_w = ui_scale.s(104)
        auto_x2 = set_x1 - ui_scale.s(8)
        auto_x1 = auto_x2 - auto_w
        auto_text = "AUTO: ON" if self.autostart_enabled else "AUTO: OFF"
        auto_fg = C_GREEN if self.autostart_enabled else C_TEXT_MUTED
        auto_bg = "#0E2419" if self.autostart_enabled else "#151B27"
        auto_border = "#1E4733" if self.autostart_enabled else "#253047"

        self.canvas.create_rectangle(auto_x1, y_top, auto_x2, y_top + btn_h, fill=auto_bg, outline=auto_border, width=1)
        self.canvas.create_text(
            (auto_x1 + auto_x2) // 2,
            y_top + btn_h // 2,
            text=f"⚡ {auto_text}",
            font=ui_scale.f_btn,
            fill=auto_fg,
            anchor="center",
        )
        self.btn_bounds["autostart"] = (auto_x1, y_top, auto_x2, y_top + btn_h)

        # Creator View Button
        creat_w = ui_scale.s(94)
        creat_x2 = auto_x1 - ui_scale.s(8)
        creat_x1 = creat_x2 - creat_w
        self.canvas.create_rectangle(creat_x1, y_top, creat_x2, y_top + btn_h, fill="#1B1428", outline="#40255F", width=1)
        self.canvas.create_text(
            (creat_x1 + creat_x2) // 2,
            y_top + btn_h // 2,
            text="🎬 CREATOR",
            font=ui_scale.f_btn,
            fill=C_PURPLE,
            anchor="center",
        )
        self.btn_bounds["creator_toggle"] = (creat_x1, y_top, creat_x2, y_top + btn_h)

        # Connection Status Pill
        if target == "ditoo":
            conn = self.state.ditoo_connected
            status_str = self.state.ditoo_status_text
            pill_color = C_GREEN if conn else (C_AMBER if "RECONNECTING" in status_str else C_RED)
            pill_bg = "#0D261B" if conn else ("#261D0D" if "RECONNECTING" in status_str else "#2A1111")
            pill_border = "#1B4D36" if conn else ("#4D361B" if "RECONNECTING" in status_str else "#4D1B1B")
        elif target == "preview":
            conn = self.state.ditoo_connected or self.state.minitoo_connected
            d_st = "DITOO ● " if self.state.ditoo_connected else "DITOO ○ "
            m_st = "MINITOO ●" if self.state.minitoo_connected else "MINITOO ○"
            status_str = f"DUAL: {d_st}| {m_st}"
            pill_color = C_ACTIVE_CYAN if conn else C_AMBER
            pill_bg = "#09222E"
            pill_border = "#13495F"
        else:
            conn = self.state.minitoo_connected
            status_str = self.state.minitoo_status_text
            pill_color = C_GREEN if conn else C_AMBER
            pill_bg = "#0D261B" if conn else "#261D0D"
            pill_border = "#1B4D36" if conn else "#4D361B"

        pill_w = ui_scale.s(138)
        px2 = creat_x1 - ui_scale.s(10)
        px1 = px2 - pill_w
        if px1 > curr_x + ui_scale.s(10):
            self.canvas.create_rectangle(px1, y_top, px2, y_top + btn_h, fill=pill_bg, outline=pill_border, width=1)
            dot_r = ui_scale.s(3)
            dot_cx = px1 + ui_scale.s(10)
            dot_cy = y_top + btn_h // 2
            self.canvas.create_oval(dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r, fill=pill_color, outline="")
            self.canvas.create_text(
                px1 + ui_scale.s(20),
                y_top + btn_h // 2,
                text=status_str[:22],
                font=ui_scale.f_meta,
                fill=pill_color,
                anchor="w",
            )

        # Subtle divider under header
        self.canvas.create_line(0, ui_scale.header_height, cur_w, ui_scale.header_height, fill="#151D2A", width=1)

    # --------------------------------------------------------------------------
    # CREATOR CAPTURE VIEW (Milestone 14 - Shorts / 16:9 Filming Surface)
    # --------------------------------------------------------------------------
    def _draw_creator_header(self, cur_w: int) -> int:
        margin = ui_scale.grid_margin
        btn_h = ui_scale.btn_h
        y_top = ui_scale.s(12)

        # Exit Button
        ex_w = ui_scale.s(130)
        self.canvas.create_rectangle(margin, y_top, margin + ex_w, y_top + btn_h, fill="#2B1414", outline=C_RED, width=1)
        self.canvas.create_text(
            margin + ex_w // 2,
            y_top + btn_h // 2,
            text="✕ EXIT CREATOR (Esc)",
            font=ui_scale.f_btn,
            fill=C_RED,
            anchor="center",
        )
        self.creator_btn_bounds["exit"] = (margin, y_top, margin + ex_w, y_top + btn_h)

        # Aspect Ratio Selector: 16:9 / 9:16 Shorts
        ax = margin + ex_w + ui_scale.s(16)
        self.canvas.create_text(ax, y_top + btn_h // 2, text="CAPTURE RATIO:", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
        ax += ui_scale.s(96)

        asp_16 = (self.creator_aspect == "16:9")
        asp_9 = (self.creator_aspect == "9:16")

        self.canvas.create_rectangle(ax, y_top, ax + ui_scale.s(64), y_top + btn_h, fill="#0B384A" if asp_16 else "#101622", outline=C_ACTIVE_CYAN if asp_16 else "#1C2536", width=2 if asp_16 else 1)
        self.canvas.create_text(ax + ui_scale.s(32), y_top + btn_h // 2, text="16:9", font=ui_scale.f_btn, fill=C_ACTIVE_CYAN if asp_16 else C_TEXT_MUTED, anchor="center")
        self.creator_btn_bounds["aspect_16_9"] = (ax, y_top, ax + ui_scale.s(64), y_top + btn_h)
        ax += ui_scale.s(70)

        self.canvas.create_rectangle(ax, y_top, ax + ui_scale.s(92), y_top + btn_h, fill="#0B384A" if asp_9 else "#101622", outline=C_ACTIVE_CYAN if asp_9 else "#1C2536", width=2 if asp_9 else 1)
        self.canvas.create_text(ax + ui_scale.s(46), y_top + btn_h // 2, text="9:16 SHORTS", font=ui_scale.f_btn, fill=C_ACTIVE_CYAN if asp_9 else C_TEXT_MUTED, anchor="center")
        self.creator_btn_bounds["aspect_9_16"] = (ax, y_top, ax + ui_scale.s(92), y_top + btn_h)
        ax += ui_scale.s(102)

        # Section Presets
        self.canvas.create_text(ax, y_top + btn_h // 2, text="PRESET:", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
        ax += ui_scale.s(52)
        for p_name in ["ALL", "AI", "CRYPTO", "STOCKS", "SYSTEM"]:
            is_active = (self.config.active_preset == p_name)
            pw = ui_scale.s(56)
            self.canvas.create_rectangle(ax, y_top, ax + pw, y_top + btn_h, fill="#0B384A" if is_active else "#101622", outline=C_ACTIVE_CYAN if is_active else "#1C2536", width=2 if is_active else 1)
            self.canvas.create_text(ax + pw // 2, y_top + btn_h // 2, text=p_name, font=ui_scale.f_btn, fill=C_ACTIVE_CYAN if is_active else C_TEXT_MUTED, anchor="center")
            self.creator_btn_bounds[f"preset_{p_name}"] = (ax, y_top, ax + pw, y_top + btn_h)
            ax += pw + ui_scale.s(6)

        # Subtle indicator line
        sep_y = y_top + btn_h + ui_scale.s(10)
        self.canvas.create_line(0, sep_y, cur_w, sep_y, fill="#1C2536", width=1)
        return sep_y + ui_scale.s(12)

    def _draw_creator_view(self, curr_y: int, cur_w: int) -> int:
        preset = self.config.active_preset
        is_vertical = (self.creator_aspect == "9:16")

        if is_vertical:
            # 9:16 Vertical Capture layout (Shorts / Reels)
            # Center a clean column of fixed readable width
            col_w = min(ui_scale.s(500), cur_w - 2 * ui_scale.grid_margin)
            cx1 = max(ui_scale.grid_margin, (cur_w - col_w) // 2)
            cx2 = cx1 + col_w

            if preset == PRESET_CRYPTO or preset == PRESET_ALL:
                coins = ["btc", "eth", "sol", "doge", "pepe"]
                card_h = ui_scale.s(140)
                for coin in coins:
                    self.card_bounds[coin] = (cx1, curr_y, cx2, curr_y + card_h)
                    page_data = self.state.get_page(coin)
                    is_active = (coin == self.state.minitoo_active_page)
                    is_hover = (coin == self.hovered_card)
                    self._draw_crypto_asset_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    curr_y += card_h + ui_scale.gap
                return curr_y

            elif preset == PRESET_AI:
                ai_cards = ["codex", "gemini", "claude", "ai_activity"]
                card_h = ui_scale.s(160)
                for c_id in ai_cards:
                    self.card_bounds[c_id] = (cx1, curr_y, cx2, curr_y + card_h)
                    page_data = self.state.get_page(c_id)
                    if c_id == "ai_activity":
                        self._draw_activity_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    else:
                        self._draw_ai_quota_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    curr_y += card_h + ui_scale.gap
                return curr_y

            elif preset == PRESET_STOCKS:
                self.card_bounds["stocks_volatile"] = (cx1, curr_y, cx2, curr_y + ui_scale.s(320))
                page_data = self.state.get_page("stocks_volatile")
                self._draw_stocks_volatile_card(page_data, cx1, curr_y, cx2, curr_y + ui_scale.s(320), False, False, True)
                return curr_y + ui_scale.s(320) + ui_scale.gap

            elif preset == PRESET_SYSTEM:
                sys_cards = ["local_pc", "dgx_spark", "services"]
                card_h = ui_scale.s(150)
                for c_id in sys_cards:
                    self.card_bounds[c_id] = (cx1, curr_y, cx2, curr_y + card_h)
                    page_data = self.state.get_page(c_id)
                    if c_id == "local_pc":
                        self._draw_local_pc_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    elif c_id == "dgx_spark":
                        self._draw_dgx_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    elif c_id == "services":
                        self._draw_services_card(page_data, cx1, curr_y, cx2, curr_y + card_h, True)
                    curr_y += card_h + ui_scale.gap
                return curr_y

        # 16:9 Widescreen clean composition
        return self._draw_minitoo_sections(curr_y, cur_w)

    # --------------------------------------------------------------------------
    # MINITOO RESPONSIVE GRID & SECTIONS (Milestone 14 Reflow Math)
    # --------------------------------------------------------------------------
    def _draw_minitoo_sections(self, curr_y: int, cur_w: int) -> int:
        if self.focus_section:
            sec_id = self.focus_section
            sec_title = SECTION_TITLES.get(sec_id, sec_id.upper())
            sec_color = SECTION_COLORS.get(sec_id, C_ACTIVE_CYAN)

            # Focus Mode Header Banner
            b_x1 = ui_scale.grid_margin
            b_y1 = curr_y
            b_x2 = cur_w - ui_scale.grid_margin
            b_h = ui_scale.s(44)
            b_y2 = b_y1 + b_h

            self.canvas.create_rectangle(b_x1, b_y1, b_x2, b_y2, fill="#0E1624", outline=C_ACTIVE_CYAN, width=1)

            # Prominent Back / All Sections Button
            back_x1 = b_x1 + ui_scale.s(6)
            back_y1 = b_y1 + ui_scale.s(6)
            back_x2 = back_x1 + ui_scale.s(140)
            back_y2 = b_y2 - ui_scale.s(6)
            self.canvas.create_rectangle(back_x1, back_y1, back_x2, back_y2, fill="#15263B", outline=C_ACTIVE_CYAN, width=1)
            self.canvas.create_text(
                (back_x1 + back_x2) // 2,
                (back_y1 + back_y2) // 2,
                text="◀ BACK TO ALL (Esc)",
                font=ui_scale.f_btn,
                fill=C_ACTIVE_CYAN,
                anchor="center",
            )
            self.focus_btn_bounds["back_all"] = (back_x1, back_y1, back_x2, back_y2)

            self.canvas.create_text(
                back_x2 + ui_scale.s(16),
                (b_y1 + b_y2) // 2,
                text=f"FOCUS PRESENTATION MODE: {sec_title}",
                font=ui_scale.f_section_title,
                fill=sec_color,
                anchor="w",
            )
            self.canvas.create_text(
                b_x2 - ui_scale.s(14),
                (b_y1 + b_y2) // 2,
                text="FULL COMMAND CENTER VIEW · 1080p/1440p",
                font=ui_scale.f_meta,
                fill=C_TEXT_DIM,
                anchor="e",
            )
            curr_y = b_y2 + ui_scale.gap + ui_scale.s(4)

            if sec_id == SECTION_CRYPTO:
                return self._draw_focus_crypto(curr_y, cur_w)
            elif sec_id == SECTION_AI_USAGE:
                return self._draw_focus_ai(curr_y, cur_w)
            elif sec_id == SECTION_STOCKS:
                return self._draw_focus_stocks(curr_y, cur_w)
            elif sec_id == SECTION_SYSTEM:
                return self._draw_focus_system(curr_y, cur_w)

        # Standard Multi-Section View with Responsive Card Reflow
        margin = ui_scale.grid_margin
        gap = ui_scale.gap
        avail_w = cur_w - 2 * margin

        for sec_id in self.config.sections_order:
            if not self.config.enabled_sections.get(sec_id, True):
                continue

            sec_title = SECTION_TITLES.get(sec_id, sec_id.upper())
            sec_color = SECTION_COLORS.get(sec_id, C_TEXT_MUTED)

            # Generous Breathing Room above Section Header
            curr_y += ui_scale.s(14)

            # Section Header Text
            self.canvas.create_text(
                margin,
                curr_y + ui_scale.s(10),
                text=f"─── [ {sec_title} ] ",
                font=ui_scale.f_section_title,
                fill=sec_color,
                anchor="w",
            )

            # Dedicated Focus button beside section header
            fx1 = margin + ui_scale.s(150)
            fy1 = curr_y
            fx2 = fx1 + ui_scale.s(78)
            fy2 = curr_y + ui_scale.s(22)
            self.canvas.create_rectangle(fx1, fy1, fx2, fy2, fill="#131B2A", outline="#25354F", width=1)
            self.canvas.create_text(
                (fx1 + fx2) // 2,
                curr_y + ui_scale.s(10),
                text="[ 🔍 FOCUS ]",
                font=ui_scale.f_btn,
                fill=C_ACTIVE_CYAN,
                anchor="center",
            )
            self.focus_btn_bounds[sec_id] = (fx1, fy1, fx2, fy2)

            # Subtle trailing divider across section
            self.canvas.create_line(
                fx2 + ui_scale.s(10),
                curr_y + ui_scale.s(10),
                cur_w - margin,
                curr_y + ui_scale.s(10),
                fill="#161F2E",
                width=1,
            )
            curr_y += ui_scale.s(28)

            # Cards in this section
            cards = [c for c in self.config.section_cards.get(sec_id, []) if self.config.enabled_cards.get(c, True)]
            if not cards:
                self.canvas.create_text(
                    margin + ui_scale.s(12),
                    curr_y + ui_scale.s(12),
                    text="All cards in this section are currently disabled in Settings.",
                    font=ui_scale.f_meta,
                    fill=C_TEXT_DIM,
                    anchor="w",
                )
                curr_y += ui_scale.s(32)
                continue

            # Special layout for stocks scanner card: wide responsive card
            if sec_id == SECTION_STOCKS and "stocks_volatile" in cards:
                sx1 = margin
                sy1 = curr_y
                sx2 = cur_w - margin
                stock_h = ui_scale.s(150)
                sy2 = sy1 + stock_h

                self.card_bounds["stocks_volatile"] = (sx1, sy1, sx2, sy2)
                page_data = self.state.get_page("stocks_volatile")
                is_active = ("stocks_volatile" == self.state.minitoo_active_page)
                is_hover = ("stocks_volatile" == self.hovered_card)
                is_enabled = self.config.enabled_cards.get("stocks_volatile", True)

                self._draw_stocks_volatile_card(page_data, sx1, sy1, sx2, sy2, is_active, is_hover, is_enabled)
                curr_y = sy2 + gap
                continue

            # Dynamic responsive grid calculation:
            # - Maintain readable card width (card_min_w)
            # - Limit maximum card width (card_max_w) so cards never stretch into ultra-wide rectangles
            # - Center the grid when capped at card_max_w
            num_cols = max(1, min(len(cards), (avail_w + gap) // (ui_scale.card_min_w + gap)))
            card_w = (avail_w - (num_cols - 1) * gap) // num_cols
            if card_w > ui_scale.card_max_w:
                card_w = ui_scale.card_max_w

            grid_total_w = num_cols * card_w + (num_cols - 1) * gap
            grid_start_x = margin + max(0, (avail_w - grid_total_w) // 2)
            card_h = ui_scale.card_h

            for idx, p_id in enumerate(cards):
                col = idx % num_cols
                row = idx // num_cols
                cx1 = grid_start_x + col * (card_w + gap)
                cy1 = curr_y + row * (card_h + gap)
                cx2 = cx1 + card_w
                cy2 = cy1 + card_h

                self.card_bounds[p_id] = (cx1, cy1, cx2, cy2)
                page_data = self.state.get_page(p_id)
                is_active = (p_id == self.state.minitoo_active_page)
                is_hover = (p_id == self.hovered_card)
                is_enabled = self.config.enabled_cards.get(p_id, True)

                self._draw_card(p_id, page_data, cx1, cy1, cx2, cy2, is_active, is_hover, is_enabled)

            total_rows = (len(cards) + num_cols - 1) // num_cols
            curr_y += total_rows * (card_h + gap) + ui_scale.s(6)

        return curr_y

    # --------------------------------------------------------------------------
    # FOCUS MODE RENDERERS (Aggressive Window Utilization & Large Sparklines)
    # --------------------------------------------------------------------------
    def _draw_focus_crypto(self, curr_y: int, cur_w: int) -> int:
        crypto_cards = ["btc", "eth", "sol", "doge", "pepe"]
        cards = [c for c in self.config.section_cards.get(SECTION_CRYPTO, crypto_cards) if self.config.enabled_cards.get(c, True) and c != "crypto"]
        if not cards:
            cards = crypto_cards

        margin = ui_scale.grid_margin
        gap = ui_scale.gap
        avail_w = cur_w - 2 * margin

        # In Focus Mode on wide monitors, place 3 or 4 large asset cards per row
        num_cols = max(1, min(len(cards), (avail_w + gap) // (ui_scale.s(320) + gap)))
        card_w = (avail_w - (num_cols - 1) * gap) // num_cols
        card_h = ui_scale.focus_card_h

        asset_titles = {
            "btc": "BTC · BITCOIN",
            "eth": "ETH · ETHEREUM",
            "sol": "SOL · SOLANA",
            "doge": "DOGE · DOGECOIN",
            "pepe": "PEPE · PEPE",
        }

        for idx, p_id in enumerate(cards):
            col = idx % num_cols
            row = idx // num_cols
            cx1 = margin + col * (card_w + gap)
            cy1 = curr_y + row * (card_h + gap)
            cx2 = cx1 + card_w
            cy2 = cy1 + card_h

            self.card_bounds[p_id] = (cx1, cy1, cx2, cy2)
            page_data = self.state.get_page(p_id)
            is_active = (p_id == self.state.minitoo_active_page)
            is_hover = (p_id == self.hovered_card)

            border_c = C_ACTIVE_CYAN if is_active else (C_CARD_HOVER if is_hover else C_CARD_BORDER)
            bg_c = "#121A2B" if is_active else ("#141A28" if is_hover else C_CARD_BG)
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, fill=bg_c, outline=border_c, width=2 if is_active else 1)

            t_color = CARD_COLORS.get(p_id, C_GOLD)
            t_text = asset_titles.get(p_id, p_id.upper())
            self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(18), text=t_text, font=ui_scale.f_card_title, fill=t_color, anchor="w")

            if is_active:
                tag_w = ui_scale.s(82)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text="ON MINITOO", font=ui_scale.f_badge, fill=C_ACTIVE_CYAN, anchor="center")
            else:
                tag_w = ui_scale.s(68)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill="#131926", outline="#202A3C")
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text="SPOT 24H", font=ui_scale.f_badge, fill=C_TEXT_MUTED, anchor="center")

            # Primary Metric (Large 24pt bold in Focus Mode)
            price_str = page_data.primary_metric.value if (page_data and page_data.primary_metric) else "N/A"
            change_str = page_data.sparkline_change if page_data else ""
            self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(48), text=price_str, font=ui_scale.f_primary_metric_focus, fill=t_color, anchor="w")

            chg_c = C_GREEN if not change_str.startswith("-") else C_RED
            self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(48), text=change_str, font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")

            # High-res Sparkline (80px height in Focus Mode)
            spark_data = page_data.sparkline_data if page_data else []
            if spark_data and len(spark_data) >= 2:
                sp_x1 = cx1 + ui_scale.s(14)
                sp_y1 = cy1 + ui_scale.s(72)
                sp_x2 = cx2 - ui_scale.s(14)
                sp_y2 = cy2 - ui_scale.s(32)

                mn = min(spark_data)
                mx = max(spark_data)
                span = (mx - mn) if mx != mn else 1.0

                pts = []
                for i, val in enumerate(spark_data):
                    px = sp_x1 + i * ((sp_x2 - sp_x1) / (len(spark_data) - 1))
                    py = sp_y2 - ((val - mn) / span) * (sp_y2 - sp_y1)
                    pts.append((px, py))

                for i in range(len(pts) - 1):
                    self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill=t_color, width=2)
                self.canvas.create_oval(pts[-1][0] - 3, pts[-1][1] - 3, pts[-1][0] + 3, pts[-1][1] + 3, fill=t_color, outline="")

            hi = page_data.sparkline_high if page_data else ""
            lo = page_data.sparkline_low if page_data else ""
            self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text=f"24H HIGH: {hi}   LOW: {lo}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(cx2 - ui_scale.s(14), cy2 - ui_scale.s(14), text="COINGECKO SPOT CACHE", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="e")

        total_rows = (len(cards) + num_cols - 1) // num_cols
        return curr_y + total_rows * (card_h + gap) + ui_scale.s(6)

    def _draw_focus_ai(self, curr_y: int, cur_w: int) -> int:
        cards = [c for c in ["codex", "gemini", "claude", "ai_activity"] if self.config.enabled_cards.get(c, True)]
        if not cards:
            cards = ["codex", "gemini", "claude"]

        margin = ui_scale.grid_margin
        gap = ui_scale.gap
        avail_w = cur_w - 2 * margin

        num_cols = max(1, min(len(cards), (avail_w + gap) // (ui_scale.s(380) + gap)))
        card_w = (avail_w - (num_cols - 1) * gap) // num_cols
        card_h = ui_scale.focus_card_h

        for idx, p_id in enumerate(cards):
            col = idx % num_cols
            row = idx // num_cols
            cx1 = margin + col * (card_w + gap)
            cy1 = curr_y + row * (card_h + gap)
            cx2 = cx1 + card_w
            cy2 = cy1 + card_h

            self.card_bounds[p_id] = (cx1, cy1, cx2, cy2)
            page_data = self.state.get_page(p_id)
            is_active = (p_id == self.state.minitoo_active_page)
            is_hover = (p_id == self.hovered_card)

            border_c = C_ACTIVE_CYAN if is_active else (C_CARD_HOVER if is_hover else C_CARD_BORDER)
            bg_c = "#121A2B" if is_active else ("#141A28" if is_hover else C_CARD_BG)
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, fill=bg_c, outline=border_c, width=2 if is_active else 1)

            t_color = CARD_COLORS.get(p_id, C_TEXT_WHITE)
            title_str = page_data.title if page_data else p_id.upper()
            self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(18), text=title_str, font=ui_scale.f_card_title, fill=t_color, anchor="w")

            if is_active:
                tag_w = ui_scale.s(82)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text="ON MINITOO", font=ui_scale.f_badge, fill=C_ACTIVE_CYAN, anchor="center")
            elif page_data:
                b_color = C_GREEN if page_data.badge_color == "green" else (C_AMBER if page_data.badge_color == "amber" else C_TEXT_MUTED)
                tag_w = ui_scale.s(72)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill="#131926", outline="#202A3C")
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text=page_data.badge[:12], font=ui_scale.f_badge, fill=b_color, anchor="center")

            if p_id in ("codex", "gemini", "claude"):
                pm = page_data.primary_metric if page_data else None
                sm = page_data.secondary_metric if page_data else None

                p_pct = pm.remaining_pct if (pm and pm.remaining_pct is not None) else (pm.pct if pm else None)
                if p_pct is not None:
                    p_text = f"{int(p_pct)}% LEFT"
                    p_col = C_GREEN if p_pct >= 30 else (C_AMBER if p_pct >= 15 else C_RED)
                elif pm and pm.value and pm.value != "N/A":
                    p_text = pm.value
                    p_col = C_GREEN
                else:
                    p_text = "N/A"
                    p_col = C_TEXT_DIM

                p_label = pm.label if pm else "PRIMARY LIMIT"
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(46), text=p_label, font=ui_scale.f_secondary_metric, fill=C_TEXT_MUTED, anchor="w")
                self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(46), text=p_text, font=ui_scale.f_primary_metric_focus, fill=p_col, anchor="e")
                self._draw_segmented_bar(cx1 + ui_scale.s(14), cy1 + ui_scale.s(60), card_w - ui_scale.s(28), ui_scale.s(10), p_pct, p_col, num_blocks=16)
                p_reset = pm.reset if (pm and pm.reset) else "RESET N/A"
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(78), text=p_reset, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

                s_pct = sm.remaining_pct if (sm and sm.remaining_pct is not None) else (sm.pct if sm else None)
                if s_pct is not None:
                    s_text = f"{int(s_pct)}% LEFT"
                    s_col = C_GREEN if s_pct >= 30 else (C_AMBER if s_pct >= 15 else C_RED)
                elif sm and sm.value and sm.value != "N/A":
                    s_text = sm.value
                    s_col = C_GREEN
                else:
                    s_text = "N/A"
                    s_col = C_TEXT_DIM

                s_label = sm.label if sm else "WEEKLY LIMIT"
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(104), text=s_label, font=ui_scale.f_secondary_metric, fill=C_TEXT_MUTED, anchor="w")
                self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(104), text=s_text, font=ui_scale.f_primary_metric, fill=s_col, anchor="e")
                self._draw_segmented_bar(cx1 + ui_scale.s(14), cy1 + ui_scale.s(118), card_w - ui_scale.s(28), ui_scale.s(8), s_pct, s_col, num_blocks=16)
                s_reset = sm.reset if (sm and sm.reset) else "RESET N/A"
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(136), text=s_reset, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

                if p_id == "claude" and page_data and page_data.extra_metrics:
                    acc_info = page_data.extra_metrics[0].value if page_data.extra_metrics else ""
                    self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text=f"{acc_info} · {page_data.footer_right}", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")
                elif page_data:
                    self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text=page_data.footer_right or "AI TELEMETRY", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")

            elif p_id == "ai_activity":
                items = page_data.items_list if page_data else []
                for i_idx, it in enumerate(items[:4]):
                    iy = cy1 + ui_scale.s(44) + i_idx * ui_scale.s(32)
                    name = it.get("name", "AGENT")
                    working = it.get("working", False)
                    elapsed = it.get("elapsed", "")

                    dot_c = C_GREEN if working else C_TEXT_DIM
                    stat_t = "WORKING" if working else "IDLE"

                    self.canvas.create_oval(cx1 + ui_scale.s(14), iy + ui_scale.s(4), cx1 + ui_scale.s(22), iy + ui_scale.s(12), fill=dot_c, outline="")
                    self.canvas.create_text(cx1 + ui_scale.s(28), iy + ui_scale.s(8), text=name[:18], font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
                    self.canvas.create_text(cx2 - ui_scale.s(14), iy + ui_scale.s(8), text=stat_t, font=ui_scale.f_secondary_metric, fill=dot_c, anchor="e")
                    if working and elapsed:
                        self.canvas.create_text(cx1 + ui_scale.s(28), iy + ui_scale.s(22), text=f"active {elapsed.lower()}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

                self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text="AGENT POOL / LOCAL DAEMONS", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")

        total_rows = (len(cards) + num_cols - 1) // num_cols
        return curr_y + total_rows * (card_h + gap) + ui_scale.s(6)

    def _draw_focus_stocks(self, curr_y: int, cur_w: int) -> int:
        margin = ui_scale.grid_margin
        sx1 = margin
        sy1 = curr_y
        sx2 = cur_w - margin
        table_h = ui_scale.s(310)
        sy2 = sy1 + table_h

        self.card_bounds["stocks_volatile"] = (sx1, sy1, sx2, sy2)
        page_data = self.state.get_page("stocks_volatile")
        is_active = ("stocks_volatile" == self.state.minitoo_active_page)
        is_hover = ("stocks_volatile" == self.hovered_card)

        border_c = C_ACTIVE_CYAN if is_active else (C_CARD_HOVER if is_hover else C_CARD_BORDER)
        bg_c = "#121A2B" if is_active else C_CARD_BG
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill=bg_c, outline=border_c, width=2 if is_active else 1)

        self.canvas.create_text(sx1 + ui_scale.s(16), sy1 + ui_scale.s(20), text="TOP 10 MOST VOLATILE US STOCKS TODAY", font=ui_scale.f_card_title, fill=C_ACTIVE_CYAN, anchor="w")

        mkt_badge = page_data.badge if page_data else "REGULAR"
        b_c = C_GREEN if "OPEN" in mkt_badge or "REG" in mkt_badge else C_AMBER
        tag_w = ui_scale.s(82)
        self.canvas.create_rectangle(sx2 - tag_w - ui_scale.s(14), sy1 + ui_scale.s(10), sx2 - ui_scale.s(14), sy1 + ui_scale.s(28), fill="#131926", outline="#202A3C")
        self.canvas.create_text(sx2 - tag_w // 2 - ui_scale.s(14), sy1 + ui_scale.s(19), text=mkt_badge, font=ui_scale.f_badge, fill=b_c, anchor="center")

        quotes = page_data.stocks_data if page_data else []
        if not quotes:
            self.canvas.create_text((sx1 + sx2) // 2, (sy1 + sy2) // 2, text="COLLECTING MARKET VOLATILITY...", font=ui_scale.f_secondary_metric, fill=C_TEXT_DIM, anchor="center")
            return sy2 + ui_scale.gap

        mid_x = (sx1 + sx2) // 2
        row_h = ui_scale.s(25)

        # Left Column: Ranks 1 to 5
        for idx, q in enumerate(quotes[:5]):
            ry = sy1 + ui_scale.s(48) + idx * row_h
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(sx1 + ui_scale.s(16), ry, text=f"#{idx+1}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(sx1 + ui_scale.s(44), ry, text=q.symbol, font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(sx1 + ui_scale.s(110), ry, text=f"${q.price:,.2f}", font=ui_scale.f_body, fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(sx1 + ui_scale.s(210), ry, text=f"{q.change_pct:+.1f}%", font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")
            self.canvas.create_text(mid_x - ui_scale.s(20), ry, text=f"VOL {q.volatility_pct:.1f}%", font=ui_scale.f_secondary_metric, fill=C_ACTIVE_CYAN, anchor="e")

        self.canvas.create_line(mid_x, sy1 + ui_scale.s(40), mid_x, sy2 - ui_scale.s(30), fill="#1A2436", width=1)

        # Right Column: Ranks 6 to 10
        for idx, q in enumerate(quotes[5:10]):
            ry = sy1 + ui_scale.s(48) + idx * row_h
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(mid_x + ui_scale.s(20), ry, text=f"#{idx+6}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(48), ry, text=q.symbol, font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(114), ry, text=f"${q.price:,.2f}", font=ui_scale.f_body, fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(214), ry, text=f"{q.change_pct:+.1f}%", font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")
            self.canvas.create_text(sx2 - ui_scale.s(20), ry, text=f"VOL {q.volatility_pct:.1f}%", font=ui_scale.f_secondary_metric, fill=C_ACTIVE_CYAN, anchor="e")

        footer_str = "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance High-Frequency Poller"
        self.canvas.create_text(sx1 + ui_scale.s(16), sy2 - ui_scale.s(14), text=footer_str, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
        return sy2 + ui_scale.gap

    def _draw_focus_system(self, curr_y: int, cur_w: int) -> int:
        cards = [c for c in ["local_pc", "dgx_spark", "services", "coding"] if self.config.enabled_cards.get(c, True)]
        if not cards:
            cards = ["local_pc", "dgx_spark", "services", "coding"]

        margin = ui_scale.grid_margin
        gap = ui_scale.gap
        avail_w = cur_w - 2 * margin

        num_cols = max(1, min(len(cards), (avail_w + gap) // (ui_scale.s(380) + gap)))
        card_w = (avail_w - (num_cols - 1) * gap) // num_cols
        card_h = ui_scale.focus_card_h

        for idx, p_id in enumerate(cards):
            col = idx % num_cols
            row = idx // num_cols
            cx1 = margin + col * (card_w + gap)
            cy1 = curr_y + row * (card_h + gap)
            cx2 = cx1 + card_w
            cy2 = cy1 + card_h

            self.card_bounds[p_id] = (cx1, cy1, cx2, cy2)
            page_data = self.state.get_page(p_id)
            is_active = (p_id == self.state.minitoo_active_page)
            is_hover = (p_id == self.hovered_card)

            border_c = C_ACTIVE_CYAN if is_active else (C_CARD_HOVER if is_hover else C_CARD_BORDER)
            bg_c = "#121A2B" if is_active else ("#141A28" if is_hover else C_CARD_BG)
            self.canvas.create_rectangle(cx1, cy1, cx2, cy2, fill=bg_c, outline=border_c, width=2 if is_active else 1)

            t_color = CARD_COLORS.get(p_id, C_TEXT_WHITE)
            title_str = page_data.title if page_data else p_id.upper()
            self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(18), text=title_str, font=ui_scale.f_card_title, fill=t_color, anchor="w")

            if is_active:
                tag_w = ui_scale.s(82)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text="ON MINITOO", font=ui_scale.f_badge, fill=C_ACTIVE_CYAN, anchor="center")
            elif page_data:
                b_color = C_GREEN if page_data.badge_color == "green" else (C_AMBER if page_data.badge_color == "amber" else C_TEXT_MUTED)
                tag_w = ui_scale.s(72)
                self.canvas.create_rectangle(cx2 - tag_w - ui_scale.s(10), cy1 + ui_scale.s(10), cx2 - ui_scale.s(10), cy1 + ui_scale.s(26), fill="#131926", outline="#202A3C")
                self.canvas.create_text(cx2 - tag_w // 2 - ui_scale.s(10), cy1 + ui_scale.s(18), text=page_data.badge[:12], font=ui_scale.f_badge, fill=b_color, anchor="center")

            if p_id == "local_pc" and page_data:
                pm = page_data.primary_metric
                sm = page_data.secondary_metric
                em = page_data.extra_metrics[0] if page_data.extra_metrics else None

                gpu_val = pm.value if pm else "N/A"
                gpu_pct = pm.pct if pm else None
                gpu_c = C_RED if (gpu_pct and gpu_pct >= 90) else (C_AMBER if (gpu_pct and gpu_pct >= 75) else C_GREEN)
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(46), text="GPU LOAD", font=ui_scale.f_secondary_metric, fill=C_TEXT_MUTED, anchor="w")
                self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(46), text=gpu_val, font=ui_scale.f_primary_metric, fill=gpu_c, anchor="e")
                self._draw_segmented_bar(cx1 + ui_scale.s(14), cy1 + ui_scale.s(60), card_w - ui_scale.s(28), ui_scale.s(9), gpu_pct, gpu_c, num_blocks=16)

                ram_val = sm.value if sm else "N/A"
                ram_pct = sm.pct if sm else None
                ram_c = C_RED if (ram_pct and ram_pct >= 90) else (C_AMBER if (ram_pct and ram_pct >= 75) else "#37C3F5")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(96), text="SYSTEM RAM", font=ui_scale.f_secondary_metric, fill=C_TEXT_MUTED, anchor="w")
                self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(96), text=ram_val, font=ui_scale.f_primary_metric, fill=ram_c, anchor="e")
                self._draw_segmented_bar(cx1 + ui_scale.s(14), cy1 + ui_scale.s(110), card_w - ui_scale.s(28), ui_scale.s(8), ram_pct, ram_c, num_blocks=16)

                cpu_val = em.value if em else "N/A"
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(140), text=f"CPU: {cpu_val}", font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text=page_data.footer_right or "WORKSTATION HARDWARE", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            elif p_id == "dgx_spark" and page_data:
                if page_data.is_offline:
                    self.canvas.create_text((cx1 + cx2) // 2, cy1 + ui_scale.s(70), text="OFFLINE", font=ui_scale.f_primary_metric_focus, fill=C_RED, anchor="center")
                    self.canvas.create_text((cx1 + cx2) // 2, cy1 + ui_scale.s(105), text=f"LAST SEEN: {page_data.offline_sub or 'N/A'}", font=ui_scale.f_secondary_metric, fill=C_AMBER, anchor="center")
                    self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text=f"ssh://{self.config.dgx_host}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
                else:
                    pm = page_data.primary_metric
                    gpu_val = pm.value if pm else "N/A"
                    gpu_pct = pm.pct if pm else None
                    self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(46), text="DGX GPU LOAD", font=ui_scale.f_secondary_metric, fill=C_TEXT_MUTED, anchor="w")
                    self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(46), text=gpu_val, font=ui_scale.f_primary_metric, fill="#76B900", anchor="e")
                    self._draw_segmented_bar(cx1 + ui_scale.s(14), cy1 + ui_scale.s(62), card_w - ui_scale.s(28), ui_scale.s(10), gpu_pct, "#76B900", num_blocks=16)
                    self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text="NVIDIA DGX SPARK · CLUSTER", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            elif p_id == "services" and page_data:
                items = page_data.items_list or []
                for s_idx, it in enumerate(items[:5]):
                    sy = cy1 + ui_scale.s(44) + s_idx * ui_scale.s(26)
                    s_name = it.get("name", "SERVICE")
                    online = it.get("online", False)
                    dot_c = C_GREEN if online else C_TEXT_DIM
                    st_text = "OK" if online else "OFF"
                    self.canvas.create_oval(cx1 + ui_scale.s(14), sy + ui_scale.s(3), cx1 + ui_scale.s(22), sy + ui_scale.s(11), fill=dot_c, outline="")
                    self.canvas.create_text(cx1 + ui_scale.s(28), sy + ui_scale.s(7), text=s_name[:20], font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
                    self.canvas.create_text(cx2 - ui_scale.s(14), sy + ui_scale.s(7), text=st_text, font=ui_scale.f_secondary_metric, fill=dot_c, anchor="e")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text="CORE SYSTEM DAEMONS", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            elif p_id == "coding" and page_data:
                pm = page_data.primary_metric
                sm = page_data.secondary_metric
                em = page_data.extra_metrics[0] if page_data.extra_metrics else None

                repo_val = pm.value if pm else "claude-minitoo"
                branch_val = sm.value if sm else "main"
                state_val = sm.reset if (sm and sm.reset) else "CLEAN"
                model_val = em.value if em else "Claude 3.7 Sonnet"

                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(48), text=f"REPO: {repo_val}", font=ui_scale.f_card_title, fill="#37C3F5", anchor="w")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(78), text=f"BRANCH: {branch_val}", font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
                st_color = C_GREEN if "CLEAN" in state_val else C_AMBER
                self.canvas.create_text(cx2 - ui_scale.s(14), cy1 + ui_scale.s(78), text=state_val, font=ui_scale.f_secondary_metric, fill=st_color, anchor="e")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy1 + ui_scale.s(108), text=f"MODEL: {model_val}", font=ui_scale.f_secondary_metric, fill=C_PURPLE, anchor="w")
                self.canvas.create_text(cx1 + ui_scale.s(14), cy2 - ui_scale.s(14), text="DEVELOPER ENVIRONMENT", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

        total_rows = (len(cards) + num_cols - 1) // num_cols
        return curr_y + total_rows * (card_h + gap) + ui_scale.s(6)

    # --------------------------------------------------------------------------
    # DITOO & DUAL PREVIEW PANELS
    # --------------------------------------------------------------------------
    def _draw_ditoo_panel(self, curr_y: int, cur_w: int) -> int:
        margin = ui_scale.grid_margin
        gap = ui_scale.gap

        # 1. Hero Live Preview Card
        c1_x1 = margin
        c1_y1 = curr_y
        c1_x2 = cur_w - margin
        c1_y2 = c1_y1 + ui_scale.s(190)

        self.canvas.create_rectangle(c1_x1, c1_y1, c1_x2, c1_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)

        prev_x = c1_x1 + ui_scale.s(14)
        prev_y = c1_y1 + ui_scale.s(14)
        active_img = self.state.ditoo_active_frame
        if active_img is None:
            active_img = Crypto16Renderer.render_icon_frame(self.state.ditoo_active_asset or "BTC")

        scaled_img = active_img.resize((160, 160), Image.Resampling.NEAREST)
        self._ditoo_photo = ImageTk.PhotoImage(scaled_img)
        self.canvas.create_image(prev_x, prev_y, image=self._ditoo_photo, anchor="nw")
        self.canvas.create_rectangle(prev_x - 1, prev_y - 1, prev_x + 160, prev_y + 160, outline="#2A384F", width=1)

        info_x = prev_x + 175
        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(22), text="DITOO 16x16 LIVE DISPLAY FEED", font=ui_scale.f_card_title, fill=C_ACTIVE_CYAN, anchor="w")

        conn = self.state.ditoo_connected
        st_text = self.state.ditoo_status_text
        st_color = C_GREEN if conn else (C_AMBER if "RECONNECTING" in st_text else C_RED)
        self.canvas.create_text(c1_x2 - ui_scale.s(16), c1_y1 + ui_scale.s(22), text=st_text, font=ui_scale.f_badge, fill=st_color, anchor="e")

        active_sym = self.state.ditoo_active_asset
        frame_t = self.state.ditoo_active_frame_type
        brand_raw = CRYPTO_BRAND_COLORS.get(active_sym, BRAND_COLORS.get(active_sym, C_GOLD))
        brand_c = rgb_to_hex(brand_raw, C_GOLD)
        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(50), text="CURRENT ASSET:", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + ui_scale.s(110), c1_y1 + ui_scale.s(50), text=f"[ {active_sym} ]", font=ui_scale.f_card_title, fill=brand_c, anchor="w")

        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(76), text="FRAME TYPE:", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + ui_scale.s(110), c1_y1 + ui_scale.s(76), text=f"[ {frame_t} ]", font=ui_scale.f_secondary_metric, fill=C_BLUE, anchor="w")

        last_mkt = self.state.ditoo_last_market_update
        mkt_str = f"{int(time.time() - last_mkt)}s ago" if last_mkt > 0 else "Live"
        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(102), text="MARKET DATA:", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + ui_scale.s(110), c1_y1 + ui_scale.s(102), text=f"{mkt_str} (Cached/Live)", font=ui_scale.f_meta, fill=C_GREEN, anchor="w")

        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(126), text="BLE ENDPOINT:", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + ui_scale.s(110), c1_y1 + ui_scale.s(126), text="DitooPro-Light (BLE Data)", font=ui_scale.f_meta, fill=C_TEXT_WHITE, anchor="w")

        b_val = self.config.ditoo_brightness
        self.canvas.create_text(info_x, c1_y1 + ui_scale.s(156), text="BRIGHTNESS:", font=ui_scale.f_meta, fill=C_TEXT_MUTED, anchor="w")

        b_btn_w = ui_scale.s(24)
        b_btn_h = ui_scale.s(22)
        b_bx1 = info_x + ui_scale.s(110)
        self.canvas.create_rectangle(b_bx1, c1_y1 + ui_scale.s(145), b_bx1 + b_btn_w, c1_y1 + ui_scale.s(145) + b_btn_h, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(b_bx1 + b_btn_w // 2, c1_y1 + ui_scale.s(156), text="-", font=ui_scale.f_btn, fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["bright_down"] = (b_bx1, c1_y1 + ui_scale.s(145), b_bx1 + b_btn_w, c1_y1 + ui_scale.s(145) + b_btn_h)

        self.canvas.create_text(b_bx1 + b_btn_w + ui_scale.s(22), c1_y1 + ui_scale.s(156), text=f"{b_val}%", font=ui_scale.f_secondary_metric, fill=C_GOLD, anchor="center")

        b_bx2 = b_bx1 + b_btn_w + ui_scale.s(44)
        self.canvas.create_rectangle(b_bx2, c1_y1 + ui_scale.s(145), b_bx2 + b_btn_w, c1_y1 + ui_scale.s(145) + b_btn_h, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(b_bx2 + b_btn_w // 2, c1_y1 + ui_scale.s(156), text="+", font=ui_scale.f_btn, fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["bright_up"] = (b_bx2, c1_y1 + ui_scale.s(145), b_bx2 + b_btn_w, c1_y1 + ui_scale.s(145) + b_btn_h)

        curr_y = c1_y2 + gap

        # 2. Crypto Rotation Card
        c2_x1 = margin
        c2_y1 = curr_y
        c2_x2 = cur_w - margin
        c2_y2 = c2_y1 + ui_scale.s(84)

        self.canvas.create_rectangle(c2_x1, c2_y1, c2_x2, c2_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        self.canvas.create_text(c2_x1 + ui_scale.s(14), c2_y1 + ui_scale.s(16), text="─── [ CRYPTO ASSETS ROTATION ]", font=ui_scale.f_card_title, fill=C_GOLD, anchor="w")

        cr_on = self.config.ditoo_enabled_crypto_page
        cr_btn_text = "CRYPTO: ENABLED" if cr_on else "CRYPTO: DISABLED"
        cr_btn_fg = C_GREEN if cr_on else C_TEXT_MUTED
        cr_btn_bg = "#0E2419" if cr_on else "#151B27"
        cr_w = ui_scale.s(135)
        self.canvas.create_rectangle(c2_x2 - cr_w - ui_scale.s(14), c2_y1 + ui_scale.s(8), c2_x2 - ui_scale.s(14), c2_y1 + ui_scale.s(28), fill=cr_btn_bg, outline="#203040")
        self.canvas.create_text(c2_x2 - cr_w // 2 - ui_scale.s(14), c2_y1 + ui_scale.s(18), text=cr_btn_text, font=ui_scale.f_btn, fill=cr_btn_fg, anchor="center")
        self.ditoo_btn_bounds["crypto_master"] = (c2_x2 - cr_w - ui_scale.s(14), c2_y1 + ui_scale.s(8), c2_x2 - ui_scale.s(14), c2_y1 + ui_scale.s(28))

        coins = ["btc", "eth", "sol", "doge", "pepe"]
        btn_w = ui_scale.s(128)
        bx_start = c2_x1 + ui_scale.s(14)
        for i, coin in enumerate(coins):
            bx1 = bx_start + i * (btn_w + ui_scale.s(8))
            by1 = c2_y1 + ui_scale.s(34)
            bx2 = bx1 + btn_w
            by2 = by1 + ui_scale.s(40)

            is_coin_on = (coin in self.config.ditoo_enabled_cryptos)
            c_bg = "#0C231A" if is_coin_on else "#0E131D"
            c_border = "#2E8B57" if is_coin_on else "#1A2230"

            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=c_bg, outline=c_border, width=1)
            mark = "[✓]" if is_coin_on else "[ ]"
            coin_raw = CRYPTO_BRAND_COLORS.get(coin.upper(), C_TEXT_WHITE)
            coin_color = rgb_to_hex(coin_raw, C_TEXT_WHITE) if is_coin_on else C_TEXT_DIM
            self.canvas.create_text(bx1 + ui_scale.s(8), by1 + ui_scale.s(13), text=f"{mark} {coin.upper()}", font=ui_scale.f_secondary_metric, fill=coin_color, anchor="w")

            asset_data = self.ditoo._crypto_data.get(coin)
            if asset_data:
                p_str = format_abbreviated_price(asset_data.price)
                d_str, d_col = format_delta_pct(asset_data.change_24h_pct)
                self.canvas.create_text(bx1 + ui_scale.s(8), by1 + ui_scale.s(28), text=f"{p_str} {d_str}", font=ui_scale.f_meta, fill=rgb_to_hex(d_col, C_GREEN) if is_coin_on else C_TEXT_DIM, anchor="w")
            else:
                self.canvas.create_text(bx1 + ui_scale.s(8), by1 + ui_scale.s(28), text="Loading...", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            self.ditoo_crypto_bounds[coin] = (bx1, by1, bx2, by2)

        curr_y = c2_y2 + gap

        # 3. Stock Tickers Card
        tickers = self.config.ditoo_stock_tickers
        c3_h = ui_scale.s(45) + max(1, len(tickers)) * ui_scale.s(28) + ui_scale.s(10)
        c3_x1 = margin
        c3_y1 = curr_y
        c3_x2 = cur_w - margin
        c3_y2 = c3_y1 + c3_h

        self.canvas.create_rectangle(c3_x1, c3_y1, c3_x2, c3_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        self.canvas.create_text(c3_x1 + ui_scale.s(14), c3_y1 + ui_scale.s(18), text="─── [ US STOCK TICKERS ROTATION ]", font=ui_scale.f_card_title, fill=C_ACTIVE_CYAN, anchor="w")

        st_on = self.config.ditoo_enabled_stock_page
        st_btn_text = "STOCKS: ENABLED" if st_on else "STOCKS: DISABLED"
        st_btn_fg = C_GREEN if st_on else C_TEXT_MUTED
        st_btn_bg = "#0E2419" if st_on else "#151B27"
        st_w = ui_scale.s(135)
        self.canvas.create_rectangle(c3_x2 - st_w - ui_scale.s(120), c3_y1 + ui_scale.s(8), c3_x2 - ui_scale.s(120), c3_y1 + ui_scale.s(28), fill=st_btn_bg, outline="#203040")
        self.canvas.create_text(c3_x2 - st_w // 2 - ui_scale.s(120), c3_y1 + ui_scale.s(18), text=st_btn_text, font=ui_scale.f_btn, fill=st_btn_fg, anchor="center")
        self.ditoo_btn_bounds["stock_master"] = (c3_x2 - st_w - ui_scale.s(120), c3_y1 + ui_scale.s(8), c3_x2 - ui_scale.s(120), c3_y1 + ui_scale.s(28))

        add_w = ui_scale.s(104)
        self.canvas.create_rectangle(c3_x2 - add_w - ui_scale.s(10), c3_y1 + ui_scale.s(8), c3_x2 - ui_scale.s(10), c3_y1 + ui_scale.s(28), fill="#132438", outline=C_ACTIVE_CYAN)
        self.canvas.create_text(c3_x2 - add_w // 2 - ui_scale.s(10), c3_y1 + ui_scale.s(18), text="+ ADD TICKER", font=ui_scale.f_btn, fill=C_ACTIVE_CYAN, anchor="center")
        self.ditoo_btn_bounds["add_stock"] = (c3_x2 - add_w - ui_scale.s(10), c3_y1 + ui_scale.s(8), c3_x2 - ui_scale.s(10), c3_y1 + ui_scale.s(28))

        row_h = ui_scale.s(28)
        for idx, sym in enumerate(tickers):
            ry = c3_y1 + ui_scale.s(38) + idx * row_h
            row_bg = "#141A28" if idx % 2 == 0 else "#0F1420"
            self.canvas.create_rectangle(c3_x1 + ui_scale.s(14), ry, c3_x2 - ui_scale.s(14), ry + row_h - ui_scale.s(4), fill=row_bg, outline="#1B2434", width=1)

            self.canvas.create_text(c3_x1 + ui_scale.s(24), ry + row_h // 2 - ui_scale.s(2), text=f"#{idx + 1}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            sym_raw = BRAND_COLORS.get(sym, C_ACTIVE_CYAN)
            sym_col = rgb_to_hex(sym_raw, C_ACTIVE_CYAN)
            self.canvas.create_text(c3_x1 + ui_scale.s(60), ry + row_h // 2 - ui_scale.s(2), text=sym, font=ui_scale.f_secondary_metric, fill=sym_col, anchor="w")

            sq = self.ditoo._stock_data.get(sym)
            if sq:
                price_str = f"${sq.price:.2f}"
                sign = "+" if sq.change_pct >= 0 else ""
                delta_str = f"{sign}{sq.change_pct:.1f}%"
                delta_col = C_GREEN if sq.change_pct >= 0 else C_RED
                self.canvas.create_text(c3_x1 + ui_scale.s(140), ry + row_h // 2 - ui_scale.s(2), text=price_str, font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
                self.canvas.create_text(c3_x1 + ui_scale.s(220), ry + row_h // 2 - ui_scale.s(2), text=delta_str, font=ui_scale.f_secondary_metric, fill=delta_col, anchor="w")
            else:
                self.canvas.create_text(c3_x1 + ui_scale.s(140), ry + row_h // 2 - ui_scale.s(2), text="Polling...", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

            ax = c3_x2 - ui_scale.s(110)
            a_btn_w = ui_scale.s(24)
            a_btn_h = row_h - ui_scale.s(8)

            self.canvas.create_rectangle(ax, ry + ui_scale.s(2), ax + a_btn_w, ry + ui_scale.s(2) + a_btn_h, fill="#1B2638", outline="#293950")
            self.canvas.create_text(ax + a_btn_w // 2, ry + a_btn_h // 2 + ui_scale.s(2), text="▲", font=ui_scale.f_btn, fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_stock_bounds[f"up_{idx}"] = (ax, ry + ui_scale.s(2), ax + a_btn_w, ry + ui_scale.s(2) + a_btn_h)

            self.canvas.create_rectangle(ax + a_btn_w + ui_scale.s(4), ry + ui_scale.s(2), ax + 2 * a_btn_w + ui_scale.s(4), ry + ui_scale.s(2) + a_btn_h, fill="#1B2638", outline="#293950")
            self.canvas.create_text(ax + a_btn_w + ui_scale.s(4) + a_btn_w // 2, ry + a_btn_h // 2 + ui_scale.s(2), text="▼", font=ui_scale.f_btn, fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_stock_bounds[f"down_{idx}"] = (ax + a_btn_w + ui_scale.s(4), ry + ui_scale.s(2), ax + 2 * a_btn_w + ui_scale.s(4), ry + ui_scale.s(2) + a_btn_h)

            self.canvas.create_rectangle(ax + 2 * a_btn_w + ui_scale.s(8), ry + ui_scale.s(2), ax + 3 * a_btn_w + ui_scale.s(8), ry + ui_scale.s(2) + a_btn_h, fill="#2D1414", outline="#502020")
            self.canvas.create_text(ax + 2 * a_btn_w + ui_scale.s(8) + a_btn_w // 2, ry + a_btn_h // 2 + ui_scale.s(2), text="✖", font=ui_scale.f_btn, fill=C_RED, anchor="center")
            self.ditoo_stock_bounds[f"del_{idx}"] = (ax + 2 * a_btn_w + ui_scale.s(8), ry + ui_scale.s(2), ax + 3 * a_btn_w + ui_scale.s(8), ry + ui_scale.s(2) + a_btn_h)

        curr_y = c3_y2 + gap
        return curr_y + ui_scale.s(10)

    def _draw_dual_preview_panel(self, curr_y: int, cur_w: int) -> int:
        margin = ui_scale.grid_margin
        gap = ui_scale.gap
        c_x1 = margin
        c_y1 = curr_y
        c_x2 = cur_w - margin
        c_y2 = c_y1 + ui_scale.s(290)

        self.canvas.create_rectangle(c_x1, c_y1, c_x2, c_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)

        # Left: MiniToo 160x128 Preview
        mx = c_x1 + ui_scale.s(24)
        my = c_y1 + ui_scale.s(40)
        self.canvas.create_text(mx, c_y1 + ui_scale.s(20), text="MINITOO DISPLAY (160x128 LCD)", font=ui_scale.f_card_title, fill=C_ACTIVE_CYAN, anchor="w")

        mini_img = self.minitoo._render_active_frame()
        if mini_img:
            m_scaled = mini_img.resize((192, 154), Image.Resampling.NEAREST)
            self._minitoo_photo = ImageTk.PhotoImage(m_scaled)
            self.canvas.create_image(mx, my, image=self._minitoo_photo, anchor="nw")
            self.canvas.create_rectangle(mx - 1, my - 1, mx + 192, my + 154, outline="#2A384F", width=1)
        else:
            self.canvas.create_rectangle(mx, my, mx + 192, my + 154, fill="#0B0F17", outline="#1F2633")
            self.canvas.create_text(mx + 96, my + 77, text="MiniToo Standby", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="center")

        p_name = self.state.minitoo_active_page.upper()
        self.canvas.create_text(mx, my + 168, text=f"ACTIVE PAGE: [ {p_name} ]", font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
        m_conn = "CONNECTED" if self.state.minitoo_connected else "NOT FOUND"
        m_col = C_GREEN if self.state.minitoo_connected else C_AMBER
        self.canvas.create_text(mx, my + 188, text=f"PORT: {self.config.minitoo_port} ({m_conn})", font=ui_scale.f_meta, fill=m_col, anchor="w")

        # Right: Ditoo 16x16 Preview
        dx = c_x1 + ui_scale.s(360)
        dy = c_y1 + ui_scale.s(40)
        self.canvas.create_text(dx, c_y1 + ui_scale.s(20), text="DITOO DISPLAY (16x16 RGB LED MATRIX)", font=ui_scale.f_card_title, fill=C_GOLD, anchor="w")

        active_img = self.state.ditoo_active_frame
        if active_img is None:
            active_img = Crypto16Renderer.render_icon_frame(self.state.ditoo_active_asset or "BTC")

        d_scaled = active_img.resize((154, 154), Image.Resampling.NEAREST)
        self._ditoo_photo = ImageTk.PhotoImage(d_scaled)
        self.canvas.create_image(dx, dy, image=self._ditoo_photo, anchor="nw")
        self.canvas.create_rectangle(dx - 1, dy - 1, dx + 154, dy + 154, outline="#2A384F", width=1)

        d_asset = self.state.ditoo_active_asset
        d_frame = self.state.ditoo_active_frame_type
        self.canvas.create_text(dx, dy + 168, text=f"ASSET: [ {d_asset} ] - {d_frame}", font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
        d_conn = "CONNECTED" if self.state.ditoo_connected else "RECONNECTING"
        d_col = C_GREEN if self.state.ditoo_connected else C_AMBER
        self.canvas.create_text(dx, dy + 188, text=f"BLE: {self.config.ditoo_mac} ({d_conn})", font=ui_scale.f_meta, fill=d_col, anchor="w")

        return c_y2 + gap

    # --------------------------------------------------------------------------
    # FOOTER BAR
    # --------------------------------------------------------------------------
    def _draw_footer(self, curr_y: int, cur_w: int):
        fy = curr_y + ui_scale.s(16)
        target = getattr(self.config, "target_device", "minitoo").upper()
        margin = ui_scale.grid_margin
        self.canvas.create_line(0, fy - ui_scale.s(8), cur_w, fy - ui_scale.s(8), fill="#151D2A", width=1)

        if target == "DITOO":
            active_a = self.state.ditoo_active_asset
            active_f = self.state.ditoo_active_frame_type
            rot_str = " | AUTO-ROTATION: ON" if self.config.ditoo_auto_rotation else " | ROTATION: PAUSED"
            foot_text = f"TARGET: [ DITOO 16x16 ]  |  ACTIVE ASSET: [ {active_a} ] ({active_f}){rot_str}"
        elif target == "PREVIEW":
            foot_text = "TARGET: [ DUAL PREVIEW ]  |  MINITOO (160x128) + DITOO (16x16)"
        else:
            active_p = self.state.minitoo_active_page.upper()
            cycle_str = " | AUTO-CYCLE: ON" if self.config.auto_cycle else ""
            focus_str = f" | FOCUS: {self.focus_section}" if self.focus_section else ""
            foot_text = f"TARGET: [ MINITOO ]  |  ACTIVE PAGE: [ {active_p} ]{cycle_str}{focus_str}"

        self.canvas.create_text(
            margin,
            fy + ui_scale.s(6),
            text=foot_text,
            font=ui_scale.f_btn,
            fill=C_ACTIVE_CYAN,
            anchor="w",
        )

        scale_text = f"SCALE: {self.config.ui_scale} ({int(ui_scale.factor * 100)}%)  |  Ctrl+, Settings  |  1..5 Presets  |  F11 Fullscreen"
        self.canvas.create_text(
            cur_w - margin,
            fy + ui_scale.s(6),
            text=scale_text,
            font=ui_scale.f_meta,
            fill=C_TEXT_DIM,
            anchor="e",
        )

    # ==========================================================================
    # CARD DRAWING ROUTINES (Milestone 14 Typography Hierarchy Polish)
    # ==========================================================================
    def _draw_card(
        self,
        page_id: str,
        data: Optional[PageData],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        is_active: bool,
        is_hover: bool,
        is_enabled: bool,
    ):
        if not is_enabled:
            border_color = "#151B26"
            border_w = 1
            bg_color = "#0B0F17"
        elif is_active:
            border_color = C_ACTIVE_CYAN
            border_w = 2
            bg_color = "#121A2B"
        elif is_hover:
            border_color = C_CARD_HOVER
            border_w = 1
            bg_color = "#141A28"
        else:
            border_color = C_CARD_BORDER
            border_w = 1
            bg_color = C_CARD_BG

        self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline=border_color, width=border_w)

        # Card Title
        title_text = data.title if data else page_id.upper()
        title_color = CARD_COLORS.get(page_id, C_TEXT_WHITE) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(
            x1 + ui_scale.s(12),
            y1 + ui_scale.s(16),
            text=title_text,
            font=ui_scale.f_card_title,
            fill=title_color,
            anchor="w",
        )

        # Status Tag / Badge
        tag_w = ui_scale.s(72)
        tag_h = ui_scale.s(16)
        if not is_enabled:
            self.canvas.create_rectangle(x2 - tag_w - ui_scale.s(8), y1 + ui_scale.s(8), x2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h, fill="#121620", outline="#1F2633")
            self.canvas.create_text(x2 - tag_w // 2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h // 2, text="DISABLED", font=ui_scale.f_badge, fill=C_TEXT_DIM, anchor="center")
        elif is_active:
            tag_w = ui_scale.s(82)
            self.canvas.create_rectangle(x2 - tag_w - ui_scale.s(8), y1 + ui_scale.s(8), x2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h, fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
            self.canvas.create_text(x2 - tag_w // 2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h // 2, text="ON MINITOO", font=ui_scale.f_badge, fill=C_ACTIVE_CYAN, anchor="center")
        elif data:
            badge_t = data.badge[:12]
            b_color = C_GREEN if data.badge_color == "green" else (
                C_AMBER if data.badge_color == "amber" else (
                    C_RED if data.badge_color == "red" else C_TEXT_MUTED
                )
            )
            self.canvas.create_rectangle(x2 - tag_w - ui_scale.s(8), y1 + ui_scale.s(8), x2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h, fill="#131926", outline="#202A3C")
            self.canvas.create_text(x2 - tag_w // 2 - ui_scale.s(8), y1 + ui_scale.s(8) + tag_h // 2, text=badge_t, font=ui_scale.f_badge, fill=b_color, anchor="center")

        if not data:
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text="COLLECTING...", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="center")
            return

        if page_id in ("codex", "gemini", "claude"):
            self._draw_ai_quota_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id in ("btc", "eth", "sol", "doge", "pepe"):
            self._draw_crypto_asset_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "crypto":
            self._draw_crypto_overview_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "local_pc":
            self._draw_local_pc_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "dgx_spark":
            self._draw_dgx_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "ai_activity":
            self._draw_activity_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "services":
            self._draw_services_card(data, x1, y1, x2, y2, is_enabled)
        elif page_id == "coding":
            self._draw_coding_card(data, x1, y1, x2, y2, is_enabled)

    # --------------------------------------------------------------------------
    # CARD TYPE RENDERERS
    # --------------------------------------------------------------------------
    def _draw_ai_quota_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        card_w = x2 - x1
        pm = page.primary_metric
        sm = page.secondary_metric

        p_label = pm.label if pm else "5H LIMIT"
        p_pct = pm.remaining_pct if (pm and pm.remaining_pct is not None) else (pm.pct if pm else None)
        if p_pct is not None:
            p_val = f"{int(p_pct)}% LEFT"
            p_color = C_GREEN if p_pct >= 30 else (C_AMBER if p_pct >= 15 else C_RED)
        elif pm and pm.value and pm.value != "N/A":
            p_val = pm.value
            p_color = C_GREEN
        else:
            p_val = "N/A"
            p_color = C_TEXT_DIM

        if not is_enabled:
            p_color = C_TEXT_DIM

        # Primary Metric: visually dominant 18pt bold
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(38), text=p_label, font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(38), text=p_val, font=ui_scale.f_primary_metric, fill=p_color, anchor="e")
        self._draw_segmented_bar(x1 + ui_scale.s(12), y1 + ui_scale.s(50), card_w - ui_scale.s(24), ui_scale.s(6), p_pct if is_enabled else None, p_color, num_blocks=12)

        p_reset = pm.reset or "RESET N/A"
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(65), text=p_reset, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

        s_label = sm.label if sm else "WEEK LIMIT"
        s_pct = sm.remaining_pct if (sm and sm.remaining_pct is not None) else (sm.pct if sm else None)
        if s_pct is not None:
            s_val = f"{int(s_pct)}% LEFT"
            s_color = C_GREEN if s_pct >= 30 else (C_AMBER if s_pct >= 15 else C_RED)
        elif sm and sm.value and sm.value != "N/A":
            s_val = sm.value
            s_color = C_GREEN
        else:
            s_val = "N/A"
            s_color = C_TEXT_DIM

        if not is_enabled:
            s_color = C_TEXT_DIM

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(82), text=s_label, font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(82), text=s_val, font=ui_scale.f_secondary_metric, fill=s_color, anchor="e")
        self._draw_segmented_bar(x1 + ui_scale.s(12), y1 + ui_scale.s(94), card_w - ui_scale.s(24), ui_scale.s(5), s_pct if is_enabled else None, s_color, num_blocks=12)

        s_reset = sm.reset or "RESET N/A"
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(109), text=s_reset, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

        if page.page_id == "claude" and page.extra_metrics:
            acc_metric = page.extra_metrics[0].value if len(page.extra_metrics) > 0 else ""
            footer_t = f"{acc_metric[:20]} · {page.footer_right}"
        else:
            footer_t = page.footer_right or page.title
        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text=footer_t[:30], font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_crypto_asset_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        price_str = page.primary_metric.value if page.primary_metric else "N/A"
        change_str = page.sparkline_change or ""

        gold_c = CARD_COLORS.get(page.page_id, C_GOLD) if is_enabled else C_TEXT_DIM
        # Primary Metric: visually dominant 18pt bold Consolas
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(40), text=price_str, font=ui_scale.f_primary_metric, fill=gold_c, anchor="w")

        chg_c = (C_GREEN if not change_str.startswith("-") else C_RED) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(40), text=change_str, font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")

        spark_data = page.sparkline_data or []
        if spark_data and len(spark_data) >= 2:
            sp_x1 = x1 + ui_scale.s(12)
            sp_y1 = y1 + ui_scale.s(56)
            sp_x2 = x2 - ui_scale.s(12)
            sp_y2 = y2 - ui_scale.s(28)

            mn = min(spark_data)
            mx = max(spark_data)
            span = (mx - mn) if mx != mn else 1.0

            pts = []
            for i, val in enumerate(spark_data):
                px = sp_x1 + i * ((sp_x2 - sp_x1) / (len(spark_data) - 1))
                py = sp_y2 - ((val - mn) / span) * (sp_y2 - sp_y1)
                pts.append((px, py))

            line_c = gold_c if is_enabled else "#253042"
            for i in range(len(pts) - 1):
                self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill=line_c, width=2)
            self.canvas.create_oval(pts[-1][0] - 2, pts[-1][1] - 2, pts[-1][0] + 2, pts[-1][1] + 2, fill=line_c, outline="")

        hi = page.sparkline_high or ""
        lo = page.sparkline_low or ""
        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text=f"24H H {hi}  L {lo}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - ui_scale.s(12), y2 - ui_scale.s(12), text="SPOT", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="e")

    def _draw_crypto_overview_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        assets = page.crypto_assets or []
        row_h = ui_scale.s(20)
        for idx, a in enumerate(assets[:5]):
            iy = y1 + ui_scale.s(34) + idx * row_h
            self.canvas.create_text(x1 + ui_scale.s(12), iy, text=f"{a.icon_char} {a.symbol}", font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + ui_scale.s(85), iy, text=a.formatted_compact_price, font=ui_scale.f_body, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
            chg_c = (C_GREEN if a.change_24h_pct >= 0 else C_RED) if is_enabled else C_TEXT_DIM
            self.canvas.create_text(x2 - ui_scale.s(12), iy, text=f"{a.change_24h_pct:+.1f}%", font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")

        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text="5 CRYPTO ASSETS (SPOT)", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_stocks_volatile_card(
        self,
        page: Optional[PageData],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        is_active: bool,
        is_hover: bool,
        is_enabled: bool,
    ):
        border_color = C_ACTIVE_CYAN if is_active else (C_CARD_HOVER if is_hover else C_CARD_BORDER)
        bg_color = "#121A2B" if is_active else C_CARD_BG
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline=border_color, width=2 if is_active else 1)

        self.canvas.create_text(x1 + ui_scale.s(14), y1 + ui_scale.s(16), text="TOP 10 MOST VOLATILE US STOCKS TODAY", font=ui_scale.f_card_title, fill=C_ACTIVE_CYAN, anchor="w")

        mkt_badge = page.badge if page else "REGULAR"
        b_c = C_GREEN if "OPEN" in mkt_badge or "REG" in mkt_badge else C_AMBER
        tag_w = ui_scale.s(76)
        self.canvas.create_rectangle(x2 - tag_w - ui_scale.s(10), y1 + ui_scale.s(8), x2 - ui_scale.s(10), y1 + ui_scale.s(24), fill="#131926", outline="#202A3C")
        self.canvas.create_text(x2 - tag_w // 2 - ui_scale.s(10), y1 + ui_scale.s(16), text=mkt_badge, font=ui_scale.f_badge, fill=b_c, anchor="center")

        quotes = page.stocks_data if page else []
        if not quotes:
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text="COLLECTING MARKET VOLATILITY...", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="center")
            return

        mid_x = (x1 + x2) // 2
        row_h = ui_scale.s(21)

        for idx, q in enumerate(quotes[:5]):
            ry = y1 + ui_scale.s(38) + idx * row_h
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(x1 + ui_scale.s(14), ry, text=f"{idx+1}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + ui_scale.s(34), ry, text=q.symbol, font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(x1 + ui_scale.s(95), ry, text=f"${q.price:,.2f}", font=ui_scale.f_body, fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(x1 + ui_scale.s(180), ry, text=f"{q.change_pct:+.1f}%", font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")
            self.canvas.create_text(mid_x - ui_scale.s(16), ry, text=f"VOL {q.volatility_pct:.1f}%", font=ui_scale.f_secondary_metric, fill=C_ACTIVE_CYAN, anchor="e")

        self.canvas.create_line(mid_x, y1 + ui_scale.s(32), mid_x, y2 - ui_scale.s(20), fill="#1A2436", width=1)

        for idx, q in enumerate(quotes[5:10]):
            ry = y1 + ui_scale.s(38) + idx * row_h
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(mid_x + ui_scale.s(16), ry, text=f"{idx+6}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(36), ry, text=q.symbol, font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(97), ry, text=f"${q.price:,.2f}", font=ui_scale.f_body, fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(mid_x + ui_scale.s(182), ry, text=f"{q.change_pct:+.1f}%", font=ui_scale.f_secondary_metric, fill=chg_c, anchor="e")
            self.canvas.create_text(x2 - ui_scale.s(14), ry, text=f"VOL {q.volatility_pct:.1f}%", font=ui_scale.f_secondary_metric, fill=C_ACTIVE_CYAN, anchor="e")

        footer_str = "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance"
        self.canvas.create_text(x1 + ui_scale.s(14), y2 - ui_scale.s(10), text=footer_str, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

    def _draw_local_pc_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        card_w = x2 - x1
        pm = page.primary_metric
        sm = page.secondary_metric
        em = page.extra_metrics[0] if page.extra_metrics else None

        gpu_val = pm.value if pm else "N/A"
        gpu_pct = pm.pct if pm else None
        gpu_c = C_RED if (gpu_pct and gpu_pct >= 90) else (C_AMBER if (gpu_pct and gpu_pct >= 75) else C_GREEN)
        if not is_enabled:
            gpu_c = C_TEXT_DIM

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(38), text="GPU LOAD", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(38), text=gpu_val, font=ui_scale.f_primary_metric, fill=gpu_c, anchor="e")
        self._draw_segmented_bar(x1 + ui_scale.s(12), y1 + ui_scale.s(50), card_w - ui_scale.s(24), ui_scale.s(6), gpu_pct if is_enabled else None, gpu_c, num_blocks=12)

        sub_info = pm.reset if pm else ""
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(65), text=sub_info, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

        ram_val = sm.value if sm else "N/A"
        ram_pct = sm.pct if sm else None
        ram_c = C_RED if (ram_pct and ram_pct >= 90) else (C_AMBER if (ram_pct and ram_pct >= 75) else "#37C3F5")
        if not is_enabled:
            ram_c = C_TEXT_DIM

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(82), text="RAM LOAD", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(82), text=ram_val, font=ui_scale.f_secondary_metric, fill=ram_c, anchor="e")
        self._draw_segmented_bar(x1 + ui_scale.s(12), y1 + ui_scale.s(94), card_w - ui_scale.s(24), ui_scale.s(5), ram_pct if is_enabled else None, ram_c, num_blocks=12)

        cpu_val = em.value if em else "N/A"
        cpu_pct = em.pct if em else None
        cpu_c = C_RED if (cpu_pct and cpu_pct >= 90) else (C_AMBER if (cpu_pct and cpu_pct >= 75) else C_GREEN)
        if not is_enabled:
            cpu_c = C_TEXT_DIM
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(110), text=f"CPU: {cpu_val}", font=ui_scale.f_meta, fill=cpu_c, anchor="w")

        footer_t = page.footer_right or "DESKTOP PC"
        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text=footer_t[:28], font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_dgx_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        card_w = x2 - x1
        if page.is_offline:
            self.canvas.create_text((x1 + x2) // 2, y1 + ui_scale.s(55), text="OFFLINE", font=ui_scale.f_primary_metric, fill=C_RED if is_enabled else C_TEXT_DIM, anchor="center")
            self.canvas.create_text((x1 + x2) // 2, y1 + ui_scale.s(82), text=f"LAST SEEN: {page.offline_sub or 'N/A'}", font=ui_scale.f_meta, fill=C_AMBER if is_enabled else C_TEXT_DIM, anchor="center")
            self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text=f"ssh://{self.config.dgx_host}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
        else:
            pm = page.primary_metric
            gpu_val = pm.value if pm else "N/A"
            gpu_pct = pm.pct if pm else None
            gpu_c = "#76B900" if is_enabled else C_TEXT_DIM

            self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(40), text="DGX GPU LOAD", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(40), text=gpu_val, font=ui_scale.f_primary_metric, fill=gpu_c, anchor="e")
            self._draw_segmented_bar(x1 + ui_scale.s(12), y1 + ui_scale.s(52), card_w - ui_scale.s(24), ui_scale.s(7), gpu_pct if is_enabled else None, gpu_c, num_blocks=12)

            if pm and pm.reset:
                self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(70), text=pm.reset, font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text="NVIDIA DGX SPARK", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_activity_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        items = page.items_list or []
        row_h = ui_scale.s(26)
        for idx, it in enumerate(items[:3]):
            iy = y1 + ui_scale.s(38) + idx * row_h
            name = it.get("name", "AGENT")
            working = it.get("working", False)
            elapsed = it.get("elapsed", "")

            dot_c = (C_GREEN if working else C_TEXT_DIM) if is_enabled else C_TEXT_DIM
            stat_t = "WORKING" if working else "IDLE"

            self.canvas.create_oval(x1 + ui_scale.s(12), iy + ui_scale.s(3), x1 + ui_scale.s(18), iy + ui_scale.s(9), fill=dot_c, outline="")
            self.canvas.create_text(x1 + ui_scale.s(24), iy + ui_scale.s(6), text=name[:14], font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - ui_scale.s(12), iy + ui_scale.s(6), text=stat_t, font=ui_scale.f_meta, fill=dot_c, anchor="e")
            if working and elapsed:
                self.canvas.create_text(x1 + ui_scale.s(24), iy + ui_scale.s(18), text=f"active {elapsed.lower()}", font=ui_scale.f_meta, fill=C_TEXT_DIM, anchor="w")

        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text="AGENT POOL / LOCAL DAEMONS", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_services_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        items = page.items_list or []
        row_h = ui_scale.s(19)
        for idx, it in enumerate(items[:5]):
            iy = y1 + ui_scale.s(34) + idx * row_h
            name = it.get("name", "SERVICE")
            online = it.get("online", False)

            dot_c = (C_GREEN if online else C_TEXT_DIM) if is_enabled else C_TEXT_DIM
            st_text = "OK" if online else "OFF"

            self.canvas.create_oval(x1 + ui_scale.s(12), iy + ui_scale.s(4), x1 + ui_scale.s(17), iy + ui_scale.s(9), fill=dot_c, outline="")
            self.canvas.create_text(x1 + ui_scale.s(22), iy + ui_scale.s(6), text=name[:16], font=ui_scale.f_body, fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - ui_scale.s(12), iy + ui_scale.s(6), text=st_text, font=ui_scale.f_secondary_metric, fill=dot_c, anchor="e")

        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text="WORKSTATION HEALTH", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_coding_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        pm = page.primary_metric
        sm = page.secondary_metric
        em = page.extra_metrics[0] if page.extra_metrics else None

        repo_val = pm.value if pm else "claude-minitoo"
        branch_val = sm.value if sm else "main"
        state_val = sm.reset if (sm and sm.reset) else "CLEAN"
        model_val = em.value if em else "Claude 3.7 Sonnet"

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(36), text="REPO", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(50), text=repo_val[:18], font=ui_scale.f_secondary_metric, fill="#37C3F5" if is_enabled else C_TEXT_DIM, anchor="w")

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(70), text="BRANCH", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(84), text=branch_val[:14], font=ui_scale.f_secondary_metric, fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")

        st_color = (C_GREEN if "CLEAN" in state_val else C_AMBER) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(70), text="GIT STATE", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="e")
        self.canvas.create_text(x2 - ui_scale.s(12), y1 + ui_scale.s(84), text=state_val[:10], font=ui_scale.f_secondary_metric, fill=st_color, anchor="e")

        self.canvas.create_text(x1 + ui_scale.s(12), y1 + ui_scale.s(104), text=f"AI: {model_val[:16]}", font=ui_scale.f_meta, fill=C_PURPLE if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + ui_scale.s(12), y2 - ui_scale.s(12), text="ACTIVE WORKSPACE", font=ui_scale.f_meta, fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_segmented_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        percent: Optional[float],
        active_color: str,
        num_blocks: int = 12,
    ):
        gap = max(1, ui_scale.s(2))
        total_gaps = (num_blocks - 1) * gap
        block_w = max(2, (width - total_gaps) // num_blocks)

        filled = 0
        if percent is not None:
            filled = max(0, min(num_blocks, round((percent / 100.0) * num_blocks)))

        for i in range(num_blocks):
            bx1 = x + i * (block_w + gap)
            by1 = y
            bx2 = bx1 + block_w
            by2 = y + height
            fill_c = active_color if i < filled else "#171F2E"
            outline_c = active_color if i < filled else "#212C40"
            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=fill_c, outline=outline_c, width=1)


def main():
    setup_logging()
    root = tk.Tk()
    app = DesktopDashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
