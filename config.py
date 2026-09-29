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
    # Crypto
    "btc", "eth", "sol", "doge", "pepe", "crypto",
    # AI Usage
    "codex", "gemini", "claude",
    # System
    "local_pc", "dgx_spark", "services", "coding", "ai_activity",
    # Stocks
    "stocks_volatile",
]

PAGE_LABELS = {
    "btc": "Bitcoin (BTC)",
    "eth": "Ethereum (ETH)",
    "sol": "Solana (SOL)",
    "doge": "Dogecoin (DOGE)",
    "pepe": "Pepe (PEPE)",
    "crypto": "Crypto Overview",
    "codex": "Codex Quota",
    "gemini": "Gemini Quota",
    "claude": "Claude Status",
    "local_pc": "Local PC Hardware",
    "dgx_spark": "DGX Spark Server",
    "services": "Workstation Services",
    "coding": "Active Workspace",
    "ai_activity": "AI Activity Monitor",
    "stocks_volatile": "Top 10 Volatile Stocks",
}

SECTION_CRYPTO = "crypto"
SECTION_AI_USAGE = "ai_usage"
SECTION_SYSTEM = "system"
SECTION_STOCKS = "stocks"

ALL_SECTIONS = [SECTION_CRYPTO, SECTION_AI_USAGE, SECTION_SYSTEM, SECTION_STOCKS]

SECTION_TITLES = {
    SECTION_CRYPTO: "CRYPTO MARKETS",
    SECTION_AI_USAGE: "AI USAGE",
    SECTION_SYSTEM: "SYSTEM & SERVICES",
    SECTION_STOCKS: "VOLATILE STOCKS",
}

DEFAULT_SECTION_CARDS = {
    SECTION_CRYPTO: ["btc", "eth", "sol", "doge", "pepe"],
    SECTION_AI_USAGE: ["codex", "gemini", "claude"],
    SECTION_SYSTEM: ["local_pc", "dgx_spark", "services", "coding", "ai_activity"],
    SECTION_STOCKS: ["stocks_volatile"],
}

# Presets
PRESET_ALL = "ALL"
PRESET_AI = "AI"
PRESET_MARKETS = "MARKETS"
PRESET_SYSTEM = "SYSTEM"

