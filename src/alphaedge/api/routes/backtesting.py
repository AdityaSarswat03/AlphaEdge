"""
Backtesting API Routes

Security:
  - Strategy now validated at schema level (Literal type).
  - Error responses sanitised.
"""

from fastapi import APIRouter, HTTPException
from alphaedge.api.schemas import BacktestRequest, BacktestResponse
from alphaedge.backtesting.engine import Backtester
from alphaedge.backtesting.strategy import STRATEGIES
from alphaedge.logger import log
from alphaedge.api._error_utils import safe_error_detail

router = APIRouter()


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest for a given ticker and strategy.

    Strategies: buy_and_hold, mean_reversion, momentum, rsi
    """
    # Strategy is already validated by the Literal type in BacktestRequest,
    # but we double-check against the runtime dict in case it drifts.
    if request.strategy not in STRATEGIES:
        # OWASP: Don't enumerate internal strategy names in production.
        log.warning(
            f"Strategy mismatch: schema accepted '{request.strategy}' but STRATEGIES dict doesn't contain it"
        )
        raise HTTPException(
            status_code=400,
            detail="Unknown strategy.",
        )
    try:
        bt = Backtester(initial_capital=request.initial_capital)
        result = bt.run(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_name=request.strategy,
        )
        # Remove large arrays for JSON response
        result.pop("equity_curve", None)
        result.pop("trades", None)
        return result
    except Exception as e:
        log.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e))


@router.get("/strategies")
async def list_strategies():
    """List available backtesting strategies."""
    return {"strategies": list(STRATEGIES.keys())}
