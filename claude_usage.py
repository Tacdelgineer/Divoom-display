#!/usr/bin/env python3
"""
Claude Code local usage reader & account diagnostics.
Reads ~/.claude.json for authoritative Anthropic usage cache,
reads ~/.claude/.credentials.json for active authentication context,
and reads ~/.claude/projects/*/*.jsonl for local session details and model history.

Milestone 12 enhancements:
- Inspects active account identity (anonymized/masked email).
- Identifies plan tier and authentication type (Subscription vs API Key).
- Probes environment variables (ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, etc.) for precedence.
- Supports isolated local ClaudeAccountProfile instances for multi-account environments.
- Enforces strict 'XX% LEFT' remaining quota semantics.
"""
from __future__ import annotations

import datetime
import glob
import json
import os
from typing import Any, Dict, Optional, List

from models import ClaudeAccountProfile


def mask_account_identifier(ident: str | None) -> str:
    """Anonymize email or account UUID to protect user privacy (e.g. 'no***@gmail.com')."""
    if not ident:
        return "UNKNOWN"
    s = ident.strip()
    if "@" in s:
        user, domain = s.split("@", 1)
        prefix = user[:2] if len(user) >= 2 else user[:1]
        return f"{prefix}***@{domain}"
    elif len(s) > 8:
        return f"{s[:4]}...{s[-4:]}"
    return f"{s[:2]}***"


def get_claude_env_diagnostics() -> Dict[str, Any]:
    """
    Inspect whether environment variables are overriding Claude Code authentication.
    Reports presence and precedence without disclosing sensitive token values.
    """
    env_keys = [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
    ]
    diag = {}
    for k in env_keys:
        diag[k] = "PRESENT" if k in os.environ and bool(os.environ[k].strip()) else "ABSENT"

    # Precedence analysis
    has_api_key = diag["ANTHROPIC_API_KEY"] == "PRESENT"
    has_oauth_token = diag["CLAUDE_CODE_OAUTH_TOKEN"] == "PRESENT"
    has_cloud = any(diag[c] == "PRESENT" for c in ["CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"])

    if has_api_key:
        active_auth = "API Key (Overridden via ANTHROPIC_API_KEY)"
        precedence = "ENV_VAR_OVERRIDE"
    elif has_oauth_token:
        active_auth = "OAuth Token (Overridden via CLAUDE_CODE_OAUTH_TOKEN)"
        precedence = "ENV_VAR_OVERRIDE"
    elif has_cloud:
        active_auth = "Cloud Bedrock/Vertex/Foundry"
        precedence = "ENV_VAR_OVERRIDE"
    else:
        active_auth = "Subscription (OAuth from local ~/.claude/.credentials.json)"
        precedence = "LOCAL_SUBSCRIPTION_ACTIVE"

    return {
        "variables": diag,
        "active_auth_type": active_auth,
        "precedence": precedence,
    }


def parse_iso(ts_str: str | None) -> datetime.datetime | None:
    if not ts_str:
        return None
    try:
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


def read_claude_account_profile(
    config_dir: Optional[str] = None,
    user_label: str = "Personal",
    profile_id: str = "personal",
    is_active: bool = True,
) -> ClaudeAccountProfile:
    """
    Read an isolated Claude Code configuration directory into a ClaudeAccountProfile.
    Does not copy secrets or modify another session.
    """
    home = os.path.expanduser("~")
    dir_path = config_dir or os.path.join(home, ".claude")

    # Locate .claude.json: either in directory itself or parent user directory
    claude_json_candidates = [
        os.path.join(dir_path, ".claude.json"),
        os.path.join(os.path.dirname(dir_path), ".claude.json") if dir_path.endswith((".claude", ".claude-secondary")) else os.path.join(home, ".claude.json"),
    ]
    claude_json_path = None
    for c in claude_json_candidates:
        if os.path.exists(c):
            claude_json_path = c
            break

    credentials_path = os.path.join(dir_path, ".credentials.json")

    masked_email = "Not Configured"
    plan_tier = "Pro"
    auth_type = "Subscription"
    status_text = "READY"
    usage_available = False
    authority = "UNAVAILABLE"

    # 1. Inspect credentials if present
    if os.path.exists(credentials_path):
        try:
            with open(credentials_path, "r", encoding="utf-8") as f:
                cred = json.load(f)
                oauth = cred.get("claudeAiOauth", {})
                if oauth:
                    stype = oauth.get("subscriptionType", "pro").upper()
                    plan_tier = f"Claude {stype.capitalize()}"
                    auth_type = "Subscription (OAuth)"
                    status_text = "AUTHENTICATED"
        except Exception:
            pass

    # 2. Inspect ~/.claude.json for account identity and usage cache
    five_hour_used: Optional[float] = None
    five_hour_rem: Optional[float] = None
    five_hour_reset_str: Optional[str] = None
    week_used: Optional[float] = None
    week_rem: Optional[float] = None
    week_reset_str: Optional[str] = None
    fetched_at_str: Optional[str] = None

    now_utc = datetime.datetime.now(datetime.timezone.utc)

    if claude_json_path and os.path.exists(claude_json_path):
        try:
            with open(claude_json_path, "r", encoding="utf-8", errors="ignore") as f:
                cdata = json.load(f)
                oauth_acc = cdata.get("oauthAccount", {})
                raw_email = oauth_acc.get("emailAddress")
                if raw_email:
                    masked_email = mask_account_identifier(raw_email)
                    status_text = "ACTIVE" if is_active else "CONFIGURED"

                org_type = oauth_acc.get("organizationType", "claude_pro")
                if "pro" in org_type.lower():
                    plan_tier = "Claude Pro"
                elif "team" in org_type.lower():
                    plan_tier = "Claude Team"
                elif "enterprise" in org_type.lower():
                    plan_tier = "Claude Enterprise"

                cached_util = cdata.get("cachedUsageUtilization", {})
                if cached_util:
                    fms = cached_util.get("fetchedAtMs")
                    if fms:
                        fdt = datetime.datetime.fromtimestamp(fms / 1000, tz=datetime.timezone.utc)
                        fetched_at_str = fdt.isoformat()
                        age_days = (now_utc - fdt).total_seconds() / 86400.0
                        if age_days < 1.0:
                            usage_available = True
                            authority = "AUTHORITATIVE"
                        else:
                            usage_available = False
                            authority = "STALE_CACHE"

                    u = cached_util.get("utilization", {})
                    fh = u.get("five_hour") or {}
                    if fh.get("utilization") is not None:
                        five_hour_used = float(fh["utilization"])
                        five_hour_rem = max(0.0, 100.0 - five_hour_used)
                        fh_res = parse_iso(fh.get("resets_at"))
                        if fh_res:
                            five_hour_reset_str = format_timedelta(fh_res - now_utc)

                    sd = u.get("seven_day") or {}
                    if sd.get("utilization") is not None:
                        week_used = float(sd["utilization"])
                        week_rem = max(0.0, 100.0 - week_used)
                        sd_res = parse_iso(sd.get("resets_at"))
                        if sd_res:
                            week_reset_str = format_timedelta(sd_res - now_utc)
        except Exception:
            pass

    # If directory doesn't exist, report pending setup
    if not os.path.exists(dir_path) and profile_id != "personal":
        status_text = "NOT_CONFIGURED"
        masked_email = "None (Setup Pending)"

    return ClaudeAccountProfile(
        id=profile_id,
        user_label=user_label,
        account_identity_masked=masked_email,
        plan=plan_tier,
        auth_type=auth_type,
        status_text=status_text,
        five_hour_used_pct=five_hour_used,
        five_hour_remaining_pct=five_hour_rem,
        five_hour_reset=five_hour_reset_str,
        weekly_used_pct=week_used,
        weekly_remaining_pct=week_rem,
        weekly_reset=week_reset_str,
        authority=authority,
        usage_available=usage_available,
        is_active=is_active,
        fetched_at=fetched_at_str,
        config_dir=dir_path,
    )


