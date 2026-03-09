"""
Technical Indicators using the `ta` library (pure-Python, no TA-Lib C dep).
"""

import pandas as pd
import numpy as np
from ta import trend, momentum, volatility, volume as ta_vol
from alphaedge.logger import log


class TechnicalIndicators:
    """Compute 25+ technical indicators on an OHLCV DataFrame."""

    @staticmethod
    def add_all(df: pd.DataFrame) -> pd.DataFrame:
        """Add every supported indicator group to *df* (in-place copy)."""
        df = df.copy()
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        vol = df["Volume"].astype(float)

        # ── Moving Averages ──────────────────────────────────────
        df["SMA_20"] = trend.sma_indicator(close, window=20)
        df["SMA_50"] = trend.sma_indicator(close, window=50)
        df["SMA_200"] = trend.sma_indicator(close, window=200)
        df["EMA_12"] = trend.ema_indicator(close, window=12)
        df["EMA_26"] = trend.ema_indicator(close, window=26)

        # ── RSI ──────────────────────────────────────────────────
        df["RSI_14"] = momentum.rsi(close, window=14)
        df["RSI_28"] = momentum.rsi(close, window=28)

        # ── MACD ─────────────────────────────────────────────────
        macd_obj = trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd_obj.macd()
        df["MACD_Signal"] = macd_obj.macd_signal()
        df["MACD_Hist"] = macd_obj.macd_diff()

        # ── Bollinger Bands ──────────────────────────────────────
        bb = volatility.BollingerBands(close, window=20, window_dev=2)
        df["BB_Upper"] = bb.bollinger_hband()
        df["BB_Middle"] = bb.bollinger_mavg()
        df["BB_Lower"] = bb.bollinger_lband()
        bb_mid = df["BB_Middle"].replace(0, np.nan)
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / bb_mid
        bb_range = (df["BB_Upper"] - df["BB_Lower"]).replace(0, np.nan)
        df["BB_Position"] = (close - df["BB_Lower"]) / bb_range

        # ── ATR ──────────────────────────────────────────────────
        df["ATR_14"] = volatility.average_true_range(high, low, close, window=14)

        # ── Stochastic ───────────────────────────────────────────
        stoch = momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()

        # ── ADX ──────────────────────────────────────────────────
        adx_obj = trend.ADXIndicator(high, low, close, window=14)
        df["ADX_14"] = adx_obj.adx()

        # ── CCI ──────────────────────────────────────────────────
        df["CCI_20"] = trend.cci(high, low, close, window=20)

        # ── Williams %R ──────────────────────────────────────────
        df["WILLR_14"] = momentum.williams_r(high, low, close, lbp=14)

        # ── OBV ──────────────────────────────────────────────────
        df["OBV"] = ta_vol.on_balance_volume(close, vol)

        # ── CMF ──────────────────────────────────────────────────
        df["CMF_20"] = ta_vol.chaikin_money_flow(high, low, close, vol, window=20)

        # ── Ichimoku ─────────────────────────────────────────────
        ichi = trend.IchimokuIndicator(high, low, window1=9, window2=26, window3=52)
        df["ICHIMOKU_A"] = ichi.ichimoku_a()
        df["ICHIMOKU_B"] = ichi.ichimoku_b()

        # ── VWAP (rolling proxy) ─────────────────────────────────
        tp = (high + low + close) / 3
        cum_tp_vol = (tp * vol).rolling(window=20).sum()
        cum_vol = vol.rolling(window=20).sum().replace(0, np.nan)
        df["VWAP_20"] = cum_tp_vol / cum_vol

        log.info(
            f"Added {len([c for c in df.columns if c not in ('Date','Open','High','Low','Close','Volume','Symbol')])} technical indicators"
        )
        return df
