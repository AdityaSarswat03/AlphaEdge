"""
Analytics API Routes

Security:
  - Ticker path param validated with same regex as schemas.
  - SentimentRequest moved to schemas.py with length limits & extra="forbid".
  - Error responses sanitised (no raw exception details).
"""

import re

from fastapi import APIRouter, HTTPException, Depends, Path
from alphaedge.api.dependencies import get_predictor
from alphaedge.api.schemas import SentimentRequest
from alphaedge.core.predictor import AlphaEdge
from alphaedge.data.sentiment import SentimentAnalyzer
from alphaedge.logger import log
from alphaedge.api._error_utils import safe_error_detail

router = APIRouter()
sentiment = SentimentAnalyzer()

# Shared ticker regex (same as schemas._TICKER_PATTERN)
_TICKER_RE = re.compile(r"^[A-Z0-9&._-]{1,20}$")


@router.get("/analytics/{ticker}")
async def get_analytics(
    ticker: str = Path(
        ...,
        min_length=1,
        max_length=20,
        description="NSE ticker symbol.",
    ),
    predictor: AlphaEdge = Depends(get_predictor),
):
    """
    Return analytics for a given ticker – fundamentals + sentiment.
    """
    ticker = ticker.strip().upper()
    if not _TICKER_RE.match(ticker):
        raise HTTPException(status_code=422, detail="Invalid ticker symbol.")
    try:
        fundamentals = predictor.fetcher.fetch_fundamentals(ticker)
        return {
            "ticker": ticker,
            "fundamentals": fundamentals,
        }
    except Exception as e:
        log.error(f"GET /analytics/{ticker} failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))


@router.post("/sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyse sentiment for financial text or a list of headlines.

    Accepts either a single ``text`` or a list of ``texts``.
    """
    try:
        if request.texts:
            items = request.texts
        elif request.text:
            items = [request.text]
        else:
            raise HTTPException(status_code=422, detail="Provide 'text' or 'texts'.")

        df = sentiment.analyze_batch(items)
        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"POST /sentiment failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))
