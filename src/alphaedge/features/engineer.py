"""
Feature Engineering Pipeline – orchestrates technical indicators,
candlestick patterns, and custom features.
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from alphaedge.logger import log
from alphaedge.features.technical import TechnicalIndicators
from alphaedge.features.patterns import CandlestickPatterns


class FeatureEngineer:
    """Engineer features for ML models."""

    def __init__(self):
        self.feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full feature-engineering pipeline.

        Args:
            df: Raw OHLCV DataFrame (must contain Date, Open, High, Low, Close, Volume).

        Returns:
            DataFrame with all engineered features appended.
        """
        df = df.copy()

        # Technical indicators (25+)
        df = TechnicalIndicators.add_all(df)

        # Candlestick patterns
        df = CandlestickPatterns.add_all(df)

        # Price features
        df = self._add_price_features(df)

        # Volume features
        df = self._add_volume_features(df)

        # Momentum features
        df = self._add_momentum_features(df)

        # Volatility features
        df = self._add_volatility_features(df)

        # Time features
        df = self._add_time_features(df)

        # Target variable
        df = self._add_target(df)

        # ── Sanitise numeric issues ────────────────────────────────
        # Many indicators produce inf/-inf from division by zero or
        # near-zero denominators (pct_change on 0 volume, BB_Width
        # when bands converge, etc.).  XGBoost rejects any inf value,
        # so we replace them with NaN first, then forward/back-fill.
        numeric_cols = df.select_dtypes(include=["number"]).columns
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

        # Clip extreme outliers (> ±1e10) that survive indicator math
        # but would still blow up tree splits or gradient computation.
        df[numeric_cols] = df[numeric_cols].clip(-1e10, 1e10)

        # Fill remaining NaNs
        df = df.ffill().bfill().fillna(0)

        self.feature_names = [
            c for c in df.columns
            if c not in ("Date", "Symbol", "Target", "Target_Direction")
        ]
        log.info(f"Feature engineering complete – {len(self.feature_names)} feature columns")
        return df

    # ── Price features ───────────────────────────────────────────
    @staticmethod
    def _add_price_features(df: pd.DataFrame) -> pd.DataFrame:
        df["Price_Change"] = df["Close"].pct_change()
        df["High_Low_Range"] = (df["High"] - df["Low"]) / df["Close"]
        df["Close_Open_Range"] = (df["Close"] - df["Open"]) / df["Open"].replace(0, np.nan)

        for col in ("SMA_20", "SMA_50"):
            if col in df.columns:
                df[f"Dist_{col}"] = (df["Close"] - df[col]) / df["Close"]
        return df

    # ── Volume features ──────────────────────────────────────────
    @staticmethod
    def _add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
        df["Volume_Change"] = df["Volume"].pct_change()
        df["Volume_SMA_20"] = df["Volume"].rolling(20).mean()
        vol_sma = df["Volume_SMA_20"].replace(0, np.nan)
        df["Volume_Ratio"] = df["Volume"] / vol_sma
        return df

    # ── Momentum features ────────────────────────────────────────
    @staticmethod
    def _add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
        for w in (5, 10, 20):
            df[f"Momentum_{w}"] = df["Close"].pct_change(w)
        df["ROC_10"] = df["Close"].pct_change(10) * 100
        return df

    # ── Volatility features ──────────────────────────────────────
    @staticmethod
    def _add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
        rets = df["Close"].pct_change()
        df["Volatility_10"] = rets.rolling(10).std()
        df["Volatility_20"] = rets.rolling(20).std()
        df["Volatility_60"] = rets.rolling(60).std()
        return df

    # ── Time features ────────────────────────────────────────────
    @staticmethod
    def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        if "Date" in df.columns:
            dt = pd.to_datetime(df["Date"])
            df["Day_of_Week"] = dt.dt.dayofweek
            df["Month"] = dt.dt.month
            df["Quarter"] = dt.dt.quarter
            df["Is_Month_Start"] = dt.dt.is_month_start.astype(int)
            df["Is_Month_End"] = dt.dt.is_month_end.astype(int)
        return df

    # ── Target variable ──────────────────────────────────────────
    @staticmethod
    def _add_target(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
        """Next-day close as regression target; direction as classification target."""
        df["Target"] = df["Close"].shift(-horizon)
        df["Target_Direction"] = (df["Target"] > df["Close"]).astype(int)
        return df

    # ── Helper: get feature matrix ───────────────────────────────
    def get_feature_columns(self) -> List[str]:
        """Return the list of feature column names (excludes Date, Symbol, Target)."""
        return self.feature_names
