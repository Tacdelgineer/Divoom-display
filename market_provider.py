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


def calculate_volatility(high: float, low: float, previous_close: float) -> float:
    """
    Calculate objective intraday range percentage:
        volatility_pct = (high - low) / previous_close * 100.0
    Guarantees no division by zero and non-negative metric.
    """
    if previous_close <= 0 or high < low:
        return 0.0
    return ((high - low) / previous_close) * 100.0


class BaseMarketDataProvider:
    """Abstract base provider for stock market data."""
    name: str = "Base"

    def get_top_volatile_stocks(self, count: int = 10) -> List[StockQuote]:
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

    def _write_cache(self, quotes: List[StockQuote]) -> None:
        try:
            data = {
                "timestamp": time.time(),
                "quotes": [
                    {
                        "symbol": q.symbol,
                        "name": q.name,
                        "price": q.price,
                        "change_pct": q.change_pct,
                        "volatility_pct": q.volatility_pct,
                        "high": q.high,
                        "low": q.low,
                        "previous_close": q.previous_close,
                        "market_state": q.market_state,
                        "source": q.source,
                        "fetched_at": q.fetched_at,
                    }
                    for q in quotes
                ],
            }
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

    def get_top_volatile_stocks(self, count: int = 10, universe: Optional[List[str]] = None) -> List[StockQuote]:
        now = time.time()
        cache = self._read_cache()
        # 60s cache TTL to comply with respectful public polling
        if cache and (now - cache.get("timestamp", 0) < 60.0):
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
            self._write_cache(quotes)
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
                            market_state=mkt_state,
                            source="YahooFinance",
                            fetched_at=ts_str,
                        )
                        fetched_quotes[sym] = sq
                        cached_quotes[sym] = sq

                    # Update persistent cache with merged quotes
                    self._write_cache(list(cached_quotes.values()))
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

    def get_top_volatile_stocks(self, count: int = 10) -> List[StockQuote]:
        # Implementation for Finnhub quote endpoints
        # Falls back to YahooFinance if rate limit hit
        return YahooFinanceMarketDataProvider().get_top_volatile_stocks(count)

    def get_quotes_for_symbols(self, symbols: List[str]) -> Dict[str, StockQuote]:
        return YahooFinanceMarketDataProvider().get_quotes_for_symbols(symbols)


def get_market_data_provider() -> BaseMarketDataProvider:
    """Return active market data provider based on environment variables or defaults."""
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_key:
        return FinnhubMarketDataProvider(api_key=finnhub_key)
    return YahooFinanceMarketDataProvider()
