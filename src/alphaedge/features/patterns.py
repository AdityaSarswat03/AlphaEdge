"""
Candlestick pattern detection (pure-Python, no TA-Lib C dep).
"""

import pandas as pd
import numpy as np
from alphaedge.logger import log


class CandlestickPatterns:
    """Detect common candlestick patterns from OHLC data."""

    @staticmethod
    def add_all(df: pd.DataFrame) -> pd.DataFrame:
        """Add pattern signals (1 = bullish, -1 = bearish, 0 = none)."""
        df = df.copy()
        o, h, low, c = df["Open"], df["High"], df["Low"], df["Close"]
        body = (c - o).abs()
        upper_shadow = h - pd.concat([o, c], axis=1).max(axis=1)
        lower_shadow = pd.concat([o, c], axis=1).min(axis=1) - low
        avg_body = body.rolling(20).mean().replace(0, np.nan)

        # ── Doji ─────────────────────────────────────────────────
        df["CDL_DOJI"] = (body < avg_body * 0.1).astype(int)

        # ── Hammer ───────────────────────────────────────────────
        df["CDL_HAMMER"] = ((lower_shadow > 2 * body) & (upper_shadow < body * 0.3)).astype(int)

        # ── Inverted Hammer ──────────────────────────────────────
        df["CDL_INV_HAMMER"] = ((upper_shadow > 2 * body) & (lower_shadow < body * 0.3)).astype(int)

        # ── Engulfing ────────────────────────────────────────────
        prev_body = body.shift(1)
        bullish_engulf = (c > o) & (o.shift(1) > c.shift(1)) & (body > prev_body)
        bearish_engulf = (o > c) & (c.shift(1) > o.shift(1)) & (body > prev_body)
        df["CDL_ENGULFING"] = bullish_engulf.astype(int) - bearish_engulf.astype(int)

        # ── Morning Star (3-bar) ─────────────────────────────────
        day1_bear = c.shift(2) < o.shift(2)
        day2_small = body.shift(1) < avg_body * 0.3
        day3_bull = (c > o) & (c > (o.shift(2) + c.shift(2)) / 2)
        df["CDL_MORNING_STAR"] = (day1_bear & day2_small & day3_bull).astype(int)

        # ── Evening Star (3-bar) ─────────────────────────────────
        day1_bull = c.shift(2) > o.shift(2)
        day3_bear = (o > c) & (c < (o.shift(2) + c.shift(2)) / 2)
        df["CDL_EVENING_STAR"] = (day1_bull & day2_small & day3_bear).astype(int) * -1

        # ── Three White Soldiers ─────────────────────────────────
        bull1 = c.shift(2) > o.shift(2)
        bull2 = c.shift(1) > o.shift(1)
        bull3 = c > o
        rising = (c > c.shift(1)) & (c.shift(1) > c.shift(2))
        df["CDL_3_WHITE_SOLDIERS"] = (bull1 & bull2 & bull3 & rising).astype(int)

        # ── Three Black Crows ────────────────────────────────────
        bear1 = o.shift(2) > c.shift(2)
        bear2 = o.shift(1) > c.shift(1)
        bear3 = o > c
        falling = (c < c.shift(1)) & (c.shift(1) < c.shift(2))
        df["CDL_3_BLACK_CROWS"] = (bear1 & bear2 & bear3 & falling).astype(int) * -1

        # ── Shooting Star ────────────────────────────────────────
        df["CDL_SHOOTING_STAR"] = (
            (upper_shadow > 2 * body) & (lower_shadow < body * 0.3) & (c < o)
        ).astype(int) * -1

        pattern_cols = [c for c in df.columns if c.startswith("CDL_")]
        log.info(f"Added {len(pattern_cols)} candlestick patterns")
        return df
