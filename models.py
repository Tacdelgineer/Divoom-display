#!/usr/bin/env python3
"""
Normalized data models for AI Desk Dashboard.
Decouples raw provider/system collector schemas from the rendering pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class MetricItem:
    """A single normalized metric entry with optional progress bar value and provenance."""
    label: str
    value: str
    pct: Optional[float] = None          # Numeric percentage for progress bar (0-100), or None
    reset: Optional[str] = None         # Sub-metric or reset timer (e.g. "9M", "51C", "+2 -1")
    authority: str = "AUTHORITATIVE"    # AUTHORITATIVE, CALCULATED, STALE_CACHE, UNAVAILABLE
    used_pct: Optional[float] = None     # Normalized used percentage (0-100)
    remaining_pct: Optional[float] = None # Normalized remaining percentage (0-100)


@dataclass
class PageData:
    """Normalized page representation rendered on any DisplayBackend."""
    page_id: str                      # "claude", "codex", "gemini", "local_pc", "dgx_spark", "coding"
    title: str                        # Display title (e.g. "LOCAL PC", "DGX SPARK")
    badge: str                        # Badge text (e.g. "ONLINE", "ACTIVE", "LOCAL ONLY", "OFFLINE")
    badge_color: str = "green"        # "green", "amber", "blue", "red", "gray"
    is_offline: bool = False
    offline_msg: Optional[str] = None # e.g. "OFFLINE"
    offline_sub: Optional[str] = None # e.g. "12M AGO"
    primary_metric: Optional[MetricItem] = None
    secondary_metric: Optional[MetricItem] = None
    extra_metrics: List[MetricItem] = field(default_factory=list)
    footer_left: str = ""             # Bottom-left label or model
    footer_right: str = ""            # Bottom-right auxiliary info
    source_info: str = ""             # Provenance / origin string for --status
    metrics_provenance: Dict[str, str] = field(default_factory=dict)
    # Visual and structured extensions for Milestone 5 and 12 pages
    sparkline_data: Optional[List[float]] = None
    sparkline_change: Optional[str] = None
    sparkline_high: Optional[str] = None
    sparkline_low: Optional[str] = None
    items_list: Optional[List[Dict[str, Any]]] = None  # For Services and AI Activity lists
    quota_debug: Optional[Dict[str, Any]] = None
    # Milestone 12 & 15 extensions
    crypto_assets: Optional[List[CryptoAsset]] = None
    stocks_data: Optional[List[StockQuote]] = None
    claude_profiles: Optional[List[ClaudeAccountProfile]] = None
    signals_data: Optional[List[PredictionMarketSignal]] = None
    news_data: Optional[List[NewsHeadline]] = None



@dataclass
class CryptoAsset:
    """Normalized multi-asset cryptocurrency model with sparkline."""
    symbol: str                     # e.g. "BTC", "ETH", "SOL", "DOGE", "PEPE"
    name: str                       # e.g. "Bitcoin", "Ethereum", "Solana", etc.
    price: float                    # USD spot price
    change_24h_pct: float           # 24H percentage delta (+/-)
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    sparkline: List[float] = field(default_factory=list)
    source: str = "CoinGecko"
    fetched_at: str = ""
    icon_char: str = ""             # e.g. "BTC", "ETH", "SOL", "DOGE", "PEPE"

    @property
    def formatted_price(self) -> str:
        """Intelligently format USD price across large and micro-cent assets."""
        if self.price >= 1000:
            return f"${self.price:,.0f}"
        elif self.price >= 1.0:
            return f"${self.price:,.2f}"
        elif self.price >= 0.001:
            return f"${self.price:.4f}"
        elif self.price > 0:
            # Intelligent micro-decimal representation for tokens like PEPE
            return f"${self.price:.7f}"
        return "$0.00"

    @property
    def formatted_compact_price(self) -> str:
        """Compact 6-8 character price string for MiniToo 128px displays."""
        if self.price >= 10000:
            return f"${self.price/1000:.1f}K"
        elif self.price >= 1000:
            return f"${self.price:,.0f}"
        elif self.price >= 10:
            return f"${self.price:.1f}"
        elif self.price >= 1.0:
            return f"${self.price:.2f}"
        elif self.price >= 0.01:
            return f"${self.price:.3f}"
        elif self.price > 0:
            # Micro token: e.g. $4.5e-6
            return f"${self.price*1e6:.1f}u"
        return "$0"


@dataclass
class StockQuote:
    """Normalized US stock quote with objective intraday volatility metric."""
    symbol: str                     # e.g. "NVDA", "TSLA", "GME"
    name: str                       # e.g. "NVIDIA Corp"
    price: float                    # Current market price
    change_pct: float               # Net day change percentage (+/-)
    volatility_pct: float = 0.0     # Intraday range: (high - low) / previous_close * 100
    high: float = 0.0
    low: float = 0.0
    previous_close: float = 0.0
    market_cap: Optional[float] = None # Market capitalization in USD
    sparkline: List[float] = field(default_factory=list) # Intraday sparkline points
    market_state: str = "REGULAR"   # "REGULAR", "POST", "PRE", "CLOSED"
    source: str = "MarketData"
    fetched_at: str = ""

    @property
    def formatted_market_cap(self) -> str:
        """Format market cap compactly (e.g. $5.55T, $845.6B)."""
        if self.market_cap is None or self.market_cap <= 0:
            return "N/A"
        if self.market_cap >= 1e12:
            return f"${self.market_cap / 1e12:.2f}T"
        elif self.market_cap >= 1e9:
            val = self.market_cap / 1e9
            return f"${val:.1f}B" if val >= 100 else f"${val:.2f}B"
        elif self.market_cap >= 1e6:
            return f"${self.market_cap / 1e6:.1f}M"
        return f"${self.market_cap:,.0f}"


    @property
    def formatted_price(self) -> str:
        """Format price with comma separator."""
        if self.price >= 1000:
            return f"${self.price:,.2f}"
        return f"${self.price:.2f}"


@dataclass
class ClaudeAccountProfile:
    """Isolated Claude account profile model supporting multiple accounts."""
    id: str                         # "personal", "secondary", etc.
    user_label: str                 # User-defined display label (e.g. "Personal", "Work")
    account_identity_masked: str    # Anonymized email (e.g. "no***@gmail.com")
    plan: str                       # "Claude Pro", "Free", etc.
    auth_type: str                  # "Subscription (OAuth)", "API Key", etc.
    status_text: str = "READY"      # "ACTIVE", "READY", "UNAVAILABLE"
    five_hour_used_pct: Optional[float] = None
    five_hour_remaining_pct: Optional[float] = None
    five_hour_reset: Optional[str] = None
    weekly_used_pct: Optional[float] = None
    weekly_remaining_pct: Optional[float] = None
    weekly_reset: Optional[str] = None
    authority: str = "UNAVAILABLE"  # AUTHORITATIVE, STALE_CACHE, UNAVAILABLE
    usage_available: bool = False
    is_active: bool = False
    fetched_at: Optional[str] = None
    config_dir: str = ""


@dataclass
class NewsHeadline:
    """Normalized external headline from RSS or financial API."""
    source: str
    headline: str
    url: str = ""
    timestamp: str = ""
    time_ago: str = ""

    def __post_init__(self):
        if not self.time_ago and self.timestamp:
            self.time_ago = self.timestamp
        elif not self.timestamp and self.time_ago:
            self.timestamp = self.time_ago


@dataclass
class PredictionMarketSignal:
    """Normalized prediction market signal (e.g. Polymarket probability)."""
    event_id: str
    question: str
    category: str                   # FINANCE, CRYPTO, TECH / AI, GEOPOLITICS, BREAKING
    yes_probability: float          # 0.0 to 1.0 (e.g. 0.64 for 64%)
    no_probability: float           # 0.0 to 1.0 (e.g. 0.36 for 36%)
    change_24h_pts: float           # 24h delta in probability points (e.g. +8.0)
    volume: float                   # Total volume in USD
    liquidity: float                # Available market liquidity in USD
    end_date: str = ""
    url: str = ""
    updated_at: str = ""
    attention_score: float = 0.0
    related_headlines: List[NewsHeadline] = field(default_factory=list)

    @property
    def formatted_prob(self) -> str:
        """Format probability as percentage integer (e.g. 64%)."""
        return f"{round(self.yes_probability * 100):.0f}%"

    @property
    def formatted_change(self) -> str:
        """Format 24H point change with sign (e.g. +8.0 pts)."""
        sign = "+" if self.change_24h_pts > 0 else ""
        return f"{sign}{self.change_24h_pts:.1f} pts"

    @property
    def formatted_volume(self) -> str:
        """Format total volume compactly (e.g. $18.5M)."""
        if self.volume >= 1e6:
            return f"${self.volume / 1e6:.1f}M"
        elif self.volume >= 1e3:
            return f"${self.volume / 1e3:.0f}K"
        return f"${self.volume:,.0f}"

    @property
    def formatted_liquidity(self) -> str:
        """Format liquidity compactly (e.g. $4.2M)."""
        if self.liquidity >= 1e6:
            return f"${self.liquidity / 1e6:.1f}M"
        elif self.liquidity >= 1e3:
            return f"${self.liquidity / 1e3:.0f}K"
        return f"${self.liquidity:,.0f}"



@dataclass
class Alert:
    """Normalized alert model for system, market, or agent conditions (Milestone 15 Architecture)."""
    source: str                     # "SYSTEM", "MARKET", "AGENT", "POLYMARKET"
    severity: str                   # "INFO", "WARNING", "CRITICAL"
    title: str                      # e.g. "CODEX 8% LEFT", "DGX 91C", "POLYMARKET +14 pts"
    value: str                      # e.g. "8%", "91°C", "+14 pts"
    timestamp: Any = 0.0
    action_url: Optional[str] = None


