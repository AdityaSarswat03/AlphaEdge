"""
SHAP-based model explainability.
"""

import numpy as np
from typing import Dict, Any
from alphaedge.logger import log


class ModelExplainer:
    """Explain predictions using SHAP values (XGBoost focus)."""

    def __init__(self):
        self._explainer = None

    def fit(self, model, X_background: np.ndarray) -> None:
        """
        Build a SHAP TreeExplainer from a trained XGBoost model.

        Args:
            model: Trained XGBRegressor instance.
            X_background: A sample of training data for the explainer.
        """
        try:
            import shap

            self._explainer = shap.TreeExplainer(model)
            log.info("SHAP explainer initialised")
        except ImportError:
            log.warning("shap not installed – explanations unavailable")

    def explain(self, X: np.ndarray, feature_names: list) -> Dict[str, Any]:
        """
        Compute SHAP values for *X*.

        Returns:
            Dict with shap_values (array), base_value, top_features.
        """
        if self._explainer is None:
            return {"error": "Explainer not initialised"}

        shap_values = self._explainer.shap_values(X)

        # Mean absolute importance across the batch
        mean_abs = np.abs(shap_values).mean(axis=0)
        top_idx = np.argsort(mean_abs)[::-1][:10]
        top_features = [
            {"feature": feature_names[i], "importance": float(mean_abs[i])} for i in top_idx
        ]

        return {
            "shap_values": shap_values.tolist(),
            "base_value": float(self._explainer.expected_value),
            "top_features": top_features,
        }
