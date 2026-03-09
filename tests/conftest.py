"""
Shared pytest fixtures for AlphaEdge tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame (100 rows)."""
    np.random.seed(42)
    n = 100
    dates = pd.bdate_range(end=datetime.now(), periods=n)
    close = 1000 + np.cumsum(np.random.randn(n) * 10)
    return pd.DataFrame(
        {
            "Open": close - np.random.rand(n) * 5,
            "High": close + np.random.rand(n) * 10,
            "Low": close - np.random.rand(n) * 10,
            "Close": close,
            "Volume": np.random.randint(100_000, 1_000_000, n),
        },
        index=dates,
    )


@pytest.fixture
def sample_featured(sample_ohlcv) -> pd.DataFrame:
    """OHLCV enriched with basic mock features and a target."""
    df = sample_ohlcv.copy()
    df["sma_20"] = df["Close"].rolling(20).mean()
    df["sma_50"] = df["Close"].rolling(50).mean()
    df["rsi"] = 50 + np.random.randn(len(df)) * 10
    df["macd"] = np.random.randn(len(df))
    df["target"] = df["Close"].shift(-1)
    df.dropna(inplace=True)
    return df


@pytest.fixture
def feature_columns():
    return ["sma_20", "sma_50", "rsi", "macd"]
