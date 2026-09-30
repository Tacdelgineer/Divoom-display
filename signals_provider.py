#!/usr/bin/env python3
"""
Prediction Market & High-Signal Event Intelligence Provider for AI Desk Dashboard.

Data Sources:
1. Polymarket Gamma API (Public Read-Only, No Auth, No Wallet Required)
   Base: https://gamma-api.polymarket.com/events
   Extracts market-implied outcome probabilities (NOT news facts), volume, liquidity, and 24h delta.
2. Financial & Tech RSS News Feed (Clean Headline Aggregation)
   Base: Yahoo Finance / Tech RSS
   Normalizes source attribution, publication timing, and links.

Category Normalization:
- FINANCE
- CRYPTO
- TECH / AI
- GEOPOLITICS
- BREAKING

Deterministic Attention Scoring Formula:
    attention_score = (abs(change_24h_pts) * 12.0) + (log10(max(volume_24h, 1000)) * 6.0) + (min(liquidity, 1000000) / 20000.0)
    Focuses on significant probability movements backed by meaningful liquidity and trading activity.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any

from models import PredictionMarketSignal, NewsHeadline


CACHE_FILE_SIGNALS = ".signals_cache.json"

ALLOWED_CATEGORIES = ["FINANCE", "CRYPTO", "TECH / AI", "GEOPOLITICS", "BREAKING"]

KEYWORD_CATEGORY_MAP = {
    "FINANCE": [
        "fed", "rate", "interest", "inflation", "cpi", "pce", "gdp", "recession",
        "stock", "market", "s&p", "nasdaq", "yield", "treasury", "tariff", "ipo",
        "bank", "debt", "dollar"
    ],
    "CRYPTO": [
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "crypto", "etf",
        "token", "blockchain", "doge", "binance", "coinbase", "halving", "defi"
    ],
    "TECH / AI": [
        "openai", "ai", "gpt", "claude", "gemini", "anthropic", "apple", "nvidia",
        "google", "microsoft", "model", "chip", "semiconductor", "robot", "llm",
        "meta", "deepmind", "agi"
    ],
    "GEOPOLITICS": [
        "election", "president", "prime minister", "parliament", "congress", "senate",
        "treaty", "nato", "un", "war", "ceasefire", "sanction", "minister", "leader",
        "vote", "ballot", "governor"
    ],
}

DEFAULT_FALLBACK_SIGNALS = [
    {
        "event_id": "poly-fed-dec",
        "question": "Fed interest rate cut by December 2026?",
        "category": "FINANCE",
        "yes_probability": 0.64,
        "no_probability": 0.36,
        "change_24h_pts": 8.0,
        "volume": 18450000.0,
        "liquidity": 4200000.0,
        "end_date": "2026-12-18",
        "url": "https://polymarket.com",
        "related_headlines": [
            {"source": "Reuters", "headline": "Fed Officials Signal Data-Dependent Path Ahead of Next Policy Meeting", "timestamp": "18m ago"},
            {"source": "Bloomberg", "headline": "Treasury Yields Consolidate as Rate Cut Probability Rises in Market Odds", "timestamp": "42m ago"},
        ]
    },
    {
        "event_id": "poly-btc-100k",
        "question": "Bitcoin to trade above $100,000 before Q4?",
        "category": "CRYPTO",
        "yes_probability": 0.71,
        "no_probability": 0.29,
        "change_24h_pts": 4.5,
        "volume": 24890000.0,
        "liquidity": 5600000.0,
        "end_date": "2026-10-31",
        "url": "https://polymarket.com",
        "related_headlines": [
            {"source": "CoinDesk", "headline": "Bitcoin Consolidates Highs as Institutional ETF Inflows Rebound", "timestamp": "25m ago"},
            {"source": "Decrypt", "headline": "Crypto Market Cap Expands with Derivatives Volume at Record Pacing", "timestamp": "1h ago"},
        ]
    },
    {
        "event_id": "poly-ai-frontier",
        "question": "Next-generation frontier AI model released this quarter?",
        "category": "TECH / AI",
        "yes_probability": 0.58,
        "no_probability": 0.42,
        "change_24h_pts": -3.2,
        "volume": 9780000.0,
        "liquidity": 2100000.0,
        "end_date": "2026-11-30",
        "url": "https://polymarket.com",
        "related_headlines": [
            {"source": "VentureBeat", "headline": "Frontier AI Labs Accelerate Reasoning Benchmark Deployments", "timestamp": "34m ago"},
            {"source": "Ars Technica", "headline": "Next Foundation Architectures Target Autonomous Workflow Reliability", "timestamp": "2h ago"},
        ]
    },
    {
        "event_id": "poly-macro-pce",
        "question": "US Core PCE inflation prints below 2.6%?",
        "category": "FINANCE",
        "yes_probability": 0.52,
        "no_probability": 0.48,
        "change_24h_pts": 5.8,
        "volume": 12400000.0,
        "liquidity": 3100000.0,
        "end_date": "2026-10-15",
        "url": "https://polymarket.com",
        "related_headlines": [
            {"source": "WSJ", "headline": "Consumer Price Index Trends Suggest Supply-Chain Moderation", "timestamp": "50m ago"},
        ]
    },
    {
        "event_id": "poly-ai-semis",
        "question": "Global semiconductor equipment accord ratified?",
        "category": "GEOPOLITICS",
        "yes_probability": 0.39,
        "no_probability": 0.61,
        "change_24h_pts": 2.1,
        "volume": 8120000.0,
        "liquidity": 1850000.0,
        "end_date": "2026-12-31",
        "url": "https://polymarket.com",
        "related_headlines": [
            {"source": "Financial Times", "headline": "Multinational Tech Councils Convene for Strategic Component Standard", "timestamp": "1h ago"},
        ]
    }
]


SPORTS_KEYWORDS = [
    "vs", "vs.", "tennis", "nfl", "nba", "mlb", "nhl", "uefa", "premier league",
    "champions league", "la liga", "serie a", "bundesliga", "formula 1", "f1",
    "open:", "round 1", "round 2", "quarterfinal", "semifinal", "champion"
]


def is_sports_event(text_or_event: Any, tags: Optional[List[str]] = None) -> bool:
    """Detect if event is an athletic sports match rather than high-signal market/world event."""
    if isinstance(text_or_event, dict):
        text = text_or_event.get("title", "") + " " + text_or_event.get("description", "")
        raw_tags = text_or_event.get("tags", [])
        extracted_tags = [t.get("label", "") if isinstance(t, dict) else str(t) for t in raw_tags]
        if tags is None:
            tags = extracted_tags
        else:
            tags = list(tags) + extracted_tags
    else:
        text = str(text_or_event or "")

    combined = text.lower()
    if tags:
        combined += " " + " ".join(str(t).lower() for t in tags)
        for t in tags:
            t_str = str(t).lower()
            if t_str in ("sports", "soccer", "football", "basketball", "baseball", "tennis", "hockey", "motorsport", "golf"):
                return True
    for kw in SPORTS_KEYWORDS:
        if kw in combined:
            return True
    return False


def classify_category(text: str, tags: Optional[List[str]] = None) -> str:
    """Classify event question or title into one of the 5 allowed categories."""
    combined = (text or "").lower()
    if tags:
        combined += " " + " ".join(str(t).lower() for t in tags)

    for cat, kws in KEYWORD_CATEGORY_MAP.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", combined):
                return cat
    return "BREAKING"


def calculate_attention_score(change_24h_pts: float, volume_24h: float, liquidity: float) -> float:
    """
    Deterministic Attention Score Formula:
        score = (abs(change_24h_pts) * 12.0) + (log10(max(volume_24h, 1000)) * 6.0) + (min(liquidity, 1000000) / 20000.0)
    Balances sudden probability moves against market depth and active participation.
    """
    vol_term = math.log10(max(volume_24h, 1000.0)) * 6.0
    liq_term = min(liquidity, 1_000_000.0) / 20_000.0
    move_term = abs(change_24h_pts) * 12.0
    return round(move_term + vol_term + liq_term, 2)


def normalize_polymarket_event(ev: Dict[str, Any], headlines: Optional[List[NewsHeadline]] = None) -> Optional[PredictionMarketSignal]:
    """Normalize a raw Polymarket Gamma event dictionary into a PredictionMarketSignal."""
    ev_id = str(ev.get("id", ""))
    ev_title = ev.get("title", "")
    ev_vol = float(ev.get("volume", 0.0) or 0.0)
    ev_vol24 = float(ev.get("volume24hr", 0.0) or 0.0)
    ev_liq = float(ev.get("liquidity", 0.0) or 0.0)
    end_d = str(ev.get("endDate", "") or "")[:10]

    raw_tags = ev.get("tags", [])
    tags = [t.get("label", "") if isinstance(t, dict) else str(t) for t in raw_tags]
    if is_sports_event(ev_title, tags):
        return None

    markets = ev.get("markets", [])
    if not markets:
        return None

    m0 = markets[0]
    q_text = m0.get("question") or ev_title
    outcome_prices = m0.get("outcomePrices") or ["0.5", "0.5"]
    if isinstance(outcome_prices, str):
        try:
            outcome_prices = json.loads(outcome_prices)
        except Exception:
            outcome_prices = ["0.5", "0.5"]

    try:
        yes_p = float(outcome_prices[0])
        no_p = float(outcome_prices[1]) if len(outcome_prices) > 1 else (1.0 - yes_p)
    except (ValueError, TypeError):
        yes_p = 0.5
        no_p = 0.5

    yes_p = max(0.001, min(0.999, yes_p))
    no_p = max(0.001, min(0.999, no_p))

    chg_24 = m0.get("oneDayPriceChange")
    chg_pts = (float(chg_24) * 100.0) if chg_24 is not None else 0.0

    cat = classify_category(q_text, tags)
    score = calculate_attention_score(chg_pts, ev_vol24 or ev_vol, ev_liq)
    poly_url = f"https://polymarket.com/event/{ev.get('slug', ev_id)}"

    matched_headlines: List[NewsHeadline] = []
    if headlines:
        q_words = {w.lower() for w in re.findall(r"\w+", q_text) if len(w) > 3}
        for h in headlines:
            h_words = {w.lower() for w in re.findall(r"\w+", h.headline) if len(w) > 3}
            if len(q_words & h_words) >= 1:
                matched_headlines.append(h)
            if len(matched_headlines) >= 2:
                break

    return PredictionMarketSignal(
        event_id=ev_id,
        question=q_text,
        category=cat,
        yes_probability=yes_p,
        no_probability=no_p,
        change_24h_pts=round(chg_pts, 1),
        volume=ev_vol,
        liquidity=ev_liq,
        end_date=end_d,
        url=poly_url,
        updated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        attention_score=score,
        related_headlines=matched_headlines,
    )


# Fallback deterministic prediction signals (List[PredictionMarketSignal])
FALLBACK_PREDICTION_SIGNALS: List[PredictionMarketSignal] = [
    PredictionMarketSignal(
        event_id=fb["event_id"],
        question=fb["question"],
        category=fb["category"],
        yes_probability=fb["yes_probability"],
        no_probability=fb["no_probability"],
        change_24h_pts=fb["change_24h_pts"],
        volume=fb["volume"],
        liquidity=fb["liquidity"],
        end_date=fb["end_date"],
        url=fb["url"],
        updated_at="2026-09-30 09:30:00",
        attention_score=calculate_attention_score(fb["change_24h_pts"], fb["volume"], fb["liquidity"]),
        related_headlines=[NewsHeadline(**h) for h in fb.get("related_headlines", [])],
    )
    for fb in DEFAULT_FALLBACK_SIGNALS
]



class BaseSignalsProvider:
    """Abstract provider for high-signal prediction events and curated news."""
    name: str = "BaseSignals"

    def get_signals(self, count: int = 5) -> List[PredictionMarketSignal]:
        raise NotImplementedError

    def get_news(self, count: int = 6) -> List[NewsHeadline]:
        raise NotImplementedError


class PolymarketSignalsProvider(BaseSignalsProvider):
    """
    Public, unauthenticated Polymarket prediction markets provider.
    Accesses public Gamma API read-only endpoints without keys or wallets.
    Normalizes market-implied probabilities and aggregates related RSS news headlines.
    """
    name: str = "Polymarket"

    def __init__(self, cache_file: str = CACHE_FILE_SIGNALS):
        self.cache_file = cache_file

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _write_cache(self, signals: List[PredictionMarketSignal], news: List[NewsHeadline]) -> None:
        try:
            data = {
                "timestamp": time.time(),
                "signals": [
                    {
                        "event_id": s.event_id,
                        "question": s.question,
                        "category": s.category,
                        "yes_probability": s.yes_probability,
                        "no_probability": s.no_probability,
                        "change_24h_pts": s.change_24h_pts,
                        "volume": s.volume,
                        "liquidity": s.liquidity,
                        "end_date": s.end_date,
                        "url": s.url,
                        "updated_at": s.updated_at,
                        "attention_score": s.attention_score,
                        "related_headlines": [
                            {"source": h.source, "headline": h.headline, "url": h.url, "timestamp": h.timestamp}
                            for h in s.related_headlines
                        ]
                    }
                    for s in signals
                ],
                "news": [
                    {"source": h.source, "headline": h.headline, "url": h.url, "timestamp": h.timestamp}
                    for h in news
                ]
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_news(self, count: int = 6) -> List[NewsHeadline]:
        """Fetch fresh financial and macro news headlines from standard RSS feed."""
        headlines: List[NewsHeadline] = []
        try:
            url = "https://finance.yahoo.com/news/rssindex"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                items = root.findall(".//item")
                for item in items[:count * 2]:
                    title_elem = item.find("title")
                    source_elem = item.find("source")
                    pub_elem = item.find("pubDate")
                    link_elem = item.find("link")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    source = source_elem.text.strip() if source_elem is not None and source_elem.text else "Financial News"
                    pub = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

                    if title:
                        # Clean relative time string
                        ts_str = "Recent"
                        if "T" in pub and "Z" in pub:
                            ts_str = pub.split("T")[1][:5]
                        elif len(pub) > 16:
                            ts_str = pub[17:22] if len(pub) >= 22 else "Recent"

                        headlines.append(
                            NewsHeadline(
                                source=source[:18],
                                headline=title,
                                url=link,
                                timestamp=ts_str,
                            )
                        )
                    if len(headlines) >= count:
                        break
        except Exception as e:
            pass

        return headlines

    def get_signals(self, count: int = 5) -> List[PredictionMarketSignal]:
        """
        Fetch top prediction market signals from Polymarket public Gamma API.
        Enforces:
        - 120s caching TTL to prevent unnecessary rate limiting.
        - Strict market-implied probability semantics.
        - 5 normalized categories.
        - Deterministic attention ranking.
        - Automatic fallback fixtures when offline.
        """
        now = time.time()
        cache = self._read_cache()

        # Cache TTL: 120 seconds
        if cache and (now - cache.get("timestamp", 0) < 120.0):
            cached_sigs = []
            for s in cache.get("signals", []):
                h_objs = [NewsHeadline(**h) for h in s.get("related_headlines", [])]
                s_copy = dict(s)
                s_copy["related_headlines"] = h_objs
                cached_sigs.append(PredictionMarketSignal(**s_copy))
            if len(cached_sigs) >= count:
                return cached_sigs[:count]

        # Fetch live news headlines first for contextual matching
        fresh_news = self.get_news(count=10)

        # Query Polymarket Gamma API
        url = "https://gamma-api.polymarket.com/events?limit=30&active=true&closed=false&order=volume24hr&ascending=false"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        signals: List[PredictionMarketSignal] = []

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                ts_now = time.strftime("%Y-%m-%d %H:%M:%S")

                for ev in data:
                    ev_id = str(ev.get("id", ""))
                    ev_title = ev.get("title", "")
                    ev_vol = float(ev.get("volume", 0.0))
                    ev_vol24 = float(ev.get("volume24hr", 0.0) or 0.0)
                    ev_liq = float(ev.get("liquidity", 0.0) or 0.0)
                    end_d = str(ev.get("endDate", "") or "")[:10]

                    tags = [t.get("label", "") for t in ev.get("tags", []) if isinstance(t, dict)]
                    if is_sports_event(ev_title, tags):
                        continue
                    markets = ev.get("markets", [])
                    if not markets:
                        continue


                    # Evaluate primary market
                    m0 = markets[0]
                    q_text = m0.get("question") or ev_title
                    outcome_prices = m0.get("outcomePrices") or ["0.5", "0.5"]
                    if isinstance(outcome_prices, str):
                        try:
                            outcome_prices = json.loads(outcome_prices)
                        except Exception:
                            outcome_prices = ["0.5", "0.5"]

                    try:
                        yes_p = float(outcome_prices[0])
                        no_p = float(outcome_prices[1]) if len(outcome_prices) > 1 else (1.0 - yes_p)
                    except (ValueError, TypeError):
                        yes_p = 0.5
                        no_p = 0.5

                    # Ensure probabilities are within 0.01 - 0.99 for active open markets
                    yes_p = max(0.001, min(0.999, yes_p))
                    no_p = max(0.001, min(0.999, no_p))

                    chg_24 = m0.get("oneDayPriceChange")
                    chg_pts = (float(chg_24) * 100.0) if chg_24 is not None else 0.0

                    cat = classify_category(q_text, tags)
                    score = calculate_attention_score(chg_pts, ev_vol24 or ev_vol, ev_liq)

                    # Match related headlines based on keywords
                    words = set(re.findall(r"\w+", q_text.lower()))
                    matched_headlines: List[NewsHeadline] = []
                    for h in fresh_news:
                        h_words = set(re.findall(r"\w+", h.headline.lower()))
                        if len(words & h_words) >= 2:
                            matched_headlines.append(h)
                        if len(matched_headlines) >= 2:
                            break

                    sig = PredictionMarketSignal(
                        event_id=ev_id,
                        question=q_text,
                        category=cat,
                        yes_probability=yes_p,
                        no_probability=no_p,
                        change_24h_pts=chg_pts,
                        volume=ev_vol,
                        liquidity=ev_liq,
                        end_date=end_d,
                        url=f"https://polymarket.com/event/{ev.get('slug', ev_id)}",
                        updated_at=ts_now,
                        attention_score=score,
                        related_headlines=matched_headlines,
                    )
                    signals.append(sig)

        except Exception as e:
            print(f"[SIGNALS] Error querying Polymarket Gamma API: {e}")

        if signals:
            # Sort descending by deterministic attention score
            signals.sort(key=lambda s: s.attention_score, reverse=True)
            top_sigs = signals[:count]

            # If any signal lacks related headlines, distribute remaining fresh news
            unassigned_news = [h for h in fresh_news]
            for s in top_sigs:
                if not s.related_headlines and unassigned_news:
                    s.related_headlines.append(unassigned_news.pop(0))
                if len(s.related_headlines) < 2 and unassigned_news:
                    s.related_headlines.append(unassigned_news.pop(0))

            self._write_cache(top_sigs, fresh_news)
            return top_sigs

        # Cache fallback
        if cache and "signals" in cache:
            cached_sigs = []
            for s in cache.get("signals", []):
                h_objs = [NewsHeadline(**h) for h in s.get("related_headlines", [])]
                s_copy = dict(s)
                s_copy["related_headlines"] = h_objs
                cached_sigs.append(PredictionMarketSignal(**s_copy))
            if cached_sigs:
                return cached_sigs[:count]

        # Offline fallback fixtures
        return list(FALLBACK_PREDICTION_SIGNALS[:count])


def get_signals_provider() -> BaseSignalsProvider:
    """Return active signals provider."""
    return PolymarketSignalsProvider()


def get_prediction_signals(count: int = 5) -> List[PredictionMarketSignal]:
    """Module-level convenience function returning top prediction market signals."""
    return get_signals_provider().get_signals(count)

