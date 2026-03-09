"""
XGBoost regression model for stock-price prediction.
"""
import numpy as np
import pandas as pd
import joblib
from typing import Any, Dict, Optional
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from alphaedge.models.base import BaseModel
from alphaedge.logger import log


class XGBoostModel(BaseModel):
    """XGBoost gradient-boosted tree regressor."""

    name = "xgboost"

    def __init__(self, **kwargs):
        defaults = dict(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.01,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
        )
        defaults.update(kwargs)
        self.model = XGBRegressor(**defaults)
        self.scaler = StandardScaler()
        self.feature_cols: list = []

    # ── Train ────────────────────────────────────────────────────
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        X_scaled = self.scaler.fit_transform(X_train)
        fit_params: Dict[str, Any] = {"verbose": False}

        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            fit_params["eval_set"] = [(X_val_scaled, y_val)]

        self.model.fit(X_scaled, y_train, **fit_params)

        preds = self.model.predict(X_scaled)
        rmse = float(np.sqrt(np.mean((preds - y_train) ** 2)))
        log.info(f"XGBoost train RMSE: {rmse:.4f}")
        return {"train_rmse": rmse}

    # ── Predict ──────────────────────────────────────────────────
    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    # ── Persistence ──────────────────────────────────────────────
    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"model": self.model, "scaler": self.scaler, "features": self.feature_cols},
            path,
        )
        log.info(f"XGBoost saved → {path}")

    def load(self, path: str) -> None:
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_cols = data.get("features", [])
        log.info(f"XGBoost loaded ← {path}")

    # ── Feature importance ───────────────────────────────────────
    def feature_importance(self) -> pd.DataFrame:
        imp = self.model.feature_importances_
        names = self.feature_cols or [f"f{i}" for i in range(len(imp))]
        return (
            pd.DataFrame({"feature": names, "importance": imp})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )
