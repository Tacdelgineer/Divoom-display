# Architecture & Technical Deep-Dive

**AI Desk Dashboard** is built on a modular pipeline designed for reliability, fast rendering, and complete hardware isolation.

> **Crucial Concept**:  
> **All dashboard logic, data collection, and rendering runs entirely on the host PC.**  
> The physical Divoom MiniToo acts strictly as a remote display peripheral receiving rendered image frames over Bluetooth SPP. No custom code or Python runs on the MiniToo firmware.

---

## 1. End-to-End Data Pipeline

The system follows a strict unidirectional data flow:

```
┌────────────────────────────────────────────────────────┐
│                    DATA COLLECTORS                     │
│  - LocalPcCollector (nvidia-smi, psutil)               │
│  - CodexUsageProvider (~/.codex/auth.json API)         │
│  - GeminiUsageProvider (agy CLI / Google backend)      │
│  - ClaudeUsageProvider (local workspace state)         │
│  - DgxSparkCollector (remote SSH / Tailscale)          │
│  - BtcCollector (CoinGecko / Binance public API)       │
│  - AiActivityCollector (agent sessions / diffs)        │
│  - ServicesCollector (TCP socket port probes)          │
│  - CodingStatusCollector (git repo status)             │
└──────────────────────────┬─────────────────────────────┘
                           │ Returns PageData models
                           ▼
┌────────────────────────────────────────────────────────┐
│           NORMALIZED STATE CONTAINER (engine.py)       │
│  - DashboardState (thread-safe dict of PageData)       │
│  - DataEngine (background scheduling thread)           │
│  - Event dispatcher (listeners notify on change)       │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     DESKTOP RENDERER      │ │     MINITOO RENDERER      │
│  (dashboard_app.py)       │ │  (renderer.py)            │
│  - Native Tkinter canvas  │ │  - Pillow 160x128 RGB     │
│  - 3x3 interactive cards  │ │  - 8x10 tile alignment    │
│  - Active card highlighting│ │  - Retro CRT palette      │
└──────────────┬────────────┘ └─────────────┬─────────────┘
               │                            │
               ▼                            ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     DESKTOP DISPLAY       │ │      MINITOO DISPLAY      │
│     Windows GUI Window    │ │     Bluetooth SPP (0x8B)  │
└───────────────────────────┘ └───────────────────────────┘
```

---

## 2. Remote DGX Compute Flow

To monitor remote GPU servers (such as an NVIDIA DGX Spark node) without blocking local UI execution:

```
Desktop Host (Windows)
   │
   │ 1. Executes lightweight Python one-liner via OpenSSH over Tailscale
   │    Command: ssh -o BatchMode=yes -o ConnectTimeout=3.0 <host> "python3 -c '...'"
   │    Routed via subproc.py (CREATE_NO_WINDOW prevents console popup)
   ▼
Remote Linux Machine (DGX)
   │
   │ 2. Queries local nvidia-smi (GPU util, VRAM, temp)
   │ 3. Reads /proc/meminfo and /proc/uptime
   │ 4. Outputs single-line JSON string over SSH stdout
   ▼
Desktop Host Collector
   │
   │ 5. Parses JSON output into normalized PageData model
   │ 6. Writes cache to .dgx_cache.json with timestamp
   │ 7. Updates DashboardState
   ▼
Renderers
   │
   │ 8. Desktop App & MiniToo update card in real time
```

### Safety & Resilience Invariant
If the DGX machine is asleep, disconnected, or Tailscale is offline:
- The SSH probe hits a strict **3.0-second timeout**.
- The collector marks the metrics `UNAVAILABLE` and displays an `OFFLINE` badge.
- The UI **never hangs, stalls, or drops frames**.

---

## 3. MiniToo Hardware Transport Flow

The Divoom MiniToo uses a proprietary Bluetooth SPP protocol over an emulated virtual serial COM port.

```
AI Desk Dashboard Host
   │
   │ 1. detector.detect_minitoo_port() scans Windows Bluetooth SPP ports
   │    Scores device metadata (Vendor ID 0x05D6, "MiniToo")
   │    Safely probes with read-only channel query (0xBD 0x13)
   ▼
Port Acquired (e.g. COM7 at 115200 baud)
   │
   │ 2. Sets device channel: 0xBD -> Custom / DIY Channel 5
   │    CRITICAL: Channel 5 prevents firmware from reverting to Clock mode!
   ▼
Image Frame Streaming
   │
   │ 3. renderer.py builds 160x128 24-bit RGB JPEG (quality 85)
   │ 4. minitoo.py packs JPEG into 8x10 tile media payload
   │ 5. Splits payload into chunked SPP frames (0x8B command)
   │ 6. Sends frames with ACK acknowledgment
   ▼
Divoom MiniToo Hardware
   │
   │ 7. Renders 160x128 image directly onto IPS LCD panel
```

---

## 4. Physical Knob Navigation Flow

The MiniToo physical rotary knob does not transmit unsolicited keypresses over Bluetooth. AI Desk Dashboard navigates pages by polling device state at ~16 Hz:

```
MiniTooInputAdapter Loop (~16 Hz)
   │
   │ 1. Queries device volume: Command 0x09
   ▼
MiniToo Responds with Current Volume (0..16)
   │
   │ 2. Compares volume with target base volume (8 / 16)
   │
   ├── If volume > 8:
   │   - Knob was rotated CLOCKWISE
   │   - Triggers NEXT_PAGE event
   │   - Restores volume back to 8 (Command 0x08)
   │
   ├── If volume < 8:
   │   - Knob was rotated COUNTER-CLOCKWISE
   │   - Triggers PREV_PAGE event
   │   - Restores volume back to 8 (Command 0x08)
   │
   └── If volume == 8:
       - No knob movement; idle loop
```

### Benefits of Base Restoration
- **Zero Audio Glitches**: Because the volume level is immediately restored to 8, no sudden volume jump occurs if an audio stream is playing.
- **Infinite Rotation**: The knob acts as an infinite optical encoder without hitting firmware 0 or 16 endpoints.
- **Hardware Debouncing**: Events are software-debounced with a 250ms window to guarantee exactly one page transition per physical knob detent.

---

## 5. Threading Model

```
Main Thread (Tkinter GUI Loop)
   ├── Renders Canvas (628x512)
   ├── Processes mouse clicks, window drag, settings modals
   └── Receives state notifications via event callbacks

DataEngine Thread (Daemon)
   ├── Loops through configured page_order
   ├── Dispatches collectors at configured refresh intervals
   └── Updates DashboardState under threading.Lock

MiniTooController Thread (Daemon)
   ├── Manages serial connection to MiniToo
   ├── Pushes active page frame when data changes or rotation triggers
   └── MiniTooInputAdapter polls rotary knob events
```
All shared state mutations in `DashboardState` are guarded by `threading.Lock`, guaranteeing thread-safe reads by the UI.
