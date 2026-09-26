#!/usr/bin/env python3
"""
Claude Code local usage reader.
Reads ~/.claude.json for authoritative Anthropic usage cache,
and reads ~/.claude/projects/*/*.jsonl for local session details and model history.
"""
from __future__ import annotations

import datetime
import glob
import json
import os
from typing import Any

def parse_iso(ts_str: str | None) -> datetime.datetime | None:
    if not ts_str:
        return None
    try:
        # Handle trailing Z or timezone offsets
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(ts_str)
    except Exception:
        return None

def format_timedelta(delta: datetime.timedelta) -> str:
    if delta.total_seconds() <= 0:
        return "NOW"
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if days > 0:
        return f"{days}D {hours}H"
    elif hours > 0:
        return f"{hours}H {minutes:02d}M"
    else:
        return f"{minutes}M"

def read_claude_usage(user_home: str | None = None) -> dict[str, Any]:
    """
    Read Claude Code usage data from local files.
    Returns a structured dictionary with values and authoritative vs estimated flags.
    """
    home = user_home or os.path.expanduser("~")
    claude_json_path = os.path.join(home, ".claude.json")
    projects_dir = os.path.join(home, ".claude", "projects")

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # 1. Read .claude.json
    cached_util = None
    fetched_at = None
    if os.path.exists(claude_json_path):
        try:
            with open(claude_json_path, "r", encoding="utf-8", errors="ignore") as f:
                config_data = json.load(f)
                cached_util = config_data.get("cachedUsageUtilization")
                if cached_util and "fetchedAtMs" in cached_util:
                    fetched_at = datetime.datetime.fromtimestamp(
                        cached_util["fetchedAtMs"] / 1000, tz=datetime.timezone.utc
                    )
        except Exception as e:
            print(f"Warning reading {claude_json_path}: {e}")

    # 2. Read session logs for latest model and active window
    latest_msg_time = None
    latest_model = "Sonnet"
    active_window_start = None
    recent_tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}

    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    for file_path in jsonl_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"model":' not in line and '"usage":' not in line:
                        continue
                    try:
                        record = json.loads(line)
                        msg = record.get("message")
                        if not isinstance(msg, dict):
                            continue
                        model = msg.get("model")
                        ts_str = record.get("timestamp")
                        ts = parse_iso(ts_str)
                        if ts:
                            if latest_msg_time is None or ts > latest_msg_time:
                                latest_msg_time = ts
                                if model:
                                    latest_model = model

                            # Check if within last 5 hours
                            if (now_utc - ts).total_seconds() <= 5 * 3600:
                                if active_window_start is None or ts < active_window_start:
                                    active_window_start = ts
                                usage = msg.get("usage", {})
                                recent_tokens["input"] += usage.get("input_tokens", 0)
                                recent_tokens["output"] += usage.get("output_tokens", 0)
                                recent_tokens["cache_read"] += usage.get("cache_read_input_tokens", 0)
                                recent_tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0)
                    except Exception:
                        continue
        except Exception:
            continue

    # Format model name nicely for 128x128 header
    clean_model = "CLAUDE"
    if "opus" in latest_model.lower():
        if "5" in latest_model:
            clean_model = "OPUS 5"
        elif "4" in latest_model:
            clean_model = "OPUS 4"
        else:
            clean_model = "OPUS"
    elif "sonnet" in latest_model.lower():
        if "4-5" in latest_model or "4.5" in latest_model:
            clean_model = "SONNET 4.5"
        else:
            clean_model = "SONNET"
    elif "haiku" in latest_model.lower():
        clean_model = "HAIKU"
    elif "fable" in latest_model.lower():
        clean_model = "FABLE"

    # Default metrics
    five_hour_pct: int | None = None
    five_hour_reset_str = "N/A"
    week_pct: int | None = None
    week_reset_str = "N/A"
    is_live = False
    is_stale = False
    freshness_str = "No cache"

    documentation = {
        "five_hour_percent": "Unavailable - no active server window or fresh cache",
        "five_hour_reset": "Unavailable",
        "week_percent": "Unavailable",
        "week_reset": "Unavailable",
        "model": "Authoritative from local session logs",
    }

    if fetched_at:
        age_hours = (now_utc - fetched_at).total_seconds() / 3600.0
        age_days = age_hours / 24.0
        if age_days >= 1.0:
            freshness_str = f"{age_days:.1f}d ago ({fetched_at.strftime('%Y-%m-%d %H:%M UTC')})"
            is_stale = True
        else:
            freshness_str = f"{age_hours:.1f}h ago ({fetched_at.strftime('%H:%M UTC')})"

    if cached_util and "utilization" in cached_util:
        u = cached_util["utilization"]
        fh = u.get("five_hour") or {}
        sd = u.get("seven_day") or {}

        # 7-day weekly usage percentage
        sd_reset = parse_iso(sd.get("resets_at"))
        raw_sd_util = sd.get("utilization")
        if raw_sd_util is not None:
            # If the weekly cycle reset occurred before now, cache is for previous period
            if sd_reset and sd_reset < now_utc:
                is_stale = True
                week_pct = int(round(raw_sd_util))
                documentation["week_percent"] = f"Stale cached snapshot ({freshness_str}) - weekly cycle expired {sd_reset.strftime('%Y-%m-%d')}"
            else:
                week_pct = int(round(raw_sd_util))
                documentation["week_percent"] = f"Authoritative Anthropic utilization percentage ({freshness_str})"

        # 7-day weekly reset
        if sd_reset:
            next_reset = sd_reset
            while next_reset < now_utc:
                next_reset += datetime.timedelta(days=7)
            week_reset_str = format_timedelta(next_reset - now_utc)
            documentation["week_reset"] = f"Calculated next cycle ({next_reset.strftime('%a %H:%M UTC')}) from Anthropic weekly schedule"

        # 5-hour usage
        fh_reset = parse_iso(fh.get("resets_at"))
        raw_fh_util = fh.get("utilization")

        if fh_reset and fh_reset > now_utc:
            # Currently active 5h window recorded in server cache
            five_hour_pct = int(round(raw_fh_util)) if raw_fh_util is not None else None
            five_hour_reset_str = format_timedelta(fh_reset - now_utc)
            is_live = True
            documentation["five_hour_percent"] = f"Authoritative Anthropic utilization ({freshness_str})"
            documentation["five_hour_reset"] = f"Authoritative Anthropic reset timestamp ({fh_reset.strftime('%H:%M UTC')})"
        elif active_window_start:
            window_end = active_window_start + datetime.timedelta(hours=5)
            if window_end > now_utc:
                five_hour_reset_str = format_timedelta(window_end - now_utc)
                # If cached utilization was fetched during this same active window
                if fetched_at and fetched_at >= active_window_start and raw_fh_util is not None:
                    five_hour_pct = int(round(raw_fh_util))
                    documentation["five_hour_percent"] = f"Authoritative Anthropic utilization ({freshness_str})"
                else:
                    # Active session exists locally, but server percentage is unknown without fresh cache
                    five_hour_pct = None
                    documentation["five_hour_percent"] = "Unavailable - active local session but server quota cache is stale"
                documentation["five_hour_reset"] = "Calculated from local session message timestamps (+5H)"
                is_live = True
            else:
                five_hour_pct = None
                five_hour_reset_str = "N/A"
                documentation["five_hour_percent"] = f"Unavailable - window expired ({freshness_str})"
                documentation["five_hour_reset"] = "N/A"
        else:
            # No active window and cached 5h window is expired
            five_hour_pct = None
            five_hour_reset_str = "N/A"
            documentation["five_hour_percent"] = f"Unavailable - cache expired ({freshness_str})"
            documentation["five_hour_reset"] = "N/A"

    return {
        "five_hour_pct": five_hour_pct,
        "five_hour_reset_str": five_hour_reset_str,
        "week_pct": week_pct,
        "week_reset_str": week_reset_str,
        "model_name": clean_model,
        "raw_model": latest_model,
        "is_live": is_live,
        "is_stale": is_stale,
        "freshness_str": freshness_str,
        "fetched_at": fetched_at.isoformat() if fetched_at else None,
        "recent_tokens": recent_tokens,
        "documentation": documentation,
    }

if __name__ == "__main__":
    data = read_claude_usage()
    print("=== Claude Usage Summary ===")
    print(f"Model: {data['model_name']} ({data['raw_model']})")
    print(f"5-Hour: {data['five_hour_pct']}% | Reset: {data['five_hour_reset_str']}")
    print(f"Week:   {data['week_pct']}% | Reset: {data['week_reset_str']}")
    print(f"Live Active: {data['is_live']}")
    print("\n=== Authority / Estimation Breakdown ===")
    for k, v in data["documentation"].items():
        print(f"  • {k}: {v}")
