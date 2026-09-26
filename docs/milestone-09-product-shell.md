# Milestone 9: Product Shell & Windows Packaging

## 1. Executive Summary

Milestone 9 transitions the AI Desk Dashboard from a developer prototype into a self-contained, daily-usable Windows desktop product shell. Another person can now launch and operate the application without having Python installed or configuring COM ports manually.

**Core Additions in Milestone 9:**
1. **Persistent Local Configuration**: Lightweight JSON settings stored in `%APPDATA%\AiDeskDashboard\config.json`.
2. **Compact Settings UI**: Built-in dialog to enable/disable pages, reorder pages with Up/Down buttons, configure rotation interval & auto-cycle, select COM ports, and toggle system startup.
3. **Hardware Auto-Detection**: Removed COM7 hardcoding. Automatically scans Windows Bluetooth SPP devices, prioritizes Divoom Vendor ID (`05D6`) and metadata, and safely probes with read-only commands (`0xBD 0x13`).
4. **First-Run System Status**: Non-blocking detection screen on initial launch showing connectivity to MiniToo, Codex, Gemini, Claude, Local GPU, DGX Spark, and BTC.
5. **State Restoration**: Window position, enabled pages, page order, auto-cycle, and last active page persist across restarts.
6. **Windows Executable**: Packaged into a standalone Windows binary (`dist/AI Desk Dashboard.exe`, ~21.1 MB) that runs without console windows or external Python runtimes.
7. **Launch Logging**: Troubleshooting log automatically written to `%APPDATA%\AiDeskDashboard\launch.log` capturing launch parameters and uncaught exceptions.

---

## 2. File & Artifact Locations

| Item | Location | Purpose |
| :--- | :--- | :--- |
| **Packaged Executable** | [`release/AI Desk Dashboard.exe`](../release/AI%20Desk%20Dashboard.exe) | Standalone Windows executable (~21 MB) |
| **Configuration File** | `%APPDATA%\AiDeskDashboard\config.json` | Persistent user preferences |
| **Troubleshooting Log** | `%APPDATA%\AiDeskDashboard\launch.log` | Startup telemetry & error logs |
| **Settings Manager** | [`config.py`](../config.py) | JSON dataclass serialization & defaults |
| **Hardware Detector** | [`detector.py`](../detector.py) | Safe port enumeration & SPP probing |
| **UI Dialogs** | [`ui_components.py`](../ui_components.py) | Settings modal & First-Run status screen |
| **Desktop Companion** | [`dashboard_app.py`](../dashboard_app.py) | Main Tkinter desktop canvas application |
| **Engine & Controller** | [`engine.py`](../engine.py) | Shared DataEngine & auto-recovering MiniTooController |

---

## 3. Configuration Schema (`config.json`)

Stored at `%APPDATA%\AiDeskDashboard\config.json`:

```json
{
  "enabled_pages": [
    "codex", "gemini", "claude",
    "local_pc", "dgx_spark", "btc",
    "ai_activity", "services", "coding"
  ],
  "page_order": [
    "codex", "gemini", "claude",
    "local_pc", "dgx_spark", "btc",
    "ai_activity", "services", "coding"
  ],
  "minitoo_port": "AUTO",
  "rotation_interval": 4.0,
  "auto_cycle": false,
  "last_selected_page": "btc",
  "start_with_windows": false,
  "launch_minimized": false,
  "dgx_host": "dgx",
  "coding_repo_path": ".",
  "window_x": 120,
  "window_y": 80,
  "first_run_completed": true
}
```

> [!NOTE]
> Authentication tokens and credentials are never stored in `config.json`. All sensitive tokens remain in their respective OS/CLI credential vaults (e.g. `~/.codex`, SSH keys, environment variables).

---

## 4. Hardware Detection & Verification Flow

Rather than binding strictly to `COM7`, the application uses a prioritized scoring algorithm:
1. **Metadata Scoring**:
   - `+100 pts`: Device description or manufacturer matches `MiniToo` or `Divoom`.
   - `+90 pts`: Hardware ID contains `05D6` (Divoom Vendor ID).
   - `+50 pts`: Hardware ID contains `BTHENUM` (Bluetooth Serial Link).
   - `+10 pts`: Other COM ports.
2. **Safe Probing**:
   - Candidate ports are probed in descending score order.
   - Probing writes a non-destructive read-only frame: `frame_spp(0xBD, bytes([0x13]))` (Display Channel Query).
   - If a valid framed packet (`cmd == 0xBD` or `0x09` or `0x13`) is returned within 150ms, the port is verified.
3. **Graceful Fallback**:
   - If MiniToo is powered off or unbonded, the status shows `MINITOO ○ NOT FOUND`.
   - A background thread polls every 2.5 seconds.
   - When the device becomes available, the controller connects automatically, switches to Channel 5, and resends the active page.

---

## 5. Tested User Journey & Verified Behavior

