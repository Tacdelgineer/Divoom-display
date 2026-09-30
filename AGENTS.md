# AGENTS.md — Autonomous Agent Operating Instructions

> **Notice to AI Coding Agents (Codex, Claude Code, Antigravity, etc.)**:  
> Read this document completely before modifying or running commands in this repository. It defines architectural invariants, safety constraints, authority semantics, and milestone workflows.

---

## 1. Project Purpose & Scope

**AI Desk Dashboard** is a retro-styled dual-mode telemetry dashboard for developers:
1. **Desktop Companion App**: A native Python Tkinter GUI with configurable sections (`CRYPTO`, `AI USAGE`, `SYSTEM`, `STOCKS`), presets (`ALL`, `AI`, `CRYPTO`, `STOCKS`, `SYSTEM`), Focus Mode for screen recording / Shorts, 5-tab Settings redesign (`GENERAL`, `DASHBOARD`, `MINITOO`, `INTEGRATIONS`, `ADVANCED`), and independent Desktop vs MiniToo card visibility.
2. **Physical Desk Display Controller**: Drives an external **Divoom MiniToo** 160×128 color IPS LCD over Bluetooth SPP in Custom Channel 5 with physical knob rotation control, multi-crypto views, stock volatility rankings, and Bluetooth audio coexistence optimization (Low Interference mode).

---

