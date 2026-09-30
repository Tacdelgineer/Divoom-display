# Device Management & Hardware Onboarding

The **AI Desk Dashboard** is built from the ground up to support both physical retro hardware and standalone desktop workstations. Physical displays are completely optional—a missing device will never hang application startup, freeze the interface, or disable desktop features.

---

## 🧭 First-Run Setup Experience

Upon launching the application for the first time without a saved configuration, the **First-Run Device Setup Wizard** greets the user with 4 clear choices:

```
┌──────────────────────────────────────────────────────────┐
│                   CHOOSE YOUR DISPLAY                    │
│                                                          │
│  [ MiniToo ]          Bluetooth Classic / SPP            │
│  [ Ditoo ]            Bluetooth LE (GATT)                │
│  [ No Physical ]      Desktop dashboard only             │
│  [ Detect Auto ]      Scan all supported interfaces      │
└──────────────────────────────────────────────────────────┘
```

1. **MiniToo (Bluetooth Classic / SPP)**: Connects to Divoom MiniToo 160×128 color IPS LCD displays via Windows Serial Port Profile (SPP).
2. **Ditoo (Bluetooth LE)**: Scans and links to Divoom Ditoo / Ditoo Plus 16×16 RGB LED pixel matrix displays over Bluetooth Low Energy GATT.
3. **No Physical Display (Desktop Only)**: Immediately enters full desktop command center mode with all background hardware probes disabled.
4. **Detect Automatically**: Probes available COM ports and BLE adapters, connecting to any already-paired peripheral or gracefully falling back to Desktop mode.

---

## 🔌 Supported Display Tiers & Connection Behavior

| Tier | Interface | Auto-Connect | Windows Pairing Required? | Hardware Absence Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Desktop Only** | Native GUI (`tkinter` + PIL) | Instant | No | Default standalone workstation mode |
| **MiniToo** | Bluetooth Classic (SPP COM port) | Automatic if paired | **Yes (Once in Windows Bluetooth)** | Shows `PAIRING REQUIRED` or `NOT FOUND`, desktop works 100% |
| **Ditoo** | Bluetooth Low Energy (BLE GATT) | Automatic scan | No PIN pairing needed for standard BLE | Shows `OFFLINE` / `NOT FOUND`, desktop works 100% |
| **Dual Mode** | SPP + BLE simultaneously | Automatic | Yes for MiniToo | Independent worker threads; either device reconnects freely |

---

## 🖧 MiniToo Setup & Bluetooth Classic Details

> [!IMPORTANT]
> **Windows Classic Bluetooth Pairing Truthfulness:**
> Windows requires Bluetooth Classic (RFCOMM/SPP) devices to be paired at the operating system level before a virtual serial port (e.g. `COM7`, `COM13`) is assigned. The application **does not** silently pair Classic Bluetooth in the background without user intervention.

### First-Time MiniToo Pairing:
1. Turn on your Divoom MiniToo.
2. In the AI Desk Dashboard setup wizard or device panel, click **[ OPEN WINDOWS BLUETOOTH SETTINGS ]** (or open `ms-settings:bluetooth`).
3. Click **Add device** → **Bluetooth**, and select your **MiniToo**.
4. Once Windows completes pairing, return to AI Desk Dashboard and click **[ RESCAN ]**.
5. The application identifies the virtual SPP port (`VID 0x05D6` / `BTHENUM`) and sends safe read-only channel handshake query frames (`0xBD 0x13`).
6. After initial setup, AI Desk Dashboard remembers your COM port and automatically reconnects on startup.

---

## 👾 Ditoo Setup & Bluetooth Low Energy (BLE)

Ditoo 16×16 displays communicate via direct Bluetooth Low Energy (BLE) GATT characteristics (Microchip ISSC Transparent UART / `DitooPro-Light` profile).

### Ditoo Discovery:
- The Ditoo controller uses asynchronous BLE discovery (`bleak` / WinRT BLE API) to scan for local advertising devices matching `Ditoo`, `Ditoo-Plus`, or `DitooPro`.
- Once detected, the GATT write characteristic is established, and the display receives 16×16 monochrome or color pixel matrices.
- Mechanical keys and joystick switches transmit input notifications back to the application.
- If no Ditoo is powered on within range, the BLE scan times out silently without delaying desktop initialization.

---

## 🏷️ Standardized Connection States

Ambiguous connection labels (e.g. "error", "waiting") have been replaced with explicit standardized states:

- **`CONNECTED`**: Device verified and actively streaming framebuffers.
- **`CONNECTING`**: Handshake sequence or initial port probe in progress.
- **`RECONNECTING`**: Connection dropped; automatic background reconnection loop active (exponential backoff).
- **`PAIRING REQUIRED`**: MiniToo Bluetooth radio detected on host, but Windows device pairing has not yet completed.
- **`NOT FOUND`**: No compatible serial port or BLE advertisement detected.
- **`OFFLINE`**: Display is turned off, out of range, or disabled in user settings.

---

## 🎛️ Interactive Compact Device Panel

Clicking the device status pill in the top header opens the compact **Device Management Panel**:

```
┌──────────────────────────────────────────────────────────┐
│                   DASHBOARD DEVICE STATUS                │
│                                                          │
│  Device:       Divoom MiniToo 160x128                    │
│  Transport:    Bluetooth SPP (COM13)                     │
│  Status:       CONNECTED                                 │
│  Last Seen:    1.2s ago (Active Stream)                  │
│  Signal/RSSI:  Direct SPP Link                           │
│                                                          │
│  [ RECONNECT ]      [ FORGET DEVICE ]     [ DIAGNOSTICS ]│
│  [ OPEN WINDOWS BLUETOOTH SETTINGS ]                     │
└──────────────────────────────────────────────────────────┘
```

- **Reconnect**: Triggers immediate port rescan and connection refresh.
- **Forget Device**: Clears remembered device selection from `config.json` and returns to desktop-only mode.
- **Diagnostics**: Runs live probe queries and displays raw baud, packet round-trip timing, and write throughput.
- **Open Windows Bluetooth Settings**: Quick launcher (`ms-settings:bluetooth`) for fast device addition or removal.
