#!/usr/bin/env python3
"""
AI Desk Dashboard - Reusable Desk Display System.
Decoupled multi-source dashboard supporting physical displays (Divoom MiniToo)
and desktop preview for local development.

Supported Pages:
  1. CLAUDE     - Claude Code utilization & model status
  2. CODEX      - OpenAI Codex / ChatGPT usage & model
  3. GEMINI     - Google Gemini / Antigravity tier & model
  4. LOCAL PC   - Local workstation GPU (RTX 5080), VRAM, Temp, CPU, and RAM
  5. DGX SPARK  - Remote NVIDIA GB10 Blackwell machine via Tailscale/SSH (with offline cache)
  6. CODING     - Active repository, branch, clean/dirty working tree, and active AI model
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import List, Optional

from backends import get_display_backend, DisplayBackend
from collectors import (
    LocalPcCollector,
    DgxSparkCollector,
    CodingStatusCollector,
    BtcCollector,
    MultiCryptoCollector,
    StockVolatilityCollector,
    AiActivityCollector,
    ServicesCollector,
    provider_to_page_data,
)
from models import PageData
from providers import get_provider
from renderer import render_dashboard_page
from inputs import BaseInputAdapter, InputEvent, MiniTooInputAdapter, frame_spp, parse_response


PAGE_KEYS = [
    "btc",
    "eth",
    "sol",
    "doge",
    "pepe",
    "crypto",
    "codex",
    "gemini",
    "claude",
    "local_pc",
    "dgx_spark",
    "coding",
    "services",
    "ai_activity",
    "stocks_volatile",
]


def collect_page(page_id: str, repo_path: str = ".", dgx_host: str = "dgx") -> PageData:
    """Collect normalized data for a given page key."""
    norm_id = page_id.lower().strip()
    if norm_id in ("claude", "codex", "gemini"):
        prov = get_provider(norm_id)
        return provider_to_page_data(prov.get_usage())
    elif norm_id in ("local_pc", "pc", "local"):
        return LocalPcCollector().collect()
    elif norm_id in ("dgx_spark", "dgx", "spark"):
        return DgxSparkCollector(host=dgx_host).collect()
    elif norm_id in ("coding", "git", "repo"):
        return CodingStatusCollector(repo_path=repo_path).collect()
    elif norm_id == "crypto":
        return MultiCryptoCollector().collect_overview()
    elif norm_id in ("btc", "eth", "sol", "doge", "pepe"):
        return MultiCryptoCollector().collect_asset(norm_id)
    elif norm_id in ("stocks_volatile", "stocks", "stock"):
        return StockVolatilityCollector().collect()
    elif norm_id in ("ai_activity", "activity"):
        return AiActivityCollector().collect()
    elif norm_id in ("services", "service"):
        return ServicesCollector(dgx_host=dgx_host).collect()
    else:
        raise ValueError(f"Unknown page key: '{page_id}'. Available: {PAGE_KEYS}")


def collect_all_pages(repo_path: str = ".", dgx_host: str = "dgx") -> List[PageData]:
    """Collect all dashboard pages in standard product order."""
    pages: List[PageData] = []
    for k in PAGE_KEYS:
        try:
            pages.append(collect_page(k, repo_path=repo_path, dgx_host=dgx_host))
        except Exception as e:
            print(f"Warning: Error collecting '{k}': {e}", file=sys.stderr)
    return pages


def print_usage_debug():
    """Print strict provenance, raw semantic, normalized used, and remaining for AI quotas."""
    providers = ["codex", "gemini", "claude"]
    print("=" * 68)
    print("  AI DESK DASHBOARD — QUOTA DATA QUALITY & USAGE DEBUG")
    print("=" * 68)
    for p_name in providers:
        prov = get_provider(p_name)
        u = prov.get_usage()
        print(f"\n{u.provider_name}")
        # Raw value & semantic
        raw_val = u.raw_primary_value or "N/A"
        print(f"Raw: {raw_val}")
        # Normalized used
        if u.normalized_primary_used is not None:
            print(f"Normalized used: {u.normalized_primary_used}%")
        else:
            print("Normalized used: N/A")
        # Remaining
        if u.normalized_primary_remaining is not None:
            print(f"Remaining: {u.normalized_primary_remaining}%")
        else:
            print("Remaining: N/A")

        # Secondary if available
        if u.raw_secondary_value and u.raw_secondary_value != "N/A":
            print(f"Secondary Raw: {u.raw_secondary_value}")
            if u.normalized_secondary_used is not None:
                print(f"Secondary Normalized used: {u.normalized_secondary_used}%")
            if u.normalized_secondary_remaining is not None:
                print(f"Secondary Remaining: {u.normalized_secondary_remaining}%")

        print(f"Source: {u.source_description}")
        print(f"Authority: {u.authority}")
        if u.age_seconds is not None:
            if u.age_seconds < 60:
                age_str = f"{u.age_seconds:.1f}s"
            elif u.age_seconds < 3600:
                age_str = f"{u.age_seconds / 60:.1f}m"
            elif u.age_seconds < 86400:
                age_str = f"{u.age_seconds / 3600:.1f}h"
            else:
                age_str = f"{u.age_seconds / 86400:.1f}d"
            print(f"Age: {age_str}")
        else:
            print("Age: N/A")
    print("\n" + "=" * 68)


def print_status(display_name: str, repo_path: str = ".", dgx_host: str = "dgx"):
    """Print comprehensive status for all providers, machines, and display backends."""
    print("=" * 68)
    print("  AI DESK DASHBOARD — STATUS & PROVENANCE REPORT")
    print("=" * 68)
    print(f"Display Backend:      {display_name.upper()}")
    print(f"Configured Git Repo:  {repo_path}")
    print(f"Configured DGX Host:  {dgx_host}")
    print("-" * 68)

    pages = collect_all_pages(repo_path=repo_path, dgx_host=dgx_host)

    for p in pages:
        status_tag = f"[{p.badge}]"
        print(f"\n{p.title.ljust(14)} {status_tag.ljust(16)} Source: {p.source_info}")
        if p.is_offline:
            print(f"  • State:            OFFLINE (Last seen: {p.offline_sub})")
        else:
            if p.primary_metric:
                pm = p.primary_metric
                sub = f" ({pm.reset})" if pm.reset else ""
                print(f"  • {pm.label.ljust(16)}: {pm.value}{sub}")
            if p.secondary_metric:
                sm = p.secondary_metric
                sub = f" ({sm.reset})" if sm.reset else ""
                print(f"  • {sm.label.ljust(16)}: {sm.value}{sub}")
            for em in p.extra_metrics:
                print(f"  • {em.label.ljust(16)}: {em.value}")
            if p.items_list:
                print("  • Items:")
                for it in p.items_list:
                    it_name = it.get("name", "")
                    if "status" in it:
                        el = f" ({it['elapsed']})" if it.get("elapsed") else ""
                        print(f"      - {it_name.ljust(12)}: {it['status']}{el}")
                    elif "online" in it:
                        st = "ONLINE" if it["online"] else "OFFLINE"
                        print(f"      - {it_name.ljust(12)}: {st}")
            if p.sparkline_data:
                print(f"  • 24H Sparkline   : {len(p.sparkline_data)} points | H {p.sparkline_high} L {p.sparkline_low}")
            if p.footer_left or p.footer_right:
                print(f"  • Metadata        : {p.footer_left} | {p.footer_right}")

        if p.metrics_provenance:
            print("  • Classification  :")
            for m_key, m_auth in p.metrics_provenance.items():
                print(f"      - {m_key.ljust(14)}: {m_auth}")

    print("\n" + "=" * 68)


def run_control_debug(port: Optional[str] = None, duration: Optional[float] = None):
    """
    Diagnostic monitor for MiniToo physical controls.
    Polls queryable registers (0x09 GET_VOL, 0x31 LIGHT_CURRENT_LEVEL, 0x13 GET_WORK_MODE, 0x32 LIGHT_SWITCH, 0x46)
    and reports state transitions in real time.
    """
    import serial

    target_port = port or MiniTooInputAdapter.find_port()
    print("=" * 68)
    print("  MINITOO PHYSICAL CONTROL STATE DIAGNOSTIC MONITOR")
    print("=" * 68)
    print(f"Target Port: {target_port} | Baud: 115200 | Poll Rate: ~10-12 Hz\n")

    try:
        ser = serial.Serial(target_port, 115200, timeout=0.04)
    except Exception as e:
        print(f"Error opening port {target_port}: {e}")
        return

    with ser:
        time.sleep(0.3)
        if ser.in_waiting:
            ser.read(ser.in_waiting)

        def query_single(cmd: int) -> Tuple[Optional[int], Optional[str]]:
            ser.write(frame_spp(cmd))
            ser.flush()
            t0 = time.time()
            buf = bytearray()
            while time.time() - t0 < 0.05:
                if ser.in_waiting:
                    buf.extend(ser.read(ser.in_waiting))
                    parsed = parse_response(bytes(buf))
                    if parsed and parsed[0] == cmd:
                        val = parsed[1][0] if parsed[1] else 0
                        return val, bytes(buf).hex()
                time.sleep(0.005)
            return None, bytes(buf).hex() if buf else None

        init_vol, r_vol = query_single(0x09)
        init_bri, r_bri = query_single(0x31)
        init_mode, r_mode = query_single(0x13)

        print("INITIAL VALUES:")
        print(f"  • Volume (0x09 GET_VOL)              : {init_vol} | raw: {r_vol}")
        print(f"  • Brightness (0x31 LIGHT_LEVEL)      : {init_bri} | raw: {r_bri}")
        print(f"  • Work Mode (0x13 GET_WORK_MODE)     : {init_mode} | raw: {r_mode}")
        print("-" * 68)
        print("TEST INSTRUCTIONS:")
        print("While this monitor is running, please physically operate one control")
        print("at a time on your MiniToo hardware:")
        print("  1. Rotate Volume Knob CLOCKWISE (+)")
        print("  2. Rotate Volume Knob COUNTER-CLOCKWISE (-)")
        print("  3. Press Volume Knob (if clickable)")
        print("  4. Press/Rotate Mode dial / Mode button")
        print("  5. Press side buttons / rocker switches")
        print("  6. Adjust brightness / light controls")
        print("Press Ctrl+C to stop.\n")
        print("LOG OF DETECTED STATE CHANGES:")
        print("-" * 68)
        sys.stdout.flush()

        last_vol = init_vol
        last_bri = init_bri
        last_mode = init_mode

        t_start = time.time()
        try:
            while True:
                if duration and (time.time() - t_start) >= duration:
                    print(f"\nDuration limit ({duration}s) reached.")
                    break

                # 1. Volume
                v, rv = query_single(0x09)
                if v is not None and v != last_vol:
                    ts = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"
                    print(f"{ts} GET_VOL {last_vol} -> {v} | raw: {rv}")
                    sys.stdout.flush()
                    last_vol = v

                # 2. Brightness
                b, rb = query_single(0x31)
                if b is not None and b != last_bri:
                    ts = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"
                    print(f"{ts} LIGHT_CURRENT_LEVEL {last_bri} -> {b} | raw: {rb}")
                    sys.stdout.flush()
                    last_bri = b

                # 3. Work Mode
                m, rm = query_single(0x13)
                if m is not None and m != last_mode:
                    ts = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"
                    print(f"{ts} GET_WORK_MODE {last_mode} -> {m} | raw: {rm}")
                    sys.stdout.flush()
                    last_mode = m

                # Check unsolicited
                if ser.in_waiting:
                    extra = ser.read(ser.in_waiting)
                    ts = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"
                    print(f"{ts} UNSOLICITED_PACKET | bytes: {extra.hex()}")
                    sys.stdout.flush()

                time.sleep(0.04)
        except KeyboardInterrupt:
            print("\nControl monitor stopped by user.")


def run_cycle(
    display: DisplayBackend,
    interval: float = 4.0,
    max_count: Optional[int] = None,
    repo_path: str = ".",
    dgx_host: str = "dgx",
    input_adapter: Optional[BaseInputAdapter] = None,
):
    """Continuously rotate through all 9 pages with physical input navigation support."""
    total_pages = len(PAGE_KEYS)
    print(f"\nStarting automatic rotation across all {total_pages} pages:")
    print(" -> ".join(k.upper() for k in PAGE_KEYS) + " -> ...")
    print(f"Interval: {interval:.1f}s per page. Physical controls: {'ACTIVE' if input_adapter else 'DISABLED'}.")
    print("Press Ctrl+C to exit.\n")

    count = 0
    current_page_idx = 0
    is_paused = False

    try:
        while True:
            p_key = PAGE_KEYS[current_page_idx]
            count += 1
            idx_1based = current_page_idx + 1

            try:
                data = collect_page(p_key, repo_path=repo_path, dgx_host=dgx_host)
            except Exception as e:
                print(f"Error collecting page '{p_key}': {e}")
                data = None

            if data:
                ts = time.strftime("%H:%M:%S")
                metric_summary = ""
                if data.is_offline:
                    metric_summary = f"OFFLINE (Last seen: {data.offline_sub})"
                elif data.primary_metric:
                    metric_summary = f"{data.primary_metric.label}={data.primary_metric.value}"
                    if data.secondary_metric:
                        metric_summary += f", {data.secondary_metric.label}={data.secondary_metric.value}"
                elif data.items_list:
                    metric_summary = f"{len(data.items_list)} items"

                pause_tag = " [PAUSED]" if is_paused else ""
                print(f"[{ts}] Page {count} [{idx_1based}/{total_pages}] {data.title}: {metric_summary} | Badge={data.badge}{pause_tag}")

                img = render_dashboard_page(data, page_num=idx_1based, total_pages=total_pages)
                active_ser = getattr(input_adapter, "ser", None)
                ok = display.show(img, ser=active_ser)
                if not ok:
                    print(f"Warning: Display backend failed for '{data.title}'.")

            if max_count and count >= max_count:
                print(f"\nCompleted {count} page rotation(s).")
                return

            # Dwell interval: poll physical input adapter for hardware navigation
            t_end = time.time() + (float("inf") if is_paused else interval)
            navigated = False
            while time.time() < t_end:
                if input_adapter:
                    event = input_adapter.poll_event()
                    if event == InputEvent.NEXT_PAGE:
                        current_page_idx = (current_page_idx + 1) % total_pages
                        navigated = True
                        break
                    elif event == InputEvent.PREV_PAGE:
                        current_page_idx = (current_page_idx - 1) % total_pages
                        navigated = True
                        break
                    elif event == InputEvent.TOGGLE_PAUSE:
                        is_paused = not is_paused
                        print(f"[{time.strftime('%H:%M:%S')}] Auto-cycle {'PAUSED' if is_paused else 'RESUMED'}")
                        if not is_paused:
                            break
                time.sleep(0.04)

            if not navigated and not is_paused:
                current_page_idx = (current_page_idx + 1) % total_pages
    except KeyboardInterrupt:
        print("\nRotation stopped by user.")
    finally:
        if input_adapter:
            input_adapter.close()
        display.close()


def main():
    parser = argparse.ArgumentParser(
        description="AI Desk Dashboard — Multi-Source Desk Display System"
    )
    parser.add_argument(
        "--display",
        type=str,
        default="minitoo",
        choices=["minitoo", "preview"],
        help="Display output backend: 'minitoo' (hardware) or 'preview' (desktop image) (default: minitoo)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Shortcut to run with --display preview (save/show image without device)",
    )
    parser.add_argument(
        "--page",
        type=str,
        default=None,
        choices=PAGE_KEYS,
        help="Render and display a single specific page instead of cycling",
    )
    parser.add_argument(
        "--cycle",
        action="store_true",
        help="Run automatic rotation across all 9 pages (default if no single page specified)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print status report with data authority and provenance for all metrics",
    )
    parser.add_argument(
        "--usage-debug",
        action="store_true",
        help="Print AI quota provenance, raw semantics, normalized used/remaining values",
    )
    parser.add_argument(
        "--control-debug",
        action="store_true",
        help="Poll physical control state (knob, buttons, light) and log transitions in real time",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Optional duration in seconds for control-debug",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=4.0,
        help="Seconds per page during cycle rotation (default: 4.0)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Maximum number of page transitions before exiting (default: infinite)",
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Bluetooth serial port for MiniToo (default: auto-detect)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to Git repository for CODING page (default: current directory)",
    )
    parser.add_argument(
        "--dgx-host",
        type=str,
        default="dgx",
        help="SSH hostname or IP for remote DGX Spark machine (default: dgx)",
    )

    args = parser.parse_args()
    if args.preview:
        args.display = "preview"

    # Control Debug mode
    if args.control_debug:
        run_control_debug(port=args.port, duration=args.duration)
        return

    # Usage Debug mode
    if args.usage_debug:
        print_usage_debug()
        return

    # Status mode
    if args.status:
        print_status(display_name=args.display, repo_path=args.repo, dgx_host=args.dgx_host)
        return

    # Initialize display backend
    display = get_display_backend(
        args.display,
        port=args.port,
        output_path="preview_dashboard.png",
        scale=3,
        auto_open=(args.display == "preview" and not args.cycle and args.page is not None),
    )

    # Single page mode
    if args.page:
        data = collect_page(args.page, repo_path=args.repo, dgx_host=args.dgx_host)
        page_num = PAGE_KEYS.index(args.page) + 1
        img = render_dashboard_page(data, page_num=page_num, total_pages=len(PAGE_KEYS))
        ok = display.show(img)
        if ok:
            print(f"Successfully displayed '{data.title}' on {args.display.upper()}.")
        else:
            print(f"Failed to display on {args.display.upper()}.", file=sys.stderr)
            sys.exit(1)
        return

    # Cycle rotation mode (default)
    input_adapter = None
    if args.display == "minitoo":
        try:
            input_adapter = MiniTooInputAdapter(port=args.port)
        except Exception as e:
            print(f"Warning: Could not start MiniToo input adapter: {e}")

    run_cycle(
        display=display,
        interval=args.interval,
        max_count=args.count,
        repo_path=args.repo,
        dgx_host=args.dgx_host,
        input_adapter=input_adapter,
    )


if __name__ == "__main__":
    main()
