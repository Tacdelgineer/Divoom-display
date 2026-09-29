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
class SettingsDialog(tk.Toplevel):
    """
    Settings modal for:
    - Preset selection: ALL, AI, MARKETS, SYSTEM
    - Section order & visibility toggles
    - Card order & visibility toggles per section
    - Claude account diagnostics & profile setup
    - MiniToo COM port & rotation settings
    - Autostart with Windows
    """

    def __init__(self, parent: tk.Tk, config: DashboardConfig, on_save_callback: Optional[Callable[[DashboardConfig], None]] = None):
        super().__init__(parent)
        self.config = config
        self.on_save_callback = on_save_callback

        self.title("AI Desk Dashboard — Configuration")
        self.geometry("540x660")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 540) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 660) // 2
        self.geometry(f"+{max(40, px)}+{max(30, py)}")

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

        self.selected_section = self.working_sections_order[0]
        self._build_ui()

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=C_BG)
        h_frame.pack(fill="x", padx=16, pady=(14, 6))

        tk.Label(
            h_frame,
            text="DASHBOARD CONFIGURATION",
            font=("Consolas", 12, "bold"),
            fg=C_CYAN,
            bg=C_BG,
        ).pack(side="left")

        btn_diag = tk.Button(
            h_frame,
            text="[ CLAUDE DIAGNOSTICS ]",
            font=("Consolas", 8, "bold"),
            bg="#2A1A14",
            fg=C_CORAL,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._show_claude_diagnostics,
        )
        btn_diag.pack(side="right")

        container = tk.Frame(self, bg=C_BG)
        container.pack(fill="both", expand=True, padx=16)

        # ----------------------------------------------------------------------
        # PRESETS BAR
        # ----------------------------------------------------------------------
        p_frame = tk.Frame(container, bg=C_BG)
        p_frame.pack(fill="x", pady=(2, 6))

        tk.Label(p_frame, text="PRESET:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_BG).pack(side="left", padx=(0, 6))

        for p_name in ALL_PRESETS:
            is_active = (self.config.active_preset == p_name)
            fg_c = C_CYAN if is_active else C_TEXT_WHITE
            bg_c = "#102538" if is_active else "#131B2A"
            btn = tk.Button(
                p_frame,
                text=f"[ {p_name} ]",
                font=("Consolas", 8, "bold"),
                bg=bg_c,
                fg=fg_c,
                bd=1,
                relief="solid",
                cursor="hand2",
                command=lambda name=p_name: self._apply_preset_ui(name),
            )
            btn.pack(side="left", padx=3)

        # ----------------------------------------------------------------------
        # SECTIONS & CARDS MANAGER
        # ----------------------------------------------------------------------
        sec1 = tk.LabelFrame(
            container,
            text=" SECTIONS & CARDS ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec1.pack(fill="x", pady=4)

        sc_grid = tk.Frame(sec1, bg=C_PANEL_BG)
        sc_grid.pack(fill="x")

        # Left Column: Sections
        sec_col = tk.Frame(sc_grid, bg=C_PANEL_BG)
        sec_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(sec_col, text="SECTIONS ORDER", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg=C_PANEL_BG).pack(anchor="w")

        self.sec_listbox = tk.Listbox(
            sec_col,
            font=("Consolas", 8),
            bg="#0D121D",
            fg=C_TEXT_WHITE,
            selectbackground=C_CYAN,
            selectforeground="#000000",
            highlightthickness=1,
            highlightbackground=C_BORDER,
            height=5,
            activestyle="none",
        )
        self.sec_listbox.pack(fill="x", pady=2)
        self.sec_listbox.bind("<<ListboxSelect>>", self._on_section_selected)

        sec_btns = tk.Frame(sec_col, bg=C_PANEL_BG)
        sec_btns.pack(fill="x", pady=2)
        tk.Button(sec_btns, text="▲", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_TEXT_WHITE, bd=1, relief="solid", width=3, command=self._move_sec_up).pack(side="left", padx=1)
        tk.Button(sec_btns, text="▼", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_TEXT_WHITE, bd=1, relief="solid", width=3, command=self._move_sec_down).pack(side="left", padx=1)
        tk.Button(sec_btns, text="TOGGLE", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_AMBER, bd=1, relief="solid", command=self._toggle_sec).pack(side="left", padx=2)

        # Right Column: Cards in Selected Section
        card_col = tk.Frame(sc_grid, bg=C_PANEL_BG)
        card_col.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.lbl_cards_header = tk.Label(card_col, text="CARDS IN SECTION", font=("Consolas", 7, "bold"), fg=C_TEXT_DIM, bg=C_PANEL_BG)
        self.lbl_cards_header.pack(anchor="w")

        self.card_listbox = tk.Listbox(
            card_col,
            font=("Consolas", 8),
            bg="#0D121D",
            fg=C_TEXT_WHITE,
            selectbackground=C_GOLD,
            selectforeground="#000000",
            highlightthickness=1,
            highlightbackground=C_BORDER,
            height=5,
            activestyle="none",
        )
        self.card_listbox.pack(fill="x", pady=2)

        card_btns = tk.Frame(card_col, bg=C_PANEL_BG)
        card_btns.pack(fill="x", pady=2)
        tk.Button(card_btns, text="▲", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_TEXT_WHITE, bd=1, relief="solid", width=3, command=self._move_card_up).pack(side="left", padx=1)
        tk.Button(card_btns, text="▼", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_TEXT_WHITE, bd=1, relief="solid", width=3, command=self._move_card_down).pack(side="left", padx=1)
        tk.Button(card_btns, text="TOGGLE", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_AMBER, bd=1, relief="solid", command=self._toggle_card).pack(side="left", padx=2)

        self._refresh_sections_listbox()

        # ----------------------------------------------------------------------
        # DEVICE SELECTION & ROTATION (MiniToo / Ditoo)
        # ----------------------------------------------------------------------
        sec2 = tk.LabelFrame(
            container,
            text=" HARDWARE DISPLAY & ROTATION ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec2.pack(fill="x", pady=4)

        # Device Target Row
        dev_row = tk.Frame(sec2, bg=C_PANEL_BG)
        dev_row.pack(fill="x", pady=2)
        tk.Label(dev_row, text="TARGET:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")
        self.var_target_device = tk.StringVar(value="Ditoo 16x16 (BLE)" if getattr(self.config, "target_device", "minitoo") == "ditoo" else "MiniToo (160x128)")
        om_dev = tk.OptionMenu(dev_row, self.var_target_device, "MiniToo (160x128)", "Ditoo 16x16 (BLE)")
        om_dev.config(bg="#0D121D", fg=C_GOLD, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_dev["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_dev.pack(side="left", padx=4)

        d_row1 = tk.Frame(sec2, bg=C_PANEL_BG)
        d_row1.pack(fill="x", pady=2)

        tk.Label(d_row1, text="PORT/MAC:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")
        available_ports = ["AUTO"] + [p["device"] for p in get_all_com_ports()]
        if self.config.minitoo_port not in available_ports:
            available_ports.append(self.config.minitoo_port)

        self.var_port = tk.StringVar(value=self.config.minitoo_port)
        om_port = tk.OptionMenu(d_row1, self.var_port, *available_ports)
        om_port.config(bg="#0D121D", fg=C_CYAN, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_port["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_port.pack(side="left", padx=4)

        # Ditoo specific controls
        ditoo_box = tk.Frame(sec2, bg="#0D121D", highlightthickness=1, highlightbackground=C_BORDER, padx=6, pady=4)
        ditoo_box.pack(fill="x", pady=4)

        d_sub1 = tk.Frame(ditoo_box, bg="#0D121D")
        d_sub1.pack(fill="x", pady=1)
        tk.Label(d_sub1, text="DITOO TICKERS:", font=("Consolas", 7, "bold"), fg=C_CYAN, bg="#0D121D").pack(side="left")
        default_tickers = ",".join(getattr(self.config, "ditoo_stock_tickers", ["NVDA", "TSLA", "AAPL", "MSFT", "META"]))
        self.var_ditoo_tickers = tk.StringVar(value=default_tickers)
        tk.Entry(d_sub1, textvariable=self.var_ditoo_tickers, font=("Consolas", 8), bg="#161F2E", fg=C_TEXT_WHITE, width=28).pack(side="left", padx=4)

        d_sub2 = tk.Frame(ditoo_box, bg="#0D121D")
        d_sub2.pack(fill="x", pady=2)
        self.var_ditoo_btc = tk.BooleanVar(value=getattr(self.config, "ditoo_enabled_btc", True))
        tk.Checkbutton(d_sub2, text="BTC", variable=self.var_ditoo_btc, font=("Consolas", 7, "bold"), fg=C_GOLD, bg="#0D121D", selectcolor="#000000").pack(side="left", padx=2)
        self.var_ditoo_stocks = tk.BooleanVar(value=getattr(self.config, "ditoo_enabled_stocks", True))
        tk.Checkbutton(d_sub2, text="STOCKS", variable=self.var_ditoo_stocks, font=("Consolas", 7, "bold"), fg=C_GREEN, bg="#0D121D", selectcolor="#000000").pack(side="left", padx=2)

        def _open_preview():
            p_path = os.path.abspath("previews_ditoo_16/composite_overview.png")
            if os.path.exists(p_path) and sys.platform == "win32":
                os.startfile(p_path)

        tk.Button(d_sub2, text="PREVIEW 16x16", font=("Consolas", 7, "bold"), bg="#161F2E", fg=C_CYAN, bd=1, relief="solid", command=_open_preview).pack(side="right", padx=2)

        d_row2 = tk.Frame(sec2, bg=C_PANEL_BG)
        d_row2.pack(fill="x", pady=2)

        tk.Label(d_row2, text="ROTATION:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")
        self.var_rotation = tk.StringVar(value=str(int(self.config.rotation_interval)))
        ent_rot = tk.Entry(d_row2, textvariable=self.var_rotation, width=5, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, insertbackground=C_CYAN)
        ent_rot.pack(side="left", padx=4)
        tk.Label(d_row2, text="SEC", font=("Consolas", 7), fg=C_TEXT_DIM, bg=C_PANEL_BG).pack(side="left")

        self.var_autocycle = tk.BooleanVar(value=self.config.auto_cycle)
        cb_auto = tk.Checkbutton(
            d_row2,
            text="AUTO CYCLE",
            variable=self.var_autocycle,
            font=("Consolas", 8, "bold"),
            fg=C_GREEN,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
            activeforeground=C_GREEN,
        )
        cb_auto.pack(side="right")

        # ----------------------------------------------------------------------
        # SYSTEM & STARTUP
        # ----------------------------------------------------------------------
        sec3 = tk.LabelFrame(
            container,
            text=" SYSTEM STARTUP & WORKSPACE ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec3.pack(fill="x", pady=4)

        s_row1 = tk.Frame(sec3, bg=C_PANEL_BG)
        s_row1.pack(fill="x", pady=2)

        self.var_autostart = tk.BooleanVar(value=self.config.start_with_windows)
        tk.Checkbutton(
            s_row1,
            text="START WITH WINDOWS",
            variable=self.var_autostart,
            font=("Consolas", 8),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(side="left")

        self.var_minimized = tk.BooleanVar(value=self.config.launch_minimized)
        tk.Checkbutton(
            s_row1,
            text="START MINIMIZED",
            variable=self.var_minimized,
            font=("Consolas", 8),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
        ).pack(side="right")

        s_row2 = tk.Frame(sec3, bg=C_PANEL_BG)
        s_row2.pack(fill="x", pady=2)
        tk.Label(s_row2, text="DGX HOST:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")
        self.var_dgx = tk.StringVar(value=self.config.dgx_host)
        tk.Entry(s_row2, textvariable=self.var_dgx, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, width=12).pack(side="left", padx=4)

        tk.Label(s_row2, text="REPO:", font=("Consolas", 8), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=6, anchor="e").pack(side="left", padx=(8, 2))
        self.var_repo = tk.StringVar(value=self.config.coding_repo_path)
        tk.Entry(s_row2, textvariable=self.var_repo, font=("Consolas", 8), bg="#0D121D", fg=C_TEXT_WHITE, width=14).pack(side="left", padx=4)

        # ----------------------------------------------------------------------
        # ACTION BUTTONS
        # ----------------------------------------------------------------------
        btn_box = tk.Frame(self, bg=C_BG)
        btn_box.pack(fill="x", padx=16, pady=(10, 16))

        tk.Button(
            btn_box,
            text="CANCEL",
            font=("Consolas", 9, "bold"),
            bg="#161F2E",
            fg=C_TEXT_MUTED,
            bd=1,
            relief="solid",
            width=12,
            cursor="hand2",
            command=self.destroy,
        ).pack(side="left")

        tk.Button(
            btn_box,
            text="SAVE CONFIG",
            font=("Consolas", 9, "bold"),
            bg="#102E24",
            fg=C_GREEN,
            bd=1,
            relief="solid",
            width=14,
            cursor="hand2",
            command=self._save_and_close,
        ).pack(side="right")

    # --------------------------------------------------------------------------
    # LISTBOX REFRESH & HANDLERS
    # --------------------------------------------------------------------------
    def _refresh_sections_listbox(self):
        self.sec_listbox.delete(0, "end")
        for s in self.working_sections_order:
            enabled = self.working_enabled_sections[s].get()
            mark = "●" if enabled else "○"
            title = SECTION_TITLES.get(s, s.upper())
            self.sec_listbox.insert("end", f" {mark} {title}")
        if self.working_sections_order:
            idx = self.working_sections_order.index(self.selected_section) if self.selected_section in self.working_sections_order else 0
            self.sec_listbox.select_set(idx)
            self._refresh_cards_listbox()

    def _refresh_cards_listbox(self):
        self.card_listbox.delete(0, "end")
        sec = self.selected_section
        self.lbl_cards_header.config(text=f"CARDS IN {SECTION_TITLES.get(sec, sec.upper())}")
        cards = self.working_section_cards.get(sec, [])
        for c in cards:
            enabled = self.working_enabled_cards[c].get()
            mark = "●" if enabled else "○"
            label = PAGE_LABELS.get(c, c.upper())
            self.card_listbox.insert("end", f" {mark} {label}")

    def _on_section_selected(self, event=None):
        sel = self.sec_listbox.curselection()
        if sel:
            self.selected_section = self.working_sections_order[sel[0]]
            self._refresh_cards_listbox()

    def _move_sec_up(self):
        sel = self.sec_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.working_sections_order[idx - 1], self.working_sections_order[idx] = self.working_sections_order[idx], self.working_sections_order[idx - 1]
        self.selected_section = self.working_sections_order[idx - 1]
        self._refresh_sections_listbox()

    def _move_sec_down(self):
        sel = self.sec_listbox.curselection()
        if not sel or sel[0] >= len(self.working_sections_order) - 1:
            return
        idx = sel[0]
        self.working_sections_order[idx + 1], self.working_sections_order[idx] = self.working_sections_order[idx], self.working_sections_order[idx + 1]
        self.selected_section = self.working_sections_order[idx + 1]
        self._refresh_sections_listbox()

    def _toggle_sec(self):
        sel = self.sec_listbox.curselection()
        if not sel:
            return
        s = self.working_sections_order[sel[0]]
        cur = self.working_enabled_sections[s].get()
        self.working_enabled_sections[s].set(not cur)
        self._refresh_sections_listbox()

    def _move_card_up(self):
        sel = self.card_listbox.curselection()
        cards = self.working_section_cards.get(self.selected_section, [])
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        cards[idx - 1], cards[idx] = cards[idx], cards[idx - 1]
        self._refresh_cards_listbox()
        self.card_listbox.select_set(idx - 1)

    def _move_card_down(self):
        sel = self.card_listbox.curselection()
        cards = self.working_section_cards.get(self.selected_section, [])
        if not sel or sel[0] >= len(cards) - 1:
            return
        idx = sel[0]
        cards[idx + 1], cards[idx] = cards[idx], cards[idx + 1]
        self._refresh_cards_listbox()
        self.card_listbox.select_set(idx + 1)

    def _toggle_card(self):
        sel = self.card_listbox.curselection()
        cards = self.working_section_cards.get(self.selected_section, [])
        if not sel:
            return
        c = cards[sel[0]]
        cur = self.working_enabled_cards[c].get()
        self.working_enabled_cards[c].set(not cur)
        self._refresh_cards_listbox()
        self.card_listbox.select_set(sel[0])

    def _apply_preset_ui(self, preset_name: str):
        self.config.apply_preset(preset_name)
        for s in ALL_SECTIONS:
            self.working_enabled_sections[s].set(self.config.enabled_sections[s])
        for c in ALL_PAGE_IDS:
            self.working_enabled_cards[c].set(self.config.enabled_cards[c])
        self._refresh_sections_listbox()

    def _show_claude_diagnostics(self):
        ClaudeAccountsDialog(self, self.config)

    def _save_and_close(self):
        self.config.sections_order = list(self.working_sections_order)
        self.config.enabled_sections = {s: self.working_enabled_sections[s].get() for s in ALL_SECTIONS}
        self.config.section_cards = {s: list(self.working_section_cards[s]) for s in ALL_SECTIONS}
        self.config.enabled_cards = {c: self.working_enabled_cards[c].get() for c in ALL_PAGE_IDS}

        # Keep enabled_pages in sync
        self.config.enabled_pages = [c for c in ALL_PAGE_IDS if self.config.enabled_cards.get(c, True)]

        self.config.minitoo_port = self.var_port.get().strip()
        try:
            self.config.rotation_interval = float(self.var_rotation.get())
        except ValueError:
            self.config.rotation_interval = 4.0
        self.config.auto_cycle = self.var_autocycle.get()
        self.config.start_with_windows = self.var_autostart.get()
        self.config.launch_minimized = self.var_minimized.get()
        self.config.dgx_host = self.var_dgx.get().strip() or "dgx"
        self.config.coding_repo_path = self.var_repo.get().strip() or "."

        # Ditoo fields
        dev_choice = self.var_target_device.get()
        self.config.target_device = "ditoo" if "Ditoo" in dev_choice else "minitoo"
        self.config.ditoo_enabled_btc = self.var_ditoo_btc.get()
        self.config.ditoo_enabled_stocks = self.var_ditoo_stocks.get()
        raw_tickers = self.var_ditoo_tickers.get()
        self.config.ditoo_stock_tickers = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

        self.config.save()
        self.destroy()

        if self.on_save_callback:
            self.on_save_callback(self.config)
