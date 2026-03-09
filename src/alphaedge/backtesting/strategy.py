"""
Trading strategies for the backtesting engine.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class Strategy(ABC):
    """Base class for trading strategies."""

    name: str = "base"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Return a Series of signals aligned with *df* index.
        1 = buy, -1 = sell, 0 = hold.
        """
        ...


class BuyAndHoldStrategy(Strategy):
    """Buy on day 1, hold forever."""

    name = "buy_and_hold"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        signals.iloc[0] = 1
        return signals


class MeanReversionStrategy(Strategy):
    """Buy when price drops below lower Bollinger Band, sell above upper."""

    name = "mean_reversion"

    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        sma = close.rolling(self.window).mean()
        std = close.rolling(self.window).std()
        upper = sma + self.num_std * std
        lower = sma - self.num_std * std

        signals = pd.Series(0, index=df.index)
        signals[close < lower] = 1  # buy
        signals[close > upper] = -1  # sell
        return signals


class MomentumStrategy(Strategy):
    """Buy when short MA crosses above long MA, sell on cross below."""

    name = "momentum"

    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short = short_window
        self.long = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        short_ma = df["Close"].rolling(self.short).mean()
        long_ma = df["Close"].rolling(self.long).mean()

        signals = pd.Series(0, index=df.index)
        signals[short_ma > long_ma] = 1
        signals[short_ma <= long_ma] = -1
        return signals


class RSIStrategy(Strategy):
    """Buy when RSI < oversold, sell when RSI > overbought."""

    name = "rsi"

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)

        signals = pd.Series(0, index=df.index)
        signals[rsi < self.oversold] = 1
        signals[rsi > self.overbought] = -1
        return signals


# Registry for easy look-up
STRATEGIES = {
    "buy_and_hold": BuyAndHoldStrategy,
    "mean_reversion": MeanReversionStrategy,
    "momentum": MomentumStrategy,
    "rsi": RSIStrategy,
}
