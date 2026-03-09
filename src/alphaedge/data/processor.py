"""
Data preprocessing and cleaning pipeline.
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from alphaedge.logger import log


class DataProcessor:
    """Clean, validate, and prepare raw OHLCV data for modelling."""

    REQUIRED_COLS = ["Date", "Open", "High", "Low", "Close", "Volume"]

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full processing pipeline.

        Steps:
            1. Validate required columns.
            2. Sort by date.
            3. Handle missing values.
            4. Remove outliers.
            5. Add returns column.
        """
        df = df.copy()
        df = self._validate(df)
        df = self._sort(df)
        df = self._handle_missing(df)
        df = self._remove_outliers(df)
        df = self._add_returns(df)
        log.info(f"Processed dataframe: {df.shape}")
        return df

    # ── internal steps ───────────────────────────────────────────
    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in self.REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        return df

    def _sort(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Date"] = pd.to_datetime(df["Date"])
        return df.sort_values("Date").reset_index(drop=True)

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number]).columns
        df[numeric] = df[numeric].ffill().bfill()
        df.dropna(subset=["Close"], inplace=True)
        return df

    def _remove_outliers(self, df: pd.DataFrame, z_threshold: float = 5.0) -> pd.DataFrame:
        """Remove rows where daily return > z_threshold std."""
        returns = df["Close"].pct_change()
        mean, std = returns.mean(), returns.std()
        if std > 0:
            z_scores = ((returns - mean) / std).abs()
            df = df[z_scores.fillna(0) < z_threshold]
        return df.reset_index(drop=True)

    def _add_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Returns"] = df["Close"].pct_change()
        df["Log_Returns"] = np.log(df["Close"] / df["Close"].shift(1))
        return df

    # ── Train / Val / Test split ─────────────────────────────────
    @staticmethod
    def split(
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Time-based split (no shuffling).

        Returns:
            (train, validation, test) DataFrames.
        """
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]
