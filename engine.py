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
import asyncio
from typing import Optional, Dict, List, Callable, Any, Tuple
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
from src.devices.ditoo import DitooDevice, DEFAULT_DITOO_BLE_MAC
from src.renderers.ditoo_16 import Crypto16Renderer, Stock16Renderer, format_abbreviated_price, format_delta_pct
from collectors import MultiCryptoCollector
from market_provider import get_market_data_provider

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
                        cmd = f'"{sys.executable}" --minimized'
                    else:
                        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard_app.py"))
                        python_exe = sys.executable
                        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                        launcher = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
                        cmd = f'"{launcher}" "{script_path}" --minimized'
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
        
        # Ditoo 16x16 State
        self._ditoo_connected: bool = False
        self._ditoo_status_text: str = "DITOO ○ DISCONNECTED"
        self._ditoo_active_asset: str = "BTC"
        self._ditoo_active_frame_type: str = "LOGO"
        self._ditoo_active_frame: Optional[Image.Image] = None
        self._ditoo_last_market_update: float = 0.0

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
    def target_device(self) -> str:
        with self._lock:
            return self.config.target_device

    @target_device.setter
    def target_device(self, dev: str):
        changed = False
        with self._lock:
            if self.config.target_device != dev:
                self.config.target_device = dev
                changed = True
        if changed:
            self.config.save()
            self._notify("device_target_changed", dev)

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

    @property
    def ditoo_connected(self) -> bool:
        with self._lock:
            return self._ditoo_connected

    @property
    def ditoo_status_text(self) -> str:
        with self._lock:
            return self._ditoo_status_text

    @property
    def ditoo_active_asset(self) -> str:
        with self._lock:
            return self._ditoo_active_asset

    @property
    def ditoo_active_frame_type(self) -> str:
        with self._lock:
            return self._ditoo_active_frame_type

    @property
    def ditoo_active_frame(self) -> Optional[Image.Image]:
        with self._lock:
            return self._ditoo_active_frame

    @property
    def ditoo_last_market_update(self) -> float:
        with self._lock:
            return self._ditoo_last_market_update

    def set_ditoo_status(self, connected: bool, status_text: str):
        with self._lock:
            self._ditoo_connected = connected
            self._ditoo_status_text = status_text
        self._notify("ditoo_status_changed", (connected, status_text))

    def set_ditoo_frame(self, asset: str, frame_type: str, img: Image.Image, market_update_time: Optional[float] = None):
        with self._lock:
            self._ditoo_active_asset = asset
            self._ditoo_active_frame_type = frame_type
            self._ditoo_active_frame = img
            if market_update_time:
                self._ditoo_last_market_update = market_update_time
        self._notify("ditoo_frame_updated", (asset, frame_type, img))


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


