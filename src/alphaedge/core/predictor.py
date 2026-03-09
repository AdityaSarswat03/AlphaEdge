"""
Core AlphaEdge Predictor – the main entry-point class.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from alphaedge.config import settings
from alphaedge.logger import log
from alphaedge.data.fetcher import DataFetcher
from alphaedge.data.processor import DataProcessor
from alphaedge.features.engineer import FeatureEngineer
from alphaedge.models.ensemble import EnsembleModel


class AlphaEdge:
    """
    Main prediction interface.

    Usage::

        alpha = AlphaEdge()
        result = alpha.predict("RELIANCE")
        print(result)
    """

    def __init__(self, model_path: Optional[str] = None):
        self.fetcher = DataFetcher()
        self.processor = DataProcessor()
        self.engineer = FeatureEngineer()
        self.model = EnsembleModel()

        if model_path:
            self.model.load(model_path)
            log.info(f"Loaded pre-trained model from {model_path}")

        log.info("AlphaEdge predictor ready")

    # ── Single prediction ────────────────────────────────────────
    def predict(
        self,
        ticker: str,
        horizon: int = 1,
        include_confidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Predict stock price for *ticker*.

        Args:
            ticker: e.g. "RELIANCE", "TCS".
            horizon: Days ahead (1-5).
            include_confidence: Add confidence intervals.

        Returns:
            Dict with predicted_price, change_percent, direction, etc.
        """
        log.info(f"Predicting {ticker}  horizon={horizon}")

        # 1. Fetch data
        end = datetime.now()
        start = end - timedelta(days=730)  # ~2 years for good features
        raw = self.fetcher.fetch_stock_data(
            ticker,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        )
        if raw.empty:
            raise ValueError(f"No data available for {ticker}")

        # 2. Process
        data = self.processor.process(raw)

        # 3. Feature engineering
        features = self.engineer.transform(data)
        feature_cols = self.engineer.get_feature_columns()

        # Remove non-numeric
        feature_cols = [
            c
            for c in feature_cols
            if c in features.columns
            and features[c].dtype in ("float64", "float32", "int64", "int32")
        ]

        # Defense-in-depth: sanitise any residual inf/NaN in feature matrix
        features[feature_cols] = features[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

        # 4. If model not trained – do a quick on-the-fly fit
        if not self.model.is_trained:
            self._quick_train(features, feature_cols)

        # 5. Ensemble prediction
        pred = self.model.predict_with_context(features, feature_cols)

        result: Dict[str, Any] = {
            "ticker": ticker,
            "current_price": round(pred["current_price"], 2),
            "predicted_price": round(pred["price"], 2),
            "change_percent": round(pred["change_percent"], 2),
            "direction": pred["direction"],
            "timestamp": datetime.now().isoformat(),
            "model_version": self.model.version,
        }
        if include_confidence:
            result["confidence"] = round(pred["confidence"], 4)
            result["lower_bound"] = round(pred["lower_bound"], 2)
            result["upper_bound"] = round(pred["upper_bound"], 2)

        log.info(f"Prediction for {ticker}: ₹{result['predicted_price']}  ({result['direction']})")
        return result

    # ── Multiple tickers ─────────────────────────────────────────
    def predict_multiple(self, tickers: List[str], horizon: int = 1) -> pd.DataFrame:
        results = []
        for t in tickers:
            try:
                results.append(self.predict(t, horizon, include_confidence=True))
            except Exception as e:
                log.warning(f"Skipping {t}: {e}")
        return pd.DataFrame(results)

    # ── Top picks ────────────────────────────────────────────────
    def get_top_picks(
        self,
        tickers: List[str],
        top_n: int = 10,
        min_confidence: float = 0.6,
    ) -> pd.DataFrame:
        preds = self.predict_multiple(tickers)
        if preds.empty:
            return preds
        preds = preds[preds["confidence"] >= min_confidence]
        return preds.sort_values("change_percent", ascending=False).head(top_n)

    # ── Backtest shortcut ────────────────────────────────────────
    def backtest(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        initial_capital: float = None,
    ) -> Dict[str, Any]:
        from alphaedge.backtesting.engine import Backtester

        bt = Backtester(initial_capital=initial_capital or settings.initial_capital)
        return bt.run(ticker, start_date, end_date)

    # ── Quick on-the-fly training (XGBoost only for speed) ───────
    def _quick_train(self, features: pd.DataFrame, feature_cols: List[str]) -> None:
        """Train XGBoost on available data so predictions can work without pre-saved models."""
        log.info("No pre-trained model – running quick XGBoost fit …")
        df = features.dropna(subset=["Target"]).copy()
        if len(df) < 100:
            log.warning("Insufficient data for training")
            return

        X = df[feature_cols].values
        y = df["Target"].values

        split = int(len(X) * 0.8)
        X_train, y_train = X[:split], y[:split]
        X_val, y_val = X[split:], y[split:]

        # Only train XGBoost for speed; LSTM/Transformer need more data
        xgb = self.model.models["xgboost"]
        xgb.feature_cols = feature_cols
        xgb.train(X_train, y_train, X_val, y_val)
        self.model.is_trained = True

        # Set weights so only XGBoost contributes
        self.model.weights = {"xgboost": 1.0, "lstm": 0.0, "transformer": 0.0}
        log.info("Quick training complete (XGBoost only)")
