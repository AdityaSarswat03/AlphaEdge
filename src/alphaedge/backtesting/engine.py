"""
Backtesting Engine – simulates trading with realistic costs.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from alphaedge.config import settings
from alphaedge.logger import log
from alphaedge.data.fetcher import DataFetcher
from alphaedge.data.processor import DataProcessor
from alphaedge.backtesting.strategy import Strategy, STRATEGIES, BuyAndHoldStrategy
from alphaedge.backtesting.metrics import PerformanceMetrics


class Backtester:
    """Simulate and evaluate trading strategies."""

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.fetcher = DataFetcher()
        self.processor = DataProcessor()

    def run(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        strategy_name: str = "momentum",
    ) -> Dict[str, Any]:
        """
        Run a full backtest.

        Args:
            ticker: Stock ticker.
            start_date / end_date: YYYY-MM-DD.
            strategy_name: One of the registered strategy names.

        Returns:
            Dict with equity_curve, metrics, trades, etc.
        """
        log.info(f"Backtesting {ticker} [{start_date} → {end_date}]  strategy={strategy_name}")

        # 1. Fetch & clean data
        raw = self.fetcher.fetch_stock_data(ticker, start_date, end_date)
        if raw.empty:
            raise ValueError(f"No data for {ticker}")
        data = self.processor.process(raw)

        # 2. Strategy signals
        strategy_cls = STRATEGIES.get(strategy_name, BuyAndHoldStrategy)
        strategy: Strategy = strategy_cls() if isinstance(strategy_cls, type) else strategy_cls
        signals = strategy.generate_signals(data)

        # 3. Simulate
        equity, trades = self._simulate(data, signals)

        # 4. Metrics
        equity_series = pd.Series(equity, index=data["Date"].iloc[: len(equity)])
        metrics = PerformanceMetrics.calculate(equity_series)

        result: Dict[str, Any] = {
            "ticker": ticker,
            "strategy": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": self.initial_capital,
            "final_value": round(equity[-1], 2),
            **metrics,
            "trades": trades,
            "equity_curve": equity,
        }
        log.info(
            f"Backtest done – return={metrics['total_return']:.2%}  "
            f"sharpe={metrics['sharpe_ratio']:.2f}"
        )
        return result

    # ── Simulation loop ──────────────────────────────────────────
    def _simulate(self, data: pd.DataFrame, signals: pd.Series):
        cash = self.initial_capital
        position = 0  # number of shares
        equity = []
        trades = []

        for i, (_, row) in enumerate(data.iterrows()):
            price = row["Close"]
            signal = signals.iloc[i] if i < len(signals) else 0

            # Execution with slippage
            exec_price = price * (1 + self.slippage) if signal == 1 else price * (1 - self.slippage)

            if signal == 1 and position == 0:
                # Buy
                shares = int(cash / (exec_price * (1 + self.commission)))
                if shares > 0:
                    cost = shares * exec_price * (1 + self.commission)
                    cash -= cost
                    position = shares
                    trades.append({
                        "date": str(row.get("Date", i)),
                        "action": "BUY",
                        "price": round(exec_price, 2),
                        "shares": shares,
                    })

            elif signal == -1 and position > 0:
                # Sell
                proceeds = position * exec_price * (1 - self.commission)
                cash += proceeds
                trades.append({
                    "date": str(row.get("Date", i)),
                    "action": "SELL",
                    "price": round(exec_price, 2),
                    "shares": position,
                })
                position = 0

            equity.append(cash + position * price)

        return equity, trades
