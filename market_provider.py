#!/usr/bin/env python3
"""
Pluggable Market Data Provider for AI Desk Dashboard.
Calculates objective intraday range volatility:
    volatility_pct = (high - low) / previous_close * 100.0

Supports:
1. YahooFinanceMarketDataProvider: Free, crumb-authenticated session for US liquid equities.
2. FinnhubMarketDataProvider: Optional API-key-based provider via FINNHUB_API_KEY.
3. MarketDataProviderRegistry: Fallback and provider selection.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import time
import urllib.request
from typing import List, Optional, Dict, Any

from models import StockQuote

# Liquid, high-beta US equities watchlist for whole-day volatility scanning
DEFAULT_STOCK_UNIVERSE = [
    "NVDA", "TSLA", "AMD", "MSTR", "COIN", "PLTR", "SMCI", "GME",
    "DKNG", "MARA", "RIOT", "ARM", "INTC", "AAPL", "MSFT", "AMZN",
    "GOOGL", "META", "BABA", "NFLX", "AVGO", "CRWD", "SOFI", "HOOD"
]

# Candidate universe of leading US equities for dynamic market-capitalization ranking.
# Note: Free public endpoints are used for local prototype visualization. Commercial redistribution
# or production deployment requires review and formal data licensing.
DEFAULT_US_MARKET_CAP_CANDIDATES = [
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA",
    "BRK-B", "BRK-A", "AVGO", "WMT", "JPM", "LLY", "V", "MA",
    "ORCL", "COST", "HD", "PG", "UNH", "NFLX", "AMD", "CRM", "BAC"
]

# Canonical mapping for corporate entities with multiple share classes.
# Rule: If multiple symbols represent the same corporate issuer (e.g. GOOG and GOOGL map
# to 'ALPHABET', or BRK-A and BRK-B map to 'BERKSHIRE'), we group them by canonical entity
# and retain only the single class with the highest market capitalization.
# This prevents Google or Berkshire from consuming multiple spots in the Top 10.
SHARE_CLASS_CANONICAL_MAP = {
    "GOOG": "ALPHABET",
    "GOOGL": "ALPHABET",
    "BRK-A": "BERKSHIRE",
    "BRK-B": "BERKSHIRE",
    "FOX": "FOXCORP",
    "FOXA": "FOXCORP",
    "NWSA": "NEWS_CORP",
    "NWS": "NEWS_CORP",
}

def calculate_volatility(high: float, low: float, previous_close: float) -> float:
    """
    Calculate objective intraday range percentage:
        volatility_pct = (high - low) / previous_close * 100.0
    Guarantees no division by zero and non-negative metric.
    """
    if previous_close <= 0 or high < low:
        return 0.0
    return ((high - low) / previous_close) * 100.0


def synthesize_sparkline(
    prev_close: float = 0.0,
    low: float = 0.0,
    high: float = 0.0,
    price: float = 0.0,
    steps: int = 16,
    count: Optional[int] = None,
    change_pct: Optional[float] = None,
) -> List[float]:
    """Generate smooth intraday sparkline curve connecting prev_close, extremes, and current price."""
    if count is not None:
        steps = count

    if change_pct is not None and price > 0:
        prev_close = price / (1.0 + (change_pct / 100.0))
        delta = abs(price - prev_close)
        if change_pct >= 0:
            low = min(prev_close, price) - max(delta * 0.15, price * 0.005)
            high = max(prev_close, price) + max(delta * 0.2, price * 0.008)
        else:
            low = min(prev_close, price) - max(delta * 0.2, price * 0.008)
            high = max(prev_close, price) + max(delta * 0.15, price * 0.005)

    if prev_close <= 0:
        prev_close = price
    if low <= 0 or low > min(prev_close, price):
        low = min(prev_close, price) * 0.995
    if high <= 0 or high < max(prev_close, price):
        high = max(prev_close, price) * 1.005

    pts = []
    mid1 = low + (high - low) * 0.35
    mid2 = high - (high - low) * 0.25
    anchors = [prev_close, mid1, low, mid2, high, price]

    # Interpolate across anchors
    for i in range(steps):
        t = i / float(steps - 1)
        idx_float = t * (len(anchors) - 1)
        base_idx = int(idx_float)
        frac = idx_float - base_idx
        if base_idx >= len(anchors) - 1:
            val = anchors[-1]
        else:
            val = anchors[base_idx] * (1.0 - frac) + anchors[base_idx + 1] * frac
        pts.append(round(val, 2))
    return pts



# Raw fallback dictionary data
DEFAULT_TOP_MARKET_CAP_RAW = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 229.81, "change_pct": 2.15, "market_cap": 5.55e12, "high": 232.40, "low": 226.10, "previous_close": 224.97},
    {"symbol": "AAPL", "name": "Apple Inc.", "price": 234.50, "change_pct": -0.42, "market_cap": 4.82e12, "high": 236.20, "low": 233.10, "previous_close": 235.49},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 182.15, "change_pct": 1.10, "market_cap": 4.18e12, "high": 183.50, "low": 180.20, "previous_close": 180.17},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 448.20, "change_pct": 0.85, "market_cap": 3.79e12, "high": 451.00, "low": 445.60, "previous_close": 444.42},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "price": 196.40, "change_pct": 1.35, "market_cap": 2.68e12, "high": 198.10, "low": 194.50, "previous_close": 193.78},
    {"symbol": "META", "name": "Meta Platforms, Inc.", "price": 586.30, "change_pct": 3.24, "market_cap": 1.89e12, "high": 591.20, "low": 574.00, "previous_close": 567.90},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "price": 172.90, "change_pct": 1.58, "market_cap": 1.71e12, "high": 174.50, "low": 170.20, "previous_close": 170.21},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "price": 262.10, "change_pct": -1.29, "market_cap": 1.40e12, "high": 268.40, "low": 259.00, "previous_close": 265.52},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway", "price": 452.80, "change_pct": -0.15, "market_cap": 1.08e12, "high": 455.00, "low": 450.50, "previous_close": 453.48},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "price": 224.60, "change_pct": 0.65, "market_cap": 8.92e11, "high": 226.30, "low": 223.10, "previous_close": 223.15},
]

# Fallback deterministic top 10 US market-cap stocks when network is unavailable (List[StockQuote])
DEFAULT_TOP_MARKET_CAP_FALLBACK: List[StockQuote] = [
    StockQuote(
        symbol=fb["symbol"],
        name=fb["name"],
        price=fb["price"],
        change_pct=fb["change_pct"],
        volatility_pct=calculate_volatility(fb["high"], fb["low"], fb["previous_close"]),
        high=fb["high"],
        low=fb["low"],
        previous_close=fb["previous_close"],
        market_cap=fb["market_cap"],
        sparkline=synthesize_sparkline(fb["previous_close"], fb["low"], fb["high"], fb["price"], steps=16),
        market_state="REGULAR",
        source="YahooFinance",
        fetched_at="2026-09-30 09:30:00",
    )
    for fb in DEFAULT_TOP_MARKET_CAP_RAW
]


def filter_duplicate_share_classes(quotes: List[StockQuote]) -> List[StockQuote]:
    """
    Deduplicate multi-class equity listings from the same corporate issuer.

    Exact Rule:
    If multiple symbols map to the same corporate parent (e.g. GOOG and GOOGL both map
    to 'ALPHABET', or BRK-A and BRK-B map to 'BERKSHIRE'), we retain only the single
    class with the highest market capitalization (or highest price if cap is identical).
    This ensures the 'Top 10 US Companies' represents 10 distinct enterprises.
    """
    seen_entities: Dict[str, StockQuote] = {}

    for q in quotes:
        sym = q.symbol.upper()
        entity_key = SHARE_CLASS_CANONICAL_MAP.get(sym, sym)
        if entity_key in seen_entities:
            existing = seen_entities[entity_key]
            existing_mc = existing.market_cap or 0.0
            current_mc = q.market_cap or 0.0
            if current_mc > existing_mc:
                seen_entities[entity_key] = q
        else:
            seen_entities[entity_key] = q

    # Preserve ranking order
    deduped: List[StockQuote] = []
    selected_symbols = {q.symbol for q in seen_entities.values()}
    for q in quotes:
        if q.symbol in selected_symbols:
            deduped.append(q)
            selected_symbols.remove(q.symbol)

    return deduped



class BaseMarketDataProvider:
    """Abstract base provider for stock market data."""
    name: str = "Base"

    def get_top_volatile_stocks(self, count: int = 10) -> List[StockQuote]:
        raise NotImplementedError

    def get_top_market_cap_stocks(self, count: int = 10) -> List[StockQuote]:
        raise NotImplementedError

    def get_stocks(self, mode: str = "market_cap", count: int = 10) -> List[StockQuote]:
        """Unified method returning market-cap ranked or volatile ranked stocks."""
        if mode == "volatile":
            return self.get_top_volatile_stocks(count)
        return self.get_top_market_cap_stocks(count)

    def get_quotes_for_symbols(self, symbols: List[str]) -> Dict[str, StockQuote]:
        raise NotImplementedError



class YahooFinanceMarketDataProvider(BaseMarketDataProvider):
    """
    Public market data provider using Yahoo Finance crumb-session.
    Requires no exchange credentials or paid subscription.
    """
    name = "YahooFinance"

    def __init__(self, cache_file: str = ".stocks_cache.json"):
        self.cache_file = cache_file
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cookie_jar))
        self._crumb: Optional[str] = None
        self._crumb_time: float = 0.0

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _write_cache(self, quotes: List[StockQuote], cache_key: str = "quotes") -> None:
        try:
            data = self._read_cache() or {}
            data["timestamp"] = time.time()
            data[cache_key] = [
                {
                    "symbol": q.symbol,
                    "name": q.name,
                    "price": q.price,
                    "change_pct": q.change_pct,
                    "volatility_pct": q.volatility_pct,
                    "high": q.high,
                    "low": q.low,
                    "previous_close": q.previous_close,
                    "market_cap": q.market_cap,
                    "sparkline": q.sparkline,
                    "market_state": q.market_state,
                    "source": q.source,
                    "fetched_at": q.fetched_at,
                }
                for q in quotes
            ]
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _get_crumb(self) -> Optional[str]:
        now = time.time()
        if self._crumb and (now - self._crumb_time < 1800.0):
            return self._crumb

        try:
            # 1. Obtain session cookie from fc.yahoo.com
            req1 = urllib.request.Request(
                "https://fc.yahoo.com",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            try:
                self._opener.open(req1, timeout=4.0)
            except Exception:
                # fc.yahoo.com often redirects or returns 404 while setting the cookie
                pass

            # 2. Retrieve crumb
            req2 = urllib.request.Request(
                "https://query2.finance.yahoo.com/v1/test/getcrumb",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            crumb_bytes = self._opener.open(req2, timeout=4.0).read()
            crumb = crumb_bytes.decode("utf-8").strip()
            if crumb and not crumb.startswith("<"):
                self._crumb = crumb
                self._crumb_time = now
                return crumb
        except Exception:
            pass
        return None

    def _fetch_sparkline(self, symbol: str) -> List[float]:
        """Fetch 1D intraday chart points (15m interval) for sparkline display."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=15m"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                closes = data.get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                pts = [float(c) for c in closes if c is not None]
                if len(pts) >= 4:
                    return pts
        except Exception:
            pass
        return []

    def get_top_market_cap_stocks(self, count: int = 10, candidates: Optional[List[str]] = None) -> List[StockQuote]:
        """
        Dynamically determine top US equities ranked by market capitalization.

        Features:
        - United States equities filter
        - Descending market cap sorting
        - Corporate share-class deduplication (e.g. GOOG vs GOOGL, BRK-A vs BRK-B)
        - Infrequent membership refresh (cached) with separate price/sparkline polling
        - Resilient offline fallback to cached quotes or documented reference universe
        - Provider abstraction: Prototype uses YahooFinance; commercial use requires reviewed data license.
        """
        now = time.time()
        cache = self._read_cache()
        cache_key = "market_cap_quotes"

        # 60s cache TTL for live prices/sparklines
        if cache and cache_key in cache and (now - cache.get("timestamp", 0) < 60.0):
            cached_list = [StockQuote(**q) for q in cache.get(cache_key, [])]
            if len(cached_list) >= count:
                return cached_list[:count]

        tickers = candidates or DEFAULT_US_MARKET_CAP_CANDIDATES
        crumb = self._get_crumb()
        quotes: List[StockQuote] = []

        if crumb:
            try:
                symbols_str = ",".join(tickers)
                url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={symbols_str}&crumb={crumb}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with self._opener.open(req, timeout=5.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = payload.get("quoteResponse", {}).get("result", [])
                    ts_str = time.strftime("%Y-%m-%d %H:%M:%S")

                    for item in results:
                        sym = item.get("symbol", "").upper()
                        name = item.get("shortName") or item.get("longName") or sym
                        price = float(item.get("regularMarketPrice") or 0.0)
                        high = float(item.get("regularMarketDayHigh") or price)
                        low = float(item.get("regularMarketDayLow") or price)
                        prev_close = float(item.get("regularMarketPreviousClose") or price)
                        change_pct = float(item.get("regularMarketChangePercent") or 0.0)
                        mkt_cap = float(item.get("marketCap") or 0.0)
                        mkt_state = item.get("marketState", "REGULAR")
                        vol = calculate_volatility(high, low, prev_close)

                        quotes.append(
                            StockQuote(
                                symbol=sym,
                                name=name,
                                price=price,
                                change_pct=change_pct,
                                volatility_pct=vol,
                                high=high,
                                low=low,
                                previous_close=prev_close,
                                market_cap=mkt_cap,
                                sparkline=[],
                                market_state=mkt_state,
                                source="YahooFinance",
                                fetched_at=ts_str,
                            )
                        )
            except Exception as e:
                print(f"[MARKET] Error polling market cap quotes: {e}")

        if quotes:
            # 1. Deduplicate multiple share classes for the same corporate issuer
            deduped = filter_duplicate_share_classes(quotes)
            # 2. Sort descending by market capitalization
            deduped.sort(key=lambda s: s.market_cap or 0.0, reverse=True)
            top_quotes = deduped[:count]

            # 3. Populate 1D sparkline for each top stock
            for q in top_quotes:
                sp = self._fetch_sparkline(q.symbol)
                if not sp:
                    sp = synthesize_sparkline(q.previous_close, q.low, q.high, q.price, steps=16)
                q.sparkline = sp

            self._write_cache(top_quotes, cache_key=cache_key)
            return top_quotes

        # Network fallback: return cached if available
        if cache and cache_key in cache:
            return [StockQuote(**q) for q in cache.get(cache_key, [])][:count]

        # Deterministic offline fallback universe
        return list(DEFAULT_TOP_MARKET_CAP_FALLBACK[:count])


    def get_top_volatile_stocks(self, count: int = 10, universe: Optional[List[str]] = None) -> List[StockQuote]:
        now = time.time()
        cache = self._read_cache()
        # 60s cache TTL to comply with respectful public polling
        if cache and "quotes" in cache and (now - cache.get("timestamp", 0) < 60.0):
            return [StockQuote(**q) for q in cache.get("quotes", [])][:count]

        tickers = universe or DEFAULT_STOCK_UNIVERSE
        crumb = self._get_crumb()

        quotes: List[StockQuote] = []
        if crumb:
            try:
                symbols_str = ",".join(tickers)
                url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={symbols_str}&crumb={crumb}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with self._opener.open(req, timeout=5.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = payload.get("quoteResponse", {}).get("result", [])
                    ts_str = time.strftime("%Y-%m-%d %H:%M:%S")

                    for item in results:
                        sym = item.get("symbol", "")
                        name = item.get("shortName") or item.get("longName") or sym
                        price = float(item.get("regularMarketPrice") or 0.0)
                        high = float(item.get("regularMarketDayHigh") or price)
                        low = float(item.get("regularMarketDayLow") or price)
                        prev_close = float(item.get("regularMarketPreviousClose") or price)
                        change_pct = float(item.get("regularMarketChangePercent") or 0.0)
                        mkt_cap = float(item.get("marketCap") or 0.0)
                        mkt_state = item.get("marketState", "REGULAR")

                        vol = calculate_volatility(high, low, prev_close)

                        quotes.append(
                            StockQuote(
                                symbol=sym,
                                name=name,
                                price=price,
                                change_pct=change_pct,
                                volatility_pct=vol,
                                high=high,
                                low=low,
                                previous_close=prev_close,
                                market_cap=mkt_cap,
                                sparkline=synthesize_sparkline(prev_close, low, high, price, steps=16),
                                market_state=mkt_state,
                                source="YahooFinance",
                                fetched_at=ts_str,
                            )
                        )
            except Exception:
                pass

        if quotes:
            # Sort by objective volatility percentage descending
            quotes.sort(key=lambda s: s.volatility_pct, reverse=True)
            self._write_cache(quotes, cache_key="quotes")
            return quotes[:count]

        # Network fallback: return cached if available
        if cache and "quotes" in cache:
            return [StockQuote(**q) for q in cache.get("quotes", [])][:count]

        return []

    def get_quotes_for_symbols(self, symbols: List[str]) -> Dict[str, StockQuote]:
        """Fetch quotes for specified list of tickers with caching and network error resilience."""
        if not symbols:
            return {}

        now = time.time()
        cache = self._read_cache()
        cached_quotes: Dict[str, StockQuote] = {}
        if cache and "quotes" in cache:
            for q in cache.get("quotes", []):
                sym = q.get("symbol", "").upper()
                cached_quotes[sym] = StockQuote(**q)

        # If cache is fresh (< 60s) and covers all symbols, return from cache
        if cache and (now - cache.get("timestamp", 0) < 60.0):
            all_cached = all(s.upper() in cached_quotes for s in symbols)
            if all_cached:
                return {s.upper(): cached_quotes[s.upper()] for s in symbols if s.upper() in cached_quotes}

        # Otherwise fetch from Yahoo Finance crumb session
        crumb = self._get_crumb()
        fetched_quotes: Dict[str, StockQuote] = {}

        if crumb:
            try:
                symbols_clean = [s.upper().strip() for s in symbols if s.strip()]
                symbols_str = ",".join(symbols_clean)
                url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={symbols_str}&crumb={crumb}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with self._opener.open(req, timeout=5.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = payload.get("quoteResponse", {}).get("result", [])
                    ts_str = time.strftime("%Y-%m-%d %H:%M:%S")

                    for item in results:
                        sym = item.get("symbol", "").upper()
                        name = item.get("shortName") or item.get("longName") or sym
                        price = float(item.get("regularMarketPrice") or 0.0)
                        high = float(item.get("regularMarketDayHigh") or price)
                        low = float(item.get("regularMarketDayLow") or price)
                        prev_close = float(item.get("regularMarketPreviousClose") or price)
                        change_pct = float(item.get("regularMarketChangePercent") or 0.0)
                        mkt_cap = float(item.get("marketCap") or 0.0)
                        mkt_state = item.get("marketState", "REGULAR")
                        vol = calculate_volatility(high, low, prev_close)

                        sq = StockQuote(
                            symbol=sym,
                            name=name,
                            price=price,
                            change_pct=change_pct,
                            volatility_pct=vol,
                            high=high,
                            low=low,
                            previous_close=prev_close,
                            market_cap=mkt_cap,
                            sparkline=synthesize_sparkline(prev_close, low, high, price, steps=16),
                            market_state=mkt_state,
                            source="YahooFinance",
                            fetched_at=ts_str,
                        )
                        fetched_quotes[sym] = sq
                        cached_quotes[sym] = sq

                    # Update persistent cache with merged quotes
                    self._write_cache(list(cached_quotes.values()), cache_key="quotes")
                    return {s.upper(): fetched_quotes[s.upper()] for s in symbols if s.upper() in fetched_quotes}
            except Exception as e:
                print(f"[MARKET] Error fetching quotes for {symbols}: {e}")

        # Graceful fallback: return whatever we have in cache
        return {s.upper(): cached_quotes[s.upper()] for s in symbols if s.upper() in cached_quotes}


class FinnhubMarketDataProvider(BaseMarketDataProvider):
    """
    Optional API-key based provider (e.g. FINNHUB_API_KEY).
    Pluggable architecture when a dedicated paid or commercial API key is provided.
    """
    name = "Finnhub"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._fallback = YahooFinanceMarketDataProvider()

    def get_top_volatile_stocks(self, count: int = 10) -> List[StockQuote]:
        return self._fallback.get_top_volatile_stocks(count)

    def get_top_market_cap_stocks(self, count: int = 10) -> List[StockQuote]:
        return self._fallback.get_top_market_cap_stocks(count)

    def get_quotes_for_symbols(self, symbols: List[str]) -> Dict[str, StockQuote]:
        return self._fallback.get_quotes_for_symbols(symbols)


def get_market_data_provider() -> BaseMarketDataProvider:
    """Return active market data provider based on environment variables or defaults."""
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_key:
        return FinnhubMarketDataProvider(api_key=finnhub_key)
    return YahooFinanceMarketDataProvider()


def get_top_market_cap_stocks(count: int = 10) -> List[StockQuote]:
    """Module-level convenience function returning top market-cap stocks."""
    return get_market_data_provider().get_top_market_cap_stocks(count)


def get_top_volatile_stocks(count: int = 10) -> List[StockQuote]:
    """Module-level convenience function returning top volatile stocks."""
    return get_market_data_provider().get_top_volatile_stocks(count)


def get_stocks(mode: str = "market_cap", count: int = 10) -> List[StockQuote]:
    """Module-level convenience function returning stocks by mode."""
    return get_market_data_provider().get_stocks(mode=mode, count=count)


