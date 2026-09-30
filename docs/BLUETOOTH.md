# Bluetooth Architecture & Audio Coexistence Guide

This document details the Bluetooth communication architecture of **AI Desk Dashboard**, explains the physical RF and bandwidth contention that can occur between Bluetooth serial devices and Bluetooth audio (headphones/speakers), and documents the mitigation strategies, transport modes, diagnostics, and advanced multi-adapter setups implemented in Milestone 13.

---

## 1. Bluetooth Protocol & Device Architecture

The **Divoom MiniToo** communicates with the host PC using **Bluetooth Classic Serial Port Profile (SPP)** over RFCOMM on standard Windows COM ports (e.g., `COM13`).

### SPP Packet Framing
Every transaction between the PC and the MiniToo is framed with a proprietary Divoom packet structure:
```
[0x01] [Length LSB] [Length MSB] [Command] [Payload...] [Checksum LSB] [Checksum MSB] [0x02]
```
- **Image Transmission:** A 160×128 pixel 16-bit RGB565 framebuffer requires 40,960 raw bytes, divided into framed chunks (initial `0x44` command header + subsequent chunk packets).
- **Physical Controls (Rotary Knob / Volume):** Polled via command `0x09` (read volume / control state) or centered base volume resets via `0x08`.
- **Channel Ownership:** Polled via command `0xBD 0x13` to confirm the device remains in Custom/DIY Channel 5.

---

## 2. Root Cause of Bluetooth Audio Interference

In many modern PCs and laptops, a single internal M.2 Wi-Fi / Bluetooth combination card (e.g., **MediaTek RZ616 / MT7921**, **Intel Wi-Fi 6E AX210 / AX200**, or **Realtek RTL8852**) handles all 2.4 GHz wireless traffic, including:
1. **Bluetooth A2DP Audio Streaming:** Requires continuous, time-sensitive isochronous slots (SBC, AAC, aptX, or LDAC codecs).
2. **Bluetooth HID (Human Interface Devices):** Wireless keyboards and mice.
3. **Bluetooth Classic RFCOMM (MiniToo SPP):** Bidirectional serial data exchanges.

### The Contention Mechanism
Prior to Milestone 13, the MiniToo controller polled the hardware knob at ~10–16 Hz (each poll sending an inquiry packet and waiting for a serial response) and executed Channel 5 queries every 8 seconds, alongside a 15-second periodic heartbeat framebuffer retransmission.

This high transaction rate created severe packet contention:
- **Bandwidth & Slot Starvation:** Bluetooth uses Time-Division Duplex (TDD) slots of 625 microseconds. Frequent, un-throttled SPP command/response round-trips saturated the baseband scheduler on shared radios, forcing the adapter to drop or delay A2DP audio packets.
- **Audible Symptoms:** Periodic audio dropouts, micro-stutters, crackling, or temporary speaker disconnections (especially on high-bitrate Bluetooth speakers like the Edifier R1700BTs).

---

## 3. Milestone 13 Traffic Reduction & Coexistence Engine

To resolve audio dropouts without losing control responsiveness, Milestone 13 implements four fundamental optimizations:

### A. Strict Frame Diffing (Zero Redundant Retransmissions)
- The framebuffer is hashed and diffed against the last transmitted byte stream before transmission.
- If data has not materially changed (or a timer fired without new pixels), **zero bytes are transmitted over Bluetooth**.
- The periodic 15-second heartbeat has been eliminated entirely.

### B. Intelligent Knob Polling Cadence
- Knob polling was reduced from an aggressive 16 Hz down to **~4 Hz (0.25s)** in NORMAL mode and **~2.8 Hz (0.35s)** in LOW INTERFERENCE mode.
- Users can also select explicit rates: `2Hz` (0.50s), `3Hz` (0.33s), `4Hz` (0.25s), or `5Hz` (0.20s), or disable knob polling entirely (`Knob Navigation: OFF`).

### C. Relaxed Health Checks
- In stable operation, Channel 5 drift checks are relaxed to **60 seconds** in NORMAL mode and **120 seconds** in LOW INTERFERENCE mode.
- High-frequency checks are only executed during reconnection.

