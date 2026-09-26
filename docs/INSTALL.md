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
- Click the **GEAR** icon in the top-right corner to open Settings.
- **Enable / Disable Pages**: Toggle checkboxes for any page you want to see.
- **Reorder Pages**: Select a page and click **▲ Move Up** or **▼ Move Down**.
- **Rotation Interval**: Adjust seconds per page for automatic cycling.
- **Start with Windows**: Enable to automatically launch the dashboard on system boot.

---

## Optional Integrations & Graceful Fallbacks

AI Desk Dashboard connects to local developer tools and workstation services. **Every integration is completely optional and failure-safe**: if an integration is unconfigured or unavailable, the rest of the dashboard continues updating smoothly.

### 1. OpenAI Codex
- **How it works**: Reads your local authenticated Codex CLI session from `~/.codex/auth.json` to query authoritative remaining quota directly from ChatGPT's backend usage API.
- **If missing / unauthenticated**: The Codex card displays `READY` or `N/A`. No errors or crashes occur.

### 2. Google Gemini & Antigravity
- **How it works**: Queries Google's backend quota via the official Antigravity CLI (`agy -p /quota`).
- **If missing / unauthenticated**: The Gemini card displays `LOCAL ONLY` or plan tier with safe fallback values.

### 3. Anthropic Claude
- **How it works**: Displays active Claude session state and current model tier.
- **Note on Anthropic quotas**: Anthropic does not currently provide a public personal quota API. The card displays active status without guessing or fabricating numbers.

### 4. NVIDIA GPU (Local PC)
- **How it works**: Queries `nvidia-smi` every 2 seconds for GPU utilization, VRAM usage, and core temperature. System RAM and CPU are collected via `psutil`.
- **If missing / non-NVIDIA**: The GPU row gracefully hides or displays `UNAVAILABLE`, while CPU and RAM metrics remain fully active.

### 5. Remote DGX Spark
- **How it works**: Probes remote cluster metrics via SSH or Tailscale. Configurable under Settings via `DGX Host / IP` (default: `dgx`).
- **If offline or unreachable**: The card displays an `OFFLINE` badge with cached timestamps. Background polling has a strict 3-second timeout that will never freeze the desktop UI.

### 6. Bitcoin (BTC)
- **How it works**: Fetches live spot price and 24-hour delta from public crypto APIs (CoinGecko / Binance) with automatic 60-second caching.
- **If offline**: Re-renders the last cached sparkline and price without interrupting page rotation.

### 7. Git / Coding Workspace
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
pip install --upgrade pip
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
