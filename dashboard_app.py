#!/usr/bin/env python3
"""
AI Desk Dashboard — Desktop Companion App & MiniToo Controller.
Milestone 12: Configurable Sections, Multi-Asset Markets, Stocks Scanner,
and Claude Account Diagnostics.

Features:
- Configurable Sections: CRYPTO, AI USAGE, SYSTEM, STOCKS.
- Lightweight Presets: ALL, AI, MARKETS, SYSTEM.
- Multi-Asset Crypto: BTC, ETH, SOL, DOGE, PEPE with 24H sparklines.
- Top 10 Most Volatile US Stocks scanner (objective intraday range volatility).
- Claude Multi-Account Diagnostics (masked email, plan, auth type, env var precedence).
- Real-time physical MiniToo routing on card click.
- Crash-resilient launch logging and persistent configuration.
"""
from __future__ import annotations

import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import simpledialog
from typing import Optional, Dict, Tuple, Any, List
from PIL import Image, ImageTk

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
            f.write(f"\n[{ts}] === AI Desk Dashboard Launch ===\n")
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

# Layout geometry
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 600
HEADER_HEIGHT = 68
FOOTER_HEIGHT = 28
GRID_MARGIN = 10
GAP = 8
CARD_WIDTH = 198
CARD_HEIGHT = 136


class DesktopDashboardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI Desk Dashboard")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        # 1. Load Persistent Configuration
        self.config = DashboardConfig.load()

        if self.config.window_x is not None and self.config.window_y is not None:
            wx = max(10, min(self.config.window_x, 2560))
            wy = max(10, min(self.config.window_y, 1440))
            self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{wx}+{wy}")

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
        self.device_tab_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_btn_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_crypto_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self.ditoo_stock_bounds: Dict[str, Tuple[int, int, int, int]] = {}
        self._ditoo_photo = None
        self._minitoo_photo = None

        # 3. Build GUI Canvas with scroll support
        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=C_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

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

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
            self.device_tab_bounds,
            self.ditoo_btn_bounds,
            self.ditoo_crypto_bounds,
            self.ditoo_stock_bounds,
        ]
        for b_dict in clickable_bounds:
            for b_name, (bx1, by1, bx2, by2) in b_dict.items():
                if bx1 <= event.x <= bx2 and by1 <= event.y <= by2:
                    has_hand = True
                    break
                # Or check canvas coordinates for scrolled elements
                if bx1 <= canvas_x <= bx2 and by1 <= canvas_y <= by2:
                    has_hand = True
                    break
            if has_hand:
                break

        self.canvas.config(cursor="hand2" if has_hand else "")

        if self.hovered_card != prev_hover:
            self._render_gui()

    def _on_mouse_click(self, event):
        x, y = event.x, event.y
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)

        # 1. Device Tab selector
        for dev_name, (dx1, dy1, dx2, dy2) in self.device_tab_bounds.items():
            if dx1 <= x <= dx2 and dy1 <= y <= dy2:
                if self.config.target_device != dev_name:
                    print(f"[APP] Switching target device -> {dev_name.upper()}")
                    self.config.target_device = dev_name
                    self.config.save()
                    self._render_gui()
                return

        # 2. Autostart button
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

        # 3. Settings button
        if "settings" in self.btn_bounds:
            sx1, sy1, sx2, sy2 = self.btn_bounds["settings"]
            if sx1 <= x <= sx2 and sy1 <= y <= sy2:
                self._open_settings()
                return

        # 4. Preset buttons (in MiniToo mode)
        for p_name, (bx1, by1, bx2, by2) in self.preset_bounds.items():
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                print(f"[APP] Applying Preset: {p_name}")
                self.config.apply_preset(p_name)
                self.config.save()
                self._render_gui()
                return

        # 5. Ditoo Controls (when in Ditoo mode)
        if self.config.target_device == "ditoo":
            # Action buttons
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

            # Crypto Checkboxes
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

            # Stock Ticker actions (up, down, delete)
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

        # 6. Card clicked -> route to MiniToo
        if self.config.target_device == "minitoo":
            for p_id, (cx1, cy1, cx2, cy2) in self.card_bounds.items():
                if cx1 <= canvas_x <= cx2 and cy1 <= canvas_y <= cy2:
                    if self.config.enabled_cards.get(p_id, True):
                        print(f"[APP] Card clicked: {p_id.upper()} -> Routing to MiniToo")
                        self.minitoo.push_page(p_id)
                        self._render_gui()
                    break

    def _open_settings(self):
        SettingsDialog(self.root, self.config, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self, new_config: DashboardConfig):
        self.config = new_config
        self.autostart_enabled = WindowsAutostart.is_enabled()
        self.engine.update_config(new_config)
        self.minitoo.update_config(new_config)
        self.ditoo.update_config(new_config)
        self._render_gui()

    def _on_close(self):
        try:
            wx = self.root.winfo_x()
            wy = self.root.winfo_y()
            if wx >= 0 and wy >= 0:
                self.config.window_x = wx
                self.config.window_y = wy
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
        self.canvas.delete("all")
        self.card_bounds.clear()
        self.preset_bounds.clear()
        self.btn_bounds.clear()
        self.device_tab_bounds.clear()
        self.ditoo_btn_bounds.clear()
        self.ditoo_crypto_bounds.clear()
        self.ditoo_stock_bounds.clear()

        # 1. Fixed Header Bar with Device Selector
        self._draw_header()

        # 2. Main Content View based on Selected Device
        curr_y = HEADER_HEIGHT + 6
        target = getattr(self.config, "target_device", "ditoo").lower()

        if target == "ditoo":
            curr_y = self._draw_ditoo_panel(curr_y)
        elif target == "preview":
            curr_y = self._draw_dual_preview_panel(curr_y)
        else:
            curr_y = self._draw_minitoo_sections(curr_y)

        # 3. Footer Bar
        self._draw_footer(curr_y)

        # Update scrollregion
        max_scroll_y = max(WINDOW_HEIGHT, curr_y + FOOTER_HEIGHT + 10)
        self.canvas.configure(scrollregion=(0, 0, WINDOW_WIDTH, max_scroll_y))

        # Schedule next periodic refresh
        if hasattr(self, "_after_id") and self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.root.after(250, self._render_gui)

    def _draw_header(self):
        target = getattr(self.config, "target_device", "ditoo").lower()

        # Line 1: Title & System Controls
        self.canvas.create_text(
            GRID_MARGIN,
            16,
            text="AI DESK DASHBOARD",
            font=("Consolas", 11, "bold"),
            fill=C_ACTIVE_CYAN,
            anchor="w",
        )

        # Device Connection Status Pill
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

        px1 = 175
        py1 = 5
        px2 = 430
        py2 = 27
        self.canvas.create_rectangle(px1, py1, px2, py2, fill=pill_bg, outline=pill_border, width=1)
        self.canvas.create_oval(px1 + 8, py1 + 7, px1 + 14, py1 + 13, fill=pill_color, outline="")
        self.canvas.create_text(
            px1 + 20,
            16,
            text=status_str,
            font=("Consolas", 7, "bold"),
            fill=pill_color,
            anchor="w",
        )

        # Autostart Button
        btn_x1 = 438
        btn_y1 = 5
        btn_x2 = 538
        btn_y2 = 27
        auto_text = "AUTOSTART: ON" if self.autostart_enabled else "AUTOSTART: OFF"
        auto_fg = C_GREEN if self.autostart_enabled else C_TEXT_MUTED
        auto_bg = "#0E2419" if self.autostart_enabled else "#151B27"
        auto_border = "#1E4733" if self.autostart_enabled else "#253047"
        self.canvas.create_rectangle(btn_x1, btn_y1, btn_x2, btn_y2, fill=auto_bg, outline=auto_border, width=1)
        self.canvas.create_text(
            (btn_x1 + btn_x2) // 2,
            16,
            text=auto_text,
            font=("Consolas", 7, "bold"),
            fill=auto_fg,
            anchor="center",
        )
        self.btn_bounds["autostart"] = (btn_x1, btn_y1, btn_x2, btn_y2)

        # Settings Button
        set_x1 = 544
        set_y1 = 5
        set_x2 = 630
        set_y2 = 27
        self.canvas.create_rectangle(set_x1, set_y1, set_x2, set_y2, fill="#131B2A", outline="#25354F", width=1)
        self.canvas.create_text(
            (set_x1 + set_x2) // 2,
            16,
            text="⚙ SETTINGS",
            font=("Consolas", 7, "bold"),
            fill=C_ACTIVE_CYAN,
            anchor="center",
        )
        self.btn_bounds["settings"] = (set_x1, set_y1, set_x2, set_y2)

        # Line 2: Prominent Display Device Selector Tabs
        self.canvas.create_text(
            GRID_MARGIN,
            46,
            text="DEVICE:",
            font=("Consolas", 7, "bold"),
            fill=C_TEXT_DIM,
            anchor="w",
        )

        tabs = [
            ("minitoo", "🖥 MiniToo", 90),
            ("ditoo", "👾 Ditoo (16x16)", 125),
            ("preview", "👁 Preview", 90),
        ]
        cur_tab_x = GRID_MARGIN + 52
        for dev_key, dev_label, tab_w in tabs:
            is_active = (target == dev_key)
            t_bg = "#0B2638" if is_active else "#101622"
            t_fg = C_ACTIVE_CYAN if is_active else C_TEXT_MUTED
            t_border = C_ACTIVE_CYAN if is_active else "#1C2536"
            tx1 = cur_tab_x
            ty1 = 36
            tx2 = tx1 + tab_w
            ty2 = 56
            self.canvas.create_rectangle(tx1, ty1, tx2, ty2, fill=t_bg, outline=t_border, width=1)
            self.canvas.create_text(
                (tx1 + tx2) // 2,
                46,
                text=dev_label,
                font=("Consolas", 7, "bold"),
                fill=t_fg,
                anchor="center",
            )
            self.device_tab_bounds[dev_key] = (tx1, ty1, tx2, ty2)
            cur_tab_x += tab_w + 6

        # Line 2 Right Side: Context Action Buttons
        if target == "minitoo":
            self.canvas.create_text(cur_tab_x + 8, 46, text="PRESET:", font=("Consolas", 7, "bold"), fill=C_TEXT_DIM, anchor="w")
            px = cur_tab_x + 58
            for p_name in ALL_PRESETS:
                is_active = (self.config.active_preset == p_name)
                p_bg = "#0B2638" if is_active else "#101622"
                p_fg = C_ACTIVE_CYAN if is_active else C_TEXT_MUTED
                p_border = C_ACTIVE_CYAN if is_active else "#1C2536"
                pw = 50
                bx1, by1, bx2, by2 = px, 36, px + pw, 56
                self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=p_bg, outline=p_border, width=1)
                self.canvas.create_text((bx1 + bx2) // 2, 46, text=p_name, font=("Consolas", 7, "bold"), fill=p_fg, anchor="center")
                self.preset_bounds[p_name] = (bx1, by1, bx2, by2)
                px += pw + 4

        elif target == "ditoo":
            # Quick rotation playback buttons on header
            px = 390
            # Prev
            self.canvas.create_rectangle(px, 36, px + 44, 56, fill="#121A28", outline="#202A3C")
            self.canvas.create_text(px + 22, 46, text="◀ PREV", font=("Consolas", 7, "bold"), fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_btn_bounds["prev"] = (px, 36, px + 44, 56)
            px += 48

            # Pause / Resume
            is_paused = self.config.ditoo_is_paused
            pause_text = "▶ RESUME" if is_paused else "⏸ PAUSE"
            pause_fg = C_AMBER if is_paused else C_GREEN
            pause_bg = "#261D0D" if is_paused else "#0D261B"
            pause_border = "#4D361B" if is_paused else "#1B4D36"
            self.canvas.create_rectangle(px, 36, px + 68, 56, fill=pause_bg, outline=pause_border)
            self.canvas.create_text(px + 34, 46, text=pause_text, font=("Consolas", 7, "bold"), fill=pause_fg, anchor="center")
            self.ditoo_btn_bounds["pause"] = (px, 36, px + 68, 56)
            px += 72

            # Next
            self.canvas.create_rectangle(px, 36, px + 44, 56, fill="#121A28", outline="#202A3C")
            self.canvas.create_text(px + 22, 46, text="NEXT ▶", font=("Consolas", 7, "bold"), fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_btn_bounds["next"] = (px, 36, px + 44, 56)
            px += 48

            # Rotation toggle
            rot_on = self.config.ditoo_auto_rotation
            rot_text = "ROT: ON" if rot_on else "ROT: OFF"
            rot_fg = C_GREEN if rot_on else C_TEXT_MUTED
            self.canvas.create_rectangle(px, 36, px + 56, 56, fill="#121A28", outline="#202A3C")
            self.canvas.create_text(px + 28, 46, text=rot_text, font=("Consolas", 7, "bold"), fill=rot_fg, anchor="center")
            self.ditoo_btn_bounds["rot_toggle"] = (px, 36, px + 56, 56)

        # Divider under header
        self.canvas.create_line(0, HEADER_HEIGHT, WINDOW_WIDTH, HEADER_HEIGHT, fill="#151D2A", width=1)

    def _draw_ditoo_panel(self, curr_y: int) -> int:
        # 1. Hero Live Preview Card
        c1_x1 = GRID_MARGIN
        c1_y1 = curr_y
        c1_x2 = WINDOW_WIDTH - GRID_MARGIN
        c1_y2 = c1_y1 + 180

        self.canvas.create_rectangle(c1_x1, c1_y1, c1_x2, c1_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)

        # Nearest-Neighbor 160x160 Live Preview (Exact 16x16 transmitted frame)
        prev_x = c1_x1 + 10
        prev_y = c1_y1 + 10
        active_img = self.state.ditoo_active_frame
        if active_img is None:
            active_img = Crypto16Renderer.render_icon_frame(self.state.ditoo_active_asset or "BTC")

        scaled_img = active_img.resize((160, 160), Image.Resampling.NEAREST)
        self._ditoo_photo = ImageTk.PhotoImage(scaled_img)
        self.canvas.create_image(prev_x, prev_y, image=self._ditoo_photo, anchor="nw")

        # Crisp border around 16x16 matrix
        self.canvas.create_rectangle(prev_x - 1, prev_y - 1, prev_x + 160, prev_y + 160, outline="#2A384F", width=1)

        # Right Side Information & Telemetry
        info_x = prev_x + 172
        # Title
        self.canvas.create_text(info_x, c1_y1 + 18, text="DITOO 16x16 LIVE DISPLAY FEED", font=("Consolas", 10, "bold"), fill=C_ACTIVE_CYAN, anchor="w")

        # Connection status badge
        conn = self.state.ditoo_connected
        st_text = self.state.ditoo_status_text
        st_color = C_GREEN if conn else (C_AMBER if "RECONNECTING" in st_text else C_RED)
        self.canvas.create_text(c1_x2 - 12, c1_y1 + 18, text=st_text, font=("Consolas", 7, "bold"), fill=st_color, anchor="e")

        # Active Asset & Frame info
        active_sym = self.state.ditoo_active_asset
        frame_t = self.state.ditoo_active_frame_type
        brand_raw = CRYPTO_BRAND_COLORS.get(active_sym, BRAND_COLORS.get(active_sym, C_GOLD))
        brand_c = rgb_to_hex(brand_raw, C_GOLD)
        self.canvas.create_text(info_x, c1_y1 + 42, text="CURRENT ASSET:", font=("Consolas", 8), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + 95, c1_y1 + 42, text=f"[ {active_sym} ]", font=("Consolas", 10, "bold"), fill=brand_c, anchor="w")

        self.canvas.create_text(info_x, c1_y1 + 64, text="FRAME TYPE:", font=("Consolas", 8), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + 95, c1_y1 + 64, text=f"[ {frame_t} ]", font=("Consolas", 9, "bold"), fill=C_BLUE, anchor="w")

        # Telemetry & Timestamps
        last_mkt = self.state.ditoo_last_market_update
        mkt_str = f"{int(time.time() - last_mkt)}s ago" if last_mkt > 0 else "Live"
        self.canvas.create_text(info_x, c1_y1 + 86, text="MARKET DATA:", font=("Consolas", 8), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + 95, c1_y1 + 86, text=f"{mkt_str} (Cached/Live)", font=("Consolas", 8, "bold"), fill=C_GREEN, anchor="w")

        self.canvas.create_text(info_x, c1_y1 + 106, text="BLE ENDPOINT:", font=("Consolas", 8), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + 95, c1_y1 + 106, text="DitooPro-Light (BLE Data)", font=("Consolas", 8), fill=C_TEXT_WHITE, anchor="w")

        self.canvas.create_text(info_x, c1_y1 + 124, text="WIN AUDIO:", font=("Consolas", 8), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_text(info_x + 95, c1_y1 + 124, text="UNTOUCHED (Isolated)", font=("Consolas", 8, "bold"), fill=C_GREEN, anchor="w")

        # Brightness stepper row
        b_val = self.config.ditoo_brightness
        self.canvas.create_text(info_x, c1_y1 + 152, text="BRIGHTNESS:", font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED, anchor="w")
        # [-]
        self.canvas.create_rectangle(info_x + 95, c1_y1 + 142, info_x + 115, c1_y1 + 162, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(info_x + 105, c1_y1 + 152, text="-", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["bright_down"] = (info_x + 95, c1_y1 + 142, info_x + 115, c1_y1 + 162)

        self.canvas.create_text(info_x + 138, c1_y1 + 152, text=f"{b_val}%", font=("Consolas", 8, "bold"), fill=C_GOLD, anchor="center")

        # [+]
        self.canvas.create_rectangle(info_x + 160, c1_y1 + 142, info_x + 180, c1_y1 + 162, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(info_x + 170, c1_y1 + 152, text="+", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["bright_up"] = (info_x + 160, c1_y1 + 142, info_x + 180, c1_y1 + 162)

        curr_y = c1_y2 + GAP

        # 2. Crypto Rotation Card
        c2_x1 = GRID_MARGIN
        c2_y1 = curr_y
        c2_x2 = WINDOW_WIDTH - GRID_MARGIN
        c2_y2 = c2_y1 + 76

        self.canvas.create_rectangle(c2_x1, c2_y1, c2_x2, c2_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        # Header line
        self.canvas.create_text(c2_x1 + 10, c2_y1 + 14, text="─── [ CRYPTO ASSETS ROTATION ]", font=("Consolas", 8, "bold"), fill=C_GOLD, anchor="w")

        cr_on = self.config.ditoo_enabled_crypto_page
        cr_btn_text = "CRYPTO: ENABLED" if cr_on else "CRYPTO: DISABLED"
        cr_btn_fg = C_GREEN if cr_on else C_TEXT_MUTED
        cr_btn_bg = "#0E2419" if cr_on else "#151B27"
        self.canvas.create_rectangle(c2_x2 - 125, c2_y1 + 5, c2_x2 - 10, c2_y1 + 23, fill=cr_btn_bg, outline="#203040")
        self.canvas.create_text(c2_x2 - 67, c2_y1 + 14, text=cr_btn_text, font=("Consolas", 7, "bold"), fill=cr_btn_fg, anchor="center")
        self.ditoo_btn_bounds["crypto_master"] = (c2_x2 - 125, c2_y1 + 5, c2_x2 - 10, c2_y1 + 23)

        # 5 individual coin toggle buttons
        coins = ["btc", "eth", "sol", "doge", "pepe"]
        btn_w = 116
        bx_start = c2_x1 + 10
        for i, coin in enumerate(coins):
            bx1 = bx_start + i * (btn_w + 8)
            by1 = c2_y1 + 30
            bx2 = bx1 + btn_w
            by2 = by1 + 36

            is_coin_on = (coin in self.config.ditoo_enabled_cryptos)
            c_bg = "#0C231A" if is_coin_on else "#0E131D"
            c_border = "#2E8B57" if is_coin_on else "#1A2230"

            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=c_bg, outline=c_border, width=1)
            mark = "[✓]" if is_coin_on else "[ ]"
            coin_raw = CRYPTO_BRAND_COLORS.get(coin.upper(), C_TEXT_WHITE)
            coin_color = rgb_to_hex(coin_raw, C_TEXT_WHITE) if is_coin_on else C_TEXT_DIM
            self.canvas.create_text(bx1 + 8, by1 + 12, text=f"{mark} {coin.upper()}", font=("Consolas", 8, "bold"), fill=coin_color, anchor="w")

            # Show price / delta
            asset_data = self.ditoo._crypto_data.get(coin)
            if asset_data:
                p_str = format_abbreviated_price(asset_data.price)
                d_str, d_col = format_delta_pct(asset_data.change_24h_pct)
                self.canvas.create_text(bx1 + 8, by1 + 25, text=f"{p_str} {d_str}", font=("Consolas", 7), fill=rgb_to_hex(d_col, C_GREEN) if is_coin_on else C_TEXT_DIM, anchor="w")
            else:
                self.canvas.create_text(bx1 + 8, by1 + 25, text="Loading...", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

            self.ditoo_crypto_bounds[coin] = (bx1, by1, bx2, by2)

        curr_y = c2_y2 + GAP

        # 3. Stock Tickers Card
        tickers = self.config.ditoo_stock_tickers
        c3_h = 40 + max(1, len(tickers)) * 26 + 10
        c3_x1 = GRID_MARGIN
        c3_y1 = curr_y
        c3_x2 = WINDOW_WIDTH - GRID_MARGIN
        c3_y2 = c3_y1 + c3_h

        self.canvas.create_rectangle(c3_x1, c3_y1, c3_x2, c3_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        self.canvas.create_text(c3_x1 + 10, c3_y1 + 16, text="─── [ US STOCK TICKERS ROTATION ]", font=("Consolas", 8, "bold"), fill=C_ACTIVE_CYAN, anchor="w")

        # Master stock toggle
        st_on = self.config.ditoo_enabled_stock_page
        st_btn_text = "STOCKS: ENABLED" if st_on else "STOCKS: DISABLED"
        st_btn_fg = C_GREEN if st_on else C_TEXT_MUTED
        st_btn_bg = "#0E2419" if st_on else "#151B27"
        self.canvas.create_rectangle(c3_x2 - 225, c3_y1 + 6, c3_x2 - 110, c3_y1 + 24, fill=st_btn_bg, outline="#203040")
        self.canvas.create_text(c3_x2 - 167, c3_y1 + 15, text=st_btn_text, font=("Consolas", 7, "bold"), fill=st_btn_fg, anchor="center")
        self.ditoo_btn_bounds["stock_master"] = (c3_x2 - 225, c3_y1 + 6, c3_x2 - 110, c3_y1 + 24)

        # [+ ADD TICKER] button
        self.canvas.create_rectangle(c3_x2 - 100, c3_y1 + 6, c3_x2 - 10, c3_y1 + 24, fill="#132438", outline=C_ACTIVE_CYAN)
        self.canvas.create_text(c3_x2 - 55, c3_y1 + 15, text="+ ADD TICKER", font=("Consolas", 7, "bold"), fill=C_ACTIVE_CYAN, anchor="center")
        self.ditoo_btn_bounds["add_stock"] = (c3_x2 - 100, c3_y1 + 6, c3_x2 - 10, c3_y1 + 24)

        # Render each configured stock ticker row
        for idx, sym in enumerate(tickers):
            ry = c3_y1 + 36 + idx * 26
            row_bg = "#141A28" if idx % 2 == 0 else "#0F1420"
            self.canvas.create_rectangle(c3_x1 + 10, ry, c3_x2 - 10, ry + 22, fill=row_bg, outline="#1B2434", width=1)

            # Order badge
            self.canvas.create_text(c3_x1 + 20, ry + 11, text=f"#{idx + 1}", font=("Consolas", 8, "bold"), fill=C_TEXT_DIM, anchor="w")

            # Symbol & Brand
            sym_raw = BRAND_COLORS.get(sym, C_ACTIVE_CYAN)
            sym_col = rgb_to_hex(sym_raw, C_ACTIVE_CYAN)
            self.canvas.create_text(c3_x1 + 55, ry + 11, text=sym, font=("Consolas", 9, "bold"), fill=sym_col, anchor="w")

            # Price & Delta from live cache
            sq = self.ditoo._stock_data.get(sym)
            if sq:
                price_str = f"${sq.price:.2f}"
                sign = "+" if sq.change_pct >= 0 else ""
                delta_str = f"{sign}{sq.change_pct:.1f}%"
                delta_col = C_GREEN if sq.change_pct >= 0 else C_RED
                self.canvas.create_text(c3_x1 + 120, ry + 11, text=price_str, font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="w")
                self.canvas.create_text(c3_x1 + 180, ry + 11, text=delta_str, font=("Consolas", 8, "bold"), fill=delta_col, anchor="w")
            else:
                self.canvas.create_text(c3_x1 + 120, ry + 11, text="Polling...", font=("Consolas", 8), fill=C_TEXT_DIM, anchor="w")

            # Action buttons on right: [▲] [▼] [✖]
            ax = c3_x2 - 95
            # Up button
            self.canvas.create_rectangle(ax, ry + 2, ax + 22, ry + 20, fill="#1B2638", outline="#293950")
            self.canvas.create_text(ax + 11, ry + 11, text="▲", font=("Consolas", 7, "bold"), fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_stock_bounds[f"up_{idx}"] = (ax, ry + 2, ax + 22, ry + 20)

            # Down button
            self.canvas.create_rectangle(ax + 26, ry + 2, ax + 48, ry + 20, fill="#1B2638", outline="#293950")
            self.canvas.create_text(ax + 37, ry + 11, text="▼", font=("Consolas", 7, "bold"), fill=C_TEXT_WHITE, anchor="center")
            self.ditoo_stock_bounds[f"down_{idx}"] = (ax + 26, ry + 2, ax + 48, ry + 20)

            # Delete button
            self.canvas.create_rectangle(ax + 54, ry + 2, ax + 76, ry + 20, fill="#2D1414", outline="#502020")
            self.canvas.create_text(ax + 65, ry + 11, text="✖", font=("Consolas", 7, "bold"), fill=C_RED, anchor="center")
            self.ditoo_stock_bounds[f"del_{idx}"] = (ax + 54, ry + 2, ax + 76, ry + 20)

        curr_y = c3_y2 + GAP

        # 4. Rotation Timing & Dwell Settings Card
        c4_x1 = GRID_MARGIN
        c4_y1 = curr_y
        c4_x2 = WINDOW_WIDTH - GRID_MARGIN
        c4_y2 = c4_y1 + 70

        self.canvas.create_rectangle(c4_x1, c4_y1, c4_x2, c4_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)
        self.canvas.create_text(c4_x1 + 10, c4_y1 + 14, text="─── [ ROTATION CADENCE & FRAME DWELL ]", font=("Consolas", 8, "bold"), fill=C_CORAL, anchor="w")

        # Steppers row
        dw_logo = self.config.ditoo_frame_logo_dwell
        dw_price = self.config.ditoo_frame_price_dwell
        dw_change = self.config.ditoo_frame_change_dwell

        # Logo dwell
        lx = c4_x1 + 12
        self.canvas.create_text(lx, c4_y1 + 34, text="LOGO DWELL:", font=("Consolas", 7, "bold"), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_rectangle(lx + 80, c4_y1 + 24, lx + 98, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(lx + 89, c4_y1 + 33, text="-", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_logo_down"] = (lx + 80, c4_y1 + 24, lx + 98, c4_y1 + 42)

        self.canvas.create_text(lx + 116, c4_y1 + 33, text=f"{dw_logo:.1f}s", font=("Consolas", 8, "bold"), fill=C_ACTIVE_CYAN, anchor="center")

        self.canvas.create_rectangle(lx + 134, c4_y1 + 24, lx + 152, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(lx + 143, c4_y1 + 33, text="+", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_logo_up"] = (lx + 134, c4_y1 + 24, lx + 152, c4_y1 + 42)

        # Price dwell
        px = c4_x1 + 180
        self.canvas.create_text(px, c4_y1 + 34, text="PRICE DWELL:", font=("Consolas", 7, "bold"), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_rectangle(px + 85, c4_y1 + 24, px + 103, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(px + 94, c4_y1 + 33, text="-", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_price_down"] = (px + 85, c4_y1 + 24, px + 103, c4_y1 + 42)

        self.canvas.create_text(px + 121, c4_y1 + 33, text=f"{dw_price:.1f}s", font=("Consolas", 8, "bold"), fill=C_ACTIVE_CYAN, anchor="center")

        self.canvas.create_rectangle(px + 139, c4_y1 + 24, px + 157, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(px + 148, c4_y1 + 33, text="+", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_price_up"] = (px + 139, c4_y1 + 24, px + 157, c4_y1 + 42)

        # Change dwell
        cx = c4_x1 + 355
        self.canvas.create_text(cx, c4_y1 + 34, text="CHANGE DWELL:", font=("Consolas", 7, "bold"), fill=C_TEXT_MUTED, anchor="w")
        self.canvas.create_rectangle(cx + 90, c4_y1 + 24, cx + 108, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(cx + 99, c4_y1 + 33, text="-", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_change_down"] = (cx + 90, c4_y1 + 24, cx + 108, c4_y1 + 42)

        self.canvas.create_text(cx + 126, c4_y1 + 33, text=f"{dw_change:.1f}s", font=("Consolas", 8, "bold"), fill=C_ACTIVE_CYAN, anchor="center")

        self.canvas.create_rectangle(cx + 144, c4_y1 + 24, cx + 162, c4_y1 + 42, fill="#161F2E", outline="#25354F")
        self.canvas.create_text(cx + 153, c4_y1 + 33, text="+", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="center")
        self.ditoo_btn_bounds["dwell_change_up"] = (cx + 144, c4_y1 + 24, cx + 162, c4_y1 + 42)

        # Rotation summary
        dwell_per_asset = dw_logo + dw_price + dw_change
        num_assets = len(self.ditoo._get_active_assets())
        tot_cycle = dwell_per_asset * num_assets
        self.canvas.create_text(
            c4_x1 + 12,
            c4_y1 + 56,
            text=f"CADENCE: {dwell_per_asset:.1f}s/asset  |  COMPLETE ROTATION CYCLE: {tot_cycle:.1f}s ({num_assets} active assets)",
            font=("Consolas", 7, "bold"),
            fill=C_TEXT_MUTED,
            anchor="w",
        )

        curr_y = c4_y2 + GAP

        # 5. Device Architecture & Audio Isolation Note
        c5_x1 = GRID_MARGIN
        c5_y1 = curr_y
        c5_x2 = WINDOW_WIDTH - GRID_MARGIN
        c5_y2 = c5_y1 + 46

        self.canvas.create_rectangle(c5_x1, c5_y1, c5_x2, c5_y2, fill="#0A0F18", outline="#182232", width=1)
        self.canvas.create_text(
            c5_x1 + 10,
            c5_y1 + 14,
            text="DEVICE: DitooPro-Light (BLE GATT UART)  |  AUDIO: Isolated (DitooPro-Audio excluded)",
            font=("Consolas", 7, "bold"),
            fill=C_GREEN,
            anchor="w",
        )
        self.canvas.create_text(
            c5_x1 + 10,
            c5_y1 + 30,
            text="PHYSICAL CONTROLS: Managed internally by Ditoo MCU firmware (No BLE key events)",
            font=("Consolas", 7),
            fill=C_TEXT_DIM,
            anchor="w",
        )

        return c5_y2 + GAP

    def _draw_dual_preview_panel(self, curr_y: int) -> int:
        c_x1 = GRID_MARGIN
        c_y1 = curr_y
        c_x2 = WINDOW_WIDTH - GRID_MARGIN
        c_y2 = c_y1 + 260

        self.canvas.create_rectangle(c_x1, c_y1, c_x2, c_y2, fill=C_CARD_BG, outline=C_CARD_BORDER, width=1)

        # Left: MiniToo 160x128 Preview
        mx = c_x1 + 20
        my = c_y1 + 30
        self.canvas.create_text(mx, c_y1 + 16, text="MINITOO DISPLAY (160x128 LCD)", font=("Consolas", 9, "bold"), fill=C_ACTIVE_CYAN, anchor="w")

        mini_img = self.minitoo._render_active_frame()
        if mini_img:
            m_scaled = mini_img.resize((192, 154), Image.Resampling.NEAREST)
            self._minitoo_photo = ImageTk.PhotoImage(m_scaled)
            self.canvas.create_image(mx, my, image=self._minitoo_photo, anchor="nw")
            self.canvas.create_rectangle(mx - 1, my - 1, mx + 192, my + 154, outline="#2A384F", width=1)
        else:
            self.canvas.create_rectangle(mx, my, mx + 192, my + 154, fill="#0B0F17", outline="#1F2633")
            self.canvas.create_text(mx + 96, my + 77, text="MiniToo Standby", font=("Consolas", 8), fill=C_TEXT_DIM, anchor="center")

        p_name = self.state.minitoo_active_page.upper()
        self.canvas.create_text(mx, my + 164, text=f"ACTIVE PAGE: [ {p_name} ]", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="w")
        m_conn = "CONNECTED" if self.state.minitoo_connected else "NOT FOUND"
        m_col = C_GREEN if self.state.minitoo_connected else C_AMBER
        self.canvas.create_text(mx, my + 178, text=f"PORT: {self.config.minitoo_port} ({m_conn})", font=("Consolas", 7), fill=m_col, anchor="w")

        # Right: Ditoo 16x16 Preview
        dx = c_x1 + 330
        dy = c_y1 + 30
        self.canvas.create_text(dx, c_y1 + 16, text="DITOO DISPLAY (16x16 RGB LED MATRIX)", font=("Consolas", 9, "bold"), fill=C_GOLD, anchor="w")

        active_img = self.state.ditoo_active_frame
        if active_img is None:
            active_img = Crypto16Renderer.render_icon_frame(self.state.ditoo_active_asset or "BTC")

        d_scaled = active_img.resize((154, 154), Image.Resampling.NEAREST)
        self._ditoo_photo = ImageTk.PhotoImage(d_scaled)
        self.canvas.create_image(dx, dy, image=self._ditoo_photo, anchor="nw")
        self.canvas.create_rectangle(dx - 1, dy - 1, dx + 154, dy + 154, outline="#2A384F", width=1)

        d_asset = self.state.ditoo_active_asset
        d_frame = self.state.ditoo_active_frame_type
        self.canvas.create_text(dx, dy + 164, text=f"ASSET: [ {d_asset} ] - {d_frame}", font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="w")
        d_conn = "CONNECTED" if self.state.ditoo_connected else "RECONNECTING"
        d_col = C_GREEN if self.state.ditoo_connected else C_AMBER
        self.canvas.create_text(dx, dy + 178, text=f"BLE: {self.config.ditoo_mac} ({d_conn})", font=("Consolas", 7), fill=d_col, anchor="w")

        # Telemetry Bar below
        ty = c_y1 + 220
        self.canvas.create_line(c_x1 + 10, ty, c_x2 - 10, ty, fill="#1A2434")
        self.canvas.create_text(
            c_x1 + 20,
            ty + 18,
            text=f"MINITOO CADENCE: {int(self.config.rotation_interval)}s  |  DITOO DWELL: {self.config.ditoo_frame_logo_dwell:.1f}s logo / {self.config.ditoo_frame_price_dwell:.1f}s price / {self.config.ditoo_frame_change_dwell:.1f}s delta",
            font=("Consolas", 7, "bold"),
            fill=C_TEXT_MUTED,
            anchor="w",
        )

        return c_y2 + GAP

    def _draw_minitoo_sections(self, curr_y: int) -> int:
        for sec_id in self.config.sections_order:
            if not self.config.enabled_sections.get(sec_id, True):
                continue

            sec_title = SECTION_TITLES.get(sec_id, sec_id.upper())
            sec_color = SECTION_COLORS.get(sec_id, C_TEXT_MUTED)

            # Section Banner
            self.canvas.create_text(
                GRID_MARGIN,
                curr_y + 8,
                text=f"─── [ {sec_title} ] ",
                font=("Consolas", 8, "bold"),
                fill=sec_color,
                anchor="w",
            )
            # Subtle trailing line across canvas
            self.canvas.create_line(
                GRID_MARGIN + 140,
                curr_y + 8,
                WINDOW_WIDTH - GRID_MARGIN,
                curr_y + 8,
                fill="#161F2E",
                width=1,
            )
            curr_y += 20

            # Cards in this section
            cards = [c for c in self.config.section_cards.get(sec_id, []) if self.config.enabled_cards.get(c, True)]
            if not cards:
                self.canvas.create_text(
                    GRID_MARGIN + 12,
                    curr_y + 12,
                    text="All cards in this section are currently disabled in Settings.",
                    font=("Consolas", 8),
                    fill=C_TEXT_DIM,
                    anchor="w",
                )
                curr_y += 32
                continue

            # Special layout for stocks scanner card: wide 2-column card
            if sec_id == SECTION_STOCKS and "stocks_volatile" in cards:
                sx1 = GRID_MARGIN
                sy1 = curr_y
                sx2 = WINDOW_WIDTH - GRID_MARGIN
                sy2 = sy1 + 138

                self.card_bounds["stocks_volatile"] = (sx1, sy1, sx2, sy2)
                page_data = self.state.get_page("stocks_volatile")
                is_active = ("stocks_volatile" == self.state.minitoo_active_page)
                is_hover = ("stocks_volatile" == self.hovered_card)
                is_enabled = self.config.enabled_cards.get("stocks_volatile", True)

                self._draw_stocks_volatile_card(page_data, sx1, sy1, sx2, sy2, is_active, is_hover, is_enabled)
                curr_y = sy2 + GAP
                continue

            # Grid layout for standard cards (3 per row)
            for idx, p_id in enumerate(cards):
                col = idx % 3
                row = idx // 3
                cx1 = GRID_MARGIN + col * (CARD_WIDTH + GAP)
                cy1 = curr_y + row * (CARD_HEIGHT + GAP)
                cx2 = cx1 + CARD_WIDTH
                cy2 = cy1 + CARD_HEIGHT

                self.card_bounds[p_id] = (cx1, cy1, cx2, cy2)
                page_data = self.state.get_page(p_id)
                is_active = (p_id == self.state.minitoo_active_page)
                is_hover = (p_id == self.hovered_card)
                is_enabled = self.config.enabled_cards.get(p_id, True)

                self._draw_card(p_id, page_data, cx1, cy1, cx2, cy2, is_active, is_hover, is_enabled)

            total_rows = (len(cards) + 2) // 3
            curr_y += total_rows * (CARD_HEIGHT + GAP) + 4

        return curr_y

    def _draw_footer(self, curr_y: int):
        fy = curr_y + 12
        target = getattr(self.config, "target_device", "ditoo").upper()
        self.canvas.create_line(0, fy - 6, WINDOW_WIDTH, fy - 6, fill="#151D2A", width=1)

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
            foot_text = f"TARGET: [ MINITOO ]  |  ACTIVE PAGE: [ {active_p} ]{cycle_str}"

        self.canvas.create_text(
            GRID_MARGIN,
            fy + 4,
            text=foot_text,
            font=("Consolas", 8, "bold"),
            fill=C_ACTIVE_CYAN,
            anchor="w",
        )

        self.canvas.create_text(
            WINDOW_WIDTH - GRID_MARGIN,
            fy + 4,
            text="DEVICE SELECTOR AT TOP",
            font=("Consolas", 7),
            fill=C_TEXT_DIM,
            anchor="e",
        )

    # ==========================================================================
    # CARD DRAWING ROUTINES
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

        # Header Title
        title_text = data.title if data else page_id.upper()
        title_color = CARD_COLORS.get(page_id, C_TEXT_WHITE) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(
            x1 + 8,
            y1 + 13,
            text=title_text,
            font=("Consolas", 9, "bold"),
            fill=title_color,
            anchor="w",
        )

        # Status Tag / Badge
        if not is_enabled:
            self.canvas.create_rectangle(x2 - 58, y1 + 5, x2 - 6, y1 + 18, fill="#121620", outline="#1F2633")
            self.canvas.create_text(x2 - 32, y1 + 11, text="DISABLED", font=("Consolas", 6, "bold"), fill=C_TEXT_DIM, anchor="center")
        elif is_active:
            self.canvas.create_rectangle(x2 - 74, y1 + 5, x2 - 6, y1 + 18, fill=C_ACTIVE_TAG_BG, outline=C_ACTIVE_CYAN)
            self.canvas.create_text(x2 - 40, y1 + 11, text="ON MINITOO", font=("Consolas", 6, "bold"), fill=C_ACTIVE_CYAN, anchor="center")
        elif data:
            badge_t = data.badge[:10]
            b_color = C_GREEN if data.badge_color == "green" else (
                C_AMBER if data.badge_color == "amber" else (
                    C_RED if data.badge_color == "red" else C_TEXT_MUTED
                )
            )
            self.canvas.create_rectangle(x2 - 58, y1 + 5, x2 - 6, y1 + 18, fill="#131926", outline="#202A3C")
            self.canvas.create_text(x2 - 32, y1 + 11, text=badge_t, font=("Consolas", 6, "bold"), fill=b_color, anchor="center")

        if not data:
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text="COLLECTING...", font=("Consolas", 8), fill=C_TEXT_DIM, anchor="center")
            return

        # Specific renderers
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
        pm = page.primary_metric
        sm = page.secondary_metric

        p_label = pm.label if pm else "5H"
        p_val = pm.value if pm else "N/A"
        p_pct = pm.remaining_pct if (pm and pm.remaining_pct is not None) else (pm.pct if pm else None)
        p_color = C_GREEN if (p_pct is not None and p_pct >= 30) else (
            C_AMBER if (p_pct is not None and p_pct >= 15) else (
                C_RED if p_pct is not None else C_TEXT_MUTED
            )
        )
        if not is_enabled:
            p_color = C_TEXT_DIM

        self.canvas.create_text(x1 + 8, y1 + 34, text=p_label, font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - 8, y1 + 34, text=p_val, font=("Consolas", 8, "bold"), fill=p_color, anchor="e")
        self._draw_segmented_bar(x1 + 8, y1 + 44, CARD_WIDTH - 16, 5, p_pct if is_enabled else None, p_color)

        p_reset = pm.reset or "RESET N/A"
        self.canvas.create_text(x1 + 8, y1 + 57, text=p_reset, font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

        s_label = sm.label if sm else "WEEK"
        s_val = sm.value if sm else "N/A"
        s_pct = sm.remaining_pct if (sm and sm.remaining_pct is not None) else (sm.pct if sm else None)
        s_color = C_GREEN if (s_pct is not None and s_pct >= 30) else (
            C_AMBER if (s_pct is not None and s_pct >= 15) else (
                C_RED if s_pct is not None else C_TEXT_MUTED
            )
        )
        if not is_enabled:
            s_color = C_TEXT_DIM

        self.canvas.create_text(x1 + 8, y1 + 72, text=s_label, font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - 8, y1 + 72, text=s_val, font=("Consolas", 8, "bold"), fill=s_color, anchor="e")
        self._draw_segmented_bar(x1 + 8, y1 + 82, CARD_WIDTH - 16, 5, s_pct if is_enabled else None, s_color)

        s_reset = sm.reset or "RESET N/A"
        self.canvas.create_text(x1 + 8, y1 + 95, text=s_reset, font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

        # Footer: model or account info
        if page.page_id == "claude" and page.extra_metrics:
            acc_metric = page.extra_metrics[0].value if len(page.extra_metrics) > 0 else ""
            footer_t = f"{acc_metric[:16]} · {page.footer_right}"
        else:
            footer_t = page.footer_right or page.title
        self.canvas.create_text(x1 + 8, y2 - 10, text=footer_t[:26], font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_crypto_asset_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        price_str = page.primary_metric.value if page.primary_metric else "N/A"
        change_str = page.sparkline_change or ""

        gold_c = CARD_COLORS.get(page.page_id, C_GOLD) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(x1 + 8, y1 + 36, text=price_str, font=("Consolas", 12, "bold"), fill=gold_c, anchor="w")

        chg_c = (C_GREEN if not change_str.startswith("-") else C_RED) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(x2 - 8, y1 + 36, text=change_str, font=("Consolas", 8, "bold"), fill=chg_c, anchor="e")

        spark_data = page.sparkline_data or []
        if spark_data and len(spark_data) >= 2:
            sp_x1 = x1 + 10
            sp_y1 = y1 + 52
            sp_x2 = x2 - 10
            sp_y2 = y1 + 94

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
        self.canvas.create_text(x1 + 8, y2 - 10, text=f"H {hi}  L {lo}", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

    def _draw_crypto_overview_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        assets = page.crypto_assets or []
        for idx, a in enumerate(assets[:5]):
            iy = y1 + 30 + idx * 18
            self.canvas.create_text(x1 + 8, iy, text=f"{a.icon_char} {a.symbol}", font=("Consolas", 7, "bold"), fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + 72, iy, text=a.formatted_compact_price, font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
            chg_c = (C_GREEN if a.change_24h_pct >= 0 else C_RED) if is_enabled else C_TEXT_DIM
            self.canvas.create_text(x2 - 8, iy, text=f"{a.change_24h_pct:+.1f}%", font=("Consolas", 7, "bold"), fill=chg_c, anchor="e")

        self.canvas.create_text(x1 + 8, y2 - 10, text="5 CRYPTO ASSETS (SPOT)", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

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

        # Header
        self.canvas.create_text(x1 + 10, y1 + 13, text="TOP 10 MOST VOLATILE US STOCKS TODAY", font=("Consolas", 9, "bold"), fill=C_ACTIVE_CYAN, anchor="w")

        mkt_badge = page.badge if page else "REGULAR"
        b_c = C_GREEN if "OPEN" in mkt_badge or "REG" in mkt_badge else C_AMBER
        self.canvas.create_rectangle(x2 - 68, y1 + 5, x2 - 8, y1 + 18, fill="#131926", outline="#202A3C")
        self.canvas.create_text(x2 - 38, y1 + 11, text=mkt_badge, font=("Consolas", 6, "bold"), fill=b_c, anchor="center")

        quotes = page.stocks_data if page else []
        if not quotes:
            self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text="COLLECTING MARKET VOLATILITY...", font=("Consolas", 8), fill=C_TEXT_DIM, anchor="center")
            return

        mid_x = (x1 + x2) // 2

        # Left Column: Ranks 1 to 5
        for idx, q in enumerate(quotes[:5]):
            ry = y1 + 32 + idx * 18
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(x1 + 10, ry, text=f"{idx+1}", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + 24, ry, text=q.symbol, font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(x1 + 75, ry, text=f"${q.price:,.2f}", font=("Consolas", 7), fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(x1 + 155, ry, text=f"{q.change_pct:+.1f}%", font=("Consolas", 7, "bold"), fill=chg_c, anchor="e")
            self.canvas.create_text(mid_x - 12, ry, text=f"VOL {q.volatility_pct:.1f}%", font=("Consolas", 7, "bold"), fill=C_ACTIVE_CYAN, anchor="e")

        # Divider between columns
        self.canvas.create_line(mid_x, y1 + 26, mid_x, y2 - 18, fill="#1A2436", width=1)

        # Right Column: Ranks 6 to 10
        for idx, q in enumerate(quotes[5:10]):
            ry = y1 + 32 + idx * 18
            chg_c = C_GREEN if q.change_pct >= 0 else C_RED
            self.canvas.create_text(mid_x + 12, ry, text=f"{idx+6}", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(mid_x + 28, ry, text=q.symbol, font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE, anchor="w")
            self.canvas.create_text(mid_x + 80, ry, text=f"${q.price:,.2f}", font=("Consolas", 7), fill=C_TEXT_MUTED, anchor="w")
            self.canvas.create_text(mid_x + 160, ry, text=f"{q.change_pct:+.1f}%", font=("Consolas", 7, "bold"), fill=chg_c, anchor="e")
            self.canvas.create_text(x2 - 10, ry, text=f"VOL {q.volatility_pct:.1f}%", font=("Consolas", 7, "bold"), fill=C_ACTIVE_CYAN, anchor="e")

        footer_str = "METRIC: Intraday Range % = (High - Low) / PrevClose · YahooFinance"
        self.canvas.create_text(x1 + 10, y2 - 9, text=footer_str, font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

    def _draw_local_pc_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        pm = page.primary_metric
        sm = page.secondary_metric
        em = page.extra_metrics[0] if page.extra_metrics else None

        gpu_val = pm.value if pm else "N/A"
        gpu_pct = pm.pct if pm else None
        gpu_c = C_RED if (gpu_pct and gpu_pct >= 90) else (C_AMBER if (gpu_pct and gpu_pct >= 75) else C_GREEN)
        if not is_enabled:
            gpu_c = C_TEXT_DIM
        self.canvas.create_text(x1 + 8, y1 + 35, text="GPU", font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - 8, y1 + 35, text=gpu_val, font=("Consolas", 8, "bold"), fill=gpu_c, anchor="e")
        self._draw_segmented_bar(x1 + 8, y1 + 44, CARD_WIDTH - 16, 5, gpu_pct if is_enabled else None, gpu_c)

        sub_info = pm.reset if pm else ""
        self.canvas.create_text(x1 + 8, y1 + 56, text=sub_info, font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")

        ram_val = sm.value if sm else "N/A"
        ram_pct = sm.pct if sm else None
        ram_c = C_RED if (ram_pct and ram_pct >= 90) else (C_AMBER if (ram_pct and ram_pct >= 75) else "#37C3F5")
        if not is_enabled:
            ram_c = C_TEXT_DIM
        self.canvas.create_text(x1 + 8, y1 + 72, text="RAM", font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x2 - 8, y1 + 72, text=ram_val, font=("Consolas", 8, "bold"), fill=ram_c, anchor="e")
        self._draw_segmented_bar(x1 + 8, y1 + 81, CARD_WIDTH - 16, 5, ram_pct if is_enabled else None, ram_c)

        cpu_val = em.value if em else "N/A"
        cpu_pct = em.pct if em else None
        cpu_c = C_RED if (cpu_pct and cpu_pct >= 90) else (C_AMBER if (cpu_pct and cpu_pct >= 75) else C_GREEN)
        if not is_enabled:
            cpu_c = C_TEXT_DIM
        self.canvas.create_text(x1 + 8, y1 + 97, text=f"CPU: {cpu_val}", font=("Consolas", 7), fill=cpu_c, anchor="w")

        footer_t = page.footer_right or "DESKTOP PC"
        self.canvas.create_text(x1 + 8, y2 - 10, text=footer_t[:24], font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_dgx_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        if page.is_offline:
            self.canvas.create_text((x1 + x2) // 2, y1 + 50, text="OFFLINE", font=("Consolas", 14, "bold"), fill=C_RED if is_enabled else C_TEXT_DIM, anchor="center")
            self.canvas.create_text((x1 + x2) // 2, y1 + 75, text=f"LAST SEEN: {page.offline_sub or 'N/A'}", font=("Consolas", 8), fill=C_AMBER if is_enabled else C_TEXT_DIM, anchor="center")
            self.canvas.create_text((x1 + x2) // 2, y1 + 95, text=f"HOST: {self.config.dgx_host}", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="center")
            self.canvas.create_text(x1 + 8, y2 - 10, text=f"ssh://{self.config.dgx_host}", font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")
        else:
            pm = page.primary_metric
            gpu_val = pm.value if pm else "N/A"
            gpu_pct = pm.pct if pm else None
            gpu_c = "#76B900" if is_enabled else C_TEXT_DIM
            self.canvas.create_text(x1 + 8, y1 + 35, text="GPU", font=("Consolas", 8, "bold"), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - 8, y1 + 35, text=gpu_val, font=("Consolas", 8, "bold"), fill=gpu_c, anchor="e")
            self._draw_segmented_bar(x1 + 8, y1 + 45, CARD_WIDTH - 16, 6, gpu_pct if is_enabled else None, gpu_c)
            if pm and pm.reset:
                self.canvas.create_text(x1 + 8, y1 + 60, text=pm.reset, font=("Consolas", 7), fill=C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x1 + 8, y2 - 10, text="NVIDIA DGX SPARK", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_activity_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        items = page.items_list or []
        for idx, it in enumerate(items[:3]):
            iy = y1 + 36 + idx * 24
            name = it.get("name", "AGENT")
            working = it.get("working", False)
            elapsed = it.get("elapsed", "")

            dot_c = (C_GREEN if working else C_TEXT_DIM) if is_enabled else C_TEXT_DIM
            stat_t = "WORKING" if working else "IDLE"

            self.canvas.create_oval(x1 + 8, iy + 3, x1 + 14, iy + 9, fill=dot_c, outline="")
            self.canvas.create_text(x1 + 18, iy + 6, text=name[:12], font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - 8, iy + 6, text=stat_t, font=("Consolas", 7, "bold"), fill=dot_c, anchor="e")
            if working and elapsed:
                self.canvas.create_text(x1 + 18, iy + 17, text=f"active {elapsed.lower()}", font=("Consolas", 6), fill=C_TEXT_DIM, anchor="w")

        self.canvas.create_text(x1 + 8, y2 - 10, text="AGENT POOL / LOCAL DAEMONS", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_services_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        items = page.items_list or []
        for idx, it in enumerate(items[:5]):
            iy = y1 + 32 + idx * 17
            name = it.get("name", "SERVICE")
            online = it.get("online", False)

            dot_c = (C_GREEN if online else C_TEXT_DIM) if is_enabled else C_TEXT_DIM
            st_text = "OK" if online else "OFF"

            self.canvas.create_oval(x1 + 8, iy + 4, x1 + 13, iy + 9, fill=dot_c, outline="")
            self.canvas.create_text(x1 + 18, iy + 6, text=name[:14], font=("Consolas", 8), fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")
            self.canvas.create_text(x2 - 8, iy + 6, text=st_text, font=("Consolas", 7, "bold"), fill=dot_c, anchor="e")

        self.canvas.create_text(x1 + 8, y2 - 10, text="WORKSTATION HEALTH", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_coding_card(self, page: PageData, x1: int, y1: int, x2: int, y2: int, is_enabled: bool = True):
        pm = page.primary_metric
        sm = page.secondary_metric
        em = page.extra_metrics[0] if page.extra_metrics else None

        repo_val = pm.value if pm else "claude-minitoo"
        branch_val = sm.value if sm else "main"
        state_val = sm.reset if (sm and sm.reset) else "CLEAN"
        model_val = em.value if em else "GPT-5.6"

        self.canvas.create_text(x1 + 8, y1 + 35, text="REPO", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + 8, y1 + 47, text=repo_val[:16], font=("Consolas", 8, "bold"), fill="#37C3F5" if is_enabled else C_TEXT_DIM, anchor="w")

        self.canvas.create_text(x1 + 8, y1 + 65, text="BRANCH", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + 8, y1 + 77, text=branch_val[:12], font=("Consolas", 8, "bold"), fill=C_TEXT_WHITE if is_enabled else C_TEXT_DIM, anchor="w")

        st_color = (C_GREEN if "CLEAN" in state_val else C_AMBER) if is_enabled else C_TEXT_DIM
        self.canvas.create_text(x2 - 8, y1 + 65, text="GIT STATE", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="e")
        self.canvas.create_text(x2 - 8, y1 + 77, text=state_val[:8], font=("Consolas", 8, "bold"), fill=st_color, anchor="e")

        self.canvas.create_text(x1 + 8, y1 + 95, text=f"AI: {model_val[:14]}", font=("Consolas", 7), fill=C_PURPLE if is_enabled else C_TEXT_DIM, anchor="w")
        self.canvas.create_text(x1 + 8, y2 - 10, text="ACTIVE WORKSPACE", font=("Consolas", 7), fill=C_TEXT_MUTED if is_enabled else C_TEXT_DIM, anchor="w")

    def _draw_segmented_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        percent: Optional[float],
        active_color: str,
        num_blocks: int = 10,
    ):
        gap = 2
        total_gaps = (num_blocks - 1) * gap
        block_w = (width - total_gaps) // num_blocks

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
