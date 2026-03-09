"""
Pydantic schemas for request / response validation.

Security hardening (OWASP):
  - All request models use ``extra = "forbid"`` to reject unexpected fields.
  - Ticker symbols are constrained by regex + max-length.
  - Free-text inputs have explicit max-length limits to prevent payload abuse.
  - Dates are validated at schema level via a ``field_validator``.
  - Strategy is restricted to a ``Literal`` enum.
"""
import re
from datetime import datetime
from typing import Literal, Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Shared constants ─────────────────────────────────────────────
# Ticker: 1-20 uppercase alphanumeric chars plus & . _ -
_TICKER_PATTERN = r"^[A-Z0-9&._-]{1,20}$"
_TICKER_DESCRIPTION = "NSE ticker symbol (e.g. RELIANCE, TCS). 1-20 uppercase alphanumeric chars."

# Allowed backtesting strategies (must match keys in STRATEGIES dict)
ALLOWED_STRATEGIES = Literal[
    "buy_and_hold", "mean_reversion", "momentum", "rsi"
]


# ── Prediction Schemas ───────────────────────────────────────────

class PredictionRequest(BaseModel):
    """Request body for single-stock prediction."""
    model_config = ConfigDict(extra="forbid")  # OWASP: reject unknown fields

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        pattern=_TICKER_PATTERN,
        description=_TICKER_DESCRIPTION,
        examples=["RELIANCE"],
    )
    horizon: int = Field(1, ge=1, le=5, description="Days ahead (1-5)")
    include_confidence: bool = True

    @field_validator("ticker", mode="before")
    @classmethod
    def _normalise_ticker(cls, v: str) -> str:
        """Strip whitespace and upper-case before regex check."""
        if isinstance(v, str):
            return v.strip().upper()
        return v


class PredictionResponse(BaseModel):
    ticker: str
    current_price: float
    predicted_price: float
    change_percent: float
    direction: str
    confidence: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    timestamp: str
    model_version: str


class BatchPredictionRequest(BaseModel):
    """Request body for multi-stock batch prediction."""
    model_config = ConfigDict(extra="forbid")

    tickers: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of ticker symbols (1-50).",
    )
    horizon: int = Field(1, ge=1, le=5)

    @field_validator("tickers", mode="before")
    @classmethod
    def _normalise_tickers(cls, v: list) -> list:
        """Normalise and validate each ticker in the list."""
        if not isinstance(v, list):
            raise ValueError("tickers must be a list")
        cleaned: list[str] = []
        for t in v:
            if not isinstance(t, str):
                raise ValueError(f"Each ticker must be a string, got {type(t).__name__}")
            t = t.strip().upper()
            if not re.match(_TICKER_PATTERN, t):
                raise ValueError(
                    f"Invalid ticker '{t}'. Must match {_TICKER_PATTERN}"
                )
            cleaned.append(t)
        return cleaned


class TopPicksResponse(BaseModel):
    picks: List[PredictionResponse]


# ── Backtesting Schemas ──────────────────────────────────────────

class BacktestRequest(BaseModel):
    """Request body for running a backtest."""
    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        pattern=_TICKER_PATTERN,
        description=_TICKER_DESCRIPTION,
        examples=["RELIANCE"],
    )
    start_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Start date in YYYY-MM-DD format.",
        examples=["2024-01-01"],
    )
    end_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="End date in YYYY-MM-DD format.",
        examples=["2025-12-31"],
    )
    strategy: ALLOWED_STRATEGIES = Field(
        "momentum",
        description="Backtesting strategy. One of: buy_and_hold, mean_reversion, momentum, rsi.",
    )
    initial_capital: float = Field(
        100_000.0,
        gt=0,
        le=1_000_000_000,  # sanity cap: 1 billion
        description="Starting capital (must be > 0).",
    )

    @field_validator("ticker", mode="before")
    @classmethod
    def _normalise_ticker(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_date(cls, v: str) -> str:
        """Ensure dates are valid YYYY-MM-DD strings."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date '{v}'. Expected format: YYYY-MM-DD.")
        return v


class BacktestResponse(BaseModel):
    ticker: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int


# ── Analytics Schemas ────────────────────────────────────────────

class SentimentRequest(BaseModel):
    """Request body for sentiment analysis.

    OWASP: length limits prevent denial-of-service via oversized payloads.
    """
    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        "",
        max_length=5_000,
        description="Single text to analyse (max 5 000 chars).",
    )
    texts: List[str] = Field(
        default_factory=list,
        max_length=100,
        description="List of texts to analyse (max 100 items).",
    )

    @field_validator("texts")
    @classmethod
    def _validate_text_lengths(cls, v: list[str]) -> list[str]:
        """Enforce per-item length limit."""
        for i, t in enumerate(v):
            if len(t) > 5_000:
                raise ValueError(
                    f"texts[{i}] exceeds 5 000 character limit ({len(t)} chars)."
                )
        return v


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class AnalyticsResponse(BaseModel):
    ticker: str
    top_features: List[FeatureImportanceItem]
