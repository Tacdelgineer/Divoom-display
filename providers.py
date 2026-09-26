"""
Multi-provider AI usage collector for Divoom MiniToo.
Supports:
1. Claude Code (~/.claude.json + session logs; honest stale cache / unavailable status)
2. OpenAI Codex / ChatGPT (ChatGPT backend usage API via ~/.codex/auth.json + state_5.sqlite)
3. Google Gemini / Antigravity (Live backend quota via 'agy -p /usage --output-format json')
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from subproc import run_hidden


@dataclass
class UsageData:
    provider_name: str          # "CLAUDE", "CODEX", "GEMINI"
    primary_label: str          # "5H", "USAGE", or "SESSION"
    primary_pct: Optional[int]  # 0-100, or None if unavailable (NEVER 0 unless explicit)
    primary_reset: Optional[str]# e.g. "2H 14M", "37M", or "N/A"
    primary_status: Optional[str] # e.g. "READY", "ACTIVE", "STALE", "LOCAL ONLY"
    secondary_label: str        # "WEEK"
    secondary_pct: Optional[int]# 0-100, or None if unavailable
    secondary_reset: Optional[str] # e.g. "5D 16H", "2D 20H", or "N/A"
    model: Optional[str]        # e.g. "OPUS 5", "GPT-5.6", "GEMINI 3.8"
    plan_tier: Optional[str]    # e.g. "PRO", "PLUS", "GOOGLE AI PRO"
    is_stale: bool = False
    freshness: Optional[str] = None
    # Classification: "authoritative", "calculated", "stale_cache", "unavailable"
    metrics_classification: Dict[str, str] = field(default_factory=dict)
    source_description: str = ""
    # Data Quality & Provenance fields (Milestone 5 Section D)
    raw_primary_value: Optional[str] = None
    raw_primary_semantic: str = "USED"   # "USED" | "REMAINING" | "UNAVAILABLE"
    normalized_primary_used: Optional[int] = None
    normalized_primary_remaining: Optional[int] = None
    raw_secondary_value: Optional[str] = None
    raw_secondary_semantic: str = "USED" # "USED" | "REMAINING" | "UNAVAILABLE"
    normalized_secondary_used: Optional[int] = None
    normalized_secondary_remaining: Optional[int] = None
    fetched_at: Optional[str] = None
    authority: str = "AUTHORITATIVE"
    age_seconds: Optional[float] = None
    account_identity: Optional[str] = None
    auth_type: Optional[str] = None
    profile: Optional[Any] = None


class BaseProvider:
    name: str = "BASE"

    def get_usage(self) -> UsageData:
        raise NotImplementedError


class ClaudeProvider(BaseProvider):
    name = "CLAUDE"

    def get_usage(self) -> UsageData:
        import claude_usage
        raw = claude_usage.read_claude_usage()

        model = raw.get("model_name", "OPUS 5")
        fetched_at_str = raw.get("fetched_at")
        freshness = raw.get("authority", "No cache")
        masked_account = raw.get("masked_account", "Not Configured")
        plan_tier = raw.get("plan_tier", "Claude Pro")
        auth_type = raw.get("auth_type", "Subscription (OAuth)")
        profile = raw.get("account_profile")

        is_live = bool(raw.get("is_live", False))
        is_stale = bool(raw.get("is_stale", True))

        fh_used = raw.get("five_hour_used_pct")
        fh_rem = raw.get("five_hour_remaining_pct")
        fh_reset = raw.get("five_hour_reset_str", "N/A")

        wk_used = raw.get("week_used_pct")
        wk_rem = raw.get("week_remaining_pct")
        wk_reset = raw.get("week_reset_str", "N/A")

        classification = {
            "primary_pct": "stale_cache" if is_stale and fh_rem is not None else ("authoritative" if is_live else "unavailable"),
            "primary_reset": "stale_cache" if is_stale and fh_reset != "N/A" else ("authoritative" if is_live else "unavailable"),
            "secondary_pct": "stale_cache" if is_stale and wk_rem is not None else ("authoritative" if is_live else "unavailable"),
            "secondary_reset": "stale_cache" if is_stale and wk_reset != "N/A" else ("authoritative" if is_live else "unavailable"),
            "model": "authoritative",
        }

        # Calculate cache age in seconds if available
        age_sec = None
        if fetched_at_str:
            try:
                dt = datetime.datetime.fromisoformat(fetched_at_str)
                age_sec = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
            except Exception:
                pass

        p_val = f"{int(fh_rem)}% LEFT (cached)" if fh_rem is not None else "N/A"
        s_val = f"{int(wk_rem)}% LEFT (cached)" if wk_rem is not None else "N/A"

        return UsageData(
            provider_name="CLAUDE",
            primary_label="5H",
            primary_pct=int(fh_used) if fh_used is not None else None,
            primary_reset=fh_reset,
            primary_status="ACTIVE" if is_live else ("STALE" if is_stale else "READY"),
            secondary_label="WEEK",
            secondary_pct=int(wk_used) if wk_used is not None else None,
            secondary_reset=wk_reset,
            model=model,
            plan_tier=plan_tier,
            is_stale=is_stale,
            freshness=freshness,
            metrics_classification=classification,
            source_description=f"~/.claude.json ({freshness})",
            raw_primary_value=p_val,
            raw_primary_semantic="REMAINING",
            normalized_primary_used=int(fh_used) if fh_used is not None else None,
            normalized_primary_remaining=int(fh_rem) if fh_rem is not None else None,
            raw_secondary_value=s_val,
            raw_secondary_semantic="REMAINING",
            normalized_secondary_used=int(wk_used) if wk_used is not None else None,
            normalized_secondary_remaining=int(wk_rem) if wk_rem is not None else None,
            fetched_at=fetched_at_str,
            authority=raw.get("authority", "UNAVAILABLE"),
            age_seconds=age_sec,
            account_identity=masked_account,
            auth_type=auth_type,
            profile=profile,
        )


class CodexProvider(BaseProvider):
    name = "CODEX"

    def get_usage(self) -> UsageData:
        home = os.path.expanduser("~")
        auth_file = os.path.join(home, ".codex", "auth.json")
        state_file = os.path.join(home, ".codex", "state_5.sqlite")
        global_state_file = os.path.join(home, ".codex", ".codex-global-state.json")

        access_token = None
        account_id = None
        plan_type = "PLUS"

        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    auth = json.load(f)
                tokens = auth.get("tokens", {})
                access_token = tokens.get("access_token")
                account_id = tokens.get("account_id")
            except Exception:
                pass

        primary_pct = None
        primary_reset = None
        secondary_pct = None
        secondary_reset = None

        classification = {
            "primary_pct": "unavailable",
            "primary_reset": "unavailable",
            "secondary_pct": "unavailable",
            "secondary_reset": "unavailable",
            "model": "unavailable",
        }

        # Query authenticated backend API if token is present
        fetch_start = time.time()
        fetch_success = False
        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "codex/0.145.0",
                "Accept": "application/json",
            }
            if account_id:
                headers["ChatGPT-Account-ID"] = account_id

            url = "https://chatgpt.com/backend-api/codex/usage"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    plan_type = (data.get("plan_type") or "PLUS").upper()
                    rate_limit = data.get("rate_limit", {})

                    pw = rate_limit.get("primary_window")
                    if pw:
                        # Raw field is "used_percent" -> semantic is explicitly USED
                        primary_pct = pw.get("used_percent")
                        classification["primary_pct"] = "authoritative"
                        sec_left = pw.get("reset_after_seconds")
                        if sec_left is not None:
                            primary_reset = self._format_seconds(sec_left)
                            classification["primary_reset"] = "authoritative"

                    sw = rate_limit.get("secondary_window")
                    if sw:
                        # Raw field is "used_percent" -> semantic is explicitly USED
                        secondary_pct = sw.get("used_percent")
                        classification["secondary_pct"] = "authoritative"
                        sec_left = sw.get("reset_after_seconds")
                        if sec_left is not None:
                            secondary_reset = self._format_seconds(sec_left)
                            classification["secondary_reset"] = "authoritative"
                    fetch_success = True
            except Exception:
                pass

        # Detect active model from state_5.sqlite
        active_model = "CODEX"
        if os.path.exists(state_file):
            try:
                conn = sqlite3.connect(f"file:{state_file}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT model FROM threads WHERE model IS NOT NULL ORDER BY updated_at_ms DESC LIMIT 1"
                )
                row = cursor.fetchone()
                if row and row[0]:
                    active_model = self._format_model_name(row[0])
                    classification["model"] = "authoritative"
                conn.close()
            except Exception:
                pass

        if active_model == "CODEX" and os.path.exists(global_state_file):
            try:
                with open(global_state_file, "r", encoding="utf-8") as f:
                    gs = json.load(f)
                recent = (
                    gs.get("electron-persisted-atom-state", {})
                    .get("composer-recent-model-configurations-v1", [])
                )
                if recent and isinstance(recent, list) and recent[0].get("model"):
                    active_model = self._format_model_name(recent[0]["model"])
                    classification["model"] = "authoritative"
            except Exception:
                pass

        # Semantics: chatgpt backend reports used_percent
        raw_p_val = f"{primary_pct}% used" if primary_pct is not None else "N/A"
        raw_s_val = f"{secondary_pct}% used" if secondary_pct is not None else "N/A"
        rem_p_pct = 100 - primary_pct if primary_pct is not None else None
        rem_s_pct = 100 - secondary_pct if secondary_pct is not None else None

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return UsageData(
            provider_name="CODEX",
            primary_label="5H",
            primary_pct=primary_pct,
            primary_reset=primary_reset if primary_reset else "N/A",
            primary_status="ACTIVE" if primary_pct is not None and primary_pct > 0 else "READY",
            secondary_label="WEEK",
            secondary_pct=secondary_pct,
            secondary_reset=secondary_reset if secondary_reset else "N/A",
            model=active_model,
            plan_tier=plan_type,
            metrics_classification=classification,
            source_description="chatgpt.com/backend-api/codex/usage (via ~/.codex/auth.json)",
            raw_primary_value=raw_p_val,
            raw_primary_semantic="USED",
            normalized_primary_used=primary_pct,
            normalized_primary_remaining=rem_p_pct,
            raw_secondary_value=raw_s_val,
            raw_secondary_semantic="USED",
            normalized_secondary_used=secondary_pct,
            normalized_secondary_remaining=rem_s_pct,
            fetched_at=now_iso if fetch_success else None,
            authority="AUTHORITATIVE_ACCOUNT_DATA / UNOFFICIAL_INTERFACE",
            age_seconds=max(0.1, time.time() - fetch_start) if fetch_success else None,
        )

    def _format_seconds(self, sec: int) -> str:
        if sec < 0:
            return "READY"
        days = sec // 86400
        rem = sec % 86400
        hours = rem // 3600
        mins = (rem % 3600) // 60
        if days > 0:
            return f"{days}D {hours}H"
        if hours > 0:
            return f"{hours}H {mins}M"
        return f"{mins}M"

    def _format_model_name(self, raw_model: str) -> str:
        name = raw_model.upper()
        if "GPT-" in name:
            parts = name.split("-")
            if len(parts) >= 2:
                return f"{parts[0]}-{parts[1]}"
        return name[:10]


class GeminiProvider(BaseProvider):
    name = "GEMINI"
    _cache: Optional[Dict[str, Any]] = None
    _cache_time: float = 0.0

    @classmethod
    def _find_agy_binary(cls) -> Optional[str]:
        # 1. Search PATH
        p = shutil.which("agy")
        if p and os.path.exists(p):
            return p
        # 2. Local AppData standard install location
        local_app = os.environ.get("LOCALAPPDATA", "")
        p2 = os.path.join(local_app, "agy", "bin", "agy.exe")
        if os.path.exists(p2):
            return p2
        # 3. User profile fallback
        home = os.path.expanduser("~")
        p3 = os.path.join(home, "AppData", "Local", "agy", "bin", "agy.exe")
        if os.path.exists(p3):
            return p3
        return None

    def _fetch_agy_usage(self) -> Optional[Dict[str, Any]]:
        """Fetch live model quota status from Antigravity backend via 'agy -p /usage --output-format json'."""
        # 60-second cache prevents spawning agy.exe on every frame rotation
        now = time.time()
        if self._cache and (now - self._cache_time < 60.0):
            return self._cache

        agy_bin = self._find_agy_binary()
        if not agy_bin:
            return None

        if not hasattr(self.__class__, "_fetch_lock"):
            self.__class__._fetch_lock = threading.Lock()
        if not self.__class__._fetch_lock.acquire(blocking=False):
            return self._cache

        cmd = [agy_bin, "-p", "/usage", "--output-format", "json"]
        try:
            # 6.0s timeout ensures dashboard never hangs
            res = run_hidden(cmd, capture_output=True, text=True, timeout=6.0)
            if res.returncode == 0 and res.stdout:
                parsed = json.loads(res.stdout)
                self.__class__._cache = parsed
                self.__class__._cache_time = now
                return parsed
        except Exception:
            pass
        finally:
            self.__class__._fetch_lock.release()
        return None

    def get_usage(self) -> UsageData:
        home = os.path.expanduser("~")
        appdata = os.environ.get("APPDATA", "")
        vscdb_path = os.path.join(appdata, "Antigravity IDE", "User", "globalStorage", "state.vscdb")

        active_model = "GEMINI 3.8"
        plan_tier = "GOOGLE AI PRO"

        # Check authoritative plan and model from Antigravity IDE state database
        if os.path.exists(vscdb_path):
            try:
                conn = sqlite3.connect(f"file:{vscdb_path}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.userStatus'")
                row = cursor.fetchone()
                if row and row[0]:
                    raw = base64.b64decode(row[0])
                    text = raw.decode("latin1", errors="ignore")
                    if "Google AI Pro" in text or "g1-pro-tier" in text:
                        plan_tier = "GOOGLE AI PRO"
                    elif "Google AI Ultra" in text or "g1-ultra-tier" in text:
                        plan_tier = "GOOGLE AI ULTRA"

                    if "Gemini 3.8 Flash" in text:
                        active_model = "GEMINI 3.8"
                    elif "Gemini 3.1 Pro" in text:
                        active_model = "GEMINI 3.1"
                conn.close()
            except Exception:
                pass

        # Fetch live authoritative usage from Google's backend via Antigravity CLI
        agy_data = self._fetch_agy_usage()

        primary_pct = None
        primary_reset = "N/A"
        secondary_pct = None
        secondary_reset = "N/A"

        raw_primary_val = None
        raw_secondary_val = None
        rem_5h_pct = None
        used_5h_pct = None
        rem_wk_pct = None
        used_wk_pct = None

        is_live = False
        age_sec = None

        classification = {
            "primary_pct": "unavailable",
            "primary_reset": "unavailable",
            "secondary_pct": "unavailable",
            "secondary_reset": "unavailable",
            "model": "authoritative",
            "plan_tier": "authoritative",
        }

        if agy_data:
            cmd_data = agy_data.get("command", {}).get("data", {})
            groups = cmd_data.get("groups", [])
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            age_sec = max(0.1, time.time() - self._cache_time)

            for g in groups:
                if "gemini" in g.get("name", "").lower():
                    for b in g.get("buckets", []):
                        bid = b.get("id", "")
                        window = b.get("window", "")
                        rem_frac = b.get("remaining_fraction")
                        reset_time_str = b.get("reset_time")

                        # Parse reset timedelta string
                        reset_fmt = "N/A"
                        if reset_time_str:
                            try:
                                rdt = datetime.datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
                                sec_left = max(0, (rdt - now_utc).total_seconds())
                                days = int(sec_left // 86400)
                                hours = int((sec_left % 86400) // 3600)
                                mins = int((sec_left % 3600) // 60)
                                if days > 0:
                                    reset_fmt = f"{days}D {hours}H"
                                elif hours > 0:
                                    reset_fmt = f"{hours}H {mins}M"
                                else:
                                    reset_fmt = f"{mins}M"
                            except Exception:
                                pass

                        if "5h" in bid or "5h" in window:
                            if rem_frac is not None:
                                rem_5h_pct = int(round(rem_frac * 100))
                                used_5h_pct = max(0, 100 - rem_5h_pct)
                                primary_pct = used_5h_pct
                                raw_primary_val = f"{rem_5h_pct}% remaining"
                                primary_reset = reset_fmt
                                classification["primary_pct"] = "authoritative"
                                classification["primary_reset"] = "authoritative"
                                is_live = True

                        elif "weekly" in bid or "weekly" in window:
                            if rem_frac is not None:
                                rem_wk_pct = int(round(rem_frac * 100))
                                used_wk_pct = max(0, 100 - rem_wk_pct)
                                secondary_pct = used_wk_pct
                                raw_secondary_val = f"{rem_wk_pct}% remaining"
                                secondary_reset = reset_fmt
                                classification["secondary_pct"] = "authoritative"
                                classification["secondary_reset"] = "authoritative"
                                is_live = True

        status = "ACTIVE" if (is_live and primary_pct is not None and primary_pct > 0) else ("READY" if is_live else "LOCAL ONLY")
        source_str = "ANTIGRAVITY /usage — LIVE" if is_live else "Antigravity state.vscdb (quotas unavailable)"

        return UsageData(
            provider_name="GEMINI",
            primary_label="5H" if is_live else "USAGE",
            primary_pct=primary_pct,
            primary_reset=primary_reset,
            primary_status=status,
            secondary_label="WEEK",
            secondary_pct=secondary_pct,
            secondary_reset=secondary_reset,
            model=active_model,
            plan_tier=plan_tier,
            is_stale=not is_live,
            freshness="LIVE" if is_live else "LOCAL ONLY",
            metrics_classification=classification,
            source_description=source_str,
            raw_primary_value=raw_primary_val or "N/A",
            raw_primary_semantic="REMAINING" if is_live else "UNAVAILABLE",
            normalized_primary_used=used_5h_pct,
            normalized_primary_remaining=rem_5h_pct,
            raw_secondary_value=raw_secondary_val or "N/A",
            raw_secondary_semantic="REMAINING" if is_live else "UNAVAILABLE",
            normalized_secondary_used=used_wk_pct,
            normalized_secondary_remaining=rem_wk_pct,
            fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat() if is_live else None,
            authority="AUTHORITATIVE" if is_live else "UNAVAILABLE",
            age_seconds=age_sec,
        )


def get_provider(name: str) -> BaseProvider:
    key = name.strip().lower()
    if key in ("claude", "claude-code"):
        return ClaudeProvider()
    elif key in ("codex", "openai", "chatgpt"):
        return CodexProvider()
    elif key in ("gemini", "antigravity"):
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown provider '{name}'. Supported: claude, codex, gemini")

