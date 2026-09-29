<div align="center">

![AI Desk Dashboard Banner](assets/banner.png)

# AI Desk Dashboard

**A retro desktop + physical desk dashboard for AI usage, system stats, multi-asset markets, stock scanner, and remote machines.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=flat-square&logo=windows)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Hardware](https://img.shields.io/badge/Hardware-Divoom%20MiniToo%20(Optional)-00F5D4?style=flat-square)](#supported-hardware)
[![Version](https://img.shields.io/badge/Release-v0.2.0-orange?style=flat-square)](docs/RELEASE_NOTES_v0.1.0.md)

</div>

---

## ⚡ Highlights

- **Multi-Device Hardware Controller**: Stream 160×128 pixel frames live to a **Divoom MiniToo** desk display over Bluetooth SPP, or stream dedicated 16×16 pixel art financial pages to a **Divoom Ditoo / Ditoo Plus** over direct BLE GATT (`DitooPro-Light`).
- **Prominent Device Selector**: Instantly switch between **MiniToo**, **Ditoo (16x16)**, and side-by-side **Dual Preview** tabs directly from the header.
- **Dedicated 16×16 Ditoo Pixel Controller**:
  - **Crypto 3-Frame Cycles**: BTC, ETH, SOL, DOGE, PEPE individually toggleable with handcrafted 16×16 pixel art coin icons -> compact USD price -> 24h delta % with up/down directional markers.
  - **Stock 3-Frame Cycles**: Configurable tickers (NVDA, TSLA, AAPL, MSFT, META default) with symbol banner -> current price -> daily % change, plus live Add/Remove/Reorder controls.
  - **Custom Rotation Timing**: Configurable dwell intervals (default: 1.0s logo, 2.0s price, 2.0s delta), auto-rotation toggle, pause/resume, and hardware LED brightness adjustment.
  - **Crisp Nearest-Neighbor Live Preview**: Real-time 160×160 preview mirroring exact pixels streamed over BLE with asset telemetry and market update timestamps.
- **Audio Routing Isolation**: Communicates exclusively with the BLE pixel/control endpoint `DitooPro-Light`. Never touches, selects, or interferes with Windows audio routing or `DitooPro-Audio`.
- **Automatic Reconnection & Offline Resilience**: Background BLE auto-reconnect engine automatically detects when the Ditoo returns and resumes rotation. Cached market data guarantees zero blank screens during API or network downtime.
- **Windows Startup**: Optional "Start with Windows" setting via user registry (`HKCU\Run`), launching minimized without requiring administrator privileges.
- **Configurable Sections & Presets**: Organize widgets into 4 modular sections (**CRYPTO**, **AI USAGE**, **SYSTEM**, **STOCKS**) with instant presets (**ALL**, **AI**, **MARKETS**, **SYSTEM**), full reordering, and visibility toggles.
- **Top 10 Volatile Stocks Scanner**: Scans high-beta US equities and ranks the top 10 most volatile stocks today using an objective, measurable intraday range formula: `(high - low) / previous_close * 100`.
- **AI Quota Tracking (% LEFT)**: Tracks live, authoritative quotas for **OpenAI Codex** and **Google Gemini / Antigravity**, enforcing strict `% LEFT` remaining semantics everywhere.
- **Claude Multi-Account Diagnostics**: Identifies active Claude account (`no***@gmail.com`), subscription plan, auth type, probes environment variable precedence, and supports isolated secondary authentication directories.
- **Physical Controls Investigation**: Rigorously documented BLE GATT telemetry showing Ditoo MCU firmware reserves mechanical keyboard/lever inputs internally for onboard clock/games, while dashboard UI provides comprehensive software controls.

---

## 📸 Screenshots

### 1. Physical MiniToo Desk Display
Running live Gemini model quota and remaining percentage on a physical Divoom MiniToo desk unit:

<div align="center">
  <img src="assets/screenshots/minitoo_desk_photo.png" alt="Physical Divoom MiniToo on Desk" width="460" />
</div>

### 2. Desktop Dashboard Overview (ALL Preset)
The modular desktop companion showing all 4 sections (Crypto Markets, AI Usage, System, and Top 10 Volatile Stocks Scanner) with active MiniToo card synchronization:

<div align="center">
  <img src="assets/screenshots/06_preset_all_dashboard.png" alt="Desktop Dashboard ALL Preset" width="640" />
</div>

### 3. Markets Preset (Crypto + Stocks Scanner)
Focused financial view featuring multi-asset crypto sparklines alongside the intraday stock volatility scanner:

<div align="center">
  <img src="assets/screenshots/07_preset_markets.png" alt="Markets Preset" width="640" />
</div>

### 4. AI Usage Preset (% LEFT)
Authoritative quota visualization showing percentage remaining, segmented progress bars, and Claude account diagnostics:

<div align="center">
  <img src="assets/screenshots/08_preset_ai.png" alt="AI Preset" width="640" />
</div>

### 5. Multi-Asset Crypto Sparklines
Spot price and 24-hour phosphor sparklines across major and micro-decimal tokens:

<div align="center">
  <img src="assets/screenshots/03_btc_sparkline.png" alt="Crypto Sparklines" width="420" />
</div>

### 6. GPU & Remote DGX Monitoring
Local workstation RTX GPU metrics alongside remote DGX Spark compute node load, VRAM, and system memory:

<div align="center">
  <img src="assets/screenshots/04_gpu_and_dgx_monitoring.png" alt="Local PC and Remote DGX Monitoring" width="420" />
</div>

---

## 🚀 Quick Start

### Path A: Windows App (No Python Required)
1. Download the standalone executable from [Releases](https://github.com/Tacdelgineer/Divoom-display/releases): `AI Desk Dashboard.exe`.
2. *(Optional)* Pair your Divoom MiniToo with Windows via Bluetooth Settings.
3. Launch `AI Desk Dashboard.exe`.
4. The dashboard automatically discovers your MiniToo COM port and begins live desktop rendering.
5. Click **SETTINGS** to customize sections, reorder cards, toggle presets, or configure Claude accounts.

### Path B: Developer Setup

```powershell
# 1. Clone the repository
git clone https://github.com/Tacdelgineer/Divoom-display.git
cd Divoom-display

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Desktop Dashboard
python dashboard_app.py
```

See [docs/INSTALL.md](docs/INSTALL.md) for complete installation instructions and optional provider configurations.

---

## 📊 Supported Sections & Data Sources

### 1. Crypto Markets Section
- **Assets**: BTC (Bitcoin), ETH (Ethereum), SOL (Solana), DOGE (Dogecoin), PEPE (Pepe).
- **Data Source**: CoinGecko Public Markets API.
- **Efficiency**: Consolidated single HTTP request for all 5 assets with 60-second caching (`.crypto_cache.json`).
- **Formatting**: Large numbers formatted cleanly (e.g. `$84,021`), micro-cent tokens formatted intelligently up to 7 decimal places (`$0.0000045`), and compact notation on MiniToo 128px displays (`$4.5u`).
- **Visuals**: Recognizable badge badges (`₿`, `Ξ`, `◎`, `Ð`, `🐸`) and 24-point phosphor sparklines with daily high/low.

### 2. AI Usage Section
- **OpenAI Codex**: Authoritative chatgpt backend API via `~/.codex/auth.json`. Displays 5-Hour and Weekly `% LEFT`.
- **Google Gemini / Antigravity**: Live Google backend quota via headless `agy -p /usage`. Displays 5-Hour and Weekly `% LEFT`.
- **Anthropic Claude Diagnostics**:
  - Exposes active account identity with privacy masking (`no***@gmail.com`).
  - Reports subscription plan (`Claude Pro`) and authentication type (`Subscription (OAuth)`).
  - Probes environment variables (`ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, etc.) and documents precedence.
  - Supports isolated secondary authentication directories (`~/.claude-secondary`) without credential scraping or session hijacking.

### 3. Volatile Stocks Scanner Section
- **Definition**: Ranks top 10 most volatile US equities today using an objective intraday range metric:
  $$\text{Volatility \%} = \frac{\text{Day High} - \text{Day Low}}{\text{Previous Close}} \times 100$$
- **Pluggable Architecture**:
  - `YahooFinanceMarketDataProvider`: Public crumb-session provider for US liquid equities (no credentials required).
  - `FinnhubMarketDataProvider`: Pluggable commercial API provider via optional `FINNHUB_API_KEY`.
- **Display**: Symbol, current price, net day change %, intraday volatility %, and market state (`OPEN`, `POST`, `CLOSED`).

### 4. System & Services Section
- **Local PC**: GPU utilization, VRAM, GPU temperature (`nvidia-smi`), CPU and RAM utilization (`psutil`).
- **DGX Spark (Remote)**: SSH / Tailscale socket probe with local JSON cache and offline grace period.
- **Services Health**: Non-blocking TCP socket connect checks across local and remote container services (`:22`, `:11434`, etc.).
- **Coding Workspace**: Working directory Git branch, clean/dirty state, and active AI model.
- **AI Activity Monitor**: Real-time detection of local agent processes (Codex, Claude, Gemini) and active write logs.

---

## 🖥️ Supported Hardware

- **Divoom MiniToo**: 160×128 color IPS LCD display over Bluetooth SPP virtual serial port.
- **Divoom Ditoo / Ditoo Plus**: 16×16 RGB LED pixel matrix display over direct BLE GATT (`DitooPro-Light` / Microchip ISSC Transparent UART) or Bluetooth SPP.
- **Physical Controls**: MiniToo rotary knob (navigation) and Ditoo mechanical keys / lever.
- **Custom Display Channel**: Uses Channel 5 (Custom/DIY) and command `0x8B` to maintain host application ownership without firmware timeout to clock mode.
- **Desktop-Only Mode**: Completely standalone mode for developers without physical hardware.

---

## 🏛️ Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          DATA COLLECTORS                               │
│  MultiCrypto (CoinGecko) · Stocks Scanner (Yahoo/Finnhub) · Local PC   │
│  DGX Spark (SSH) · Codex · Gemini (Antigravity) · Claude Diagnostics   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Unified 60s/10s/2s polling intervals
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        NORMALIZED STATE ENGINE                         │
│           DashboardState  ·  DataEngine  ·  DashboardConfig            │
│         Sections Order  ·  Cards Order  ·  Presets (ALL/AI/...)        │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
┌───────────────────────────────────────┐ ┌──────────────────────────────┐
│           DESKTOP RENDERER            │ │       MINITOO RENDERER       │
│  Modular Sections & Presets (Tkinter) │ │   PIL 160x128 Framebuffer    │
│  Scrollable Canvas & Settings Dialog  │ │   Channel 5 Keep-Alive & Spp │
└───────────────────┬───────────────────┘ └──────────────┬───────────────┘
                    │                                    │ Bluetooth SPP
                    ▼                                    ▼
┌───────────────────────────────────────┐ ┌──────────────────────────────┐
│        Desktop Companion App          │ │        Divoom MiniToo        │
│        (Interactive Controller)       │ │     (Physical Hardware)      │
└───────────────────────────────────────┘ └──────────────────────────────┘
```

For detailed protocol specifications, SPP framing diagrams, and remote SSH flow, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🔒 Privacy & Security Model

- **100% Local Execution**: All metrics collection and rendering executes strictly on your local machine.
- **Zero Secret Ingestion**: The dashboard configuration (`config.json`) stores only UI preferences. It **never** stores API keys, OAuth tokens, or passwords.
- **Masked Account Identities**: Emails and account identifiers are strictly masked in diagnostics (e.g. `no***@gmail.com`).
- **Defense in Depth**: Subprocess invocations for local CLIs (`agy`, `git`, `ssh`) run directly via system binary paths without shell interpolation (`shell=False`).
- **No Third-Party Telemetry**: Zero analytics, trackers, or telemetry beacons.

---

## 🛠️ Development & Testing

```powershell
# Run full unit test suite (30 tests, mock-isolated)
pytest tests/ -v

# Run headless dashboard terminal status report
python dashboard.py --status

# Test hardware port auto-detection
python -c "from detector import detect_minitoo_port; print('Port:', detect_minitoo_port())"

# Export static 160x128 preview frames
python dashboard.py --preview

# Rebuild documentation screenshots
python tools/build_screenshots.py

# Build single-file executable using PyInstaller
pyinstaller "AI Desk Dashboard.spec"
```

For guidelines on repository structure and contributing, read [CONTRIBUTING.md](CONTRIBUTING.md).

For autonomous coding agents (Codex, Claude Code, Antigravity), see [AGENTS.md](AGENTS.md) and [docs/AGENT-QUICKSTART.md](docs/AGENT-QUICKSTART.md).

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
