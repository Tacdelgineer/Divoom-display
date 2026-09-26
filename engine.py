#!/usr/bin/env python3
"""
Shared Data Engine & MiniToo Controller for AI Desk Dashboard.
Coordinates:
1. DashboardState - Thread-safe state container holding PageData for all 9 cards.
2. DataEngine - Background collector scheduler honoring per-source refresh rates.
3. MiniTooController - Long-running Bluetooth SPP link with exponential auto-reconnect,
   frame change detection, and physical knob/button navigation.
4. WindowsAutostart - Clean Windows Registry autostart management.
"""
from __future__ import annotations

import io
import os
import sys
import time
import winreg
import threading
from typing import Optional, Dict, List, Callable, Any
from PIL import Image

try:
    import serial
except ImportError:
    serial = None

from models import PageData, MetricItem
from dashboard import collect_page, PAGE_KEYS
from renderer import render_dashboard_page
from backends import MiniTooDisplay, get_display_backend
from inputs import MiniTooInputAdapter, InputEvent
from config import DashboardConfig, ALL_PAGE_IDS
from detector import detect_minitoo_port

# Standard 3x3 Card Grid Order
PAGE_ORDER = list(ALL_PAGE_IDS)

# Per-source suggested refresh intervals (seconds)
REFRESH_INTERVALS = {
    "local_pc": 2.0,
    "ai_activity": 2.0,
    "dgx_spark": 3.0,
    "services": 10.0,
    "coding": 10.0,
    "btc": 30.0,
    "codex": 30.0,
    "gemini": 30.0,
    "claude": 30.0,
}


# ==============================================================================
# 1. WINDOWS AUTOSTART HELPER
# ==============================================================================
class WindowsAutostart:
    """Manages Windows startup via HKCU Run registry key."""

    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "AiDeskDashboard"

    @classmethod
    def is_enabled(cls) -> bool:
        if sys.platform != "win32":
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, cls.APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    @classmethod
    def set_enabled(cls, enable: bool) -> bool:
        if sys.platform != "win32":
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_SET_VALUE)
            try:
                if enable:
                    # Check if running as packaged executable
                    if getattr(sys, "frozen", False):
                        cmd = f'"{sys.executable}"'
                    else:
                        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard_app.py"))
                        python_exe = sys.executable
                        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                        launcher = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
                        cmd = f'"{launcher}" "{script_path}"'
                    winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, cls.APP_NAME)
                    except FileNotFoundError:
                        pass
                return True
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"[AUTOSTART] Error updating registry: {e}")
            return False


# ==============================================================================
# 2. THREAD-SAFE DASHBOARD STATE CONTAINER
# ==============================================================================
class DashboardState:
    """
    Unified state container shared between Desktop UI and MiniToo hardware.
    Maintains normalized PageData for all cards and active display routing.
    """

    def __init__(self, config: Optional[DashboardConfig] = None, initial_page: Optional[str] = None):
        self._lock = threading.RLock()
        self.config = config or DashboardConfig.load()
        init_p = initial_page or self.config.last_selected_page
        if init_p not in ALL_PAGE_IDS:
            init_p = "btc"
        self._pages: Dict[str, PageData] = {}
        self._minitoo_active_page: str = init_p
        self._minitoo_connected: bool = False
        self._minitoo_status_text: str = "MINITOO ○ CONNECTING..."
        self._last_update_time: float = 0.0
        self._listeners: List[Callable[[str, Any], None]] = []

    def add_listener(self, callback: Callable[[str, Any], None]):
        with self._lock:
            self._listeners.append(callback)

    def _notify(self, event_type: str, data: Any = None):
        for cb in list(self._listeners):
            try:
                cb(event_type, data)
            except Exception as e:
                print(f"[STATE] Error in listener callback: {e}")

    def update_page(self, page_id: str, data: PageData):
        with self._lock:
            self._pages[page_id] = data
            self._last_update_time = time.time()
        self._notify("page_updated", page_id)

    def get_page(self, page_id: str) -> Optional[PageData]:
        with self._lock:
            return self._pages.get(page_id)

    def get_all_pages(self) -> Dict[str, PageData]:
        with self._lock:
            return dict(self._pages)

    @property
    def minitoo_active_page(self) -> str:
        with self._lock:
            return self._minitoo_active_page

    @minitoo_active_page.setter
    def minitoo_active_page(self, page_id: str):
        changed = False
        with self._lock:
            if self._minitoo_active_page != page_id:
                self._minitoo_active_page = page_id
                self.config.last_selected_page = page_id
                changed = True
        if changed:
            self.config.save()
            self._notify("minitoo_page_changed", page_id)

    @property
    def minitoo_connected(self) -> bool:
        with self._lock:
            return self._minitoo_connected

    @property
    def minitoo_status_text(self) -> str:
        with self._lock:
            return self._minitoo_status_text

    def set_minitoo_status(self, connected: bool, status_text: str):
        with self._lock:
            self._minitoo_connected = connected
            self._minitoo_status_text = status_text
        self._notify("minitoo_status_changed", (connected, status_text))