### D. Decoupled Collector Refresh vs. Screen Transmission
- Internal metric collectors (GPU, CPU, Quotas, Crypto, Stocks) continue updating `DashboardState` at their normal live frequencies.
- **MiniToo physical transmission only occurs for the currently displayed page.** If the MiniToo is showing `BTC`, background GPU or Claude collector refreshes trigger 0 Bluetooth packets.

---

## 4. NORMAL vs. LOW INTERFERENCE Mode

Users can configure the Bluetooth transport mode directly under **Settings → MiniToo → Transport Mode**:

| Parameter | NORMAL Mode | LOW INTERFERENCE Mode |
| :--- | :--- | :--- |
| **Primary Goal** | Balanced responsiveness | Maximum audio coexistence & low radio contention |
| **Knob Poll Rate (AUTO)** | ~4 Hz (0.25s interval) | ~2.8 Hz (0.35s interval) |
| **Physical Frame Throttle** | 0.5s minimum cadence | 3.0s minimum cadence |
| **Channel 5 Check** | 60 seconds | 120 seconds |
| **Desktop Companion** | Fully live (instant) | Fully live (instant) |
| **Typical SPP Writes** | ~240 writes / min | ~150–170 writes / min (~35–45% reduction) |
| **Frame Heartbeats** | 0 (Strict diffing) | 0 (Strict diffing) |

---

## 5. Hardware Diagnostics & Telemetry

Real-time Bluetooth telemetry is exposed in the **Settings → MiniToo** panel:

- **Status & Port:** Active connection state and assigned Windows COM port.
- **Transport Mode:** `NORMAL` or `LOW INTERFERENCE`.
- **Rolling Traffic (Last 60s):**
  - SPP Writes / min
  - SPP Reads / min
  - Frames Transmitted / min
  - Bytes Transmitted / min & KB/min
  - Knob Polls / sec (Hz)
  - Channel Checks / min
- **Session Totals:** Cumulative frames sent, bytes sent, reconnect count, and last error.

### Copying Diagnostics
Click the **`[ 📋 COPY DIAGNOSTICS ]`** button in the Settings dialog to copy a formatted report to the Windows clipboard for debugging or GitHub issue reporting.

---

## 6. Advanced Workaround: Dedicated Secondary Bluetooth Adapter

If you use a high-bitrate Bluetooth audio codec (LDAC / aptX HD) and your PC motherboard radio still exhibits contention even in LOW INTERFERENCE mode, you can physically isolate the MiniToo using a secondary USB Bluetooth adapter:

1. **Insert a Dedicated USB Bluetooth Dongle:**
   - Standard USB Bluetooth 5.0 or 5.3 dongles (e.g. TP-Link UB500, Asus USB-BT500) cost ~$10.
2. **Windows Device Association:**
   - In Windows *Settings → Bluetooth & Devices*, remove the MiniToo pairing.
   - Insert the secondary USB dongle. If Windows automatically uses the primary radio, you can disable the primary radio in Device Manager temporarily during pairing, or assign the MiniToo specifically through the secondary adapter's vendor software.
   - Pair the MiniToo so that its incoming and outgoing COM ports (`COM13`, etc.) route through the dedicated USB dongle.
3. **Audio Routing:**
   - Keep your Bluetooth speakers or headphones paired to the primary motherboard Bluetooth radio.
   - Now, MiniToo SPP serial traffic and Bluetooth audio run on **completely independent radios and antennas**, achieving 100% hardware isolation with zero interference.

---

## 7. Troubleshooting & FAQ

### Q: Why does the MiniToo show "Access is denied" on its COM port?
**A:** Windows Bluetooth COM ports allow only one process at a time. If an existing background instance of `AI Desk Dashboard.exe` or another terminal process is holding the port open, close the running app or terminate it in Task Manager before restarting.

### Q: Audio still micro-stutters during initial connection. Why?
**A:** When the MiniToo first powers on or reconnects, the PC must transmit an initial full 40 KB framebuffer and negotiate RFCOMM channels. This takes ~1–2 seconds. Once connected, traffic drops to the minimal ~2.8–4 Hz knob cadence with zero redundant frames.

### Q: Does Low Interference mode affect the desktop dashboard?
**A:** No. The desktop application window remains fully live with all charts, sparklines, and metric meters updating in real time. Low Interference mode only optimizes physical Bluetooth transmission to the MiniToo screen.
