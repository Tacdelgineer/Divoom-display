#!/usr/bin/env python3
"""
UI Components for AI Desk Dashboard:
1. FirstRunDialog - Initial setup & system service detection screen.
2. SettingsDialog - Lightweight modal for page ordering, port selection,
   rotation interval, auto-cycle, DGX host, and system startup.
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

from config import DashboardConfig, ALL_PAGE_IDS, PAGE_LABELS
from detector import detect_minitoo_port, get_all_com_ports
from subproc import check_output_hidden, run_hidden

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
        self.geometry("440x480")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 440) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 480) // 2
        self.geometry(f"+{max(40, px)}+{max(40, py)}")

        self.status_labels: Dict[str, tk.Label] = {}
        self._build_ui()
        self._run_probes()

    def _build_ui(self):
        # Header
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

        # Status Table Container
        tbl = tk.Frame(self, bg=C_PANEL_BG, highlightbackground=C_BORDER, highlightthickness=1)
        tbl.pack(fill="both", expand=True, padx=20, pady=10)

        rows = [
            ("minitoo", "MiniToo"),
            ("codex", "Codex"),
            ("gemini", "Gemini"),
            ("claude", "Claude"),
            ("gpu", "Local GPU"),
            ("dgx", "DGX Spark"),
            ("btc", "BTC"),
        ]

        for idx, (key, title) in enumerate(rows):
            rf = tk.Frame(tbl, bg=C_PANEL_BG)
            rf.pack(fill="x", padx=16, pady=8)

            tk.Label(
                rf,
                text=title,
                font=("Consolas", 10, "bold"),
                fg=C_TEXT_WHITE,
                bg=C_PANEL_BG,
                width=14,
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

        # Bottom Action Bar
        btn_frame = tk.Frame(self, bg=C_BG)
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.btn_open = tk.Button(
            btn_frame,
            text="[ OPEN DASHBOARD ]",
            font=("Consolas", 11, "bold"),
            bg="#0E2419",
            fg=C_GREEN,
            activebackground=C_GREEN,
            activeforeground="#000000",
            highlightbackground="#1E4733",
            bd=1,
            relief="solid",
            cursor="hand2",
            pady=8,
            command=self._on_confirm,
        )
        self.btn_open.pack(fill="x")

    def _run_probes(self):
        """Run non-blocking background probes for all services."""
        def probe_worker():
            # 1. MiniToo
            mt = detect_minitoo_port(self.config.minitoo_port)
            mt_text = f"CONNECTED ({mt})" if mt else "NOT FOUND"
            mt_color = C_GREEN if mt else C_AMBER
            self._update_status("minitoo", mt_text, mt_color)

            # 2. Codex
            cx = shutil.which("codex") is not None or os.path.exists(os.path.expanduser("~/.codex"))
            self._update_status("codex", "READY" if cx else "NOT FOUND", C_GREEN if cx else C_TEXT_DIM)

            # 3. Gemini
            gm = shutil.which("agy") is not None or shutil.which("gemini") is not None
            self._update_status("gemini", "READY" if gm else "NOT FOUND", C_GREEN if gm else C_TEXT_DIM)

            # 4. Claude
            self._update_status("claude", "READY / QUOTA N/A", C_CORAL)

            # 5. Local GPU
            gpu_str = "N/A"
            try:
                smi = check_output_hidden(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    text=True,
                    timeout=2.0
                ).strip()
                if smi:
                    gpu_str = smi.splitlines()[0][:20]
            except Exception:
                gpu_str = "ACTIVE / N/A"
            self._update_status("gpu", gpu_str, C_CYAN)

            # 6. DGX Spark
            dgx_on = False
            try:
                res = run_hidden(
                    ["ssh", "-o", "ConnectTimeout=1", "-o", "BatchMode=yes", self.config.dgx_host, "echo 1"],
                    capture_output=True,
                    timeout=1.5
                )
                dgx_on = (res.returncode == 0)
            except Exception:
                pass
            self._update_status("dgx", "ONLINE" if dgx_on else "OFFLINE", C_GREEN if dgx_on else C_AMBER)

            # 7. BTC
            self._update_status("btc", "READY", C_GOLD)

        threading.Thread(target=probe_worker, daemon=True).start()

    def _update_status(self, key: str, text: str, color: str):
        def apply():
            lbl = self.status_labels.get(key)
            if lbl and lbl.winfo_exists():
                lbl.config(text=text, fg=color)
        self.after(0, apply)

    def _on_confirm(self):
        self.config.first_run_completed = True
        self.config.save()
        self.destroy()
        if self.on_open_dashboard:
            self.on_open_dashboard()


# ==============================================================================
# 2. COMPACT RETRO SETTINGS DIALOG
# ==============================================================================
class SettingsDialog(tk.Toplevel):
    """
    Compact settings window allowing user to:
    - Enable/disable pages with checkboxes
    - Reorder pages using Up / Down buttons
    - Select MiniToo port (Auto-detect or COM ports)
    - Configure rotation interval & toggle auto-cycle
    - Toggle Start with Windows and Launch Minimized
    - Configure DGX host and coding repo path
    """

    def __init__(self, parent: tk.Tk, config: DashboardConfig, on_save_callback: Callable[[DashboardConfig], None]):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.on_save_callback = on_save_callback

        self.title("AI Desk Dashboard — Settings")
        self.geometry("490x600")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 490) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{max(40, px)}+{max(30, py)}")

        # Working state copies
        self.working_page_order = list(self.config.page_order)
        self.working_enabled: Dict[str, tk.BooleanVar] = {}
        for p in ALL_PAGE_IDS:
            self.working_enabled[p] = tk.BooleanVar(value=(p in self.config.enabled_pages))

        self.selected_page_idx: Optional[int] = None
        self._build_ui()

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=C_BG)
        h_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            h_frame,
            text="DASHBOARD SETTINGS",
            font=("Consolas", 12, "bold"),
            fg=C_CYAN,
            bg=C_BG,
        ).pack(side="left")

        btn_status = tk.Button(
            h_frame,
            text="[ SYSTEM HEALTH ]",
            font=("Consolas", 8, "bold"),
            bg="#141E2F",
            fg=C_CYAN,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._show_system_health,
        )
        btn_status.pack(side="right")

        # Scrollable / sectioned content
        container = tk.Frame(self, bg=C_BG)
        container.pack(fill="both", expand=True, padx=16)

        # ----------------------------------------------------------------------
        # SECTION 1: PAGES & REORDERING
        # ----------------------------------------------------------------------
        sec1 = tk.LabelFrame(
            container,
            text=" PAGES & DISPLAY ORDER ",
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

        p_row = tk.Frame(sec1, bg=C_PANEL_BG)
        p_row.pack(fill="x")

        # Page Listbox container
        self.listbox = tk.Listbox(
            p_row,
            font=("Consolas", 9),
            bg="#0D121D",
            fg=C_TEXT_WHITE,
            selectbackground=C_CYAN,
            selectforeground="#000000",
            highlightthickness=1,
            highlightbackground=C_BORDER,
            height=6,
            activestyle="none",
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        # Up / Down Reorder Buttons
        reorder_btn_box = tk.Frame(p_row, bg=C_PANEL_BG)
        reorder_btn_box.pack(side="right", padx=(8, 0))

        btn_up = tk.Button(
            reorder_btn_box,
            text="▲ UP",
            font=("Consolas", 8, "bold"),
            bg="#161F2E",
            fg=C_TEXT_WHITE,
            bd=1,
            relief="solid",
            width=8,
            cursor="hand2",
            command=self._move_up,
        )
        btn_up.pack(pady=3)

        btn_down = tk.Button(
            reorder_btn_box,
            text="▼ DOWN",
            font=("Consolas", 8, "bold"),
            bg="#161F2E",
            fg=C_TEXT_WHITE,
            bd=1,
            relief="solid",
            width=8,
            cursor="hand2",
            command=self._move_down,
        )
        btn_down.pack(pady=3)

        btn_toggle = tk.Button(
            reorder_btn_box,
            text="TOGGLE",
            font=("Consolas", 8, "bold"),
            bg="#161F2E",
            fg=C_AMBER,
            bd=1,
            relief="solid",
            width=8,
            cursor="hand2",
            command=self._toggle_selected,
        )
        btn_toggle.pack(pady=3)

        self._refresh_page_listbox()

        # ----------------------------------------------------------------------
        # SECTION 2: DEVICE & ROTATION
        # ----------------------------------------------------------------------
        sec2 = tk.LabelFrame(
            container,
            text=" MINITOO DEVICE & ROTATION ",
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

        d_row1 = tk.Frame(sec2, bg=C_PANEL_BG)
        d_row1.pack(fill="x", pady=2)

        tk.Label(d_row1, text="PORT:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")

        # Discover ports for dropdown
        available_ports = ["AUTO"] + [p["device"] for p in get_all_com_ports()]
        if self.config.minitoo_port not in available_ports:
            available_ports.append(self.config.minitoo_port)

        self.var_port = tk.StringVar(value=self.config.minitoo_port)
        om_port = tk.OptionMenu(d_row1, self.var_port, *available_ports)
        om_port.config(bg="#0D121D", fg=C_CYAN, font=("Consolas", 8, "bold"), highlightthickness=1, highlightbackground=C_BORDER)
        om_port["menu"].config(bg="#0D121D", fg=C_TEXT_WHITE, font=("Consolas", 8))
        om_port.pack(side="left", padx=4)

        d_row2 = tk.Frame(sec2, bg=C_PANEL_BG)
        d_row2.pack(fill="x", pady=4)

        tk.Label(d_row2, text="ROTATION:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=10, anchor="w").pack(side="left")

        self.var_rotation = tk.StringVar(value=str(int(self.config.rotation_interval)))
        ent_rot = tk.Entry(d_row2, textvariable=self.var_rotation, width=6, font=("Consolas", 9), bg="#0D121D", fg=C_TEXT_WHITE, insertbackground=C_CYAN)
        ent_rot.pack(side="left", padx=4)

        tk.Label(d_row2, text="SEC", font=("Consolas", 8), fg=C_TEXT_DIM, bg=C_PANEL_BG).pack(side="left", padx=2)

        self.var_autocycle = tk.BooleanVar(value=self.config.auto_cycle)
        cb_auto = tk.Checkbutton(
            d_row2,
            text="AUTO CYCLE PAGES",
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
        # SECTION 3: SYSTEM
        # ----------------------------------------------------------------------
        sec3 = tk.LabelFrame(
            container,
            text=" SYSTEM STARTUP ",
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

        s_row = tk.Frame(sec3, bg=C_PANEL_BG)
        s_row.pack(fill="x")

        self.var_autostart = tk.BooleanVar(value=self.config.start_with_windows)
        cb_start = tk.Checkbutton(
            s_row,
            text="START WITH WINDOWS",
            variable=self.var_autostart,
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
            activeforeground=C_TEXT_WHITE,
        )
        cb_start.pack(side="left")

        self.var_minimized = tk.BooleanVar(value=self.config.launch_minimized)
        cb_min = tk.Checkbutton(
            s_row,
            text="LAUNCH MINIMIZED",
            variable=self.var_minimized,
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_WHITE,
            bg=C_PANEL_BG,
            selectcolor="#0D121D",
            activebackground=C_PANEL_BG,
            activeforeground=C_TEXT_WHITE,
        )
        cb_min.pack(side="right")

        # ----------------------------------------------------------------------
        # SECTION 4: INTEGRATIONS (DGX & REPO)
        # ----------------------------------------------------------------------
        sec4 = tk.LabelFrame(
            container,
            text=" HOST & WORKSPACE ",
            font=("Consolas", 8, "bold"),
            fg=C_TEXT_MUTED,
            bg=C_PANEL_BG,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=6,
        )
        sec4.pack(fill="x", pady=6)

        i_row1 = tk.Frame(sec4, bg=C_PANEL_BG)
        i_row1.pack(fill="x", pady=2)
        tk.Label(i_row1, text="DGX HOST:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=12, anchor="w").pack(side="left")
        self.var_dgx = tk.StringVar(value=self.config.dgx_host)
        ent_dgx = tk.Entry(i_row1, textvariable=self.var_dgx, font=("Consolas", 9), bg="#0D121D", fg=C_TEXT_WHITE, insertbackground=C_CYAN)
        ent_dgx.pack(side="left", fill="x", expand=True)

        i_row2 = tk.Frame(sec4, bg=C_PANEL_BG)
        i_row2.pack(fill="x", pady=2)
        tk.Label(i_row2, text="CODING REPO:", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_PANEL_BG, width=12, anchor="w").pack(side="left")
        self.var_repo = tk.StringVar(value=self.config.coding_repo_path)
        ent_repo = tk.Entry(i_row2, textvariable=self.var_repo, font=("Consolas", 9), bg="#0D121D", fg=C_TEXT_WHITE, insertbackground=C_CYAN)
        ent_repo.pack(side="left", fill="x", expand=True)

        # ----------------------------------------------------------------------
        # BOTTOM BUTTONS
        # ----------------------------------------------------------------------
        b_frame = tk.Frame(self, bg=C_BG)
        b_frame.pack(fill="x", padx=16, pady=14)

        btn_save = tk.Button(
            b_frame,
            text="[ SAVE SETTINGS ]",
            font=("Consolas", 10, "bold"),
            bg="#0E2419",
            fg=C_GREEN,
            activebackground=C_GREEN,
            activeforeground="#000000",
            highlightbackground="#1E4733",
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._save_and_close,
        )
        btn_save.pack(side="left")

        btn_cancel = tk.Button(
            b_frame,
            text="[ CANCEL ]",
            font=("Consolas", 10),
            bg="#161B26",
            fg=C_TEXT_MUTED,
            activebackground="#202838",
            activeforeground=C_TEXT_WHITE,
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.destroy,
        )
        btn_cancel.pack(side="right")

    def _refresh_page_listbox(self):
        cur_sel = self.listbox.curselection()
        self.listbox.delete(0, tk.END)
        for idx, p_id in enumerate(self.working_page_order):
            is_enabled = self.working_enabled[p_id].get()
            mark = "[X]" if is_enabled else "[ ]"
            name = PAGE_LABELS.get(p_id, p_id.upper())
            self.listbox.insert(tk.END, f" {mark}  {name}")
            if not is_enabled:
                self.listbox.itemconfig(idx, fg=C_TEXT_DIM)
            else:
                self.listbox.itemconfig(idx, fg=C_TEXT_WHITE)

        if cur_sel:
            self.listbox.select_set(cur_sel[0])

    def _on_list_select(self, event):
        sel = self.listbox.curselection()
        if sel:
            self.selected_page_idx = sel[0]

    def _move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.working_page_order[idx - 1], self.working_page_order[idx] = (
            self.working_page_order[idx],
            self.working_page_order[idx - 1],
        )
        self._refresh_page_listbox()
        self.listbox.select_set(idx - 1)
        self.selected_page_idx = idx - 1

    def _move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.working_page_order) - 1:
            return
        idx = sel[0]
        self.working_page_order[idx + 1], self.working_page_order[idx] = (
            self.working_page_order[idx],
            self.working_page_order[idx + 1],
        )
        self._refresh_page_listbox()
        self.listbox.select_set(idx + 1)
        self.selected_page_idx = idx + 1

    def _toggle_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        p_id = self.working_page_order[idx]
        cur_val = self.working_enabled[p_id].get()
        self.working_enabled[p_id].set(not cur_val)
        self._refresh_page_listbox()

    def _show_system_health(self):
        FirstRunDialog(self, self.config, on_open_dashboard=lambda: None)

    def _save_and_close(self):
        # Update config fields
        self.config.page_order = list(self.working_page_order)
        self.config.enabled_pages = [
            p for p in self.working_page_order if self.working_enabled[p].get()
        ]
        if not self.config.enabled_pages:
            self.config.enabled_pages = ["btc"]

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

        self.config.save()
        self.destroy()

        if self.on_save_callback:
            self.on_save_callback(self.config)
