# Autonomous Agent Quickstart Guide

This guide contains copy-and-paste prompts to bootstrap and guide AI coding agents (OpenAI Codex, Anthropic Claude Code, Google Antigravity, GitHub Copilot, etc.) working on the **AI Desk Dashboard** repository.

---

## 1. Initial Repo Inspection Prompt (Bootstrap)

Paste this prompt when an agent opens the repository for the first time:

```text
You are an expert systems and Python developer pair-programming on AI Desk Dashboard.

First, do NOT make any changes or edit any files yet.

Perform an initial health and status check:
1. Read AGENTS.md to understand project purpose, architecture, and critical safety rules.
2. Inspect the repository structure and key files (models.py, engine.py, collectors.py, dashboard_app.py).
3. Run python dashboard.py --status to inspect current data providers and authority classifications.
4. Verify that pytest runs and passes cleanly.
5. Report current repository health, detected hardware ports, and active provider status.
```

---

## 2. Feature Extension Prompts

### Prompt A: Adding a New Data Collector

Use this prompt to add a new metric source (e.g., weather, GitHub notifications, Ollama models, system temperatures):

```text
Task: Add a new data collector to AI Desk Dashboard.

Requirements:
1. Inspect models.py (PageData, MetricItem) and collectors.py for established collector patterns.
2. Create a new collector class in collectors.py (or dedicated module):
   - Wrap network or system calls with non-blocking timeouts (<= 3.0s).
   - If calling system binaries, use subproc.check_output_hidden() or run_hidden() to prevent Windows console flashing.
   - Set metric authority strictly: AUTHORITATIVE, CALCULATED, STALE_CACHE, or UNAVAILABLE.
   - Never turn unavailable or null values into 0.
   - Cache results locally if polling expensive or rate-limited endpoints.
3. Register the collector in dashboard.py:collect_page() and engine.py.
4. Add a test in tests/ to verify collection and failure fallback.
5. Run tests and report output without modifying unrelated components.
```

### Prompt B: Adding a New Dashboard Page

Use this prompt to add a new visual card to the Desktop Companion and MiniToo screen:

```text
Task: Add a new dashboard page to AI Desk Dashboard.

Requirements:
1. Inspect renderer.py to see how 160x128 pixel frames are constructed with Pillow.
2. Inspect dashboard_app.py to see how cards are rendered on the Tkinter canvas.
3. Implement the page rendering:
   - For MiniToo (renderer.py): Follow the 160x128 layout, retro terminal color palette, and header/footer bounds.
   - For Desktop (dashboard_app.py): Implement the card drawing routine in _draw_*_card() matching CARD_WIDTH (196) and CARD_HEIGHT (136).
4. Register the new page key in config.py:ALL_PAGE_IDS and REFRESH_INTERVALS.
5. Verify with python dashboard.py --preview and ensure no layout overlap occurs.
```

### Prompt C: Adding a New Display Backend

Use this prompt to add a new hardware display backend (e.g., Tidbyt, Pixoo 64, Raspberry Pi OLED, e-paper):

```text
Task: Add a new display backend to AI Desk Dashboard.

Requirements:
1. Inspect backends.py and models.py to understand the DisplayBackend abstract base class.
2. Implement your new backend class inheriting from DisplayBackend:
   - Implement render(page: PageData) -> bool.
   - Implement connection lifecycle and safe auto-reconnection.
   - Isolate hardware timeouts so failure never stalls DataEngine.
3. Integrate the backend option into engine.py and config.py.
4. Verify that desktop-only mode remains 100% functional when the new display backend is disconnected.
5. Run tests and verify clean exit on shutdown.
```
