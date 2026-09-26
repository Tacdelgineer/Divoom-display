# AGENTS.md — Autonomous Agent Operating Instructions

> **Notice to AI Coding Agents (Codex, Claude Code, Antigravity, etc.)**:  
> Read this document completely before modifying or running commands in this repository. It defines architectural invariants, safety constraints, authority semantics, and milestone workflows.

---

## 1. Project Purpose & Scope

**AI Desk Dashboard** is a retro-styled dual-mode telemetry dashboard for developers:
1. **Desktop Companion App**: A native Python Tkinter 628×512 GUI displaying 9 telemetry cards in a 3×3 grid.
2. **Physical Desk Display Controller**: Drives an external **Divoom MiniToo** 160×128 color IPS LCD over Bluetooth SPP in Custom Channel 5 with physical knob rotation control.

---

## 2. Architecture Map & Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA COLLECTORS                       │
│  collectors.py · providers.py · subproc.py                  │
│  - Non-blocking (strict timeouts <= 3.0s)                  │
│  - Zero Windows console flashing (CREATE_NO_WINDOW)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Returns PageData models
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 NORMALIZED STATE ENGINE                     │
│  engine.py (DataEngine, DashboardState, MiniTooController)  │
│  - Schedules collectors at specific refresh rates           │
│  - Maintains thread-safe page cache                         │
│  - Handles MiniToo connection recovery                      │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│       DESKTOP RENDERER       │ │      MINITOO RENDERER      │
│  dashboard_app.py            │ │  renderer.py (Pillow)      │
│  - Native Tkinter canvas     │ │  - 160x128 24-bit RGB JPEG │
│  - Interactive card clicks   │ │  - Frame buffer payload    │
└──────────────┬───────────────┘ └─────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      DESKTOP COMPANION       │ │     MINITOO BACKEND        │
│      Windows GUI Window      │ │  backends.py · inputs.py   │
│                              │ │  - Bluetooth SPP (0x8B)    │
│                              │ │  - Channel 5 lock (0xBD)   │
│                              │ │  - Polled knob input (0x09)│
└──────────────────────────────┘ └────────────────────────────┘
```

---

## 3. Key Files & Responsibilities

| File | Purpose | Critical Rules |
| :--- | :--- | :--- |
| `dashboard_app.py` | Main Desktop Companion application | Pure Tkinter; no web views; handles window events & settings |
| `engine.py` | Background scheduler & MiniToo controller | Thread-safe state container; auto-reconnects on device loss |
| `collectors.py` | Data collectors (GPU, DGX, BTC, Git, Services) | Independent timeouts; never let one collector block others |
| `providers.py` | AI Quota providers (Codex, Gemini, Claude) | Preserves authority levels; calculates remaining percentage |
| `models.py` | Unified data structures (`PageData`, `MetricItem`) | Dataclasses for consistent UI rendering across backends |
| `renderer.py` | Pixel-perfect 160×128 image generator | Pillow graphics; 8×10 tile alignment; retro terminal palette |
| `detector.py` | Bluetooth SPP hardware discovery | Scores COM ports; safely probes `0xBD 0x13`; never hardcodes |
| `inputs.py` | Physical rotary knob & button listener | Polls volume delta `0x09`; restores base volume; debounces |
| `backends.py` | MiniToo frame transmission transport | Multi-packet SPP streaming `0x8B`; ACK timeout handling |
| `config.py` | Persistent user configuration | Stored in `%APPDATA%\AiDeskDashboard\config.json`; no tokens |
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
- **Display Channel Retention**: Query / set display mode `0xBD` to Channel 5 (Custom/DIY). This prevents the device firmware from reverting to Clock mode.
- **Physical Controls**: The MiniToo does not emit unsolicited button packets. Knobs and buttons are read via high-frequency polled state queries (`0x09` volume level, `0x46` light mode). Rotary turns generate volume deltas, which are translated into NEXT / PREV page transitions and then immediately restored to the base volume level (`8/16`).

---

## 5. Important Commands

```powershell
# Run the Desktop Companion application
python dashboard_app.py

# Run terminal status & quota provenance check
python dashboard.py --status

# Run single page collection test
python -c "from dashboard import collect_page; print(collect_page('codex'))"

# Verify MiniToo COM port detection
python -c "from detector import detect_minitoo_port; print(detect_minitoo_port())"

# Run tests
pytest tests/ -v

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
   - UI metrics for AI quotas always display **Remaining** (`% LEFT`), not used.
   - For Codex: `remaining = 100 - used_percent`.
   - For Gemini: `remaining = remaining_fraction * 100`.
   - For Claude: `N/A` (never calculate or guess a percentage).
4. **DO NOT Hardcode COM Ports**:
   - Always route hardware connections through `detector.detect_minitoo_port()` or user-specified config.
   - Never default or fall back to `"COM7"`.
5. **No Visible Child Console Flashing on Windows**:
   - Always route child processes (`nvidia-smi`, `git`, `ssh`, `agy`) through `subproc.py`.
   - Injects `CREATE_NO_WINDOW = 0x08000000`, `SW_HIDE`, and `shell=False`.
6. **Zero-Dependency Desktop Mode**:
   - The application must operate 100% reliably when MiniToo hardware is disconnected, turned off, or absent.
7. **Independent Failure Safety**:
   - Collectors must be wrapped in try/except blocks. A timeout in the DGX collector or a failure in Gemini collection must never crash the engine or prevent other widgets from rendering.
8. **Keep Dependencies Minimal**:
   - Use standard library wherever possible. External runtime dependencies are limited to: `pillow`, `pyserial`, `requests`, and `psutil`. Do not introduce heavyweight frameworks (no Electron, no web servers, no Qt).

---

## 7. Milestone Workflow for Agents

When assigned a task or feature in this repository:
1. **Understand & Verify**: Inspect existing code and check active behavior. Do not assume or rewrite working components.
2. **Scope the Edit**: Make the minimal, surgical set of changes required for the current milestone.
3. **Run Validation Checks**: Run Python compilation, unit tests, and terminal diagnostic checks.
4. **Update Documentation**: Keep docs in sync with any schema or interface changes.
5. **Stop**: Report results clearly and wait for user review before proceeding to subsequent milestones.