## 2. Architecture Map & Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA COLLECTORS                       │
│  collectors.py · providers.py · market_provider.py          │
│  - Non-blocking (strict timeouts <= 3.0s)                  │
│  - Zero Windows console flashing (subproc.py)              │
│  - Multi-asset crypto (BTC, ETH, SOL, DOGE, PEPE via 1 req) │
│  - US Stock volatility scanner (intraday high-low range)    │
│  - Safe Claude diagnostics (masked email, env precedence)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Returns PageData models
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 NORMALIZED STATE ENGINE                     │
│  engine.py (DataEngine, DashboardState, MiniTooController)  │
│  - Schedules collectors at specific refresh rates           │
│  - Maintains thread-safe page cache                         │
│  - Decoupled: collector updates NEVER force MiniToo frames  │
│  - Eliminates redundant frames (diff hashing; 0 heartbeats) │
│  - Manages Low Interference mode & rolling 60s telemetry    │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│       DESKTOP RENDERER       │ │      MINITOO RENDERER      │
│  dashboard_app.py            │ │  renderer.py (Pillow)      │
│  - 5 Presets (ALL, AI, etc.) │ │  - 160x128 24-bit RGB JPEG │
│  - Focus Mode (creator view) │ │  - Multi-asset table / 128p│
│  - 5-tab SettingsDialog      │ │  - Frame buffer payload    │
│  - Desktop vs MiniToo toggles│ │  - Page rotation engine    │
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      DESKTOP COMPANION       │ │     MINITOO BACKEND        │
│      Windows GUI Window      │ │  backends.py · inputs.py   │
│                              │ │  - Bluetooth SPP (0x8B)    │
│                              │ │  - Channel 5 keep-alive    │
│                              │ │  - Polled knob input (0x09)│
│                              │ │  - Rolling 60s telemetry   │
└──────────────────────────────┘ └────────────────────────────┘
```

---

## 3. Key Files & Responsibilities

| File | Purpose | Critical Rules |
| :--- | :--- | :--- |
| `dashboard_app.py` | Main Desktop Companion application | Pure Tkinter; High-DPI; responsive reflow; presets; Focus; Creator views |
| `ui_scale.py` | Centralized UI scale & High-DPI tokens | Per-Monitor-V2 awareness; font scaling; never used for MiniToo 160x128 |
| `ui_components.py` | Redesigned 5-tab SettingsDialog | Left navigation; UI scale dropdown; independent Desktop vs MiniToo toggles |
| `engine.py` | Background scheduler & MiniToo controller | Decoupled collector updates; 0 redundant frames; telemetry report |
| `market_provider.py` | Stock quote & volatility provider abstraction | Pluggable interface; YahooFinance (free) & Finnhub; cached |
| `collectors.py` | Data collectors (GPU, DGX, Multi-Crypto, Stocks, Git) | Consolidated requests; 60s caches; never block the UI thread |
| `claude_usage.py` | Claude account diagnostics & profile reader | Safe masking (`no***@gmail.com`); env precedence; no token scraping |
| `providers.py` | AI Quota providers (Codex, Gemini, Claude) | Preserves authority levels; strictly calculates % LEFT |
| `models.py` | Unified data structures (`PageData`, `CryptoAsset`, `StockQuote`) | Clean dataclasses; formatting helpers for micro-tokens |
| `renderer.py` | Pixel-perfect 160×128 image generator | Pillow graphics; 8×10 tile alignment; multi-asset tables |
| `detector.py` | Bluetooth SPP hardware discovery | Scores COM ports; safely probes `0xBD 0x13`; never hardcodes |
| `inputs.py` | Physical rotary knob & button listener | ~2.8–4 Hz polling; stops queries if disconnected; debounces |
| `backends.py` | MiniToo frame transmission transport | Multi-packet SPP streaming `0x8B`; rolling 60-second telemetry |
| `config.py` | Persistent user configuration & section definitions | Stored in `%APPDATA%\AiDeskDashboard\config.json`; no secrets |
| `subproc.py` | Silent subprocess execution helper | Always use `run_hidden()` / `check_output_hidden()` on Windows |

---

## 4. MiniToo Hardware Protocol Summary

- **Physical Connection**: Bluetooth SPP (Serial Port Profile) over RFCOMM emulated COM port at 115200 baud.
- **Display Resolution**: 160×128 pixels (IPS LCD).
- **SPP Framing**:
  - Start byte: `0x01`
  - Length: 2 bytes little-endian (`len - 4`)
  - Command ID: 1 byte
  - Payload: N bytes
  - Checksum: 2 bytes little-endian (sum of payload bytes `& 0xFFFF`)
  - End byte: `0x02`
- **Display Channel Retention**: Query / set display mode `0xBD` to Channel 5 (Custom/DIY). In Milestone 13, health checks are relaxed to 60s (Normal) / 120s (Low Interference) to minimize radio slot contention.
- **Physical Controls**: The MiniToo does not emit unsolicited button packets. Polled via volume queries (`0x09`). In Milestone 13, polling frequency is capped at ~2.8 Hz (Low Interference) to 4 Hz (Normal), down from 16 Hz, freeing Bluetooth radio airtime for headphones and speakers.
- **Diff-Based Frame Elision**: Never retransmits identical pixel frames on timer ticks. Frames are sent strictly when the active page changes, data materially updates, or reconnect requires restoring the screen. Redundant frame transmissions are 0.
- **Bluetooth Coexistence**: Documented in `docs/BLUETOOTH.md`. Selectable `NORMAL` vs `LOW_INTERFERENCE` mode.

---

## 5. Important Commands

```powershell
# Run the Desktop Companion application
python dashboard_app.py

# Run terminal status & quota provenance check
python dashboard.py --status

# Run single page collection test
python -c "from dashboard import collect_page; print(collect_page('crypto'))"

# Verify MiniToo COM port detection
python -c "from detector import detect_minitoo_port; print(detect_minitoo_port())"

# Run tests
pytest tests/ -v

# Run physical Bluetooth coexistence benchmark script
python scripts/test_bluetooth_coexistence.py

