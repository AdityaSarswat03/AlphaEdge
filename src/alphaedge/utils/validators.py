"""
Data validation helpers.
"""
import re
from datetime import datetime
from typing import List


def validate_ticker(ticker: str) -> str:
    """Validate and normalise a ticker symbol."""
    ticker = ticker.strip().upper()
    if not re.match(r"^[A-Z0-9&._-]{1,20}$", ticker):
        raise ValueError(f"Invalid ticker symbol: {ticker}")
    return ticker


def validate_date(date_str: str) -> str:
    """Validate YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
    return date_str


def validate_tickers(tickers: List[str]) -> List[str]:
    """Validate a list of ticker symbols."""
    return [validate_ticker(t) for t in tickers]


def validate_horizon(horizon: int) -> int:
    """Validate prediction horizon."""
    if not 1 <= horizon <= 30:
        raise ValueError(f"Horizon must be 1-30, got {horizon}")
    return horizon