ALL_PRESETS = [PRESET_ALL, PRESET_AI, PRESET_MARKETS, PRESET_SYSTEM]


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

    # Milestone 12 Section System
    sections_order: List[str] = field(default_factory=lambda: list(ALL_SECTIONS))
    enabled_sections: Dict[str, bool] = field(default_factory=lambda: {s: True for s in ALL_SECTIONS})
    section_cards: Dict[str, List[str]] = field(default_factory=lambda: {s: list(DEFAULT_SECTION_CARDS[s]) for s in ALL_SECTIONS})
    enabled_cards: Dict[str, bool] = field(default_factory=lambda: {c: True for c in ALL_PAGE_IDS})
    active_preset: str = PRESET_ALL

    # Milestone 12 Claude Account Profiles
    claude_profiles: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"id": "personal", "user_label": "Personal", "config_dir": os.path.expanduser("~/.claude")},
        {"id": "secondary", "user_label": "Secondary", "config_dir": os.path.expanduser("~/.claude-secondary")},
    ])

    # Ditoo 16x16 Hardware Display Configuration
    target_device: str = "ditoo"  # "minitoo", "ditoo", or "preview"
    ditoo_mac: str = "B1:21:81:5B:E3:16"
    ditoo_port: str = "AUTO"
    ditoo_auto_connect: bool = True
    ditoo_auto_rotation: bool = True
    ditoo_is_paused: bool = False
    ditoo_enabled_crypto_page: bool = True
    ditoo_enabled_stock_page: bool = True
    ditoo_enabled_cryptos: List[str] = field(default_factory=lambda: ["btc", "eth", "sol", "doge", "pepe"])
    ditoo_stock_tickers: List[str] = field(default_factory=lambda: ["NVDA", "TSLA", "AAPL", "MSFT", "META"])
    ditoo_frame_logo_dwell: float = 1.0    # Seconds for ticker/logo frame
    ditoo_frame_price_dwell: float = 2.0   # Seconds for price frame
    ditoo_frame_change_dwell: float = 2.0  # Seconds for change % frame
    ditoo_brightness: int = 100            # Display brightness (0-100)
    ditoo_layout_mode: str = "cycle"       # "cycle", "split", "scroll"

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

        # Validate sections_order
        s_ordered = [s for s in self.sections_order if s in ALL_SECTIONS]
        for s in ALL_SECTIONS:
            if s not in s_ordered:
                s_ordered.append(s)
        self.sections_order = s_ordered

        # Validate enabled_sections
        for s in ALL_SECTIONS:
            if s not in self.enabled_sections:
                self.enabled_sections[s] = True

        # Validate section_cards
        for s in ALL_SECTIONS:
            if s not in self.section_cards:
                self.section_cards[s] = list(DEFAULT_SECTION_CARDS[s])
            else:
                valid_cards = [c for c in self.section_cards[s] if c in ALL_PAGE_IDS]
                for def_c in DEFAULT_SECTION_CARDS[s]:
                    if def_c not in valid_cards:
                        valid_cards.append(def_c)
                self.section_cards[s] = valid_cards

        # Validate enabled_cards
        for c in ALL_PAGE_IDS:
            if c not in self.enabled_cards:
                self.enabled_cards[c] = True

        # Validate last_selected_page
        if self.last_selected_page not in ALL_PAGE_IDS:
            self.last_selected_page = "btc"

        # Validate rotation interval
        if self.rotation_interval < 1.0:
            self.rotation_interval = 1.0
        elif self.rotation_interval > 300.0:
            self.rotation_interval = 300.0

    def apply_preset(self, preset_name: str) -> None:
        """Apply one of the built-in dashboard presets."""
        p = preset_name.upper().strip()
        if p not in ALL_PRESETS:
            p = PRESET_ALL
        self.active_preset = p

        if p == PRESET_ALL:
            for s in ALL_SECTIONS:
                self.enabled_sections[s] = True
            for c in ALL_PAGE_IDS:
                self.enabled_cards[c] = True

        elif p == PRESET_AI:
            self.enabled_sections[SECTION_AI_USAGE] = True
            self.enabled_sections[SECTION_SYSTEM] = True
            self.enabled_sections[SECTION_CRYPTO] = False
            self.enabled_sections[SECTION_STOCKS] = False
            for c in ALL_PAGE_IDS:
                if c in ("codex", "gemini", "claude", "ai_activity"):
                    self.enabled_cards[c] = True
                else:
                    self.enabled_cards[c] = False

        elif p == PRESET_MARKETS:
            self.enabled_sections[SECTION_CRYPTO] = True
            self.enabled_sections[SECTION_STOCKS] = True
            self.enabled_sections[SECTION_AI_USAGE] = False
            self.enabled_sections[SECTION_SYSTEM] = False
            for c in ALL_PAGE_IDS:
                if c in ("btc", "eth", "sol", "doge", "pepe", "crypto", "stocks_volatile"):
                    self.enabled_cards[c] = True
                else:
                    self.enabled_cards[c] = False

        elif p == PRESET_SYSTEM:
            self.enabled_sections[SECTION_SYSTEM] = True
            self.enabled_sections[SECTION_CRYPTO] = False
            self.enabled_sections[SECTION_AI_USAGE] = False
            self.enabled_sections[SECTION_STOCKS] = False
            for c in ALL_PAGE_IDS:
                if c in ("local_pc", "dgx_spark", "services", "coding"):
                    self.enabled_cards[c] = True
                else:
                    self.enabled_cards[c] = False

    def get_active_pages(self) -> List[str]:
        """Return the enabled pages in the customized order for MiniToo rotation."""
        active = []
        for p in self.page_order:
            # Check if card is enabled and its parent section is enabled
            if self.enabled_cards.get(p, True):
                parent_sec = None
                for s, cards in self.section_cards.items():
                    if p in cards:
                        parent_sec = s
                        break
                if parent_sec is None or self.enabled_sections.get(parent_sec, True):
                    active.append(p)
        return active if active else ["btc"]

    @classmethod
    def load(cls) -> DashboardConfig:
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.from_dict(data)
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
            sections_order=data.get("sections_order", list(ALL_SECTIONS)),
            enabled_sections=data.get("enabled_sections", {s: True for s in ALL_SECTIONS}),
            section_cards=data.get("section_cards", {s: list(DEFAULT_SECTION_CARDS[s]) for s in ALL_SECTIONS}),
            enabled_cards=data.get("enabled_cards", {c: True for c in ALL_PAGE_IDS}),
            active_preset=data.get("active_preset", PRESET_ALL),
            claude_profiles=data.get("claude_profiles", [
                {"id": "personal", "user_label": "Personal", "config_dir": os.path.expanduser("~/.claude")},
                {"id": "secondary", "user_label": "Secondary", "config_dir": os.path.expanduser("~/.claude-secondary")},
            ]),
            target_device=data.get("target_device", "ditoo"),
            ditoo_mac=data.get("ditoo_mac", "B1:21:81:5B:E3:16"),
            ditoo_port=data.get("ditoo_port", "AUTO"),
            ditoo_auto_connect=bool(data.get("ditoo_auto_connect", True)),
            ditoo_auto_rotation=bool(data.get("ditoo_auto_rotation", True)),
            ditoo_is_paused=bool(data.get("ditoo_is_paused", False)),
            ditoo_enabled_crypto_page=bool(data.get("ditoo_enabled_crypto_page", True)),
            ditoo_enabled_stock_page=bool(data.get("ditoo_enabled_stock_page", True)),
            ditoo_enabled_cryptos=data.get("ditoo_enabled_cryptos", ["btc", "eth", "sol", "doge", "pepe"]),
            ditoo_stock_tickers=data.get("ditoo_stock_tickers", ["NVDA", "TSLA", "AAPL", "MSFT", "META"]),
            ditoo_frame_logo_dwell=float(data.get("ditoo_frame_logo_dwell", 1.0)),
            ditoo_frame_price_dwell=float(data.get("ditoo_frame_price_dwell", 2.0)),
            ditoo_frame_change_dwell=float(data.get("ditoo_frame_change_dwell", 2.0)),
            ditoo_brightness=int(data.get("ditoo_brightness", 100)),
            ditoo_layout_mode=data.get("ditoo_layout_mode", "cycle"),
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