# Build standalone Windows executable
pyinstaller "AI Desk Dashboard.spec"
```

---

## 6. Critical Safety & Engineering Constraints

1. **NO Destructive Firmware Commands**: Never send raw, unverified write commands to hardware registers or memory addresses outside the documented frame commands (`0x8B`, `0xBD`, `0x09`, `0x46`).
2. **Preserve Data-Source Authority**:
   - Every metric must declare an authority level: `AUTHORITATIVE`, `CALCULATED`, `STALE_CACHE`, or `UNAVAILABLE`.
   - Never turn unavailable values into `0` or `0%`. If a metric is missing, report `N/A` with authority `UNAVAILABLE`.
3. **Quota Semantics (% LEFT)**:
   - UI metrics for AI quotas always display **Remaining** (`% LEFT`), never used.
   - For Codex: `remaining = 100 - used_percent`.
   - For Gemini: `remaining = remaining_fraction * 100`.
   - For Claude: Displays cached remaining or `N/A` (never fabricate).
4. **DO NOT Log or Expose Secrets or Identifiers**:
   - Never log or store raw API keys, OAuth tokens, or unmasked email addresses.
   - User account emails must always be masked (e.g. `no***@gmail.com`).
5. **No Visible Child Console Flashing on Windows**:
   - Always route child processes (`nvidia-smi`, `git`, `ssh`, `agy`) through `subproc.py`.
   - Injects `CREATE_NO_WINDOW = 0x08000000`, `SW_HIDE`, and `shell=False`.
6. **Zero-Dependency Desktop Mode**:
   - The application must operate 100% reliably when MiniToo hardware is disconnected, turned off, or absent.
7. **Independent Failure Safety**:
   - Collectors must be wrapped in try/except blocks. A timeout in the DGX collector or a rate limit on CoinGecko must never crash the engine or prevent other widgets from rendering.
8. **Defensible Volatility Metric**:
   - Volatility is calculated as `(high - low) / previous_close * 100`. Never substitute daily percentage gainers for volatility.
9. **Safe Claude Multi-Account Handling**:
   - Claude Code CLI does not support simultaneous multi-account switching within a single profile folder.
   - Support multiple accounts *only* via isolated configuration directories (`CLAUDE_CONFIG_DIR`). Never scrape tokens, steal browser cookies, or hijack existing sessions.
10. **Bluetooth Traffic Minimization & Audio Coexistence**:
    - Never flood the serial connection with high-frequency control polls while audio is active.
    - Decouple background collector updates: background refreshes for inactive pages must never trigger MiniToo display transmissions.
    - Zero redundant frame transmissions: elide frames if pixel/payload hash matches the currently displayed buffer.

11. **UI Interaction Invariant (High-DPI & Navigation Hit Targets)**:
    - *"Visual position and interactive hit target must always derive from the same scaled geometry."*
    - Navigation headers and desktop controls must use native interactive widgets (`tk.Button` with `command=` callbacks, hand cursors, and dynamic hover styling) pinned to persistent frames above scrollable viewports. Never mix raw viewport `(event.x, event.y)` hit detection with canvas-scrolled or DPI-scaled content, and never clear interactive geometry bindings during canvas redraws.
    - Decouple device state from desktop controls: a disconnected or reconnecting peripheral (e.g., MiniToo or Ditoo) must never disable unrelated desktop controls (Settings, Creator mode, Presets).

---

## 7. Milestone Workflow for Agents

When assigned a task or feature in this repository:
1. **Understand & Verify**: Inspect existing code and check active behavior. Do not assume or rewrite working components.
2. **Scope the Edit**: Make the minimal, surgical set of changes required for the current milestone.
3. **Run Validation Checks**: Run Python compilation, unit tests, and terminal diagnostic checks.
4. **Update Documentation**: Keep docs in sync with any schema or interface changes.
5. **Stop**: Report results clearly and wait for user review before proceeding to subsequent milestones.

### Milestone 14.1 Hotfix Regression Note
- **Fixed Issue**: Top navigation buttons rendered visually on high-DPI screens but mouse clicks were swallowed or offset.
- **Root Causes**:
  1. Coordinate divergence: Buttons drawn on `self.canvas` with canvas coordinates were tested against raw window `(event.x, event.y)` without accounting for scroll offsets.
  2. Canvas delete race: 350ms periodic `self.canvas.delete("all")` constantly wiped hit bounds dictionaries between clicks.
  3. DPI coordinate collisions between left-growing and right-growing button bars.
- **Solution**: Refactored header into a pinned `self.header_frame` above the canvas with native retro `tk.Button` controls, hand cursors, dynamic hover feedback, and direct `command=` callbacks. Fully decoupled device reconnect state from desktop navigation.
