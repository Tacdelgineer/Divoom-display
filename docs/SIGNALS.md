# Signals & Prediction Markets Intelligence

The **SIGNALS** section delivers high-signal, probabilistic world-event intelligence directly to your desktop command center and physical desk displays.

Rather than flooding the screen with noisy headline feeds or algorithmic spam, SIGNALS focuses on real-time **market-implied odds** backed by liquid capital commitment.

---

## 🎲 1. Polymarket Public Data Provider

The primary engine for event probability queries is **Polymarket** via its public, read-only **Gamma API**.

### Zero Authentication & Security Model
- **Public Read-Only Endpoints**: Accesses `https://gamma-api.polymarket.com/events`.
- **Zero Web3 Dependencies**: No crypto wallets, private keys, MetaMask plugins, or RPC signing nodes required.
- **No Trading or Execution**: AI Desk Dashboard is an observation and monitoring dashboard only; it executes no financial transactions or bets.
- **No API Keys Required**: Polymarket public market data is openly accessible for read-only tracking.

### Caching & Rate-Limiting Architecture
- In-memory and disk cache (`.signals_cache.json`) with a **120-second TTL**.
- Respects upstream public rate limits and ensures startup is instantaneous even when offline.

---

## ⚖️ 2. Probability Semantics: Market-Implied Odds vs News Facts

> [!IMPORTANT]
> **Probabilities are NOT news facts.**
> A prediction market probability (e.g. `FED CUT BY DEC? 64%`) represents the **market-implied consensus price** of traders staking capital on that outcome. It does not represent guaranteed future reality, official government policy, or editorial endorsement.

The dashboard displays probabilities strictly with:
- Bold integer percentage (`64%`) representing YES outcome implied probability.
- 24-hour delta movement (`▲ 8.0 pts / 24H` or `▼ 3.5 pts / 24H`).
- Transparent volume and available market liquidity metrics (`VOL: $18.5M   LIQ: $4.2M`).

---

## 🏷️ 3. Category Normalization

Raw events from Polymarket are classified into 5 strict macro categories:

1. **`FINANCE`**: Central bank policy (Fed, ECB), inflation (CPI, PCE), interest rate decisions, recessions, treasury yields, tariffs, sovereign debt.
2. **`CRYPTO`**: Bitcoin milestones, ETF approvals/flows, Ethereum protocol upgrades, Solana ecosystem, institutional adoption.
3. **`TECH / AI`**: Frontier model releases (GPT-5, Claude, Gemini), GPU/semiconductor manufacturing, AI hardware, product launches, corporate AI acquisitions.
4. **`GEOPOLITICS`**: International treaties, summits, elections, trade accords, strategic supply-chain alliances.
5. **`BREAKING`**: Sudden high-velocity breaking developments with abrupt volume surges.

### Sports Filtering
Athletic matches (Premier League, tennis opens, NBA games) often generate high short-term volume but dilute the macro intelligence focus of the dashboard. The provider automatically filters sports fixtures via keyword and tag analysis (`is_sports_event`).

---

## 🧮 4. Deterministic Attention Ranking Formula

To present the top 5 highest-signal events without manual human curation, the engine computes a deterministic **Attention Score**:

$$\text{Attention Score} = (|\Delta_{\text{24h}}| \times 12.0) + (\log_{10}(\max(V_{\text{24h}}, 1000)) \times 6.0) + \left(\frac{\min(L, 10^6)}{20,000}\right)$$

Where:
- $|\Delta_{\text{24h}}|$ is the absolute 24-hour probability point change (e.g. 8.0 points).
- $V_{\text{24h}}$ is 24-hour traded volume in USD.
- $L$ is total available liquidity in USD (capped at $1,000,000 to prevent whale bias).

### Formula Rationale:
- **Probability Velocity (Weight: 12.0)**: Sudden moves in probability indicate new information or breaking consensus shifts.
- **Liquidity Backing (Weight: 6.0)**: Logarithmic volume ensures moves backed by millions of dollars rank higher than thin, illiquid markets.
- **Order Depth ($L / 20,000$)**: Smoothly rewards deep books where odds cannot easily be manipulated by single trades.

---

## 📰 5. Related News Headlines

Beneath each signal card, the dashboard matches clean financial and technology RSS headlines related to the event topic:
- Displays source publication (`Reuters`, `Bloomberg`, `CoinDesk`, `WSJ`, `FT`), headline text, and relative time (`18m ago`).
- Avoids full-page web scraping; extracts structured title, link, and timestamp from RSS feeds or optional `Finnhub` company news API endpoints.

---

## 🖥️ 6. Physical Display Rendering

### MiniToo (160×128 Color IPS LCD)
- **Top Bar**: Event category badge and source attribution.
- **Center**: Truncated question title with giant, glowing probability percentage (e.g., `64%` in cyan/gold).
- **Bottom Bar**: 24h point change (`▲ 8.0 pts`) and total volume (`$18.5M`).

### Ditoo (16×16 RGB LED Matrix)
- 4-phase rotating animation:
  1. Topic acronym / icon (e.g. `FED` / `BTC`).
  2. Large 2-digit probability percentage (e.g. `64%`).
  3. Directional arrow and point change (e.g. `▲8`).
  4. Visual split probability gauge bar.

---

## ⚖️ 7. Data Licensing & Commercial Notice

> [!NOTE]
> Public Polymarket Gamma API endpoints and Yahoo Finance RSS feeds are utilized for **local, personal prototype visualization**. Commercial redistribution, hosted multi-tenant services, or enterprise deployment require formal review of respective API terms and commercial data licensing agreements.
