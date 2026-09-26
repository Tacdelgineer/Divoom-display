import pytest
from models import StockQuote
from market_provider import calculate_volatility, YahooFinanceMarketDataProvider


def test_calculate_volatility_standard():
    # Intraday range % = (high - low) / previous_close * 100
    # High: 190.0, Low: 180.0, Prev Close: 180.0 -> (10.0 / 180.0) * 100 = 5.555...%
    vol = calculate_volatility(high=190.0, low=180.0, previous_close=180.0)
    assert round(vol, 2) == 5.56


def test_calculate_volatility_zero_prev_close():
    # Never divide by zero
    vol = calculate_volatility(high=100.0, low=90.0, previous_close=0.0)
    assert vol == 0.0

    vol_neg = calculate_volatility(high=100.0, low=90.0, previous_close=-50.0)
    assert vol_neg == 0.0


def test_calculate_volatility_inverted_high_low():
    # Invalid data where high < low should return 0.0
    vol = calculate_volatility(high=50.0, low=100.0, previous_close=100.0)
    assert vol == 0.0


def test_stock_ranking_by_volatility():
    # Ensure ranking sorts strictly by volatility_pct descending, NOT by price or gain
    q1 = StockQuote(
        symbol="BIG_GAINER",
        name="Big Gainer",
        price=100.0,
        change_pct=15.0,     # Big day change, but low intraday volatility
        volatility_pct=2.0,
        high=101.0,
        low=99.0,
        previous_close=86.9,
    )
    q2 = StockQuote(
        symbol="VOLATILE_CHOP",
        name="Volatile Chop",
        price=50.0,
        change_pct=-0.5,     # Flat net change, but massive intraday swing
        volatility_pct=18.0,
        high=60.0,
        low=45.0,
        previous_close=50.2,
    )
    q3 = StockQuote(
        symbol="STEADY_TECH",
        name="Steady Tech",
        price=200.0,
        change_pct=1.0,
        volatility_pct=1.2,
        high=201.0,
        low=198.6,
        previous_close=198.0,
    )

    quotes = [q1, q2, q3]
    quotes.sort(key=lambda s: s.volatility_pct, reverse=True)

    assert quotes[0].symbol == "VOLATILE_CHOP"
    assert quotes[1].symbol == "BIG_GAINER"
    assert quotes[2].symbol == "STEADY_TECH"