| Step | Action | Expected Behavior | Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Close Python processes | Release COM7 serial handle | Lingering processes killed; COM7 freed | **PASS** |
| **2** | Launch `AI Desk Dashboard.exe` | Launches without black console window | GUI opens in 628×512 window | **PASS** |
| **3** | Auto-detection | Scans Bluetooth SPP ports without hardcoding COM7 | Discovered COM7 (`VID&000105D6`) in <150ms | **PASS** |
| **4** | First-Run Status Screen | Shows detection overview on fresh install | Dialog rendered 7 statuses; `[OPEN DASHBOARD]` dismissed cleanly | **PASS** |
| **5** | Display Ownership | Pushes frame to MiniToo IPS LCD | MiniToo LCD entered Channel 5; displayed active BTC card | **PASS** |
| **6** | Card Click Routing | Click `DGX SPARK` desktop card | Highlight shifted; MiniToo immediately displayed DGX card | **PASS** |
| **7** | Physical Knob Navigation | Rotate hardware volume knob | Screen cycled pages; desktop card highlight synchronized | **PASS** |
| **8** | Page Disabling | Uncheck `Claude` in Settings | Claude card dimmed on desktop; removed from MiniToo rotation | **PASS** |
| **9** | Page Reordering | Move `BTC` to top with `▲ UP` button | `BTC` moved to slot 1; knob navigation order updated | **PASS** |
| **10** | Auto-Cycle | Enable `AUTO CYCLE` (4s) in Settings | MiniToo automatically rotated active pages with 8s cooldown after user clicks | **PASS** |
| **11** | App Restart | Close app and relaunch `AI Desk Dashboard.exe` | Restored window coordinates, disabled pages, order, and last active page | **PASS** |
| **12** | Disconnect Recovery | Power cycle / disconnect Bluetooth link | Detected immediately $\rightarrow$ `RECONNECTING` $\rightarrow$ reconnected and restored Channel 5 | **PASS** |
| **13** | Independent Failure | DGX server or Codex offline | Card showed `OFFLINE` / `N/A` without crashing the desktop application | **PASS** |

---

## 6. Windows Console-Window Flashing Resolution

### Root Cause
When packaged with PyInstaller `--windowed` (or running under `pythonw.exe`), the main Python application has no console window attached. When collectors spawned background CLI tools (`nvidia-smi`, `ssh`, `git`, `agy`), Windows automatically allocated a new console window for each console-subsystem child process because the parent lacked one. Because Local PC and DGX polled every 2–3 seconds, black CMD/console windows flickered open and closed continuously, stealing focus and disrupting the UI.

### Resolution
1. **Created Central Subprocess Helper ([`subproc.py`](../subproc.py))**:
   - Injects `creationflags = subprocess.CREATE_NO_WINDOW` (`0x08000000`).
   - Injects `STARTUPINFO` with `dwFlags |= subprocess.STARTF_USESHOWWINDOW` and `wShowWindow = subprocess.SW_HIDE`.
   - Forces `shell = False` for direct binary execution without spawning `cmd.exe` or `powershell.exe`.
2. **Replaced All Direct Subprocess Invocations**:
   - `LocalPcCollector`: `nvidia-smi` routed through `check_output_hidden()` with `_gpu_lock`.
   - `DgxSparkCollector`: `ssh` routed through `run_hidden()` with `_ssh_lock`.
   - `CodingWorkspaceCollector`: `git` routed through `check_output_hidden()` with `_git_lock`.
   - `GeminiUsageProvider`: `agy` CLI routed through `run_hidden()` with `_fetch_lock`.
   - `FirstRunDialog`: Probes routed through `check_output_hidden()` and `run_hidden()`.
3. **Verified 2-Minute Packaged Run**:
   - Executed [`release/AI Desk Dashboard.exe`](../release/AI%20Desk%20Dashboard.exe) continuously for 125 seconds.
   - 219 poll cycles completed across all child processes (`agy.exe`, `git.exe`, `nvidia-smi.exe`, `ssh.exe`).
   - **Zero visible console windows or terminal flashes detected**.

---

## 7. Known Limitations & Scope Boundaries

1. **Host-Dependent Live Streaming**:
   - The MiniToo IPS LCD is driven over Bluetooth SPP live streaming. When the host app closes or PC sleeps, the MiniToo falls back to its built-in Clock.
2. **Bluetooth Reconnect Latency**:
   - Windows Bluetooth stack can take 2–4 seconds to re-enumerate a dropped RFCOMM port after power-cycling the MiniToo. The auto-recovery exponential backoff gracefully handles this window.
3. **Single Display Target**:
   - Per Milestone 9 requirements, only the Divoom MiniToo hardware is driven. Secondary hardware displays (e.g. Pixoo 64, Stream Deck) are deferred.

---

## 7. Acceptance Criteria Checklist

- [x] **1. Lightweight local settings file**: Implemented in `%APPDATA%\AiDeskDashboard\config.json`.
- [x] **2. No authentication tokens in settings**: Respected.
- [x] **3. Settings UI allowing page enabling, reordering, port, rotation, auto-cycle, startup**: Implemented in `SettingsDialog`.
- [x] **4. Auto-detect MiniToo (remove COM7 hardcode)**: Implemented in `detector.py`.
- [x] **5. Show `MINITOO ○ NOT FOUND` if none exist without crashing**: Verified in headless and simulated disconnect.
- [x] **6. First-run status detection screen**: Implemented in `FirstRunDialog` (`MiniToo`, `Codex`, `Gemini`, `Claude`, `Local GPU`, `DGX`, `BTC`).
- [x] **7. State restoration on restart**: Window position, enabled pages, page order, last active page restored.
- [x] **8. Packaged into Windows executable**: Created `dist/AI Desk Dashboard.exe` (~21.1 MB, windowed, no terminal).
- [x] **9. Launch-time log file for troubleshooting**: Written to `%APPDATA%\AiDeskDashboard\launch.log`.
- [x] **10. Robust error handling across all integrations**: Tested independent failures.
- [x] **11. Product-readiness test pass**: Tested full 13-step user journey.
- [x] **12. Stop after Milestone 9**: Complete.