# ==============================================================================
# 3. BACKGROUND DATA COLLECTOR SCHEDULER
# ==============================================================================
class DataEngine:
    """
    Background worker that schedules collectors at their respective refresh rates
    and updates DashboardState without blocking the UI.
    """

    def __init__(self, state: DashboardState, config: Optional[DashboardConfig] = None):
        self.state = state
        self.config = config or state.config
        self.repo_path = self.config.coding_repo_path
        self.dgx_host = self.config.dgx_host
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_collected: Dict[str, float] = {}

    def update_config(self, config: DashboardConfig):
        self.config = config
        self.repo_path = config.coding_repo_path
        self.dgx_host = config.dgx_host

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="DataEngine")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _collect_one(self, page_id: str):
        try:
            data = collect_page(page_id, repo_path=self.repo_path, dgx_host=self.dgx_host)
            self.state.update_page(page_id, data)
        except Exception as e:
            # Component fails independently
            print(f"[DATA] Error collecting '{page_id}': {e}", file=sys.stderr)

    def _run(self):
        # Initial collection for all pages in order
        for p_id in list(self.config.page_order):
            if not self._running:
                return
            self._collect_one(p_id)
            self._last_collected[p_id] = time.time()
            time.sleep(0.05)

        # Continuous refresh loop
        while self._running:
            now = time.time()
            for p_id in list(self.config.page_order):
                if not self._running:
                    break
                interval = REFRESH_INTERVALS.get(p_id, 10.0)
                last = self._last_collected.get(p_id, 0.0)
                if now - last >= interval:
                    self._collect_one(p_id)
                    self._last_collected[p_id] = time.time()
            time.sleep(0.2)


