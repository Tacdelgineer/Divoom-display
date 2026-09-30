#!/usr/bin/env python3
"""
Centralized UI Scale and High-DPI Management System for AI Desk Dashboard.
Provides:
- Per-Monitor-V2 DPI awareness initialization for Windows.
- System DPI discovery and fallback logic.
- Configurable scale settings: AUTO, 100%, 125%, 150%, 175%, 200%.
- Shared design tokens and font scaling helpers.
"""
from __future__ import annotations

import sys
import os
from typing import Tuple, List

UI_SCALE_OPTIONS: List[str] = ["AUTO", "100%", "125%", "150%", "175%", "200%"]

_DPI_INITIALIZED = False


def enable_high_dpi_awareness() -> bool:
    """
    Enable High-DPI awareness on Windows before creating the Tk GUI root.
    Prefers Per-Monitor-V2 awareness (Windows 10 1703+), falling back to
    Per-Monitor-V1 (Windows 8.1+) or System-DPI (Windows Vista+).
    Safe no-op on non-Windows platforms.
    """
    global _DPI_INITIALIZED
    if _DPI_INITIALIZED or sys.platform != "win32":
        return True

    _DPI_INITIALIZED = True
    try:
        import ctypes
        # 1. Try Per-Monitor-V2 DPI Awareness (DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4)
        try:
            res = ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            if res:
                return True
        except Exception:
            pass

        # 2. Try Per-Monitor-V1 via shcore.dll (PROCESS_PER_MONITOR_DPI_AWARE = 2)
        try:
            res = ctypes.windll.shcore.SetProcessDpiAwareness(2)
            if res == 0:
                return True
        except Exception:
            pass

        # 3. Fallback to System DPI awareness (Vista+)
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            return True
        except Exception:
            pass
    except Exception:
        pass
    return False


def get_system_dpi_scale() -> float:
    """
    Query the operating system's current display scaling ratio.
    Returns 1.0 for 96 DPI (100%), 1.25 for 120 DPI (125%), 1.5 for 144 DPI (150%), etc.
    """
    if sys.platform != "win32":
        return 1.0

    try:
        import ctypes
        # Windows 10 1607+ GetDpiForSystem
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
            if dpi and dpi > 0:
                return round(dpi / 96.0, 2)
        except Exception:
            pass

        # GDI DC fallback
        try:
            hdc = ctypes.windll.user32.GetDC(0)
            if hdc:
                LOGPIXELSX = 88
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                if dpi and dpi > 0:
                    return round(dpi / 96.0, 2)
        except Exception:
            pass
    except Exception:
        pass
    return 1.0


class UiScale:
    """
    Centralized design token and scaling engine for desktop rendering.
    Calculates pixel metrics, typography, and hit targets based on user preference or monitor DPI.
    """

    def __init__(self, scale_setting: str = "AUTO"):
        self.scale_setting = scale_setting if scale_setting in UI_SCALE_OPTIONS else "AUTO"
        self.system_scale = get_system_dpi_scale()
        self.factor = self._resolve_factor()

    def _resolve_factor(self) -> float:
        if self.scale_setting == "100%":
            return 1.0
        elif self.scale_setting == "125%":
            return 1.25
        elif self.scale_setting == "150%":
            return 1.50
        elif self.scale_setting == "175%":
            return 1.75
        elif self.scale_setting == "200%":
            return 2.00
        else:  # AUTO
            # Clamp auto scale between 1.0 and 2.0
            return max(1.0, min(2.0, self.system_scale))

    def update_setting(self, new_setting: str) -> None:
        self.scale_setting = new_setting if new_setting in UI_SCALE_OPTIONS else "AUTO"
        self.system_scale = get_system_dpi_scale()
        self.factor = self._resolve_factor()

    def s(self, px: int) -> int:
        """Scale an integer pixel value by the current scale factor."""
        if px == 0:
            return 0
        val = int(round(px * self.factor))
        return max(1, val) if px > 0 else val

    # Typography helpers
    def font(self, size: int, weight: str = "normal", family: str = "Consolas") -> Tuple[str, int, str]:
        """Produce a scaled Tkinter font descriptor."""
        scaled_size = max(7, int(round(size * self.factor)))
        return (family, scaled_size, weight)

    @property
    def f_app_title(self) -> Tuple[str, int, str]:
        return self.font(14, "bold")

    @property
    def f_section_title(self) -> Tuple[str, int, str]:
        return self.font(12, "bold")

    @property
    def f_card_title(self) -> Tuple[str, int, str]:
        return self.font(11, "bold")

    @property
    def f_primary_metric(self) -> Tuple[str, int, str]:
        return self.font(18, "bold")

    @property
    def f_primary_metric_focus(self) -> Tuple[str, int, str]:
        return self.font(24, "bold")

    @property
    def f_secondary_metric(self) -> Tuple[str, int, str]:
        return self.font(11, "bold")

    @property
    def f_badge(self) -> Tuple[str, int, str]:
        return self.font(9, "bold")

    @property
    def f_body(self) -> Tuple[str, int, str]:
        return self.font(9, "normal")

    @property
    def f_meta(self) -> Tuple[str, int, str]:
        return self.font(8, "normal")

    @property
    def f_btn(self) -> Tuple[str, int, str]:
        return self.font(9, "bold")

    # Layout tokens
    @property
    def default_window_w(self) -> int:
        return self.s(1240)

    @property
    def default_window_h(self) -> int:
        return self.s(780)

    @property
    def min_window_w(self) -> int:
        return self.s(760)

    @property
    def min_window_h(self) -> int:
        return self.s(580)

    @property
    def header_height(self) -> int:
        return self.s(68)

    @property
    def footer_height(self) -> int:
        return self.s(30)

    @property
    def grid_margin(self) -> int:
        return self.s(14)

    @property
    def gap(self) -> int:
        return self.s(10)

    @property
    def card_min_w(self) -> int:
        return self.s(260)

    @property
    def card_max_w(self) -> int:
        return self.s(420)

    @property
    def card_h(self) -> int:
        return self.s(150)

    @property
    def focus_card_h(self) -> int:
        return self.s(205)

    @property
    def btn_h(self) -> int:
        return self.s(28)


# Default global instance
ui_scale = UiScale("AUTO")
