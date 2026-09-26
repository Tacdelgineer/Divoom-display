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
    # Visual and structured extensions for Milestone 5 pages
    sparkline_data: Optional[List[float]] = None
    sparkline_change: Optional[str] = None
    sparkline_high: Optional[str] = None
    sparkline_low: Optional[str] = None
    items_list: Optional[List[Dict[str, Any]]] = None  # For Services and AI Activity lists
    quota_debug: Optional[Dict[str, Any]] = None
