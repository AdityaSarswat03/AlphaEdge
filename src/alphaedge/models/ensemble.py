"""
Ensemble Model – weighted combination of XGBoost, LSTM, and Transformer.
"""
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from pathlib import Path
from alphaedge.models.base import BaseModel
from alphaedge.models.xgboost_model import XGBoostModel
from alphaedge.models.lstm_model import LSTMModel
from alphaedge.models.transformer import TransformerModel
from alphaedge.logger import log


class EnsembleModel:
    """Weighted ensemble of multiple models."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.models: Dict[str, BaseModel] = {
            "xgboost": XGBoostModel(),
            "lstm": LSTMModel(),
            "transformer": TransformerModel(),
        }
        self.weights = weights or {
            "xgboost": 0.45,
            "lstm": 0.30,
            "transformer": 0.25,
        }
        self.version = "1.0.0"
        self.is_trained = False
        log.info("EnsembleModel initialised  weights=" + str(self.weights))

    # ── Train all ────────────────────────────────────────────────
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, Dict[str, Any]]:
        metrics: Dict[str, Dict[str, Any]] = {}
        for name, model in self.models.items():
            log.info(f"Training {name} …")
            m = model.train(X_train, y_train, X_val, y_val)
            metrics[name] = m
        self.is_trained = True
        return metrics

    # ── Predict (single row or batch) ────────────────────────────
    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Generate ensemble prediction.

        For XGBoost the full feature matrix is used; for sequence models
        (LSTM / Transformer) sliding windows are created internally.

        Returns a dict with price, confidence, direction, etc.
        """
        predictions: Dict[str, float] = {}

        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                # We take the *last* predicted value
                predictions[name] = float(pred[-1]) if len(pred) > 0 else float(pred)
            except Exception as e:
                log.warning(f"Model {name} prediction failed: {e}")

        if not predictions:
            raise ValueError("All models failed to produce predictions")

        # Weighted average
        total_weight = sum(self.weights.get(n, 0) for n in predictions)
        if total_weight == 0:
            total_weight = 1.0
        weighted_pred = sum(predictions[n] * self.weights.get(n, 0) for n in predictions) / total_weight

        # Confidence from inter-model agreement
        pred_vals = np.array(list(predictions.values()))
        mean_pred = np.mean(pred_vals)
        if mean_pred != 0:
            confidence = float(max(0.0, min(1.0, 1.0 - np.std(pred_vals) / abs(mean_pred))))
        else:
            confidence = 0.5

        return {
            "price": float(weighted_pred),
            "confidence": confidence,
            "lower_bound": float(weighted_pred * 0.97),
            "upper_bound": float(weighted_pred * 1.03),
            "model_predictions": predictions,
        }

    # ── Predict with context (used by AlphaEdge predictor) ───────
    def predict_with_context(self, features: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """
        Convenience wrapper that extracts current price, computes
        direction and change_percent on top of raw predict().
        """
        X = features[feature_cols].values
        result = self.predict(X)

        current_price = float(features["Close"].iloc[-1])
        predicted = result["price"]
        change_pct = ((predicted - current_price) / current_price) * 100

        result.update({
            "current_price": current_price,
            "change_percent": change_pct,
            "direction": "UP" if change_pct > 0 else "DOWN",
        })
        return result

    # ── Persistence ──────────────────────────────────────────────
    def save(self, directory: str) -> None:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            ext = ".pt" if name in ("lstm", "transformer") else ".pkl"
            model.save(str(d / f"{name}{ext}"))
        log.info(f"Ensemble saved → {directory}")

    def load(self, directory: str) -> None:
        d = Path(directory)
        for name, model in self.models.items():
            ext = ".pt" if name in ("lstm", "transformer") else ".pkl"
            fpath = d / f"{name}{ext}"
            if fpath.exists():
                model.load(str(fpath))
        self.is_trained = True
        log.info(f"Ensemble loaded ← {directory}")
