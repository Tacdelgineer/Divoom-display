#!/usr/bin/env python3
"""
UI Components for AI Desk Dashboard:
1. FirstRunDialog - Initial setup & system service detection screen.
2. ClaudeAccountsDialog - Multi-account inspector & diagnostic modal.
3. SettingsDialog - Lightweight modal for section ordering, card ordering,
   presets, Claude profiles, port selection, rotation interval, and auto-cycle.
Styled strictly in the dark retro/pixel dashboard aesthetic.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional, Dict, List, Any

from config import (
    DashboardConfig,
    ALL_PAGE_IDS,
    PAGE_LABELS,
    ALL_SECTIONS,
    SECTION_TITLES,
    DEFAULT_SECTION_CARDS,
    ALL_PRESETS,
    PRESET_ALL,
    PRESET_AI,
    PRESET_CRYPTO,
    PRESET_STOCKS,
    PRESET_MARKETS,
    PRESET_SYSTEM,
)
from detector import detect_minitoo_port, get_all_com_ports
from subproc import check_output_hidden, run_hidden
import claude_usage

# Design System
C_BG = "#0A0E17"
C_PANEL_BG = "#111622"
C_BORDER = "#1E273A"
C_HOVER = "#2D3B54"
C_CYAN = "#00E5FF"
C_GREEN = "#32E68C"
C_AMBER = "#F5AF32"
C_RED = "#F54B4B"
C_CORAL = "#F58C3C"
C_GOLD = "#F7931A"
C_PURPLE = "#B98CFF"
C_TEXT_WHITE = "#E6EDF5"
C_TEXT_MUTED = "#7D8C9F"
C_TEXT_DIM = "#505E73"


# ==============================================================================
# 1. FIRST-RUN STATUS / SYSTEM DETECTION DIALOG
# ==============================================================================
class FirstRunDialog(tk.Toplevel):
    """
    First-launch detection screen showing status of MiniToo and all service integrations.
    Non-blocking detection; does not require login or block if a service is unavailable.
    """

    def __init__(self, parent: tk.Tk, config: DashboardConfig, on_open_dashboard: Callable[[], None]):
        super().__init__(parent)
        self.config = config
        self.on_open_dashboard = on_open_dashboard

        self.title("AI Desk Dashboard — System Setup")
        self.geometry("440x510")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 440) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 510) // 2
        self.geometry(f"+{max(40, px)}+{max(30, py)}")

        self.status_labels: Dict[str, tk.Label] = {}
        self._build_ui()
        self._run_probes()

    def _build_ui(self):
        h_frame = tk.Frame(self, bg=C_BG)
        h_frame.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(
            h_frame,
            text="AI DESK DASHBOARD",
            font=("Consolas", 14, "bold"),
            fg=C_CYAN,
            bg=C_BG,
        ).pack(anchor="w")

        tk.Label(
            h_frame,
            text="HARDWARE & SERVICE DETECTION",
            font=("Consolas", 8),
            fg=C_TEXT_DIM,
            bg=C_BG,
        ).pack(anchor="w", pady=(2, 0))

        tbl = tk.Frame(self, bg=C_PANEL_BG, highlightbackground=C_BORDER, highlightthickness=1)
        tbl.pack(fill="both", expand=True, padx=20, pady=10)

        rows = [
            ("minitoo", "MiniToo"),
            ("codex", "Codex"),
            ("gemini", "Gemini"),
            ("claude", "Claude"),
            ("gpu", "Local GPU"),
            ("dgx", "DGX Spark"),
            ("crypto", "Crypto Markets"),
            ("stocks", "Stocks Scanner"),
        ]

        for idx, (key, title) in enumerate(rows):
            rf = tk.Frame(tbl, bg=C_PANEL_BG)
            rf.pack(fill="x", padx=16, pady=7)

            tk.Label(
                rf,
                text=title,
                font=("Consolas", 10, "bold"),
                fg=C_TEXT_WHITE,
                bg=C_PANEL_BG,
                width=16,
                anchor="w",
            ).pack(side="left")

            lbl = tk.Label(
                rf,
                text="PROBING...",
                font=("Consolas", 9, "bold"),
                fg=C_AMBER,
                bg=C_PANEL_BG,
                anchor="e",
            )
            lbl.pack(side="right")
            self.status_labels[key] = lbl

            if idx < len(rows) - 1:
                tk.Frame(tbl, bg=C_BORDER, height=1).pack(fill="x", padx=12)

        btn_frame = tk.Frame(self, bg=C_BG)
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.btn_open = tk.Button(
            btn_frame,
            text="[ OPEN DASHBOARD ]",
            font=("Consolas", 10, "bold"),
            bg="#102538",
            fg=C_CYAN,
            activebackground="#173550",
            activeforeground=C_CYAN,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._finish,
        )
        self.btn_open.pack(fill="x")

    def _update_status(self, key: str, text: str, color: str):
        if key in self.status_labels:
            self.status_labels[key].config(text=text, fg=color)

    def _run_probes(self):
        def probe_worker():
            # 1. MiniToo Port
            port = detect_minitoo_port(self.config.minitoo_port)
            if port:
                self._update_status("minitoo", f"FOUND ({port})", C_GREEN)
            else:
                self._update_status("minitoo", "NOT DETECTED", C_AMBER)

            # 2. Codex
            home = os.path.expanduser("~")
            codex_auth = os.path.join(home, ".codex", "auth.json")
            if os.path.exists(codex_auth):
                self._update_status("codex", "READY", C_GREEN)
            else:
                self._update_status("codex", "NOT CONFIGURED", C_TEXT_DIM)

            # 3. Gemini / Antigravity
            agy_bin = shutil.which("agy") or os.path.exists(os.path.join(home, "AppData", "Local", "agy", "bin", "agy.exe"))
            if agy_bin:
                self._update_status("gemini", "READY", C_GREEN)
            else:
                self._update_status("gemini", "LOCAL ONLY", C_AMBER)

            # 4. Claude
            claude_data = claude_usage.read_claude_usage()
            if claude_data.get("masked_account") and claude_data["masked_account"] != "Not Configured":
                self._update_status("claude", f"READY ({claude_data['masked_account']})", C_CORAL)
            else:
                self._update_status("claude", "NOT CONFIGURED", C_TEXT_DIM)

            # 5. Local GPU
            if shutil.which("nvidia-smi"):
                try:
                    out = check_output_hidden(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], text=True, timeout=2.0).strip()
                    gname = out.split("\n")[0].strip()
                    for pfx in ("NVIDIA GeForce ", "NVIDIA ", "GeForce "):
                        if gname.startswith(pfx):
                            gname = gname[len(pfx):]
                    self._update_status("gpu", f"ONLINE ({gname[:12]})", C_GREEN)
                except Exception:
                    self._update_status("gpu", "ERROR", C_AMBER)
            else:
                self._update_status("gpu", "NO NVIDIA GPU", C_TEXT_DIM)

            # 6. DGX Spark Host
            try:
                out = check_output_hidden(["ssh", "-o", "ConnectTimeout=2", "-o", "BatchMode=yes", self.config.dgx_host, "hostname"], text=True, timeout=2.5).strip()
                if out:
                    self._update_status("dgx", "ONLINE", C_GREEN)
                else:
                    self._update_status("dgx", "OFFLINE (CACHED)", C_AMBER)
            except Exception:
                self._update_status("dgx", "OFFLINE (CACHED)", C_AMBER)

            # 7. Crypto
            self._update_status("crypto", "5 ASSETS LIVE", C_GOLD)

            # 8. Stocks
            self._update_status("stocks", "VOLATILITY READY", C_CYAN)

        threading.Thread(target=probe_worker, daemon=True).start()

    def _finish(self):
        self.config.first_run_completed = True
        self.config.save()
        self.destroy()
        if self.on_open_dashboard:
            self.on_open_dashboard()


# ==============================================================================
# 2. CLAUDE MULTI-ACCOUNT DIAGNOSTICS MODAL
# ==============================================================================
class ClaudeAccountsDialog(tk.Toplevel):
    """
    Diagnostics and account management modal for Claude Code profiles.
    Exposes active account, authentication type, plan, environment variables,
    and instructions for configuring isolated secondary profiles safely.
    """

    def __init__(self, parent: tk.Tk, config: DashboardConfig):
        super().__init__(parent)
        self.config = config

        self.title("Claude Account Diagnostics & Profiles")
        self.geometry("520x560")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 520) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 560) // 2
        self.geometry(f"+{max(40, px)}+{max(30, py)}")

        self._build_ui()

    def _build_ui(self):
        h_frame = tk.Frame(self, bg=C_BG)
        h_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            h_frame,
            text="CLAUDE ACCOUNT DIAGNOSTICS",
            font=("Consolas", 12, "bold"),
            fg=C_CORAL,
            bg=C_BG,
        ).pack(anchor="w")

        tk.Label(
            h_frame,
            text="AUTH ISOLATION & ENVIRONMENT VARIABLE PRECEDENCE",
            font=("Consolas", 8),
            fg=C_TEXT_DIM,
            bg=C_BG,
        ).pack(anchor="w", pady=(2, 0))

        container = tk.Frame(self, bg=C_BG)
        container.pack(fill="both", expand=True, padx=16)

        # 1. Active Account Box
        sec1 = tk.LabelFrame(
            container,
            text=" ACTIVE CLAUDE PROFILE ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec1.pack(fill="x", pady=6)

        raw = claude_usage.read_claude_usage()
        prof = raw.get("account_profile")

        fields = [
            ("ACCOUNT:", raw.get("masked_account", "Not Configured"), C_TEXT_WHITE),
            ("PLAN:", raw.get("plan_tier", "Claude Pro"), C_CORAL),
            ("AUTH TYPE:", raw.get("auth_type", "Subscription (OAuth)"), C_CYAN),
            ("5H QUOTA:", f"{raw.get('five_hour_remaining_pct')}% LEFT" if raw.get('five_hour_remaining_pct') is not None else "N/A", C_GREEN),
            ("WEEK QUOTA:", f"{raw.get('week_remaining_pct')}% LEFT" if raw.get('week_remaining_pct') is not None else "N/A", C_GREEN),
            ("AUTHORITY:", raw.get("authority", "UNAVAILABLE"), C_AMBER if raw.get("is_stale") else C_GREEN),
        ]

        for label, val, color in fields:
            row = tk.Frame(sec1, bg=C_PANEL_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=("Consolas", 8, "bold"), fg=color, bg=C_PANEL_BG, anchor="w").pack(side="left")

        # 2. Environment Variables & Precedence
        sec2 = tk.LabelFrame(
            container,
            text=" ENVIRONMENT VARIABLES & OVERRIDES ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec2.pack(fill="x", pady=6)

        diag = raw.get("env_diagnostics", {})
        vars_map = diag.get("variables", {})

        for var_name, state in vars_map.items():
            row = tk.Frame(sec2, bg=C_PANEL_BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=var_name, font=("Consolas", 7), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=28, anchor="w").pack(side="left")
            color = C_AMBER if state == "PRESENT" else C_TEXT_DIM
            tk.Label(row, text=state, font=("Consolas", 7, "bold"), fg=color, bg=C_PANEL_BG, anchor="e").pack(side="right")

        prec_row = tk.Frame(sec2, bg=C_PANEL_BG)
        prec_row.pack(fill="x", pady=(4, 0))
        tk.Label(prec_row, text="PRECEDENCE:", font=("Consolas", 7, "bold"), fg=C_CYAN, bg=C_PANEL_BG, width=14, anchor="w").pack(side="left")
        tk.Label(prec_row, text=diag.get("precedence", "LOCAL_SUBSCRIPTION"), font=("Consolas", 7), fg=C_TEXT_WHITE, bg=C_PANEL_BG).pack(side="left")

        # 3. Multi-Account Isolation Instructions
        sec3 = tk.LabelFrame(
            container,
            text=" SECONDARY ACCOUNT SETUP ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec3.pack(fill="x", pady=6)

        desc = (
            "To add an isolated second account without modifying your primary session:\n"
            "1. Run in PowerShell:\n"
            '   $env:CLAUDE_CONFIG_DIR="$HOME\\.claude-secondary"\n'
            "   claude auth login\n"
            "2. AI Desk Dashboard will automatically read the secondary profile."
        )
        tk.Label(
            sec3,
            text=desc,
            font=("Consolas", 7),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            justify="left",
            anchor="w",
        ).pack(fill="x")

        # Close button
        tk.Button(
            self,
            text="[ CLOSE ]",
            font=("Consolas", 9, "bold"),
            bg="#161F2E",
            fg=C_TEXT_WHITE,
            bd=1,
            relief="solid",
            cursor="hand2",
            pady=6,
            command=self.destroy,
        ).pack(fill="x", padx=16, pady=(6, 16))


# ==============================================================================
# 3. COMPREHENSIVE SETTINGS DIALOG (SECTIONS, CARDS, PRESETS, ROTATION)
# ==============================================================================
# ==============================================================================
# 3. REDESIGNED TABBED SETTINGS DIALOG (GENERAL, DASHBOARD, MINITOO, INTEGRATIONS, ADVANCED)
# ==============================================================================
class SettingsDialog(tk.Toplevel):
    """
    Redesigned Tabbed / Left-Navigation Settings Modal:
    - GENERAL: Autostart, Launch minimized, Default preset, Desktop refresh rate, Theme
    - DASHBOARD: Hierarchical sections (AI USAGE, CRYPTO, STOCKS, SYSTEM), individual cards,
      separate Desktop vs MiniToo visibility toggles, clear reorder buttons beside items
    - MINITOO: Connection status, COM port, NORMAL vs LOW INTERFERENCE mode, Auto-cycle,
      Rotation interval, Knob navigation & poll rate, Live diagnostics & Copy Diagnostics
    - INTEGRATIONS: Claude account profiles & diagnostics, DGX host, Workspace path, Stocks provider, Ditoo
    - ADVANCED: Protocol internals, Diagnostic output, Channel 5 re-entry, Reset to defaults
    """

    TAB_GENERAL = "GENERAL"
    TAB_DASHBOARD = "DASHBOARD"
    TAB_MINITOO = "MINITOO"
    TAB_INTEGRATIONS = "INTEGRATIONS"
    TAB_ADVANCED = "ADVANCED"

    ALL_TABS = [TAB_GENERAL, TAB_DASHBOARD, TAB_MINITOO, TAB_INTEGRATIONS, TAB_ADVANCED]

    def __init__(
        self,
        parent: tk.Tk,
        config: DashboardConfig,
        on_save_callback: Optional[Callable[[DashboardConfig], None]] = None,
        minitoo: Optional[Any] = None,
        state: Optional[Any] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.on_save_callback = on_save_callback
        self.minitoo = minitoo
        self.state = state

        self.title("AI Desk Dashboard — Configuration")
        self.geometry("740x640")
        self.minsize(680, 520)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 740) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 640) // 2
        self.geometry(f"+{max(20, px)}+{max(20, py)}")

        # Working state copies
        self.working_sections_order = list(self.config.sections_order)
        self.working_enabled_sections: Dict[str, tk.BooleanVar] = {
            s: tk.BooleanVar(value=self.config.enabled_sections.get(s, True)) for s in ALL_SECTIONS
        }
        self.working_section_cards: Dict[str, List[str]] = {
            s: list(self.config.section_cards.get(s, DEFAULT_SECTION_CARDS[s])) for s in ALL_SECTIONS
        }
        self.working_enabled_cards: Dict[str, tk.BooleanVar] = {
            c: tk.BooleanVar(value=self.config.enabled_cards.get(c, True)) for c in ALL_PAGE_IDS
        }
        self.working_enabled_cards_minitoo: Dict[str, tk.BooleanVar] = {
            c: tk.BooleanVar(value=self.config.enabled_cards_minitoo.get(c, True)) for c in ALL_PAGE_IDS
        }

        # General Tab Variables
        self.var_autostart = tk.BooleanVar(value=self.config.start_with_windows)
        self.var_minimized = tk.BooleanVar(value=self.config.launch_minimized)
        self.var_default_preset = tk.StringVar(value=self.config.default_preset or PRESET_ALL)
        self.var_refresh_mode = tk.StringVar(value=self.config.desktop_refresh_mode or "standard")

        # MiniToo Tab Variables
        self.var_minitoo_port = tk.StringVar(value=self.config.minitoo_port or "AUTO")
        self.var_bt_mode = tk.StringVar(value=getattr(self.config, "minitoo_bt_mode", "NORMAL"))
        self.var_autocycle = tk.BooleanVar(value=self.config.auto_cycle)
        self.var_rotation = tk.StringVar(value=str(round(self.config.rotation_interval, 1)))
        self.var_knob_enabled = tk.BooleanVar(value=getattr(self.config, "minitoo_knob_enabled", True))
        self.var_poll_rate = tk.StringVar(value=getattr(self.config, "minitoo_poll_rate", "AUTO"))

        # Integrations Tab Variables
        self.var_dgx = tk.StringVar(value=self.config.dgx_host or "dgx")
        self.var_repo = tk.StringVar(value=self.config.coding_repo_path or ".")
        self.var_target_device = tk.StringVar(
            value="Ditoo 16x16 (BLE)" if getattr(self.config, "target_device", "minitoo") == "ditoo" else "MiniToo (160x128)"
        )
        self.var_ditoo_mac = tk.StringVar(value=getattr(self.config, "ditoo_mac", "B1:21:81:5B:E3:16"))
        self.var_ditoo_tickers = tk.StringVar(value=",".join(getattr(self.config, "ditoo_stock_tickers", ["NVDA", "TSLA", "AAPL", "MSFT", "META"])))

        # Active tab & frames container
        self.active_tab = self.TAB_DASHBOARD
        self.nav_buttons: Dict[str, tk.Button] = {}
        self.tab_frames: Dict[str, tk.Frame] = {}

        self._diag_status_labels: Dict[str, tk.Label] = {}
        self._poll_active = True

        self._build_shell()
        self._switch_tab(self.TAB_DASHBOARD)
        self._schedule_diagnostics_refresh()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._poll_active = False
        self.destroy()

    def _build_shell(self):
        # 1. Header Bar
        h_frame = tk.Frame(self, bg=C_BG)
        h_frame.pack(fill="x", padx=16, pady=(12, 8))

        tk.Label(
            h_frame,
            text="AI DESK DASHBOARD — CONFIGURATION",
            font=("Consolas", 12, "bold"),
            fg=C_CYAN,
            bg=C_BG,
        ).pack(side="left")

        # Top preset indicator
        self.lbl_top_preset = tk.Label(
            h_frame,
            text=f"ACTIVE PRESET: [ {self.config.active_preset} ]",
            font=("Consolas", 8, "bold"),
            fg=C_AMBER,
            bg="#1B2232",
            padx=8,
            pady=3,
            bd=1,
            relief="solid",
        )
        self.lbl_top_preset.pack(side="right")

        # 2. Main Horizontal Container (Left Navigation + Right Content)
        main_box = tk.Frame(self, bg=C_BG)
        main_box.pack(fill="both", expand=True, padx=14, pady=4)

        # Left Navigation Sidebar
        nav_col = tk.Frame(main_box, bg="#0D121D", width=145, highlightthickness=1, highlightbackground=C_BORDER)
        nav_col.pack(side="left", fill="y", padx=(0, 10))
        nav_col.pack_propagate(False)

        tk.Label(
            nav_col,
            text="SETTINGS",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_DIM,
            bg="#0D121D",
            pady=8,
        ).pack(anchor="w", padx=12)

        tab_icons = {
            self.TAB_GENERAL: "⚙ GENERAL",
            self.TAB_DASHBOARD: "📊 DASHBOARD",
            self.TAB_MINITOO: "🖥 MINITOO",
            self.TAB_INTEGRATIONS: "🔌 INTEGRATIONS",
            self.TAB_ADVANCED: "🛠 ADVANCED",
        }

        for tab_id in self.ALL_TABS:
            btn = tk.Button(
                nav_col,
                text=tab_icons[tab_id],
                font=("Consolas", 8, "bold"),
                anchor="w",
                padx=10,
                pady=7,
                bd=1,
                relief="solid",
                cursor="hand2",
                command=lambda t=tab_id: self._switch_tab(t),
            )
            btn.pack(fill="x", padx=6, pady=3)
            self.nav_buttons[tab_id] = btn

        # Right Content View Area
        self.content_area = tk.Frame(main_box, bg=C_BG)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Initialize tab frames
        self._build_general_tab()
        self._build_dashboard_tab()
        self._build_minitoo_tab()
        self._build_integrations_tab()
        self._build_advanced_tab()

        # 3. Bottom Action Buttons Bar
        b_frame = tk.Frame(self, bg=C_BG)
        b_frame.pack(fill="x", padx=16, pady=(10, 14))

        tk.Button(
            b_frame,
            text="CANCEL",
            font=("Consolas", 9, "bold"),
            bg="#161F2E",
            fg=C_TEXT_MUTED,
            bd=1,
            relief="solid",
            width=14,
            pady=4,
            cursor="hand2",
            command=self._on_close,
        ).pack(side="left")

        tk.Button(
            b_frame,
            text="SAVE CONFIG",
            font=("Consolas", 9, "bold"),
            bg="#102E24",
            fg=C_GREEN,
            bd=1,
            relief="solid",
            width=16,
            pady=4,
            cursor="hand2",
            command=self._save_and_close,
        ).pack(side="right")

    def _switch_tab(self, tab_id: str):
        self.active_tab = tab_id
        for t, btn in self.nav_buttons.items():
            if t == tab_id:
                btn.config(bg="#0B2538", fg=C_CYAN, highlightbackground=C_CYAN)
            else:
                btn.config(bg="#101622", fg=C_TEXT_MUTED, highlightbackground=C_BORDER)

        for t, frame in self.tab_frames.items():
            if t == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        if tab_id == self.TAB_MINITOO:
            self._update_diagnostics_display()

    # ==========================================================================
    # TAB 1: GENERAL
    # ==========================================================================
    def _build_general_tab(self):
        frame = tk.Frame(self.content_area, bg=C_BG)
        self.tab_frames[self.TAB_GENERAL] = frame

        # Startup Box
        s_box = tk.LabelFrame(
            frame,
            text=" STARTUP & WINDOW ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10,
        )
        s_box.pack(fill="x", pady=(0, 10))

        tk.Checkbutton(
            s_box,
            text="START WITH WINDOWS (Registry Run Key)",
            variable=self.var_autostart,
            font=("Consolas", 8),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(anchor="w", pady=3)

        tk.Checkbutton(
            s_box,
            text="LAUNCH MINIMIZED (Silent Tray / Taskbar)",
            variable=self.var_minimized,
            font=("Consolas", 8),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(anchor="w", pady=3)

        # Default Preset Box
        p_box = tk.LabelFrame(
            frame,
            text=" DEFAULT PRESET ON STARTUP ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10,
        )
        p_box.pack(fill="x", pady=6)

        p_row = tk.Frame(p_box, bg=C_PANEL_BG)
        p_row.pack(fill="x", pady=2)
        tk.Label(p_row, text="INITIAL PRESET:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=16, anchor="w").pack(side="left")
        om_preset = tk.OptionMenu(p_row, self.var_default_preset, *ALL_PRESETS)
        om_preset.config(bg="#0D121D", fg=C_GOLD, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_preset["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_preset.pack(side="left", padx=4)

        tk.Label(
            p_box,
            text="Select which content view activates when the app opens.",
            font=("Consolas", 7),
            fg=C_TEXT_DIM,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=(6, 0))

        # Refresh Behavior Box
        r_box = tk.LabelFrame(
            frame,
            text=" TELEMETRY REFRESH BEHAVIOR ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10,
        )
        r_box.pack(fill="x", pady=6)

        r_row = tk.Frame(r_box, bg=C_PANEL_BG)
        r_row.pack(fill="x", pady=2)
        tk.Label(r_row, text="CADENCE MODE:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=16, anchor="w").pack(side="left")
        om_ref = tk.OptionMenu(r_row, self.var_refresh_mode, "standard", "relaxed", "low_resource")
        om_ref.config(bg="#0D121D", fg=C_GREEN, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_ref["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_ref.pack(side="left", padx=4)

        tk.Label(
            r_box,
            text="standard: live 2-10s refresh | relaxed: 5-20s | low_resource: 10-30s",
            font=("Consolas", 7),
            fg=C_TEXT_DIM,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=(6, 0))

        # Theme & Window Position Box
        t_box = tk.LabelFrame(
            frame,
            text=" THEME & APPEARANCE ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=14,
            pady=10,
        )
        t_box.pack(fill="x", pady=6)

        tk.Label(
            t_box,
            text="ACTIVE THEME: Dark Retro Cyberpunk (Default)",
            font=("Consolas", 8, "bold"),
            fg=C_GREEN,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=2)

        def _reset_win_pos():
            self.config.window_x = 100
            self.config.window_y = 100
            self.master.geometry("640x600+100+100")

        tk.Button(
            t_box,
            text="[ RESET WINDOW POSITION ]",
            font=("Consolas", 8),
            bg="#161F2E",
            fg=C_TEXT_WHITE,
            bd=1,
            relief="solid",
            command=_reset_win_pos,
        ).pack(anchor="w", pady=(6, 2))

    # ==========================================================================
    # TAB 2: DASHBOARD (SECTIONS, CARDS, DESKTOP VS MINITOO VISIBILITY)
    # ==========================================================================
    def _build_dashboard_tab(self):
        frame = tk.Frame(self.content_area, bg=C_BG)
        self.tab_frames[self.TAB_DASHBOARD] = frame

        # Top presets bar
        p_frame = tk.Frame(frame, bg="#0D121D", highlightthickness=1, highlightbackground=C_BORDER, padx=8, pady=5)
        p_frame.pack(fill="x", pady=(0, 6))

        tk.Label(p_frame, text="APPLY PRESET:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg="#0D121D").pack(side="left", padx=(0, 6))
        for p_name in ALL_PRESETS:
            btn = tk.Button(
                p_frame,
                text=p_name,
                font=("Consolas", 7, "bold"),
                bg="#121A28",
                fg=C_TEXT_WHITE,
                bd=1,
                relief="solid",
                padx=6,
                command=lambda name=p_name: self._apply_preset_to_working_state(name),
            )
            btn.pack(side="left", padx=2)

        # Instructions Header
        hdr_row = tk.Frame(frame, bg=C_BG)
        hdr_row.pack(fill="x", pady=2)
        tk.Label(
            hdr_row,
            text="SECTIONS & CARDS ORDER / VISIBILITY",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_BG,
        ).pack(side="left")
        tk.Label(
            hdr_row,
            text="Configure Desktop vs MiniToo separately per card.",
            font=("Consolas", 7),
            fg=C_TEXT_DIM,
            bg=C_BG,
        ).pack(side="right")

        # Scrollable Canvas Container for Sections and Cards
        self.sec_cards_container = tk.Frame(frame, bg=C_BG)
        self.sec_cards_container.pack(fill="both", expand=True)

        self.sec_canvas = tk.Canvas(self.sec_cards_container, bg=C_BG, highlightthickness=0)
        self.sec_scrollbar = tk.Scrollbar(self.sec_cards_container, orient="vertical", command=self.sec_canvas.yview)
        self.sec_scroll_frame = tk.Frame(self.sec_canvas, bg=C_BG)

        self.sec_scroll_frame.bind(
            "<Configure>",
            lambda e: self.sec_canvas.configure(scrollregion=self.sec_canvas.bbox("all")),
        )
        self.sec_canvas_window = self.sec_canvas.create_window((0, 0), window=self.sec_scroll_frame, anchor="nw")
        self.sec_canvas.configure(yscrollcommand=self.sec_scrollbar.set)

        self.sec_canvas.pack(side="left", fill="both", expand=True)
        self.sec_scrollbar.pack(side="right", fill="y")

        self.sec_canvas.bind_all("<MouseWheel>", self._on_sec_mousewheel)
        self.sec_canvas.bind("<Configure>", lambda e: self.sec_canvas.itemconfig(self.sec_canvas_window, width=e.width))

        self._refresh_dashboard_sections_view()

    def _on_sec_mousewheel(self, event):
        if self.active_tab == self.TAB_DASHBOARD and self.sec_canvas.winfo_exists():
            self.sec_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _refresh_dashboard_sections_view(self):
        for widget in self.sec_scroll_frame.winfo_children():
            widget.destroy()

        brand_colors = {
            "crypto": C_GOLD,
            "ai_usage": C_CORAL,
            "stocks": C_CYAN,
            "system": C_GREEN,
        }

        for s_idx, sec_id in enumerate(self.working_sections_order):
            sec_title = SECTION_TITLES.get(sec_id, sec_id.upper())
            sec_color = brand_colors.get(sec_id, C_TEXT_WHITE)

            # Section Box
            s_box = tk.LabelFrame(
                self.sec_scroll_frame,
                text=f" ─── {sec_title} ─── ",
                font=("Consolas", 8, "bold"),
                fg=sec_color,
                bg=C_PANEL_BG,
                highlightbackground=C_BORDER,
                highlightthickness=1,
                bd=0,
                padx=8,
                pady=6,
            )
            s_box.pack(fill="x", pady=4, padx=2)

            # Section Header Row (Enable Checkbox + Arrow Buttons)
            s_hdr = tk.Frame(s_box, bg=C_PANEL_BG)
            s_hdr.pack(fill="x", pady=(0, 4))

            cb_sec = tk.Checkbutton(
                s_hdr,
                text="SECTION ENABLED",
                variable=self.working_enabled_sections[sec_id],
                font=("Consolas", 8, "bold"),
                fg=C_TEXT_WHITE,
                bg=C_PANEL_BG,
                selectcolor="#0D121D",
                activebackground=C_PANEL_BG,
            )
            cb_sec.pack(side="left")

            # Section Reorder Arrow Buttons
            btn_up = tk.Button(
                s_hdr,
                text="▲",
                font=("Consolas", 7, "bold"),
                bg="#161F2E",
                fg=C_TEXT_WHITE,
                bd=1,
                relief="solid",
                width=3,
                command=lambda idx=s_idx: self._move_section(idx, -1),
            )
            btn_up.pack(side="right", padx=1)
            btn_down = tk.Button(
                s_hdr,
                text="▼",
                font=("Consolas", 7, "bold"),
                bg="#161F2E",
                fg=C_TEXT_WHITE,
                bd=1,
                relief="solid",
                width=3,
                command=lambda idx=s_idx: self._move_section(idx, 1),
            )
            btn_down.pack(side="right", padx=1)

            # Column Headers for Cards
            c_hdr = tk.Frame(s_box, bg="#0D121D", padx=6, pady=2)
            c_hdr.pack(fill="x", pady=(2, 4))
            tk.Label(c_hdr, text="CARD NAME", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg="#0D121D", width=22, anchor="w").pack(side="left")
            tk.Label(c_hdr, text="DESKTOP", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg="#0D121D", width=10, anchor="center").pack(side="left")
            tk.Label(c_hdr, text="MINITOO", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg="#0D121D", width=10, anchor="center").pack(side="left")
            tk.Label(c_hdr, text="ORDER", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg="#0D121D", width=8, anchor="e").pack(side="right")

            # Cards List in this Section
            cards = self.working_section_cards.get(sec_id, [])
            for c_idx, card_id in enumerate(cards):
                card_label = PAGE_LABELS.get(card_id, card_id.upper())
                c_row = tk.Frame(s_box, bg=C_PANEL_BG, padx=4, pady=2)
                c_row.pack(fill="x", pady=1)

                # Card Name
                tk.Label(
                    c_row,
                    text=f"• {card_label}",
                    font=("Consolas", 8),
                    fg=C_TEXT_WHITE,
                    bg=C_PANEL_BG,
                    width=22,
                    anchor="w",
                ).pack(side="left")

                # Desktop Visibility Checkbox
                if card_id not in self.working_enabled_cards:
                    self.working_enabled_cards[card_id] = tk.BooleanVar(value=True)
                cb_desk = tk.Checkbutton(
                    c_row,
                    text="Show",
                    variable=self.working_enabled_cards[card_id],
                    font=("Consolas", 7),
                    fg=C_GREEN,
                    bg=C_PANEL_BG,
                    selectcolor="#0D121D",
                    activebackground=C_PANEL_BG,
                    width=8,
                )
                cb_desk.pack(side="left", padx=4)

                # MiniToo Visibility Checkbox
                if card_id not in self.working_enabled_cards_minitoo:
                    self.working_enabled_cards_minitoo[card_id] = tk.BooleanVar(value=True)
                cb_mini = tk.Checkbutton(
                    c_row,
                    text="Show",
                    variable=self.working_enabled_cards_minitoo[card_id],
                    font=("Consolas", 7),
                    fg=C_CYAN,
                    bg=C_PANEL_BG,
                    selectcolor="#0D121D",
                    activebackground=C_PANEL_BG,
                    width=8,
                )
                cb_mini.pack(side="left", padx=4)

                # Card Order Arrow Buttons
                c_btn_down = tk.Button(
                    c_row,
                    text="▼",
                    font=("Consolas", 6, "bold"),
                    bg="#161F2E",
                    fg=C_TEXT_WHITE,
                    bd=1,
                    relief="solid",
                    width=2,
                    command=lambda sid=sec_id, idx=c_idx: self._move_card(sid, idx, 1),
                )
                c_btn_down.pack(side="right", padx=1)

                c_btn_up = tk.Button(
                    c_row,
                    text="▲",
                    font=("Consolas", 6, "bold"),
                    bg="#161F2E",
                    fg=C_TEXT_WHITE,
                    bd=1,
                    relief="solid",
                    width=2,
                    command=lambda sid=sec_id, idx=c_idx: self._move_card(sid, idx, -1),
                )
                c_btn_up.pack(side="right", padx=1)

    def _move_section(self, idx: int, delta: int):
        new_idx = idx + delta
        if 0 <= new_idx < len(self.working_sections_order):
            self.working_sections_order[idx], self.working_sections_order[new_idx] = (
                self.working_sections_order[new_idx],
                self.working_sections_order[idx],
            )
            self._refresh_dashboard_sections_view()

    def _move_card(self, sec_id: str, idx: int, delta: int):
        cards = self.working_section_cards.get(sec_id, [])
        new_idx = idx + delta
        if 0 <= new_idx < len(cards):
            cards[idx], cards[new_idx] = cards[new_idx], cards[idx]
            self._refresh_dashboard_sections_view()

    def _apply_preset_to_working_state(self, preset_name: str):
        self.config.apply_preset(preset_name)
        for s in ALL_SECTIONS:
            self.working_enabled_sections[s].set(self.config.enabled_sections[s])
        for c in ALL_PAGE_IDS:
            self.working_enabled_cards[c].set(self.config.enabled_cards[c])
        self.lbl_top_preset.config(text=f"ACTIVE PRESET: [ {self.config.active_preset} ]")
        self._refresh_dashboard_sections_view()

    # ==========================================================================
    # TAB 3: MINITOO (DEVICE, DISPLAY, CONTROLS, DIAGNOSTICS & ACTIONS)
    # ==========================================================================
    def _build_minitoo_tab(self):
        frame = tk.Frame(self.content_area, bg=C_BG)
        self.tab_frames[self.TAB_MINITOO] = frame

        # 1. Device Box
        dev_box = tk.LabelFrame(
            frame,
            text=" DEVICE & HARDWARE LINK ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        dev_box.pack(fill="x", pady=(0, 6))

        # Status row
        d_row1 = tk.Frame(dev_box, bg=C_PANEL_BG)
        d_row1.pack(fill="x", pady=2)
        tk.Label(d_row1, text="DEVICE STATUS:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=15, anchor="w").pack(side="left")
        self.lbl_mini_status = tk.Label(d_row1, text="CONNECTING...", font=("Consolas", 8, "bold"), fg=C_AMBER, bg="#1B2232", padx=6)
        self.lbl_mini_status.pack(side="left")

        # Port row
        d_row2 = tk.Frame(dev_box, bg=C_PANEL_BG)
        d_row2.pack(fill="x", pady=2)
        tk.Label(d_row2, text="PORT (COM):", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=15, anchor="w").pack(side="left")
        available_ports = ["AUTO"] + [p["device"] for p in get_all_com_ports()]
        if self.config.minitoo_port not in available_ports:
            available_ports.append(self.config.minitoo_port)
        om_port = tk.OptionMenu(d_row2, self.var_minitoo_port, *available_ports)
        om_port.config(bg="#0D121D", fg=C_CYAN, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_port["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_port.pack(side="left", padx=2)

        # Mode row
        d_row3 = tk.Frame(dev_box, bg=C_PANEL_BG)
        d_row3.pack(fill="x", pady=2)
        tk.Label(d_row3, text="TRANSPORT MODE:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=15, anchor="w").pack(side="left")
        om_mode = tk.OptionMenu(d_row3, self.var_bt_mode, "NORMAL", "LOW_INTERFERENCE")
        om_mode.config(bg="#0D121D", fg=C_GOLD, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_mode["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_mode.pack(side="left", padx=2)

        tk.Label(
            dev_box,
            text="LOW INTERFERENCE reduces knob queries & Channel 5 checks to prevent Bluetooth audio stutter.",
            font=("Consolas", 7),
            fg=C_TEXT_DIM,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=(4, 0))

        # 2. Display & Rotation Box
        rot_box = tk.LabelFrame(
            frame,
            text=" DISPLAY ROTATION ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        rot_box.pack(fill="x", pady=6)

        r_sub1 = tk.Frame(rot_box, bg=C_PANEL_BG)
        r_sub1.pack(fill="x", pady=2)
        tk.Checkbutton(
            r_sub1,
            text="AUTO CYCLE PAGES",
            variable=self.var_autocycle,
            font=("Consolas", 8, "bold"),
            fg=C_GREEN,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(side="left")

        tk.Label(r_sub1, text="ROTATION DWELL:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG).pack(side="left", padx=(20, 4))
        ent_dwell = tk.Entry(r_sub1, textvariable=self.var_rotation, width=5, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE)
        ent_dwell.pack(side="left")
        tk.Label(r_sub1, text="sec", font=("Consolas", 8), fg=C_TEXT_DIM, bg=C_PANEL_BG).pack(side="left", padx=2)

        # 3. Hardware Controls Box
        ctrl_box = tk.LabelFrame(
            frame,
            text=" PHYSICAL CONTROLS (ROTARY KNOB / BUTTONS) ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        ctrl_box.pack(fill="x", pady=6)

        c_sub1 = tk.Frame(ctrl_box, bg=C_PANEL_BG)
        c_sub1.pack(fill="x", pady=2)
        tk.Checkbutton(
            c_sub1,
            text="KNOB NAVIGATION (Turns = Next/Prev Page)",
            variable=self.var_knob_enabled,
            font=("Consolas", 8),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(side="left")

        tk.Label(c_sub1, text="POLL RATE:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG).pack(side="left", padx=(16, 4))
        om_poll = tk.OptionMenu(c_sub1, self.var_poll_rate, "AUTO", "2Hz", "3Hz", "4Hz", "5Hz")
        om_poll.config(bg="#0D121D", fg=C_GOLD, font=("Consolas", 8), highlightthickness=1, highlightbackground=C_BORDER)
        om_poll["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_poll.pack(side="left")

        # 4. Live Telemetry & Diagnostics Box
        diag_box = tk.LabelFrame(
            frame,
            text=" LIVE BLUETOOTH TRAFFIC & DIAGNOSTICS ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=6,
        )
        diag_box.pack(fill="x", pady=6)

        d_grid = tk.Frame(diag_box, bg=C_PANEL_BG)
        d_grid.pack(fill="x")

        # Left Column: Rates
        col1 = tk.Frame(d_grid, bg=C_PANEL_BG)
        col1.pack(side="left", fill="both", expand=True)

        self._diag_status_labels["frames_min"] = self._create_diag_row(col1, "Frames / min:", "0")
        self._diag_status_labels["traffic_min"] = self._create_diag_row(col1, "Traffic Rate:", "0.0 KB/min")
        self._diag_status_labels["writes_min"] = self._create_diag_row(col1, "SPP Writes / min:", "0")

        # Right Column: Controls & Health
        col2 = tk.Frame(d_grid, bg=C_PANEL_BG)
        col2.pack(side="right", fill="both", expand=True)

        self._diag_status_labels["knob_polls"] = self._create_diag_row(col2, "Knob Polls / sec:", "0.0 Hz")
        self._diag_status_labels["reconnects"] = self._create_diag_row(col2, "Reconnects:", "0")
        self._diag_status_labels["last_error"] = self._create_diag_row(col2, "Last Error:", "None")

        # Action Buttons Row
        btn_bar = tk.Frame(frame, bg=C_BG)
        btn_bar.pack(fill="x", pady=(8, 2))

        tk.Button(
            btn_bar,
            text="[ 🔄 TEST DISPLAY ]",
            font=("Consolas", 8, "bold"),
            bg="#102538",
            fg=C_CYAN,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._do_test_display,
        ).pack(side="left", padx=2)

        tk.Button(
            btn_bar,
            text="[ 🔌 RECONNECT ]",
            font=("Consolas", 8, "bold"),
            bg="#2A1E10",
            fg=C_AMBER,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._do_reconnect,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_bar,
            text="[ 📋 COPY DIAGNOSTICS ]",
            font=("Consolas", 8, "bold"),
            bg="#161F2E",
            fg=C_GREEN,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._do_copy_diagnostics,
        ).pack(side="right", padx=2)

        self.lbl_copy_msg = tk.Label(btn_bar, text="", font=("Consolas", 7), fg=C_GREEN, bg=C_BG)
        self.lbl_copy_msg.pack(side="right", padx=4)

    def _create_diag_row(self, parent: tk.Widget, label_text: str, default_val: str) -> tk.Label:
        row = tk.Frame(parent, bg=C_PANEL_BG)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=label_text, font=("Consolas", 7), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=18, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=default_val, font=("Consolas", 7, "bold"), fg=C_TEXT_WHITE, bg=C_PANEL_BG, anchor="w")
        lbl.pack(side="left")
        return lbl

    def _do_test_display(self):
        if self.minitoo and hasattr(self.minitoo, "test_display"):
            self.minitoo.test_display()
            self.lbl_copy_msg.config(text="Test frame dispatched!", fg=C_CYAN)
        else:
            self.lbl_copy_msg.config(text="Hardware link unavailable", fg=C_AMBER)

    def _do_reconnect(self):
        if self.minitoo and hasattr(self.minitoo, "trigger_reconnect"):
            self.minitoo.trigger_reconnect()
            self.lbl_copy_msg.config(text="Reconnect cycle triggered", fg=C_AMBER)

    def _do_copy_diagnostics(self):
        if self.minitoo and hasattr(self.minitoo, "format_diagnostics_report"):
            report = self.minitoo.format_diagnostics_report()
        else:
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            report = (
                f"=== MINITOO BLUETOOTH TRANSPORT DIAGNOSTICS ===\n"
                f"Timestamp:             {now_str}\n"
                f"Connection Status:     {self.config.minitoo_port}\n"
                f"Transport Mode:        {self.var_bt_mode.get()}\n"
                f"Knob Navigation:       {'ENABLED' if self.var_knob_enabled.get() else 'DISABLED'}\n"
                f"================================================\n"
            )
        try:
            self.clipboard_clear()
            self.clipboard_append(report)
            self.lbl_copy_msg.config(text="Copied to clipboard!", fg=C_GREEN)
        except Exception as e:
            self.lbl_copy_msg.config(text=f"Copy error: {e}", fg=C_RED)

    def _update_diagnostics_display(self):
        if not self._poll_active:
            return
        if self.minitoo and hasattr(self.minitoo, "get_diagnostics"):
            d = self.minitoo.get_diagnostics()
            st_text = d.get("status", "DISCONNECTED")
            st_col = C_GREEN if st_text == "CONNECTED" else C_AMBER
            self.lbl_mini_status.config(text=f"{st_text} ({d.get('port', 'AUTO')})", fg=st_col)

            if "frames_min" in self._diag_status_labels:
                self._diag_status_labels["frames_min"].config(text=str(d.get("frames_per_min", 0)))
                self._diag_status_labels["traffic_min"].config(text=f"{d.get('kb_per_min', 0.0)} KB/min")
                self._diag_status_labels["writes_min"].config(text=str(d.get("writes_per_min", 0)))
                self._diag_status_labels["knob_polls"].config(text=f"{d.get('knob_polls_per_sec', 0.0):.1f} Hz")
                self._diag_status_labels["reconnects"].config(text=str(d.get("reconnect_count", 0)))
                err = d.get("last_error") or "None"
                self._diag_status_labels["last_error"].config(text=err if len(err) < 25 else err[:22] + "...")
        elif self.state:
            conn = self.state.minitoo_connected
            self.lbl_mini_status.config(text="CONNECTED" if conn else "DISCONNECTED", fg=C_GREEN if conn else C_AMBER)

    def _schedule_diagnostics_refresh(self):
        if self._poll_active:
            self._update_diagnostics_display()
            self.after(1000, self._schedule_diagnostics_refresh)

    # ==========================================================================
    # TAB 4: INTEGRATIONS (CLAUDE, DGX, GIT, STOCKS, DITOO)
    # ==========================================================================
    def _build_integrations_tab(self):
        frame = tk.Frame(self.content_area, bg=C_BG)
        self.tab_frames[self.TAB_INTEGRATIONS] = frame

        # Claude Multi-Account
        c_box = tk.LabelFrame(
            frame,
            text=" ANTHROPIC CLAUDE CODE INTEGRATION ",
            font=("Consolas", 8, "bold"),
            fg=C_CORAL,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        c_box.pack(fill="x", pady=(0, 6))

        tk.Label(
            c_box,
            text="Multi-account isolation supported via distinct CLAUDE_CONFIG_DIR environments.",
            font=("Consolas", 7),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=(0, 4))

        tk.Button(
            c_box,
            text="[ OPEN CLAUDE ACCOUNTS & DIAGNOSTICS ]",
            font=("Consolas", 8, "bold"),
            bg="#2A1A14",
            fg=C_CORAL,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._show_claude_diagnostics,
        ).pack(anchor="w", pady=2)

        # DGX Spark & Workspace
        s_box = tk.LabelFrame(
            frame,
            text=" DGX SPARK & ACTIVE REPOSITORY ",
            font=("Consolas", 8, "bold"),
            fg=C_GREEN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        s_box.pack(fill="x", pady=6)

        dgx_row = tk.Frame(s_box, bg=C_PANEL_BG)
        dgx_row.pack(fill="x", pady=2)
        tk.Label(dgx_row, text="DGX HOST / IP:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=16, anchor="w").pack(side="left")
        tk.Entry(dgx_row, textvariable=self.var_dgx, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, width=18).pack(side="left")

        repo_row = tk.Frame(s_box, bg=C_PANEL_BG)
        repo_row.pack(fill="x", pady=2)
        tk.Label(repo_row, text="WORKSPACE PATH:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=16, anchor="w").pack(side="left")
        tk.Entry(repo_row, textvariable=self.var_repo, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, width=32).pack(side="left")

        # Market & Ditoo
        m_box = tk.LabelFrame(
            frame,
            text=" STOCKS & DITOO 16x16 INTEGRATION ",
            font=("Consolas", 8, "bold"),
            fg=C_GOLD,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        m_box.pack(fill="x", pady=6)

        tk.Label(
            m_box,
            text="Market Data Provider: YahooFinance (Free quotes & intraday volatility)",
            font=("Consolas", 7),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
        ).pack(anchor="w", pady=2)

        d_row = tk.Frame(m_box, bg=C_PANEL_BG)
        d_row.pack(fill="x", pady=2)
        tk.Label(d_row, text="DITOO TICKERS:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=16, anchor="w").pack(side="left")
        tk.Entry(d_row, textvariable=self.var_ditoo_tickers, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, width=32).pack(side="left")

    def _show_claude_diagnostics(self):
        ClaudeAccountsDialog(self, self.config)

    # ==========================================================================
    # TAB 5: ADVANCED (PROTOCOL, LOGS, RE-ENTRY & RESET)
    # ==========================================================================
    def _build_advanced_tab(self):
        frame = tk.Frame(self.content_area, bg=C_BG)
        self.tab_frames[self.TAB_ADVANCED] = frame

        # Architecture & Specs
        a_box = tk.LabelFrame(
            frame,
            text=" PROTOCOL ARCHITECTURE & BLUETOOTH COEXISTENCE ",
            font=("Consolas", 8, "bold"),
            fg=C_CYAN,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        a_box.pack(fill="x", pady=(0, 6))

        spec_text = (
            "• Transport: Bluetooth Classic SPP (RFCOMM) at 115200 baud\n"
            "• Display Resolution: 160x128 pixels (IPS LCD, Custom Channel 5)\n"
            "• Frame Diffing: Transmits only when frame payload hash changes\n"
            "• Bluetooth Coexistence: LOW INTERFERENCE mode caps polling to ~2.5Hz\n"
            "  and extends Channel 5 check interval to 120s to prevent A2DP speaker dropouts."
        )
        tk.Label(
            a_box,
            text=spec_text,
            font=("Consolas", 7),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=2)

        # Maintenance Tools
        m_box = tk.LabelFrame(
            frame,
            text=" MAINTENANCE ACTIONS ",
            font=("Consolas", 8, "bold"),
            fg=C_AMBER,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=8,
        )
        m_box.pack(fill="x", pady=6)

        m_row = tk.Frame(m_box, bg=C_PANEL_BG)
        m_row.pack(fill="x", pady=2)

        def _force_ch5():
            if self.minitoo and hasattr(self.minitoo, "_adapter") and self.minitoo._adapter:
                self.minitoo._adapter.set_channel(5)
                self.lbl_adv_msg.config(text="Channel 5 re-entered successfully", fg=C_GREEN)
            else:
                self.lbl_adv_msg.config(text="Device not connected", fg=C_AMBER)

        tk.Button(
            m_row,
            text="[ FORCE CHANNEL 5 RE-ENTRY ]",
            font=("Consolas", 8),
            bg="#161F2E",
            fg=C_CYAN,
            bd=1,
            relief="solid",
            command=_force_ch5,
        ).pack(side="left", padx=2)

        def _reset_defaults():
            self.working_sections_order = list(ALL_SECTIONS)
            self.working_enabled_sections = {s: tk.BooleanVar(value=True) for s in ALL_SECTIONS}
            self.working_section_cards = {s: list(DEFAULT_SECTION_CARDS[s]) for s in ALL_SECTIONS}
            self.working_enabled_cards = {c: tk.BooleanVar(value=True) for c in ALL_PAGE_IDS}
            self.working_enabled_cards_minitoo = {c: tk.BooleanVar(value=True) for c in ALL_PAGE_IDS}
            self.var_minitoo_port.set("AUTO")
            self.var_bt_mode.set("NORMAL")
            self.var_poll_rate.set("AUTO")
            self.var_rotation.set("4.0")
            self.var_autocycle.set(False)
            self._refresh_dashboard_sections_view()
            self.lbl_adv_msg.config(text="All settings restored to defaults", fg=C_GREEN)

        tk.Button(
            m_row,
            text="[ RESET TO DEFAULTS ]",
            font=("Consolas", 8),
            bg="#2A1616",
            fg=C_RED,
            bd=1,
            relief="solid",
            command=_reset_defaults,
        ).pack(side="left", padx=8)

        self.lbl_adv_msg = tk.Label(m_box, text="", font=("Consolas", 7), fg=C_GREEN, bg=C_PANEL_BG)
        self.lbl_adv_msg.pack(anchor="w", pady=(4, 0))

    # ==========================================================================
    # SAVE & PERSISTENCE
    # ==========================================================================
    def _save_and_close(self):
        self._poll_active = False

        # Sections and cards
        self.config.sections_order = list(self.working_sections_order)
        self.config.enabled_sections = {s: self.working_enabled_sections[s].get() for s in ALL_SECTIONS}
        self.config.section_cards = {s: list(self.working_section_cards[s]) for s in ALL_SECTIONS}
        self.config.enabled_cards = {c: self.working_enabled_cards[c].get() for c in ALL_PAGE_IDS}
        self.config.enabled_cards_minitoo = {c: self.working_enabled_cards_minitoo[c].get() for c in ALL_PAGE_IDS}

        # Keep enabled_pages in sync with enabled_cards
        self.config.enabled_pages = [c for c in ALL_PAGE_IDS if self.config.enabled_cards.get(c, True)]

        # General
        self.config.start_with_windows = self.var_autostart.get()
        self.config.launch_minimized = self.var_minimized.get()
        self.config.default_preset = self.var_default_preset.get().strip() or PRESET_ALL
        self.config.desktop_refresh_mode = self.var_refresh_mode.get().strip() or "standard"

        # MiniToo
        self.config.minitoo_port = self.var_minitoo_port.get().strip() or "AUTO"
        self.config.minitoo_bt_mode = self.var_bt_mode.get().strip() or "NORMAL"
        self.config.auto_cycle = self.var_autocycle.get()
        try:
            self.config.rotation_interval = float(self.var_rotation.get())
        except ValueError:
            self.config.rotation_interval = 4.0
        self.config.minitoo_knob_enabled = self.var_knob_enabled.get()
        self.config.minitoo_poll_rate = self.var_poll_rate.get().strip() or "AUTO"

        # Integrations
        self.config.dgx_host = self.var_dgx.get().strip() or "dgx"
        self.config.coding_repo_path = self.var_repo.get().strip() or "."
        raw_tickers = self.var_ditoo_tickers.get()
        self.config.ditoo_stock_tickers = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

        self.config.save()
        self.destroy()

        if self.on_save_callback:
            self.on_save_callback(self.config)

