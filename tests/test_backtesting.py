"""
Tests for backtesting engine.
"""
import pytest
import pandas as pd
import numpy as np


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics."""

    def test_calculate_returns_dict(self):
        from alphaedge.backtesting.metrics import PerformanceMetrics

        returns = pd.Series(np.random.randn(252) * 0.01)
        metrics = PerformanceMetrics.calculate(returns)

        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics

    def test_positive_returns(self):
        from alphaedge.backtesting.metrics import PerformanceMetrics

        returns = pd.Series([0.01] * 252)
        metrics = PerformanceMetrics.calculate(returns)
        assert metrics["total_return"] > 0


class TestStrategies:
    """Tests for trading strategies."""

    def test_buy_and_hold(self, sample_ohlcv):
        from alphaedge.backtesting.strategy import BuyAndHoldStrategy

        strategy = BuyAndHoldStrategy()
        signals = strategy.generate_signals(sample_ohlcv)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_ohlcv)

    def test_rsi_strategy(self, sample_ohlcv):
        from alphaedge.backtesting.strategy import RSIStrategy

        strategy = RSIStrategy()
        signals = strategy.generate_signals(sample_ohlcv)

        assert isinstance(signals, pd.Series)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_momentum_strategy(self, sample_ohlcv):
        from alphaedge.backtesting.strategy import MomentumStrategy

        strategy = MomentumStrategy()
        signals = strategy.generate_signals(sample_ohlcv)

        assert isinstance(signals, pd.Series)

    def test_mean_reversion_strategy(self, sample_ohlcv):
        from alphaedge.backtesting.strategy import MeanReversionStrategy

        strategy = MeanReversionStrategy()
        signals = strategy.generate_signals(sample_ohlcv)

        assert isinstance(signals, pd.Series)


class TestBacktester:
    """Tests for the Backtester engine."""

    def test_run_returns_results(self, sample_ohlcv, monkeypatch):
        from alphaedge.backtesting.engine import Backtester

        # Monkey-patch fetcher to return our fixture data
        def fake_fetch(self, ticker, **kwargs):
            return sample_ohlcv

        from alphaedge.data import fetcher as fetcher_mod
        monkeypatch.setattr(fetcher_mod.DataFetcher, "fetch_stock_data", fake_fetch)

        bt = Backtester()
        results = bt.run(ticker="TEST", strategy_name="buy_and_hold")

        assert isinstance(results, dict)
        assert "metrics" in results
