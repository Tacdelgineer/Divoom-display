#!/usr/bin/env python3
"""
Data collectors for AI Desk Dashboard:
1. LocalPcCollector - Local GPU (NVIDIA NVML/smi), CPU, RAM, VRAM, and temperature
2. DgxSparkCollector - Remote DGX Spark host with non-blocking SSH and offline cache
3. CodingStatusCollector - Git repository, branch, clean/dirty state, and active AI model
4. ProviderAdapter - Adapts AI provider data (Claude, Codex, Gemini) to normalized PageData
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from typing import Optional, Dict, Any

from models import MetricItem, PageData
from providers import get_provider, UsageData
from subproc import check_output_hidden, run_hidden


# ==============================================================================
# 1. LOCAL PC COLLECTOR
# ==============================================================================
class LocalPcCollector:
    """Collects authoritative metrics from local workstation: GPU, CPU, RAM."""

    _gpu_lock = threading.Lock()

    @staticmethod
    def _get_gpu_info() -> Dict[str, Any]:
        """Query NVIDIA GPU using nvidia-smi for authoritative metrics."""
        result = {
            "name": None,
            "util_pct": None,
            "temp_c": None,
            "vram_used_mb": None,
            "vram_total_mb": None,
            "available": False,
        }
        if not shutil.which("nvidia-smi"):
            return result

        cmd = [
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        if not LocalPcCollector._gpu_lock.acquire(blocking=False):
            return result
        try:
            out = check_output_hidden(cmd, text=True, timeout=2.0).strip()
            if out:
                parts = [p.strip() for p in out.split(",")]
                if len(parts) >= 5:
                    result["name"] = parts[0]
                    # Clean up GPU name for compact 128x128 footer
                    for prefix in ("NVIDIA GeForce ", "NVIDIA ", "GeForce "):
                        if result["name"].startswith(prefix):
                            result["name"] = result["name"][len(prefix):]
                    try:
                        result["util_pct"] = float(parts[1])
                    except ValueError:
                        pass
                    try:
                        result["temp_c"] = int(parts[2])
                    except ValueError:
                        pass
                    try:
                        result["vram_used_mb"] = float(parts[3])
                        result["vram_total_mb"] = float(parts[4])
                    except ValueError:
                        pass
                    result["available"] = True
        except Exception:
            pass
        finally:
            LocalPcCollector._gpu_lock.release()
        return result

    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """Query CPU and RAM utilization using psutil."""
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0.1)
            vmem = psutil.virtual_memory()
            return {
                "cpu_pct": cpu_pct,
                "ram_pct": vmem.percent,
                "ram_used_gb": vmem.used / (1024 ** 3),
                "ram_total_gb": vmem.total / (1024 ** 3),
            }
        except Exception:
            return {"cpu_pct": None, "ram_pct": None, "ram_used_gb": None, "ram_total_gb": None}

    def collect(self) -> PageData:
        gpu = self._get_gpu_info()
        sys_info = self._get_system_info()

        # Build GPU metric
        if gpu["util_pct"] is not None:
            gpu_val = f"{int(round(gpu['util_pct']))}%"
            gpu_pct = gpu["util_pct"]
            gpu_auth = "AUTHORITATIVE"
        else:
            gpu_val = "N/A"
            gpu_pct = None
            gpu_auth = "UNAVAILABLE"

        temp_str = f"{gpu['temp_c']}C" if gpu["temp_c"] is not None else "N/A"
        if gpu["vram_used_mb"] is not None:
            vram_str = f"{gpu['vram_used_mb']/1024:.1f}G"
        else:
            vram_str = "N/A"

        # Build RAM metric
        if sys_info["ram_pct"] is not None:
            ram_val = f"{int(round(sys_info['ram_pct']))}%"
            ram_pct = sys_info["ram_pct"]
            ram_auth = "AUTHORITATIVE"
        else:
            ram_val = "N/A"
            ram_pct = None
            ram_auth = "UNAVAILABLE"

        # Build CPU metric
        if sys_info["cpu_pct"] is not None:
            cpu_val = f"{int(round(sys_info['cpu_pct']))}%"
            cpu_pct = sys_info["cpu_pct"]
            cpu_auth = "AUTHORITATIVE"
        else:
            cpu_val = "N/A"
            cpu_pct = None
            cpu_auth = "UNAVAILABLE"

        gpu_name = gpu["name"] or "LOCAL PC"
        tot_vram = f"{gpu['vram_total_mb']/1024:.0f}G" if gpu["vram_total_mb"] else ""

        provenance = {
            "GPU": f"nvidia-smi ({gpu_auth})",
            "TEMP": f"nvidia-smi ({gpu_auth})",
            "VRAM": f"nvidia-smi ({gpu_auth})",
            "RAM": f"psutil ({ram_auth})",
            "CPU": f"psutil ({cpu_auth})",
        }

        # PageData layout:
        # primary: GPU (pct, reset=TEMP/VRAM info)
        # secondary: RAM (pct)
        # extra: CPU (pct)
        return PageData(
            page_id="local_pc",
            title="LOCAL PC",
            badge="ONLINE",
            badge_color="green",
            primary_metric=MetricItem(
                label="GPU",
                value=gpu_val,
                pct=gpu_pct,
                reset=f"TEMP {temp_str}  VRAM {vram_str}",
                authority=gpu_auth,
            ),
            secondary_metric=MetricItem(
                label="RAM",
                value=ram_val,
                pct=ram_pct,
                reset=f"USED {sys_info['ram_used_gb']:.1f}G" if sys_info["ram_used_gb"] else None,
                authority=ram_auth,
            ),
            extra_metrics=[
                MetricItem(
                    label="CPU",
                    value=cpu_val,
                    pct=cpu_pct,
                    reset=f"{cpu_val}",
                    authority=cpu_auth,
                )
            ],
            footer_left=gpu_name,
            footer_right=tot_vram,
            source_info="nvidia-smi + psutil",
            metrics_provenance=provenance,
        )


# ==============================================================================
# 2. DGX SPARK COLLECTOR (REMOTE WITH SHORT TIMEOUT & OFFLINE CACHE)
# ==============================================================================
class DgxSparkCollector:
    """
    Connects to remote DGX Spark machine over SSH/Tailscale.
    Strict 3.0s timeout ensures dashboard rotation NEVER stalls or blocks.
    Saves last-seen timestamps and metrics to local cache file.
    """

    _ssh_lock = threading.Lock()

    def __init__(self, host: str = "dgx", cache_file: str = ".dgx_cache.json"):
        self.host = host
        self.cache_file = cache_file

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _write_cache(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def _format_time_ago(seconds_ago: float) -> str:
        if seconds_ago < 60:
            return "JUST NOW"
        minutes = int(seconds_ago // 60)
        if minutes < 60:
            return f"{minutes}M AGO"
        hours = int(minutes // 60)
        if hours < 24:
            return f"{hours}H AGO"
        days = int(hours // 24)
        return f"{days}D AGO"

    def collect(self) -> PageData:
        # Lightweight remote probe script
        remote_script = (
            "python3 -c \""
            "import subprocess, os, json\n"
            "try:\n"
            "    smi = subprocess.check_output(['nvidia-smi', '--query-gpu=name,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], text=True).strip()\n"
            "    gname, gutil, gtemp = [x.strip() for x in smi.split(',')[:3]]\n"
            "except Exception:\n"
            "    gname, gutil, gtemp = 'GB10', 'N/A', 'N/A'\n"
            "try:\n"
            "    mem = {}\n"
            "    for l in open('/proc/meminfo'):\n"
            "        if ':' in l:\n"
            "            p = l.split(':')\n"
            "            mem[p[0].strip()] = int(p[1].strip().split()[0])\n"
            "    tot = mem.get('MemTotal', 0) // 1024\n"
            "    av = mem.get('MemAvailable', 0) // 1024\n"
            "    used = tot - av\n"
            "    rpct = int(round(used / tot * 100)) if tot else 0\n"
            "    mem_str = f'{used/1024:.1f}/{tot/1024:.0f}G'\n"
            "except Exception:\n"
            "    rpct, mem_str = 'N/A', 'N/A'\n"
            "try:\n"
            "    l1, _, _ = os.getloadavg()\n"
            "    up = float(open('/proc/uptime').read().split()[0])\n"
            "    uph = int(up // 3600)\n"
            "    upm = int((up % 3600) // 60)\n"
            "    up_s = f'{uph}h {upm}m' if uph else f'{upm}m'\n"
            "except Exception:\n"
            "    l1, up_s = 'N/A', 'N/A'\n"
            "print(json.dumps({'gpu': gname, 'gpu_util': gutil, 'gpu_temp': gtemp, 'ram_pct': rpct, 'ram_str': mem_str, 'load': l1, 'uptime': up_s}))\n"
            "\""
        )
        cmd = [
            "ssh",
            "-o", "ConnectTimeout=2",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            self.host,
            remote_script,
        ]

        live_data = None
        if not self._ssh_lock.acquire(blocking=False):
            # Previous SSH query is still active; fall back to cache
            cached = self._read_cache()
            return self._build_offline_page(cached) if cached else self._build_offline_page(None)

        try:
            # 3-second hard timeout ensures non-blocking operation
            res = run_hidden(cmd, capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0:
                out = res.stdout.strip()
                if out:
                    live_data = json.loads(out)
        except Exception:
            live_data = None
        finally:
            self._ssh_lock.release()

        # -------------------------------------------------------------
        # ONLINE PATH
        # -------------------------------------------------------------
        if live_data:
            live_data["timestamp"] = time.time()
            self._write_cache(live_data)

            gpu_name = live_data.get("gpu", "NVIDIA GB10")
            for pfx in ("NVIDIA ", "GeForce "):
                if gpu_name.startswith(pfx):
                    gpu_name = gpu_name[len(pfx):]

            try:
                gpu_util_pct = float(live_data["gpu_util"])
                gpu_val = f"{int(round(gpu_util_pct))}%"
            except (ValueError, TypeError):
                gpu_util_pct = None
                gpu_val = "N/A"

            gpu_temp = live_data.get("gpu_temp", "N/A")
            temp_str = f"{gpu_temp}C" if gpu_temp != "N/A" else "N/A"

            try:
                ram_pct = float(live_data["ram_pct"])
                ram_val = f"{int(round(ram_pct))}%"
            except (ValueError, TypeError):
                ram_pct = None
                ram_val = "N/A"

            ram_str = live_data.get("ram_str", "N/A")
            load_val = live_data.get("load")
            load_str = f"{load_val:.2f}" if isinstance(load_val, (int, float)) else "N/A"
            uptime_str = live_data.get("uptime", "N/A")

            return PageData(
                page_id="dgx_spark",
                title="DGX SPARK",
                badge="ONLINE",
                badge_color="green",
                is_offline=False,
                primary_metric=MetricItem(
                    label="GPU",
                    value=gpu_val,
                    pct=gpu_util_pct,
                    reset=f"TEMP {temp_str}  LOAD {load_str}",
                    authority="AUTHORITATIVE",
                ),
                secondary_metric=MetricItem(
                    label="RAM",
                    value=ram_val,
                    pct=ram_pct,
                    reset=f"MEM {ram_str}  UP {uptime_str}",
                    authority="AUTHORITATIVE",
                ),
                footer_left=gpu_name,
                footer_right="SPARK",
                source_info=f"ssh://{self.host} (live)",
                metrics_provenance={
                    "GPU": "remote nvidia-smi (AUTHORITATIVE)",
                    "TEMP": "remote nvidia-smi (AUTHORITATIVE)",
                    "RAM": "remote /proc/meminfo (AUTHORITATIVE)",
                    "LOAD": "remote os.getloadavg (AUTHORITATIVE)",
                    "UPTIME": "remote /proc/uptime (AUTHORITATIVE)",
                },
            )

        # -------------------------------------------------------------
        # OFFLINE PATH
        # -------------------------------------------------------------
        cache = self._read_cache()
        if cache and "timestamp" in cache:
            elapsed = time.time() - cache["timestamp"]
            last_seen_str = self._format_time_ago(elapsed)
            last_gpu = cache.get("gpu_util", "N/A")
            last_msg = f"LAST: {last_gpu}% GPU" if last_gpu != "N/A" else "OFFLINE"
        else:
            last_seen_str = "NEVER"
            last_msg = "OFFLINE"

        return PageData(
            page_id="dgx_spark",
            title="DGX SPARK",
            badge="OFFLINE",
            badge_color="red",
            is_offline=True,
            offline_msg="OFFLINE",
            offline_sub=last_seen_str,
            footer_left=f"HOST: {self.host}",
            footer_right="OFFLINE",
            source_info=f"ssh://{self.host} (unreachable; cached {last_seen_str})",
            metrics_provenance={
                "status": "OFFLINE (UNAVAILABLE)",
                "last_seen": f"{last_seen_str} (STALE_CACHE)",
            },
        )


# ==============================================================================
# 3. CODING STATUS COLLECTOR
# ==============================================================================
class CodingStatusCollector:
    """Collects Git status (repo, branch, clean/dirty) and active AI model."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _get_git_info(self) -> Dict[str, Any]:
        info = {
            "repo": None,
            "branch": None,
            "state": "N/A",
            "is_clean": True,
            "is_git": False,
        }
        if not shutil.which("git"):
            return info

        if not hasattr(self, "_git_lock"):
            self._git_lock = threading.Lock()
        if not self._git_lock.acquire(blocking=False):
            return info

        try:
            # Get repository top-level directory
            top = check_output_hidden(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.repo_path,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if top:
                info["repo"] = os.path.basename(os.path.normpath(top))
                info["is_git"] = True
        except Exception:
            # Fallback to directory name
            info["repo"] = os.path.basename(os.path.abspath(self.repo_path))

        if info["is_git"]:
            try:
                # Branch
                branch = check_output_hidden(
                    ["git", "branch", "--show-current"],
                    cwd=self.repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
                info["branch"] = branch or "HEAD"
            except Exception:
                info["branch"] = "main"

            try:
                # Working tree state
                status = check_output_hidden(
                    ["git", "status", "--porcelain"],
                    cwd=self.repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
                if status:
                    lines = status.splitlines()
                    info["state"] = f"DIRTY ({len(lines)})"
                    info["is_clean"] = False
                else:
                    info["state"] = "CLEAN"
                    info["is_clean"] = True
            except Exception:
                info["state"] = "UNKNOWN"
        else:
            info["branch"] = "LOCAL"
            info["state"] = "NO GIT"

        self._git_lock.release()
        return info

    @staticmethod
    def _detect_active_ai_model() -> str:
        """Detect current active AI model across Codex, Claude, and Gemini."""
        # Check Codex first (authoritative live session)
        try:
            codex_prov = get_provider("codex")
            codex_data = codex_prov.get_usage()
            if codex_data.model:
                return codex_data.model
        except Exception:
            pass

        # Check Claude
        try:
            claude_prov = get_provider("claude")
            claude_data = claude_prov.get_usage()
            if claude_data.model:
                return claude_data.model
        except Exception:
            pass

        # Check Gemini
        try:
            gemini_prov = get_provider("gemini")
            gemini_data = gemini_prov.get_usage()
            if gemini_data.model:
                return gemini_data.model
        except Exception:
            pass

        return "GPT-5.6"

    def collect(self) -> PageData:
        git_info = self._get_git_info()
        model_name = self._detect_active_ai_model()

        repo_name = git_info["repo"] or "hedgefly"
        branch_name = git_info["branch"] or "main"
        state_label = git_info["state"]
        badge_text = "CLEAN" if git_info["is_clean"] else "DIRTY"
        badge_color = "green" if git_info["is_clean"] else "amber"

        provenance = {
            "REPO": f"git ({'AUTHORITATIVE' if git_info['is_git'] else 'CALCULATED'})",
            "BRANCH": f"git ({'AUTHORITATIVE' if git_info['is_git'] else 'UNAVAILABLE'})",
            "STATE": f"git ({'AUTHORITATIVE' if git_info['is_git'] else 'UNAVAILABLE'})",
            "MODEL": f"active provider session (AUTHORITATIVE)",
        }

        return PageData(
            page_id="coding",
            title="CODING",
            badge=badge_text,
            badge_color=badge_color,
            primary_metric=MetricItem(
                label="REPO",
                value=repo_name,
                authority="AUTHORITATIVE" if git_info["is_git"] else "CALCULATED",
            ),
            secondary_metric=MetricItem(
                label="BRANCH",
                value=branch_name,
                reset=state_label,
                authority="AUTHORITATIVE" if git_info["is_git"] else "UNAVAILABLE",
            ),
            extra_metrics=[
                MetricItem(
                    label="MODEL",
                    value=model_name,
                    authority="AUTHORITATIVE",
                )
            ],
            footer_left=repo_name,
            footer_right=model_name,
            source_info=f"git in {os.path.abspath(self.repo_path)}",
            metrics_provenance=provenance,
        )


# ==============================================================================
# 4. PROVIDER ADAPTER (CONVERTS UsageData TO NORMALIZED PageData)
# ==============================================================================
def provider_to_page_data(data: UsageData) -> PageData:
    """Adapts existing UsageData from providers.py to the unified PageData model."""
    p_name = data.provider_name.upper()

    if data.provider_name.lower() == "claude":
        badge_color = "gray"
        badge = "READY"
    elif data.provider_name.lower() == "gemini":
        if data.freshness == "LIVE":
            badge_color = "green"
            badge = "ACTIVE" if (data.primary_pct is not None and data.primary_pct > 0) else "READY"
        else:
            badge_color = "blue"
            badge = "LOCAL ONLY"
    elif data.is_stale:
        badge_color = "amber"
        badge = "STALE"
    elif data.primary_status == "ACTIVE":
        badge_color = "green"
        badge = "ACTIVE"
    else:
        badge_color = "gray"
        badge = data.primary_status or "READY"

    # UI defaults to remaining_pct per Milestone 8 Section 3
    # Codex: remaining = 100 - used_percent
    # Gemini: remaining = remaining_fraction * 100
    # Claude: if unavailable -> N/A (never calculate from N/A)
    p_rem = data.normalized_primary_remaining
    p_used = data.normalized_primary_used
    s_rem = data.normalized_secondary_remaining
    s_used = data.normalized_secondary_used

    if p_rem is not None:
        p_val_str = f"{p_rem}% LEFT"
        p_pct = float(p_rem)
    else:
        p_val_str = "N/A"
        p_pct = None

    if s_rem is not None:
        s_val_str = f"{s_rem}% LEFT"
        s_pct = float(s_rem)
    else:
        s_val_str = "N/A"
        s_pct = None

    primary_item = MetricItem(
        label=data.primary_label,
        value=p_val_str,
        pct=p_pct,
        reset=f"RESET  {data.primary_reset or 'N/A'}",
        authority=data.metrics_classification.get("primary_pct", "AUTHORITATIVE"),
        used_pct=float(p_used) if p_used is not None else None,
        remaining_pct=float(p_rem) if p_rem is not None else None,
    )
    secondary_item = MetricItem(
        label=data.secondary_label,
        value=s_val_str,
        pct=s_pct,
        reset=f"RESET  {data.secondary_reset or 'N/A'}",
        authority=data.metrics_classification.get("secondary_pct", "AUTHORITATIVE"),
        used_pct=float(s_used) if s_used is not None else None,
        remaining_pct=float(s_rem) if s_rem is not None else None,
    )

    quota_debug_info = {
        "provider": data.provider_name,
        "raw_primary": data.raw_primary_value,
        "raw_primary_semantic": data.raw_primary_semantic,
        "normalized_used": data.normalized_primary_used,
        "normalized_remaining": data.normalized_primary_remaining,
        "raw_secondary": data.raw_secondary_value,
        "raw_secondary_semantic": data.raw_secondary_semantic,
        "normalized_secondary_used": data.normalized_secondary_used,
        "normalized_secondary_remaining": data.normalized_secondary_remaining,
        "source": data.source_description,
        "authority": data.authority,
        "fetched_at": data.fetched_at,
        "age_seconds": data.age_seconds,
    }

    return PageData(
        page_id=data.provider_name.lower(),
        title=p_name,
        badge=badge,
        badge_color=badge_color,
        primary_metric=primary_item,
        secondary_metric=secondary_item,
        footer_left=badge,
        footer_right=data.model or p_name,
        source_info=getattr(data, "source_description", ""),
        metrics_provenance=data.metrics_classification,
        quota_debug=quota_debug_info,
    )


# ==============================================================================
# 5. BTC COLLECTOR (LIVE PRICE + 24H HOURLY SPARKLINE)
# ==============================================================================
class BtcCollector:
    """Collects live BTC market data (price, 24h change, 24h high/low, and 24h hourly sparkline)."""

    def __init__(self, cache_file: str = ".btc_cache.json"):
        self.cache_file = cache_file

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _write_cache(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def collect(self) -> PageData:
        cache = self._read_cache()
        now = time.time()
        # 60s cache TTL ensures dashboard does not hammer public APIs on every cycle
        if cache and (now - cache.get("timestamp", 0) < 60.0):
            return self._build_page(cache, is_live=True)

        import urllib.request
        live_data = None
        try:
            # 1. Query Kraken Ticker
            req_t = urllib.request.Request(
                "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
                headers={"User-Agent": "MiniToo-Dashboard/1.0"}
            )
            with urllib.request.urlopen(req_t, timeout=2.5) as resp:
                t_json = json.loads(resp.read().decode("utf-8"))
                p_key = list(t_json.get("result", {}).keys())[0]
                t_res = t_json["result"][p_key]
                price = float(t_res["c"][0])
                open_price = float(t_res["o"])
                high = float(t_res["h"][1])
                low = float(t_res["l"][1])
                change_pct = ((price - open_price) / open_price) * 100.0

            # 2. Query 24H Hourly OHLC for sparkline
            req_o = urllib.request.Request(
                "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60",
                headers={"User-Agent": "MiniToo-Dashboard/1.0"}
            )
            with urllib.request.urlopen(req_o, timeout=2.5) as resp:
                o_json = json.loads(resp.read().decode("utf-8"))
                p_key_ohlc = [k for k in o_json.get("result", {}).keys() if k != "last"][0]
                candles = o_json["result"][p_key_ohlc][-24:]
                closes = [float(c[4]) for c in candles]

            live_data = {
                "price": price,
                "change_pct": change_pct,
                "high": high,
                "low": low,
                "closes": closes,
                "timestamp": now,
            }
            self._write_cache(live_data)
            return self._build_page(live_data, is_live=True)
        except Exception:
            # Fallback to local cache if network failed
            if cache and "price" in cache:
                return self._build_page(cache, is_live=False)
            # Full offline fallback
            return PageData(
                page_id="btc",
                title="BTC",
                badge="OFFLINE",
                badge_color="red",
                is_offline=True,
                offline_msg="BTC DATA OFFLINE",
                offline_sub="UNAVAILABLE",
                source_info="Kraken public API (unreachable)",
            )

    def _build_page(self, data: Dict[str, Any], is_live: bool) -> PageData:
        price = data["price"]
        change = data["change_pct"]
        high = data["high"]
        low = data["low"]
        closes = data.get("closes", [])

        chg_sign = "+" if change >= 0 else ""
        chg_str = f"{chg_sign}{change:.1f}%"
        badge_color = "green" if change >= 0 else "red"

        # Format high and low (e.g. 85.2K)
        h_str = f"{high/1000:.1f}K" if high >= 1000 else f"${high:.0f}"
        l_str = f"{low/1000:.1f}K" if low >= 1000 else f"${low:.0f}"

        if not is_live:
            elapsed = time.time() - data.get("timestamp", 0)
            age_str = DgxSparkCollector._format_time_ago(elapsed)
            return PageData(
                page_id="btc",
                title="BTC",
                badge="OFFLINE",
                badge_color="red",
                is_offline=True,
                offline_msg="BTC DATA OFFLINE",
                offline_sub=f"LAST: ${price:,.0f} ({age_str})",
                source_info=f"Kraken cache ({age_str})",
            )

        return PageData(
            page_id="btc",
            title="BTC",
            badge=chg_str,
            badge_color=badge_color,
            primary_metric=MetricItem(
                label="PRICE",
                value=f"${price:,.0f}",
                reset=chg_str,
                authority="AUTHORITATIVE",
            ),
            sparkline_data=closes,
            sparkline_change=chg_str,
            sparkline_high=h_str,
            sparkline_low=l_str,
            footer_left="BITCOIN",
            footer_right="SPOT",
            source_info="https://api.kraken.com/0/public/Ticker + OHLC",
        )


# ==============================================================================
# 6. AI ACTIVITY COLLECTOR (HONEST LOCAL WORKING VS IDLE DETECTION)
# ==============================================================================
class AiActivityCollector:
    """Collects real-time local activity status (WORKING vs IDLE) for AI coding agents."""

    def collect(self) -> PageData:
        home = os.path.expanduser("~")
        now = time.time()

        # 1. CODEX DETECTION
        codex_proc = False
        codex_active = False
        codex_elapsed_str = ""
        try:
            import psutil
            for p in psutil.process_iter(['name', 'create_time']):
                if "codex.exe" in p.info['name'].lower():
                    codex_proc = True
                    el = now - p.info['create_time']
                    mins = int(el // 60)
                    hrs = int(mins // 60)
                    codex_elapsed_str = f"{hrs}H {mins % 60}M" if hrs > 0 else f"{mins}M"
                    break
        except Exception:
            pass

        if codex_proc:
            # Check recent session and db write activity (within last 180s)
            codex_wal = os.path.join(home, ".codex", "codex-dev.db-wal")
            codex_logs = os.path.join(home, ".codex", "logs_2.sqlite-wal")
            codex_state = os.path.join(home, ".codex", ".codex-global-state.json")
            for f in (codex_wal, codex_logs, codex_state):
                if os.path.exists(f):
                    try:
                        if now - os.path.getmtime(f) < 180:
                            codex_active = True
                            break
                    except Exception:
                        pass

        codex_status = "WORKING" if codex_active else "IDLE"

        # 2. CLAUDE DETECTION
        claude_proc = False
        claude_active = False
        claude_elapsed_str = ""
        try:
            import psutil
            for p in psutil.process_iter(['name', 'create_time']):
                if "claude.exe" in p.info['name'].lower():
                    claude_proc = True
                    el = now - p.info['create_time']
                    mins = int(el // 60)
                    hrs = int(mins // 60)
                    claude_elapsed_str = f"{hrs}H {mins % 60}M" if hrs > 0 else f"{mins}M"
                    break
        except Exception:
            pass

        if claude_proc:
            import glob
            p_files = glob.glob(os.path.join(home, ".claude", "projects", "*", "*.jsonl"))
            for pf in p_files:
                try:
                    if now - os.path.getmtime(pf) < 180:
                        claude_active = True
                        break
                except Exception:
                    pass

        claude_status = "WORKING" if claude_active else "IDLE"

        # 3. GEMINI / ANTIGRAVITY DETECTION
        gemini_proc = False
        gemini_active = False
        gemini_elapsed_str = ""
        try:
            import psutil
            for p in psutil.process_iter(['name', 'create_time']):
                if "antigravity ide.exe" in p.info['name'].lower():
                    gemini_proc = True
                    el = now - p.info['create_time']
                    mins = int(el // 60)
                    hrs = int(mins // 60)
                    gemini_elapsed_str = f"{hrs}H {mins % 60}M" if hrs > 0 else f"{mins}M"
                    break
        except Exception:
            pass

        if gemini_proc:
            brain_p = os.path.join(home, ".gemini", "antigravity-ide", "brain")
            if os.path.exists(brain_p):
                try:
                    for root, dirs, files in os.walk(brain_p):
                        for f in files:
                            fp = os.path.join(root, f)
                            if now - os.path.getmtime(fp) < 300:
                                gemini_active = True
                                break
                        if gemini_active:
                            break
                except Exception:
                    pass
            else:
                gemini_active = True

        gemini_status = "WORKING" if gemini_active else "IDLE"

        items = [
            {"name": "CODEX", "status": codex_status, "elapsed": codex_elapsed_str, "working": codex_active},
            {"name": "CLAUDE", "status": claude_status, "elapsed": claude_elapsed_str, "working": claude_active},
            {"name": "GEMINI", "status": gemini_status, "elapsed": gemini_elapsed_str, "working": gemini_active},
        ]

        active_count = sum(1 for it in items if it["working"])
        badge_text = f"{active_count} ACTIVE" if active_count > 0 else "IDLE"
        badge_color = "green" if active_count > 0 else "gray"

        return PageData(
            page_id="ai_activity",
            title="AI ACTIVITY",
            badge=badge_text,
            badge_color=badge_color,
            items_list=items,
            footer_left=f"{active_count}/3 ACTIVE",
            footer_right="MONITOR",
            source_info="Local process table + session logs",
        )


# ==============================================================================
# 7. SERVICES COLLECTOR (LIGHTWEIGHT NON-BLOCKING SOCKET HEALTH PROBES)
# ==============================================================================
class ServicesCollector:
    """Collects lightweight health check statuses for workstation machines and services."""

    def __init__(self, dgx_host: str = "dgx", cache_file: str = ".services_cache.json"):
        self.dgx_host = dgx_host or "dgx"
        self.cache_file = cache_file

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _write_cache(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def _probe_tcp(host: str, port: int, timeout: float = 0.3) -> bool:
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                return True
        except Exception:
            return False

    def collect(self) -> PageData:
        now = time.time()
        cache = self._read_cache()
        # 15s cache TTL guarantees zero delay to dashboard rotation
        if cache and (now - cache.get("timestamp", 0) < 15.0):
            items = cache.get("items", [])
        else:
            # 1. DGX (SSH on configured dgx_host:22)
            dgx_up = self._probe_tcp(self.dgx_host, 22, timeout=0.3)
            # 2. Ollama (configured dgx_host:11434 or 127.0.0.1:11434)
            ollama_up = self._probe_tcp(self.dgx_host, 11434, timeout=0.3) or self._probe_tcp("127.0.0.1", 11434, timeout=0.1)
            # 3. ComfyUI (Docker service on DGX host)
            comfy_up = dgx_up
            # 4. Forge3D (DGX forge3d service port 18788)
            forge_up = dgx_up and self._probe_tcp(self.dgx_host, 18788, timeout=0.3)
            # 5. Hermes (Local or DGX hermes service)
            hermes_up = self._probe_tcp("127.0.0.1", 8000, timeout=0.1) or self._probe_tcp(self.dgx_host, 8000, timeout=0.2)

            items = [
                {"name": "DGX", "online": dgx_up},
                {"name": "OLLAMA", "online": ollama_up},
                {"name": "COMFY", "online": comfy_up},
                {"name": "FORGE3D", "online": forge_up},
                {"name": "HERMES", "online": hermes_up},
            ]
            self._write_cache({"items": items, "timestamp": now})

        up_count = sum(1 for it in items if it["online"])
        tot = len(items)
        badge_text = f"{up_count}/{tot} UP"
        badge_color = "green" if up_count >= 3 else ("amber" if up_count > 0 else "red")

        return PageData(
            page_id="services",
            title="SERVICES",
            badge=badge_text,
            badge_color=badge_color,
            items_list=items,
            footer_left="TAILSCALE",
            footer_right="HEALTH",
            source_info="TCP socket probes (dgx, ollama, comfy, forge3d, hermes)",
        )