def read_claude_usage(user_home: str | None = None) -> dict[str, Any]:
    """
    Read Claude Code usage and active account profile.
    Returns structured dictionary with strict remaining_pct quota semantics.
    """
    home = user_home or os.path.expanduser("~")
    projects_dir = os.path.join(home, ".claude", "projects")

    # Read active account profile
    active_profile = read_claude_account_profile(
        config_dir=os.path.join(home, ".claude"),
        user_label="Personal",
        profile_id="personal",
        is_active=True,
    )

    env_diag = get_claude_env_diagnostics()

    # Model and session log reading
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    latest_msg_time = None
    latest_model = "Sonnet"
    jsonl_files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    for file_path in jsonl_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"model":' not in line:
                        continue
                    try:
                        record = json.loads(line)
                        msg = record.get("message")
                        if isinstance(msg, dict):
                            model = msg.get("model")
                            ts = parse_iso(record.get("timestamp"))
                            if ts and (latest_msg_time is None or ts > latest_msg_time):
                                latest_msg_time = ts
                                if model:
                                    latest_model = model
                    except Exception:
                        pass
        except Exception:
            pass

    clean_model = "CLAUDE"
    if "opus" in latest_model.lower():
        clean_model = "OPUS 5" if "5" in latest_model else "OPUS"
    elif "sonnet" in latest_model.lower():
        clean_model = "SONNET 4.5" if "4-5" in latest_model or "4.5" in latest_model else "SONNET"
    elif "haiku" in latest_model.lower():
        clean_model = "HAIKU"

    return {
        "account_profile": active_profile,
        "env_diagnostics": env_diag,
        "masked_account": active_profile.account_identity_masked,
        "plan_tier": active_profile.plan,
        "auth_type": active_profile.auth_type,
        "five_hour_used_pct": active_profile.five_hour_used_pct,
        "five_hour_remaining_pct": active_profile.five_hour_remaining_pct,
        "five_hour_reset_str": active_profile.five_hour_reset or "N/A",
        "week_used_pct": active_profile.weekly_used_pct,
        "week_remaining_pct": active_profile.weekly_remaining_pct,
        "week_reset_str": active_profile.weekly_reset or "N/A",
        "model_name": clean_model,
        "raw_model": latest_model,
        "is_live": active_profile.usage_available,
        "is_stale": active_profile.authority == "STALE_CACHE",
        "authority": active_profile.authority,
        "fetched_at": active_profile.fetched_at,
    }


if __name__ == "__main__":
    data = read_claude_usage()
    print("=== Active Claude Account & Usage ===")
    print(f"Account: {data['masked_account']}")
    print(f"Plan:    {data['plan_tier']}")
    print(f"Auth:    {data['auth_type']}")
    print(f"Model:   {data['model_name']}")
    print(f"5-Hour:  {data['five_hour_remaining_pct']}% LEFT (Used: {data['five_hour_used_pct']}%)")
    print(f"Weekly:  {data['week_remaining_pct']}% LEFT (Used: {data['week_used_pct']}%)")
    print(f"Authority: {data['authority']}")
    print("\n=== Environment Diagnostics ===")
    for k, v in data["env_diagnostics"]["variables"].items():
        print(f"  {k:<28}: {v}")
    print(f"Precedence: {data['env_diagnostics']['precedence']}")
