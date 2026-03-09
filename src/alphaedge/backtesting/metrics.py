"""
Performance metrics for backtesting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


class PerformanceMetrics:
    """Calculate risk-adjusted performance metrics from an equity curve."""

    @staticmethod
    def calculate(equity_curve: pd.Series, risk_free_rate: float = 0.05) -> Dict[str, Any]:
        """
        Compute a full suite of metrics.

        Args:
            equity_curve: Series of portfolio values indexed by date.
            risk_free_rate: Annual risk-free rate (default 5 %).

        Returns:
            Dict of named metrics.
        """
        returns = equity_curve.pct_change().dropna()

        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        n_days = len(equity_curve)
        n_years = n_days / 252

        # Annualised return
        annual_return = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1

        # Annualised volatility
        annual_vol = returns.std() * np.sqrt(252)

        # Sharpe ratio
        sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0.0

        # Sortino (down-side deviation)
        downside = (
            returns[returns < 0].std() * np.sqrt(252) if len(returns[returns < 0]) > 0 else 1e-6
        )
        sortino = (annual_return - risk_free_rate) / downside

        # Max drawdown
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_dd = drawdown.min()

        # Calmar ratio
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0.0

        # Win rate
        winning = (returns > 0).sum()
        win_rate = winning / len(returns) if len(returns) > 0 else 0.0

        # Profit factor
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum()) or 1e-6
        profit_factor = gross_profit / gross_loss

        return {
            "total_return": round(float(total_return), 4),
            "annual_return": round(float(annual_return), 4),
            "annual_volatility": round(float(annual_vol), 4),
            "sharpe_ratio": round(float(sharpe), 4),
            "sortino_ratio": round(float(sortino), 4),
            "max_drawdown": round(float(max_dd), 4),
            "calmar_ratio": round(float(calmar), 4),
            "win_rate": round(float(win_rate), 4),
            "profit_factor": round(float(profit_factor), 4),
            "total_trades": int(len(returns)),
            "trading_days": n_days,
        }
