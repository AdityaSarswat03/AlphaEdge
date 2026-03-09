"""
Prediction API Routes (protected by Clerk auth)

Security:
  - All request bodies validated via strict Pydantic schemas (extra="forbid").
  - GET path/query params validated with Path() / Query() constraints.
  - Error responses sanitised — raw exception messages never reach the client.
"""
import re

from fastapi import APIRouter, HTTPException, Depends, Path, Query
from typing import List, Optional
from alphaedge.api.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
)
from alphaedge.api.dependencies import get_predictor, get_optional_user, ClerkUser
from alphaedge.core.predictor import AlphaEdge
from alphaedge.utils.firebase_db import save_prediction
from alphaedge.logger import log
from alphaedge.api._error_utils import safe_error_detail

router = APIRouter()

DEFAULT_TICKERS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
                   "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "WIPRO"]

# Shared ticker regex (same as schemas._TICKER_PATTERN)
_TICKER_RE = re.compile(r"^[A-Z0-9&._-]{1,20}$")


@router.post("/predict", response_model=PredictionResponse)
async def predict_stock(
    request: PredictionRequest,
    predictor: AlphaEdge = Depends(get_predictor),
    user: Optional[ClerkUser] = Depends(get_optional_user),
):
    """
    Predict the next-day stock price.

    - **ticker**: NSE ticker symbol (e.g. RELIANCE, TCS)
    - **horizon**: Days ahead (1-5)
    """
    try:
        result = predictor.predict(
            ticker=request.ticker,
            horizon=request.horizon,
            include_confidence=request.include_confidence,
        )
        # Persist to Firebase
        save_prediction(request.ticker, {
            **result,
            "requested_by": user.user_id if user else "anonymous",
        })
        return result
    except Exception as e:
        log.error(f"POST /predict failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))


@router.get("/predict/{ticker}", response_model=PredictionResponse)
async def predict_stock_get(
    ticker: str = Path(
        ...,
        min_length=1,
        max_length=20,
        description="NSE ticker symbol.",
    ),
    horizon: int = Query(1, ge=1, le=5, description="Days ahead (1-5)"),
    predictor: AlphaEdge = Depends(get_predictor),
):
    """Quick prediction via GET."""
    ticker = ticker.strip().upper()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(status_code=422, detail="Invalid ticker symbol.")
    try:
        return predictor.predict(ticker=ticker, horizon=horizon)
    except Exception as e:
        log.error(f"GET /predict/{ticker} failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))


@router.post("/predict/batch")
async def predict_batch(
    request: BatchPredictionRequest,
    predictor: AlphaEdge = Depends(get_predictor),
):
    """Predict multiple stocks at once."""
    try:
        df = predictor.predict_multiple(request.tickers, horizon=request.horizon)
        return df.to_dict(orient="records")
    except Exception as e:
        log.error(f"POST /predict/batch failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))


@router.get("/top-picks")
async def top_picks(
    top_n: int = Query(10, ge=1, le=50, description="Number of picks (1-50)"),
    min_confidence: float = Query(
        0.6, ge=0.0, le=1.0, description="Minimum confidence threshold (0.0-1.0)"
    ),
    predictor: AlphaEdge = Depends(get_predictor),
):
    """Get top stock picks sorted by predicted return."""
    try:
        df = predictor.get_top_picks(DEFAULT_TICKERS, top_n=top_n, min_confidence=min_confidence)
        return df.to_dict(orient="records")
    except Exception as e:
        log.error(f"GET /top-picks failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))