# ==============================================================================
# 4. LONG-RUNNING MINITOO CONTROLLER WITH RECOVERY
# ==============================================================================
class MiniTooController:
    """
    Manages long-running connection to Divoom MiniToo:
    - Auto-detection and auto-recovery on disconnect with exponential backoff (1s, 2s, 5s, 10s max).
    - Ensures device remains in proven Custom/DIY Channel 5.
    - Physical volume knob / button polling at ~16 Hz (NEXT/PREV navigation).
    - Auto-cycle through enabled pages with configurable rotation interval.
    - Caches transmitted frame to eliminate redundant Bluetooth transfers.
    - Responds immediately to desktop card clicks.
    """

    BACKOFF_STEPS = [1.0, 2.0, 5.0, 10.0]

    def __init__(self, state: DashboardState, config: Optional[DashboardConfig] = None):
        self.state = state
        self.config = config or state.config
        self.port: Optional[str] = None
        self.display = MiniTooDisplay(port=None)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._force_push = False
        self._adapter: Optional[MiniTooInputAdapter] = None
        self._last_sent_bytes: Optional[bytes] = None
        self._last_cycle_time: float = time.time()
        self._last_user_interaction: float = time.time()

    def update_config(self, config: DashboardConfig):
        port_changed = (config.minitoo_port != self.config.minitoo_port)
        self.config = config
        active_pages = self.config.get_active_pages()
        if self.state.minitoo_active_page not in active_pages:
            self.push_page(active_pages[0])
        else:
            self._force_push = True

        if port_changed and self._adapter:
            try:
                self._adapter.close()
            except Exception:
                pass
            self._adapter = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="MiniTooController")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._adapter:
            try:
                self._adapter.close()
            except Exception:
                pass
            self._adapter = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def push_page(self, page_id: str):
        """Immediately switch MiniToo to a requested page (e.g. from Desktop Card click)."""
        self.state.minitoo_active_page = page_id
        self._last_user_interaction = time.time()
        self._force_push = True

    def _render_active_frame(self) -> Optional[Image.Image]:
        p_id = self.state.minitoo_active_page
        data = self.state.get_page(p_id)
        if not data:
            try:
                data = collect_page(p_id, repo_path=self.config.coding_repo_path, dgx_host=self.config.dgx_host)
                self.state.update_page(p_id, data)
            except Exception:
                return None
        active_pages = self.config.get_active_pages()
        idx = active_pages.index(p_id) + 1 if p_id in active_pages else 1
        return render_dashboard_page(data, page_num=idx, total_pages=len(active_pages))

    def _run(self):
        backoff_idx = 0

        while self._running:
            # 1. Port Detection & Resolution
            target_port = detect_minitoo_port(self.config.minitoo_port)
            if not target_port:
                self.state.set_minitoo_status(False, "MINITOO ○ NOT FOUND")
                t_end = time.time() + 2.5
                while self._running and time.time() < t_end:
                    time.sleep(0.1)
                continue

            self.port = target_port
            self.display.port = target_port

            # 2. Connection Phase
            self.state.set_minitoo_status(False, f"MINITOO ○ CONNECTING ({self.port})...")
            try:
                self._adapter = MiniTooInputAdapter(port=self.port)
            except Exception as e:
                self._adapter = None

            if not self._adapter or not self._adapter.ser or not self._adapter.ser.is_open:
                delay = self.BACKOFF_STEPS[min(backoff_idx, len(self.BACKOFF_STEPS) - 1)]
                self.state.set_minitoo_status(False, f"MINITOO ○ RECONNECTING ({int(delay)}s)")
                backoff_idx += 1
                t_end = time.time() + delay
                while self._running and time.time() < t_end:
                    time.sleep(0.1)
                continue

            # Connection Succeeded!
            backoff_idx = 0
            self.state.set_minitoo_status(True, f"MINITOO ● CONNECTED ({self.port})")
            self._last_sent_bytes = None
            self._force_push = True

            # Ensure device is explicitly in Channel 5 (Custom/DIY)
            if self._adapter:
                self._adapter.set_channel(5)

            # Ensure last selected page is pushed
            active_pages = self.config.get_active_pages()
            if self.config.last_selected_page in active_pages:
                self.state.minitoo_active_page = self.config.last_selected_page
            elif active_pages:
                self.state.minitoo_active_page = active_pages[0]

            # 3. Connected Operational Loop
            last_heartbeat = time.time()
            last_channel_check = time.time()
            self._last_cycle_time = time.time()

            try:
                while self._running:
                    now = time.time()
                    active_pages = self.config.get_active_pages()

                    # 15s display keep-alive heartbeat
                    if now - last_heartbeat >= 15.0:
                        self._force_push = True
                        last_heartbeat = now

                    # 8s display channel drift check (re-enter channel 5 if firmware drifted to clock)
                    if now - last_channel_check >= 8.0:
                        last_channel_check = now
                        ch = self._adapter.query_channel()
                        if ch is not None and ch != 5:
                            print(f"[MINITOO] Channel drift detected (current: {ch}). Re-entering Custom/DIY Channel 5...")
                            self._adapter.set_channel(5)
                            self._force_push = True

                    # Auto-cycle check
                    if self.config.auto_cycle and len(active_pages) > 1:
                        if now - self._last_cycle_time >= self.config.rotation_interval and now - self._last_user_interaction >= 8.0:
                            cur_p = self.state.minitoo_active_page
                            cur_idx = active_pages.index(cur_p) if cur_p in active_pages else 0
                            next_p = active_pages[(cur_idx + 1) % len(active_pages)]
                            self.state.minitoo_active_page = next_p
                            self._last_cycle_time = now
                            self._force_push = True

                    # Check physical controls (Knob / Volume buttons)
                    event = self._adapter.poll_event()
                    if event == InputEvent.NEXT_PAGE:
                        cur_p = self.state.minitoo_active_page
                        cur_idx = active_pages.index(cur_p) if cur_p in active_pages else 0
                        next_p = active_pages[(cur_idx + 1) % len(active_pages)]
                        print(f"[MINITOO] Hardware NEXT -> {next_p.upper()}")
                        self.state.minitoo_active_page = next_p
                        self._last_user_interaction = now
                        self._force_push = True

                    elif event == InputEvent.PREV_PAGE:
                        cur_p = self.state.minitoo_active_page
                        cur_idx = active_pages.index(cur_p) if cur_p in active_pages else 0
                        prev_p = active_pages[(cur_idx - 1) % len(active_pages)]
                        print(f"[MINITOO] Hardware PREV -> {prev_p.upper()}")
                        self.state.minitoo_active_page = prev_p
                        self._last_user_interaction = now
                        self._force_push = True

                    # Render and transmit frame if needed
                    img = self._render_active_frame()
                    if img:
                        # Fast comparison to avoid redundant Bluetooth streaming
                        frame_bytes = img.tobytes()
                        if self._force_push or frame_bytes != self._last_sent_bytes:
                            # Stream frame to device (ser maintained open)
                            ok = self.display.show(img, ser=self._adapter.ser)
                            if ok:
                                self._last_sent_bytes = frame_bytes
                                self._force_push = False
                                print(f"[MINITOO] Frame updated -> {self.state.minitoo_active_page.upper()}", flush=True)
                            else:
                                raise serial.SerialException("Display stream failed")

                    time.sleep(0.06)  # ~16 Hz poll cadence

            except Exception as e:
                print(f"[MINITOO] Disconnect detected: {e}")
                if self._adapter:
                    try:
                        self._adapter.close()
                    except Exception:
                        pass
                    self._adapter = None

                self.state.set_minitoo_status(False, "MINITOO ○ DISCONNECTED")
                time.sleep(0.5)
