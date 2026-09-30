# Installation & Setup Guide

**AI Desk Dashboard** is designed to work out of the box with zero configuration for casual users, while offering deep customization and extensibility for developers.

Choose your installation path below:

---

## Path A: Normal User (Windows Executable)

No Python, command line, or build tools required.

### 1. Download & Launch
1. Download the latest `AI Desk Dashboard.exe` from the [Releases](https://github.com/Tacdelgineer/Divoom-display/releases) page.
2. Place `AI Desk Dashboard.exe` in any folder of your choice (e.g., `C:\Users\<YourUser>\AppData\Local\Programs\AiDeskDashboard\` or your Desktop).
3. Double-click `AI Desk Dashboard.exe` to start.

### 2. Pair Divoom MiniToo (Optional Hardware)
If using the physical Divoom MiniToo display:
1. Turn on your MiniToo.
2. Open Windows **Settings → Bluetooth & devices → Add device**.
3. Select **Bluetooth** and pair with `MiniToo-xxxx` (or `Divoom-xxxx`).
4. Once paired, launch or reopen AI Desk Dashboard.
5. The application automatically enumerates Bluetooth SPP serial ports and links to your MiniToo. The status in the header will switch to **MINITOO OK**.

### 3. Customize Your Dashboard
- **Creator Presets**: Use header buttons `[ ALL ]`, `[ AI ]`, `[ CRYPTO ]`, `[ STOCKS ]`, `[ SYSTEM ]` for instant layout switching.
- **Creator Focus Mode**: Click `[ 🔍 FOCUS ]` on any section header to film or view that section in a dedicated enlarged hero layout. Click `[ ◀ BACK / ALL ]` to return.
- **Redesigned 5-Tab Settings**: Click the **⚙ SETTINGS** button in the header to open the categorized configuration modal:
  - **GENERAL**: Windows startup (`HKCU\Run`), launch minimized, default startup preset, refresh behavior.
  - **DASHBOARD**: Expandable section tree with independent **Desktop [x]** and **MiniToo [x]** toggles per card, plus dedicated `▲` / `▼` ordering buttons.
  - **MINITOO**: Bluetooth connection status, transport mode (**NORMAL** vs **LOW INTERFERENCE**), auto-cycle toggle, dwell interval (seconds per page), knob toggle, poll rate, live rolling 60-second telemetry, and hardware action buttons (**TEST DISPLAY**, **RECONNECT**, **COPY DIAGNOSTICS**).
  - **INTEGRATIONS**: Remote DGX Spark hostname/Tailscale IP, optional Finnhub API key, and Claude account profile discovery.
  - **ADVANCED**: Protocol debug logs and diagnostic reporting.
- **Bluetooth Headphones / Audio Coexistence**:
  If your Bluetooth headphones or speakers experience audio stutters or drops while communicating with the MiniToo, set **Bluetooth Mode** to **LOW INTERFERENCE** under **Settings → MiniToo**. This throttles knob polling to ~2.8 Hz and elides redundant frame transfers, freeing 2.4 GHz radio airtime. For complete troubleshooting, see [docs/BLUETOOTH.md](BLUETOOTH.md).

---

## Data Providers & Integrations

AI Desk Dashboard connects to local developer tools, system sensors, and market feeds. **Every integration is completely optional and failure-safe**: if an integration is unconfigured or unavailable, the rest of the dashboard continues updating smoothly.

### 1. Multi-Asset Crypto (`BTC`, `ETH`, `SOL`, `DOGE`, `PEPE`)
- **How it works**: Queries live spot prices, 24-hour deltas, and highs/lows for 5 major assets simultaneously using a **single** CoinGecko simple price request.
- **Cache**: 60-second local JSON cache (`.crypto_cache.json`) to stay within public rate limits without needing exchange credentials.
- **Micro-Token Formatting**: For tokens under $0.01 (such as PEPE at ~$0.0000045), prices format cleanly as `$0.0000045` on desktop and `$4.5u` on MiniToo displays.

### 2. Top 10 Volatile US Stocks Scanner
- **How it works**: Evaluates a high-volume liquid US equities basket and ranks the Top 10 by objective intraday volatility:
  $$\text{Volatility \%} = \frac{\text{Day High} - \text{Day Low}}{\text{Previous Close}} \times 100$$
- **Default Provider**: `YahooFinanceMarketDataProvider` (zero API key required; fetches quotes via session cookies and crumbs with a 60-second cache).
- **Optional Finnhub Provider**: Set the environment variable `FINNHUB_API_KEY` to route quotes through Finnhub's official REST API.
- **Market Hours**: Automatically detects regular trading hours (`OPEN`), pre-market (`PRE`), after-hours (`POST`), or weekend/holiday (`CLOSED`).

### 3. Anthropic Claude (Diagnostics & Secondary Profile)
- **Account Discovery**: Safely inspects active authentication from `~/.claude.json`. Displays account email (masked: `no***@gmail.com`), subscription plan tier, and auth type.
- **Diagnostics Dialog**: Click **CLAUDE ACCOUNTS** in Settings or on the Claude card to view active profile details, environment variable precedence, and usage cache status.
- **Adding a Secondary Account**:
  Claude Code does not support simultaneous logins in the same directory, but natively supports `CLAUDE_CONFIG_DIR`. To configure a secondary profile:
  1. Open PowerShell and run:
     ```powershell
     $env:CLAUDE_CONFIG_DIR = "$HOME\.claude-secondary"
     claude auth login
     ```
  2. In AI Desk Dashboard, the secondary profile will be read from its isolated folder without altering your primary Claude session.

### 4. OpenAI Codex
- **How it works**: Reads your local authenticated Codex CLI session from `~/.codex/auth.json` to query authoritative remaining quota directly from ChatGPT's backend usage API.
- **If missing / unauthenticated**: The Codex card displays `READY` or `N/A`. No errors or crashes occur.

### 5. Google Gemini & Antigravity
- **How it works**: Queries Google's backend quota via the official Antigravity CLI (`agy -p /quota`).
- **If missing / unauthenticated**: The Gemini card displays `LOCAL ONLY` or plan tier with safe fallback values.

### 6. NVIDIA GPU (Local PC)
- **How it works**: Queries `nvidia-smi` every 2 seconds for GPU utilization, VRAM usage, and core temperature. System RAM and CPU are collected via `psutil`.
- **If missing / non-NVIDIA**: The GPU row gracefully hides or displays `UNAVAILABLE`, while CPU and RAM metrics remain fully active.

### 7. Remote DGX Spark
- **How it works**: Probes remote cluster metrics via SSH or Tailscale. Configurable under Settings via `DGX Host / IP` (default: `dgx`).
- **If offline or unreachable**: The card displays an `OFFLINE` badge with cached timestamps. Background polling has a strict 3-second timeout that will never freeze the desktop UI.

### 8. Git / Coding Workspace
- **How it works**: Checks git branch, uncommitted diffs, and recent commit history for the configured repository path.
- **If not a git repository**: Displays directory name and standard status.

---

## Path B: Developer Setup (From Source)

### Prerequisites
- Python 3.10 or higher
- Git
- Windows 10 or 11 (primary supported OS)

### 1. Clone & Setup Environment

```powershell
# Clone the repository
git clone https://github.com/Tacdelgineer/Divoom-display.git
cd Divoom-display

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### 2. Run Applications

```powershell
# Run the Desktop Companion GUI application
python dashboard_app.py

# Run headless terminal diagnostic report
python dashboard.py --status

# Run MiniToo physical display driver in CLI rotation mode
python dashboard.py --cycle --interval 5.0

# Export static 160x128 preview PNGs
python dashboard.py --preview

# Run unit tests
pytest tests/ -v
```

### 3. Build Windows Executable

To package a standalone executable matching official releases:

```powershell
pyinstaller "AI Desk Dashboard.spec"
```

The resulting binary will be created at `dist\AI Desk Dashboard.exe`.

---

## Troubleshooting

- **MiniToo not connecting?**
  1. Open Windows Bluetooth Settings and confirm the MiniToo is listed as **Paired** or **Connected**.
  2. Run `python -c "from detector import detect_minitoo_port; print(detect_minitoo_port())"` to check port resolution.
  3. Ensure no other application (such as the Divoom mobile app or another terminal window) holds an active serial handle to the port.
- **Console window flashing?**
  All subprocesses in AI Desk Dashboard use `subproc.py` with `CREATE_NO_WINDOW` and `SW_HIDE`. If you add custom scripts, always route subprocess calls through `subproc.run_hidden()` or `subproc.check_output_hidden()`.
- **Logs location**:
  Startup and diagnostic logs are written to:
  `%APPDATA%\AiDeskDashboard\launch.log`
