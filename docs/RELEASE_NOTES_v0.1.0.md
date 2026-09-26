# Release Notes — v0.1.0 (Early Public Preview)

**Release Date**: September 2026  
**Status**: Early Public Preview / Prototype  
**Primary Supported Platform**: Windows 10 & Windows 11  

---

## Overview

AI Desk Dashboard v0.1.0 is the first public preview release of an open-source, retro-styled telemetry companion for AI developers and power users. It provides simultaneous monitoring across:
1. **Interactive Windows Desktop Companion**: A 3×3 grid of retro cards displaying AI quotas, hardware telemetry, crypto markets, and remote node health.
2. **Divoom MiniToo Physical Hardware Display**: Continuous 160×128 pixel frame streaming over Bluetooth SPP in Custom Channel 5 with physical rotary knob navigation.

---

## What's Included

### AI Usage & Quotas (% LEFT)
- **OpenAI Codex**: Live remaining quota tracking (`% LEFT`) via authenticated local CLI session (`~/.codex/auth.json`) with primary 5-hour and weekly reset countdowns.
- **Google Gemini & Antigravity**: Authoritative quota collection via the headless Antigravity CLI (`agy -p /quota`), tracking Flash and Pro model usage.
- **Anthropic Claude**: Transparent status and model reporting without guessing or fabricating unavailable metric values.

### System & Infrastructure Telemetry
- **Local PC Hardware**: NVIDIA RTX GPU utilization, core temperature, and VRAM via `nvidia-smi`, plus system RAM and CPU load via `psutil`.
- **Remote DGX Spark Node**: Non-blocking SSH and Tailscale metrics collection with a strict 3-second timeout and offline caching.
- **Workstation Services**: High-frequency TCP socket health checks for local and remote containers (SSH, Ollama, ComfyUI, Forge3D, Hermes).
- **Bitcoin (BTC)**: Live spot price and 16-point phosphor sparkline with 60-second caching and automated public API failover.
- **Coding Workspace**: Git branch, uncommitted diff stats, and commit telemetry.

### Hardware & Desktop Engine
- **MiniToo Auto-Detection**: Eliminates hardcoded COM port assumptions by scoring Bluetooth SPP devices and safely probing with read-only commands (`0xBD 0x13`).
- **Physical Knob Page Navigation**: Translates MiniToo volume dial rotations into page transitions while immediately restoring the base volume level (`8/16`).
- **Zero-Flicker Subprocess Engine**: All child CLI invocations are wrapped with `CREATE_NO_WINDOW` and `SW_HIDE`, ensuring zero terminal flashing when running as a windowed application.
- **Persistent Preferences**: Settings saved to `%APPDATA%\AiDeskDashboard\config.json` with in-app reordering and optional Windows autostart.
- **Standalone Windows Executable**: Ready-to-run single-file binary (`AI Desk Dashboard.exe`).

---

## Known Limitations & Boundaries

As an early public preview and developer prototype:

1. **Local CLI Authentication Required**:
   AI quota integrations (Codex, Antigravity) depend on having the respective developer tools installed and logged in locally. If absent or unauthenticated, the dashboard safely displays `READY` or `LOCAL ONLY`.
2. **Anthropic Claude Quota Automation**:
   Anthropic does not currently provide an official programmatic personal quota endpoint. Claude usage is displayed transparently as active status without calculating estimated percentages.
3. **MiniToo is the Primary Tested Hardware**:
   While the architecture is designed for extensible display backends, the Divoom MiniToo (160×128 IPS LCD) is currently the primary physically validated device.
4. **Windows is the Primary Supported Host**:
   Packaging and Bluetooth SPP auto-detection are currently optimized for Windows 10 and 11. Cross-platform Linux and macOS desktop support is scheduled on the roadmap.

---

## Upgrading & Feedback

- Submit bug reports or feature requests via GitHub Issues:  
  [https://github.com/Tacdelgineer/Divoom-display/issues](https://github.com/Tacdelgineer/Divoom-display/issues)
- Source code and contributions:  
  [https://github.com/Tacdelgineer/Divoom-display](https://github.com/Tacdelgineer/Divoom-display)
