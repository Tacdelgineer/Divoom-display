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
│  - ClaudeUsageProvider (local profile ~/.claude.json)  │
│  - DgxSparkCollector (remote SSH / Tailscale)          │
│  - MultiCryptoCollector (BTC, ETH, SOL, DOGE, PEPE)    │
│  - StockVolatilityCollector (Top 10 Volatile US Stocks)│
│  - AiActivityCollector (agent sessions / diffs)        │
│  - ServicesCollector (TCP socket port probes)          │
│  - CodingStatusCollector (git repo status)             │
└──────────────────────────┬─────────────────────────────┘
                           │ Returns PageData / Market models
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
│  - Section-based Canvas   │ │  - Pillow 160x128 RGB     │
│  - Presets (ALL, AI, etc.)│ │  - 8x10 tile alignment    │
│  - Dynamic section groups │ │  - Multi-asset tables     │
│  - Interactive card clicks│ │  - Coin sparkline pages   │
└──────────────┬────────────┘ └─────────────┬─────────────┘
               │                            │
               ▼                            ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     DESKTOP DISPLAY       │ │      MINITOO DISPLAY      │
│     Windows GUI Window    │ │     Bluetooth SPP (0x8B)  │
└───────────────────────────┘ └───────────────────────────┘
```

---

## 2. Section-Based Architecture & Presets

Starting in Milestone 12, AI Desk Dashboard transitioned from a fixed 3×3 grid to a fully configurable, section-based layout:

### Default Sections
- **`CRYPTO`**: Cards for `BTC`, `ETH`, `SOL`, `DOGE`, `PEPE`.
- **`AI USAGE`**: Cards for `CODEX`, `GEMINI`, `CLAUDE` (active profile).
- **`SYSTEM`**: Cards for `LOCAL PC`, `DGX SPARK`, `SERVICES`, `CODING WORKSPACE`, `AI ACTIVITY`.
- **`STOCKS`**: Card for `TOP 10 VOLATILE US STOCKS` scanner.

### Configuration Model (`config.py`)
Each section is defined by a `DashboardSectionConfig`:
```python
@dataclass
class DashboardSectionConfig:
    id: str
    title: str
    enabled: bool = True
    cards: list[str] = field(default_factory=list)
```

The user configuration stores:
- `section_order`: List of section IDs defining top-to-bottom rendering order.
- `sections`: Map of section ID to `DashboardSectionConfig` (card order, enabled states).
- `enabled_cards`: Set of card keys enabled for the Desktop application.
- `enabled_cards_minitoo`: Set of card keys enabled for physical MiniToo page rotation.

### Presets & Focus Mode
Presets allow instant focus switching without altering saved layouts:
- **`[ ALL ]`**: Enables all 4 sections (`CRYPTO`, `AI USAGE`, `SYSTEM`, `STOCKS`).
- **`[ AI ]`**: Enables `AI USAGE` and AI Activity.
- **`[ CRYPTO ]`**: Focuses exclusively on cryptocurrency assets (`BTC`, `ETH`, `SOL`, `DOGE`, `PEPE`) with expanded sparklines.
- **`[ STOCKS ]`**: Focuses on US equity market volatility rankings.
- **`[ SYSTEM ]`**: Focuses on hardware cluster metrics (Local RTX GPU, remote DGX Spark, Services health, Coding workspace).

#### Focus Mode (Creator / Shorts View)
Clicking `[ 🔍 FOCUS ]` on any section header instantly switches the dashboard into an isolated, enlarged hero layout with high-resolution sparklines and prominent metrics. A prominent top banner provides an immediate `[ ◀ BACK / ALL ]` escape action.

### Adding a New Dashboard Section
To add a new section in code:
1. Define the section identifier in `config.py` (`DEFAULT_SECTIONS`):
   ```python
   DashboardSectionConfig(id="networking", title="NETWORKING", cards=["ping", "bandwidth"])
   ```
2. Register corresponding page collectors in `collectors.py` and page keys in `dashboard.py`.
3. Add renderers in `renderer.py` (for MiniToo 160×128) and card layouts in `dashboard_app.py`.
4. Ensure default config migration initializes missing sections automatically.

---

## 3. Market Data Providers & Crypto Architecture

### Pluggable `MarketDataProvider` (`market_provider.py`)
To avoid fragile HTML scraping while keeping the project free of mandatory paid subscriptions, market queries route through an abstract interface:

```python
class MarketDataProvider(ABC):
    @abstractmethod
    def get_stock_quotes(self, symbols: list[str]) -> list[StockQuote]: ...
    @abstractmethod
    def get_top_volatile_stocks(self, limit: int = 10) -> tuple[list[StockQuote], str]: ...