# ==============================================================================
# 5. LONG-RUNNING DITOO CONTROLLER WITH BLE AUTO-RECOVERY & ASSET ROTATION
# ==============================================================================
class DitooController:
    """
    Manages long-running BLE connection and animation rotation for Divoom Ditoo 16x16:
    - Auto-detects and connects to DitooPro-Light over BLE (remembered MAC or scan).
    - Auto-reconnects with backoff if Ditoo is powered off or moves out of range.
    - Independent market data polling (crypto & stocks) with resilient caching.
    - Rotates through enabled Crypto coins and configured Stock tickers:
        1. Ticker / Logo (1s)
        2. USD Price (2s)
        3. 24h Change % with direction indicator (2s)
    - Updates DashboardState with the exact 16x16 pixel frame for sharp GUI live preview.
    - Pause / Resume, Next / Previous navigation, and Brightness control.
    """

    def __init__(self, state: DashboardState, config: Optional[DashboardConfig] = None):
        self.state = state
        self.config = config or state.config
        self.device = DitooDevice(ble_address=self.config.ditoo_mac)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Market data providers & caches
        self._crypto_collector = MultiCryptoCollector()
        self._market_provider = get_market_data_provider()
        self._crypto_data: Dict[str, Any] = {}
        self._stock_data: Dict[str, Any] = {}
        self._last_market_update_time: float = 0.0

        # Animation & rotation state
        self._asset_index: int = 0
        self._frame_step: int = 0  # 0: Logo, 1: Price, 2: Change
        self._step_start_time: float = time.time()
        self._force_push: bool = True
        self._last_brightness: int = self.config.ditoo_brightness
        self._last_sent_bytes: Optional[bytes] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="DitooController")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def update_config(self, config: DashboardConfig):
        mac_changed = (config.ditoo_mac != self.config.ditoo_mac)
        self.config = config
        self.device.ble_address = config.ditoo_mac
        if config.ditoo_brightness != self._last_brightness:
            self._force_push = True
        if mac_changed and self.device.is_connected:
            if self._loop:
                asyncio.run_coroutine_threadsafe(self.device.disconnect(), self._loop)

    def next_asset(self):
        """Advance to next asset immediately."""
        assets = self._get_active_assets()
        if assets:
            self._asset_index = (self._asset_index + 1) % len(assets)
        self._frame_step = 0
        self._step_start_time = time.time()
        self._force_push = True

    def prev_asset(self):
        """Go to previous asset immediately."""
        assets = self._get_active_assets()
        if assets:
            self._asset_index = (self._asset_index - 1) % len(assets)
        self._frame_step = 0
        self._step_start_time = time.time()
        self._force_push = True

    def toggle_pause(self):
        """Toggle pause state."""
        self.config.ditoo_is_paused = not self.config.ditoo_is_paused
        self.config.save()
        self._step_start_time = time.time()

    def set_brightness(self, val: int):
        """Set screen brightness (0-100)."""
        self.config.ditoo_brightness = max(0, min(100, int(val)))
        self.config.save()
        self._force_push = True

    def _get_active_assets(self) -> List[Tuple[str, str]]:
        assets: List[Tuple[str, str]] = []
        if self.config.ditoo_enabled_crypto_page:
            for c in self.config.ditoo_enabled_cryptos:
                assets.append(("crypto", c.upper()))
        if self.config.ditoo_enabled_stock_page:
            for s in self.config.ditoo_stock_tickers:
                assets.append(("stock", s.upper()))
        if not assets:
            assets.append(("crypto", "BTC"))
        return assets

    def _poll_market_data(self):
        """Fetch market data from existing providers without blanking on error."""
        # 1. Crypto
        try:
            c_assets = self._crypto_collector.get_all_assets()
            if c_assets:
                self._crypto_data.update(c_assets)
                self._last_market_update_time = time.time()
        except Exception as e:
            print(f"[DITOO DATA] Crypto poll error: {e}")

        # 2. Stocks
        try:
            tickers = self.config.ditoo_stock_tickers
            if tickers:
                s_quotes = self._market_provider.get_quotes_for_symbols(tickers)
                if s_quotes:
                    self._stock_data.update(s_quotes)
                    self._last_market_update_time = time.time()
        except Exception as e:
            print(f"[DITOO DATA] Stock poll error: {e}")

    def _render_current_frame(self, asset_type: str, symbol: str) -> Tuple[Image.Image, str, float]:
        """Render the 16x16 frame for current step and return (Image, frame_type, dwell_seconds)."""
        dwell = 2.0
        frame_type = "LOGO"

        if asset_type == "crypto":
            asset_obj = self._crypto_data.get(symbol.lower())
            price = asset_obj.price if asset_obj else 0.0
            change_pct = asset_obj.change_24h if asset_obj else 0.0

            if self._frame_step == 0:
                img = Crypto16Renderer.render_icon_frame(symbol)
                frame_type = "ICON"
                dwell = self.config.ditoo_frame_logo_dwell
            elif self._frame_step == 1:
                img = Crypto16Renderer.render_price_frame(symbol, price)
                frame_type = "PRICE"
                dwell = self.config.ditoo_frame_price_dwell
            else:
                img = Crypto16Renderer.render_change_frame(change_pct)
                frame_type = "CHANGE"
                dwell = self.config.ditoo_frame_change_dwell

        else:
            stock_obj = self._stock_data.get(symbol.upper())
            price = stock_obj.price if stock_obj else 0.0
            change_pct = stock_obj.change_pct if stock_obj else 0.0

            if self._frame_step == 0:
                img = Stock16Renderer.render_symbol_frame(symbol)
                frame_type = "TICKER"
                dwell = self.config.ditoo_frame_logo_dwell
            elif self._frame_step == 1:
                img = Stock16Renderer.render_price_frame(symbol, price)
                frame_type = "PRICE"
                dwell = self.config.ditoo_frame_price_dwell
            else:
                img = Stock16Renderer.render_change_frame(change_pct)
                frame_type = "CHANGE"
                dwell = self.config.ditoo_frame_change_dwell

        return img, frame_type, dwell

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main_async_loop())
        finally:
            self._loop.close()

    async def _main_async_loop(self):
        # Initial market data poll
        self._poll_market_data()

        # Run concurrent background tasks
        data_task = asyncio.create_task(self._market_data_loop())
        display_task = asyncio.create_task(self._display_loop())

        await asyncio.gather(data_task, display_task)

    async def _market_data_loop(self):
        """Independent market data refresh loop (every 35 seconds)."""
        while self._running:
            try:
                await asyncio.sleep(35.0)
                if not self._running:
                    break
                await asyncio.to_thread(self._poll_market_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DITOO DATA] Error in market data loop: {e}")
                await asyncio.sleep(5.0)

    async def _display_loop(self):
        """Main connection management, frame rotation, and hardware stream loop."""
        reconnect_delay = 3.0

        while self._running:
            # 1. Connection Phase
            if not self.device.is_connected:
                self.state.set_ditoo_status(False, "DITOO ○ RECONNECTING...")
                try:
                    ok = await self.device.connect_ble(timeout=6.0)
                    if ok:
                        self.state.set_ditoo_status(True, f"DITOO ● CONNECTED ({self.device.ble_address})")
                        # Sync brightness
                        await self.device.set_brightness(self.config.ditoo_brightness)
                        self._last_brightness = self.config.ditoo_brightness
                        self._force_push = True
                    else:
                        self.state.set_ditoo_status(False, "DITOO ○ RECONNECTING (3s)")
                        # Even if BLE is disconnected, generate preview frames
                        await self._advance_preview_frame()
                        await asyncio.sleep(reconnect_delay)
                        continue
                except Exception as ce:
                    print(f"[DITOO] Connection attempt error: {ce}")
                    self.state.set_ditoo_status(False, "DITOO ○ RECONNECTING (3s)")
                    await self._advance_preview_frame()
                    await asyncio.sleep(reconnect_delay)
                    continue

            # 2. Operational Connected Loop
            try:
                active_assets = self._get_active_assets()
                if not active_assets:
                    await asyncio.sleep(0.5)
                    continue

                if self._asset_index >= len(active_assets):
                    self._asset_index = 0

                asset_type, symbol = active_assets[self._asset_index]
                now = time.time()

                # Render current frame
                img, frame_type, dwell = self._render_current_frame(asset_type, symbol)
                frame_bytes = img.tobytes()

                # Push to hardware if changed or forced
                if self._force_push or frame_bytes != self._last_sent_bytes:
                    sent_ok = await self.device.show_frame(img)
                    if sent_ok:
                        self._last_sent_bytes = frame_bytes
                        self._force_push = False
                        # Update state for Desktop GUI Live Preview
                        self.state.set_ditoo_frame(symbol, frame_type, img, self._last_market_update_time)
                    else:
                        raise RuntimeError("BLE frame transmission failed")

                # Handle brightness change
                if self.config.ditoo_brightness != self._last_brightness:
                    await self.device.set_brightness(self.config.ditoo_brightness)
                    self._last_brightness = self.config.ditoo_brightness

                # Check dwell timer for step progression
                if not self.config.ditoo_is_paused and self.config.ditoo_auto_rotation:
                    if now - self._step_start_time >= dwell:
                        self._frame_step = (self._frame_step + 1) % 3
                        self._step_start_time = now
                        if self._frame_step == 0:
                            # Advance to next asset
                            self._asset_index = (self._asset_index + 1) % len(active_assets)
                        self._force_push = True

                await asyncio.sleep(0.08)

            except Exception as e:
                print(f"[DITOO] Disconnection or transmission failure: {e}")
                await self.device.disconnect()
                self.state.set_ditoo_status(False, "DITOO ○ DISCONNECTED")
                await asyncio.sleep(1.0)

    async def _advance_preview_frame(self):
        """Keep GUI preview animated even when physical device is offline."""
        try:
            active_assets = self._get_active_assets()
            if not active_assets:
                return
            if self._asset_index >= len(active_assets):
                self._asset_index = 0
            asset_type, symbol = active_assets[self._asset_index]
            now = time.time()
            img, frame_type, dwell = self._render_current_frame(asset_type, symbol)
            self.state.set_ditoo_frame(symbol, frame_type, img, self._last_market_update_time)
            if not self.config.ditoo_is_paused and self.config.ditoo_auto_rotation:
                if now - self._step_start_time >= dwell:
                    self._frame_step = (self._frame_step + 1) % 3
                    self._step_start_time = now
                    if self._frame_step == 0:
                        self._asset_index = (self._asset_index + 1) % len(active_assets)
        except Exception:
            pass
