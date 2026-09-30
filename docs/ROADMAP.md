# AI Desk Dashboard Architecture & Future Roadmap

This document outlines the architectural blueprints for upcoming milestones and future card expansions across AI Desk Dashboard.

---

## 🚨 Alert Engine Architecture (Milestone 15/16 Foundation)

To support real-time proactive notification across both the desktop dashboard and physical desk hardware without overbuilding a bloated messaging subsystem, Milestone 15 establishes the normalized `Alert` container:

```python
@dataclass
class Alert:
    source: str                     # "SYSTEM", "MARKET", "AGENT", "POLYMARKET"
    severity: str                   # "INFO", "WARNING", "CRITICAL"
    title: str                      # e.g. "CODEX 8% LEFT", "DGX 91C", "POLYMARKET +14 pts"
    value: str                      # e.g. "8%", "91°C", "+14 pts"
    timestamp: Any = 0.0            # Unix epoch or formatted local time
    action_url: Optional[str] = None
```

### Alert Priority & Display Routing:
- **Desktop Command Center**: Banner toast notification pill in top navigation bar with direct click-through action.
- **MiniToo (160×128)**: High-contrast alert takeover frame with flashing amber/red border and audible buzzer ping (optional).
- **Ditoo (16×16)**: Flashing warning icon / ticker overlay before resuming standard rotation.

---

## 🧩 Future Module & Card Library (Architectural Blueprints)

### 1. AI Agents & Local LLM Telemetry
- **`AGENT NEEDS YOU`**: Hooks into Antigravity, Claude Code, and Codex notification channels when an autonomous agent pauses awaiting human confirmation or tool approval.
- **`AGENT PASS / FAIL`**: Real-time terminal status badge when a long-running agentic workflow finishes or encounters an unhandled exception.
- **`Tokens / Sec Speedometer`**: Live generation speed metrics for local Ollama, vLLM, or LM Studio instances.
- **`Ollama Loaded Model`**: Current active model in VRAM (e.g. `llama3.3:70b`, `deepseek-r1:32b`) and offload ratio.
- **`ComfyUI / SD Generation Progress`**: Step-by-step progress bar and queue depth indicator for diffusion image generation.
- **`Rate-Limit Velocity Alerts`**: Predictive alert when consumption pacing is on track to exhaust Codex/Gemini quotas prior to reset.

### 2. System & Workstation Infrastructure
- **`Docker Container Monitor`**: Active, paused, and failed container counts with high-RAM outlier highlights.
- **`Disk Usage & Storage Meters`**: Visual partition usage gauges (`C: 78%`, `D: 42%`) with threshold warnings.
- **`Network Ping & Gateway Latency`**: Real-time latency graph to primary DNS, default gateway, and remote cluster.
- **`Process Leaders`**: Top 3 processes sorted by CPU and GPU memory consumption.
- **`Tailscale Mesh Fleet`**: Online/offline indicators for connected mesh machines (workstation, server, laptop).
- **`NAS Health & Smart Status`**: TrueNAS / Synology pool status, disk temperatures, and scrub status.

### 3. Macro Markets & Equities
- **`Index Big Three (SPY | QQQ | VIX)`**: Real-time broad market indicators alongside crypto assets.
- **`Market Session Countdown`**: Dynamic status pill showing minutes to NYSE Open / Close and pre/post-market indicators.
- **`Personal Watchlist`**: Customizable user equity cards (e.g., PLTR, MSTR, ARM, COIN).
- **`Earnings Calendar Countdown`**: Days and hours until major portfolio earnings reports.
- **`Crypto Dominance & ETF Flow`**: BTC/ETH dominance percentage and aggregate spot Bitcoin ETF net daily inflow/outflow metrics.

### 4. Creator & Media Studio
- **`Latest YouTube Video Performance`**: 24-hour views/hour velocity and like ratio.
- **`Subscriber Milestone Counter`**: Live subscriber count with celebratory animation upon reaching targets.
- **`Scheduled Upload Tracker`**: Next scheduled release countdown across YouTube, TikTok, and podcast feeds.
- **`Social Uploader Status`**: Automated publishing pipeline health (transcoding, tagging, upload confirmation).

### 5. Signals & World Prediction Odds
- **`Polymarket Fast Movers`**: Highlight events with >10 point probability swings in the last 4 hours.
- **`Major Breaking Headlines`**: High-signal headline stream filtered against market-moving keywords.
- **`Fed Interest Rate Odds Tracker`**: Implied probability matrix for upcoming FOMC meetings.
- **`Crypto Milestone Markets`**: Odds on BTC price hurdles, ETF approvals, or regulatory milestones.
- **`AI Frontier Race Markets`**: Implied probabilities of frontier benchmark clearances or company product releases.

### 6. Developer Productivity & CI/CD
- **`Next Calendar Event`**: Google / Outlook calendar integration showing upcoming meeting title and countdown.
- **`Focus Pomodoro & Timer`**: 25/5 interval timer controllable via MiniToo rotary knob or keyboard shortcut.
- **`GitHub Actions Workflow Status`**: Real-time pass/fail indicators across repositories for push/PR CI pipelines.
- **`Local Build Status`**: Status of local compiler/bundler daemons (`tsc --watch`, `pytest`, `cargo build`).