```

1. **`YahooFinanceMarketDataProvider` (Default / Free)**:
   - Retrieves live quotes for high-volume US equities (`NVDA`, `TSLA`, `AMD`, `AAPL`, `MSFT`, `AMZN`, `META`, `GOOGL`, `COIN`, `PLTR`, `MARA`, `MSTR`, `SMCI`, `ARM`, `SOFI`, `INTC`, etc.).
   - Utilizes Yahoo's v7 quote API with automated session cookie and crumb acquisition (`https://fc.yahoo.com` -> `query2.finance.yahoo.com/v1/test/getcrumb`).
   - Caches quotes locally for 60 seconds.
2. **`FinnhubMarketDataProvider` (Optional)**:
   - Activated automatically when `FINNHUB_API_KEY` is detected in the environment.
   - Queries official Finnhub `/quote` endpoints.

### Consolidated Multi-Crypto Collector (`MultiCryptoCollector`)
- Queries Bitcoin (`BTC`), Ethereum (`ETH`), Solana (`SOL`), Dogecoin (`DOGE`), and Pepe (`PEPE`) simultaneously using a **single** CoinGecko simple price request:
  `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dogecoin,pepe&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true`
- Employs a 60-second local JSON cache (`.crypto_cache.json`) to prevent rate-limit exhaustion.
- Formats micro-tokens intelligently:
  - Tokens under $0.01 (e.g. PEPE at `$0.0000045`) render as `$0.0000045` on desktop and compact `$4.5u` on MiniToo 128px displays to avoid string clipping.

### Adding a New Market Asset
1. Add the token ID / ticker to `CRYPTO_IDS` in `collectors.py`:
   ```python
   "AVAX": "avalanche-2",
   ```
2. Add the corresponding card key to `config.py` in the `crypto` section cards.
3. Update `renderer.py` if an individualized sparkline page is desired.

---

## 4. Stock Volatility Definition & Scanner

### Objective Intraday Volatility Metric
Market volatility in AI Desk Dashboard is mathematically defined as the **intraday price range relative to the previous trading session's closing price**:

$$\text{Volatility \%} = \frac{\text{Day High} - \text{Day Low}}{\text{Previous Close}} \times 100$$

This guarantees:
- Large price swings within the day are captured regardless of whether the net change is positive or negative.
- The metric is normalized across share prices ($20 stock vs. $500 stock).
- It never falsely equates net daily gainers with volatility (a stock that opened +10% and stayed flat has 0% intraday volatility).

### Stock Scanner Features
- Evaluates a liquid basket of volatile US equities.
- Sorts descending by volatility percentage.
- Displays: Ticker, Current Price, Day Change %, and Intraday Volatility %.
- Detects market session state: `OPEN` (regular hours 09:30–16:00 EST), `PRE` (pre-market), `POST` (after-hours), or `CLOSED` (weekends/holidays).

---

## 5. Claude Account Diagnostics & Multi-Profile Isolation

### The Investigation: Why Claude Showed N/A
1. `claude -p "/status"` is not supported in Claude Code print mode (slash commands require an interactive TTY).
2. The user has an authenticated Claude Code CLI installation using Stripe subscription billing (`Claude Pro`).
3. Claude Code stores cached usage in `~/.claude.json` under `cachedUsageUtilization`. When no interactive Claude session has run recently, this cache expires, returning `N/A`.

### Diagnostic Inspection (`claude_usage.py`)
The dashboard queries:
- **Account Identity**: Masked email (e.g. `no***@gmail.com`) read safely from `~/.claude.json` (`oauthAccount.emailAddress`). Raw email is never displayed or committed.
- **Plan Tier**: Read from `organizationType` (`claude_pro`) and `billingType`.
- **Auth Type**: `Subscription (OAuth)` vs `API Key`.
- **Environment Variables**: Audited in strict order of precedence:
  1. `ANTHROPIC_API_KEY`
  2. `CLAUDE_CODE_OAUTH_TOKEN`
  3. `ANTHROPIC_BASE_URL`
  4. `CLAUDE_CODE_USE_BEDROCK`
  5. `CLAUDE_CODE_USE_VERTEX`
  6. `CLAUDE_CODE_USE_FOUNDRY`
  Presence and precedence are reported without exposing secret strings.

### Safe Multi-Account Profile Isolation
- **Claude Code CLI Limitation**: Claude Code v2.x does **not** support simultaneous multi-account switching within a single active session directory.
- **Architectural Solution**: Claude Code natively supports the `CLAUDE_CONFIG_DIR` environment variable. Separate accounts can be safely isolated in independent configuration directories:
  - **Primary Account**: `~/.claude` (default)
  - **Secondary Account**: `~/.claude-secondary`
- The dashboard supports configuring multiple `ClaudeAccountProfile` records in `config.json`. Each profile reads its own directory independently without:
  - Copying tokens into the repository.
  - Scraping browser session cookies.
  - Stealing credentials.
  - Logging users out of existing sessions.

---

## 6. Remote DGX Compute Flow

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

## 7. MiniToo Hardware Transport Flow

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

## 8. Physical Knob Navigation Flow

The MiniToo physical rotary knob does not transmit unsolicited keypresses over Bluetooth. AI Desk Dashboard navigates pages by polling device state at a low, radio-friendly frequency (~2.8 Hz in Low Interference, ~4.0 Hz in Normal mode, down from 16 Hz):

