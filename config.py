#!/usr/bin/env python3
"""
Persistent Settings Manager for AI Desk Dashboard.
Stores configuration in %APPDATA%/AiDeskDashboard/config.json.
Contains:
- enabled dashboard pages
- page order
- MiniToo preferred device / COM port (AUTO or COMx)
- MiniToo rotation interval & auto-cycle toggle
- last selected page
- Start with Windows & Launch Minimized flags
- DGX host and coding repo path
- Window position
- first_run_completed status
No authentication tokens are stored here.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

ALL_PAGE_IDS = [
    "codex", "gemini", "claude",
    "local_pc", "dgx_spark", "btc",
    "ai_activity", "services", "coding"
]

PAGE_LABELS = {
    "codex": "Codex Quota",
    "gemini": "Gemini Quota",
    "claude": "Claude Status",
    "local_pc": "Local PC Hardware",
    "dgx_spark": "DGX Spark Server",
    "btc": "Bitcoin Price & Chart",
    "ai_activity": "AI Activity Monitor",
    "services": "Workstation Services",
    "coding": "Active Workspace",
}


def get_app_dir() -> str:
    """Return platform-appropriate application configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if not base:
            base = os.path.expanduser("~")
        app_dir = os.path.join(base, "AiDeskDashboard")
    else:
        app_dir = os.path.expanduser("~/.config/aideskdashboard")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_config_path() -> str:
    return os.path.join(get_app_dir(), "config.json")


def get_log_path() -> str:
    return os.path.join(get_app_dir(), "launch.log")


@dataclass
class DashboardConfig:
    enabled_pages: List[str] = field(default_factory=lambda: list(ALL_PAGE_IDS))
    page_order: List[str] = field(default_factory=lambda: list(ALL_PAGE_IDS))
    minitoo_port: str = "AUTO"
    rotation_interval: float = 4.0
    auto_cycle: bool = False
    last_selected_page: str = "btc"
    start_with_windows: bool = False
    launch_minimized: bool = False
    dgx_host: str = "dgx"
    coding_repo_path: str = "."
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    first_run_completed: bool = False

    def validate(self) -> None:
        """Sanitize and ensure lists contain valid items."""
        # Ensure enabled_pages only contains recognized page IDs
        self.enabled_pages = [p for p in self.enabled_pages if p in ALL_PAGE_IDS]
        if not self.enabled_pages:
            self.enabled_pages = list(ALL_PAGE_IDS)

        # Ensure page_order contains all recognized pages exactly once
        ordered = [p for p in self.page_order if p in ALL_PAGE_IDS]
        for p in ALL_PAGE_IDS:
            if p not in ordered:
                ordered.append(p)
        self.page_order = ordered

        # Validate last_selected_page
        if self.last_selected_page not in ALL_PAGE_IDS:
            self.last_selected_page = self.enabled_pages[0] if self.enabled_pages else "btc"

        # Validate rotation interval
        if self.rotation_interval < 1.0:
            self.rotation_interval = 1.0
        elif self.rotation_interval > 300.0:
            self.rotation_interval = 300.0

    def get_active_pages(self) -> List[str]:
        """Return the enabled pages in the customized order."""
        active = [p for p in self.page_order if p in self.enabled_pages]
        return active if active else ["btc"]

    @classmethod
    def load(cls) -> DashboardConfig:
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cfg = cls(
                    enabled_pages=data.get("enabled_pages", list(ALL_PAGE_IDS)),
                    page_order=data.get("page_order", list(ALL_PAGE_IDS)),
                    minitoo_port=data.get("minitoo_port", "AUTO"),
                    rotation_interval=float(data.get("rotation_interval", 4.0)),
                    auto_cycle=bool(data.get("auto_cycle", False)),
                    last_selected_page=data.get("last_selected_page", "btc"),
                    start_with_windows=bool(data.get("start_with_windows", False)),
                    launch_minimized=bool(data.get("launch_minimized", False)),
                    dgx_host=data.get("dgx_host", "dgx"),
                    coding_repo_path=data.get("coding_repo_path", "."),
                    window_x=data.get("window_x"),
                    window_y=data.get("window_y"),
                    first_run_completed=bool(data.get("first_run_completed", False)),
                )
                cfg.validate()
                return cfg
            except Exception as e:
                print(f"[CONFIG] Warning loading {config_path}: {e}. Using defaults.")
        
        cfg = cls()
        cfg.validate()
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a standard dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DashboardConfig:
        """Construct configuration from dictionary with validation."""
        cfg = cls(
            enabled_pages=data.get("enabled_pages", list(ALL_PAGE_IDS)),
            page_order=data.get("page_order", list(ALL_PAGE_IDS)),
            minitoo_port=data.get("minitoo_port", "AUTO"),
            rotation_interval=float(data.get("rotation_interval", 4.0)),
            auto_cycle=bool(data.get("auto_cycle", False)),
            last_selected_page=data.get("last_selected_page", "btc"),
            start_with_windows=bool(data.get("start_with_windows", False)),
            launch_minimized=bool(data.get("launch_minimized", False)),
            dgx_host=data.get("dgx_host", "dgx"),
            coding_repo_path=data.get("coding_repo_path", "."),
            window_x=data.get("window_x"),
            window_y=data.get("window_y"),
            first_run_completed=bool(data.get("first_run_completed", False)),
        )
        cfg.validate()
        return cfg

    def save(self) -> bool:
        self.validate()
        config_path = get_config_path()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"[CONFIG] Error saving {config_path}: {e}")
            return False