```
MiniTooInputAdapter Loop (~2.8–4 Hz)
   │
   │ 1. Checks connection state (skips query immediately if disconnected)
   │ 2. Queries device volume: Command 0x09
   ▼
MiniToo Responds with Current Volume (0..16)
   │
   │ 3. Compares volume with target base volume (8 / 16)
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

### Benefits of Base Restoration & Lower Polling
- **Bluetooth Audio Coexistence**: Dropping knob queries from 16 Hz down to 2.8–4 Hz cuts serial Bluetooth packet contention by over 75%, preventing A2DP buffer starvation on Bluetooth speakers and headphones.
- **Zero Audio Glitches**: Because the volume level is immediately restored to 8, no sudden volume jump occurs if an audio stream is playing.
- **Infinite Rotation**: The knob acts as an infinite optical encoder without hitting firmware 0 or 16 endpoints.
- **Hardware Debouncing**: Events are software-debounced with a 250ms window to guarantee exactly one page transition per physical knob detent.

---

## 9. Threading Model

```
Main Thread (Tkinter GUI Loop)
   ├── Renders Canvas (628x512 min, resizable) with scroll support
   ├── Processes mouse clicks, window drag, presets, Focus mode, settings modals
   └── Receives state notifications via event callbacks

DataEngine Thread (Daemon)
   ├── Loops through configured sections and cards
   ├── Dispatches collectors at configured refresh intervals
   └── Updates DashboardState under threading.Lock

MiniTooController Thread (Daemon)
   ├── Manages serial connection to MiniToo
   ├── Decoupled: collector updates NEVER force frames unless current page changed
   ├── Pushes active page frame ONLY when rendered image payload differs
   └── MiniTooInputAdapter polls rotary knob events (~2.8–4 Hz)
```
All shared state mutations in `DashboardState` are guarded by `threading.Lock`, guaranteeing thread-safe reads by the UI.

---

## 10. Bluetooth Coexistence & Traffic Reduction Engine

### Root Cause of Bluetooth Audio Stutter
Personal computers with integrated Wi-Fi + Bluetooth modules (e.g. MediaTek MT7922 / RZ616, Intel AX200/AX211) use a **single shared 2.4 GHz radio**. The radio controller divides time slots between:
- **A2DP Audio Profile**: High-bitrate isochronous streaming packets with strict latency deadlines.
- **RFCOMM SPP Profile**: Serial port command packets for device communication.

When the host PC floods the serial link with 16 Hz volume polling (32 transactions/sec) + 8s channel checks + periodic frame heartbeats, the Bluetooth controller's TDD (Time-Division Duplex) scheduler starves A2DP audio packets, leading to audible clicks, pops, and audio dropouts.

### Architectural Solution
1. **Decoupled Collector Updates**:
   When background collectors refresh (e.g., local GPU updates every 2 seconds, DGX every 10 seconds), they write to the central state cache. If the MiniToo display is showing BTC or Gemini, **zero bytes are transmitted over Bluetooth**. Only the actively displayed page is pushed.
2. **Diff-Based Frame Elision**:
   Every rendered frame is hashed. If the pixel/payload hash matches the currently displayed buffer, the frame send is elided completely. Retransmission heartbeats are eliminated.
3. **Optimized Knob Polling**:
   Lowered from 16 Hz to ~2.8 Hz in Low Interference mode (0.35s delay) and ~4.0 Hz in Normal mode (0.25s delay).
4. **Relaxed Channel 5 Health Checks**:
   Once display ownership is locked, Channel 5 queries run at 60-second (Normal) or 120-second (Low Interference) intervals.
5. **Rolling 60-Second Telemetry Window**:
   `RollingTelemetryWindow` in `backends.py` tracks exact rolling metrics: SPP writes/min, reads/min, frames/min, and throughput (KB/min) to diagnose radio contention.
6. **Detailed Bluetooth Guide**:
   See [docs/BLUETOOTH.md](BLUETOOTH.md) for full coexistence benchmarks and dedicated USB adapter routing strategies.

---

## 11. Redesigned Settings Architecture

The Settings dialog (`ui_components.py`) uses a 5-tab left-navigation structure:
- **GENERAL**: Launch minimized, Start with Windows, default preset, refresh behavior.
- **DASHBOARD**: Section trees with per-card independent `Desktop [x]` vs `MiniToo [x]` toggles and dedicated `▲` / `▼` ordering buttons.
- **MINITOO**: Connection port, transport mode selector (**NORMAL** vs **LOW INTERFERENCE**), auto-cycle toggle, dwell interval, live rolling telemetry display, and action buttons (`TEST DISPLAY`, `RECONNECT`, `COPY DIAGNOSTICS`).
- **INTEGRATIONS**: Tailscale DGX node host, API keys, and Claude profile discovery.
- **ADVANCED**: Debug logging, raw protocol inspector, and factory reset.
