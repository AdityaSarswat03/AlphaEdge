"""
Tests for ML model classes.
"""

import numpy as np


class TestXGBoostModel:
    """Tests for XGBoostModel."""

    def test_train_and_predict(self, sample_featured, feature_columns):
        from alphaedge.models.xgboost_model import XGBoostModel

        model = XGBoostModel()
        X = sample_featured[feature_columns]
        y = sample_featured["target"]

        model.train(X, y)
        preds = model.predict(X)

        assert preds is not None
        assert len(preds) == len(X)
        assert all(np.isfinite(preds))

    def test_feature_importance(self, sample_featured, feature_columns):
        from alphaedge.models.xgboost_model import XGBoostModel

        model = XGBoostModel()
        X = sample_featured[feature_columns]
        y = sample_featured["target"]
        model.train(X, y)

        importance = model.feature_importance()
        assert isinstance(importance, dict)
        assert len(importance) > 0

    def test_save_and_load(self, sample_featured, feature_columns, tmp_path):
        from alphaedge.models.xgboost_model import XGBoostModel

        model = XGBoostModel()
        X = sample_featured[feature_columns]
        y = sample_featured["target"]
        model.train(X, y)

        path = str(tmp_path / "xgb_test.json")
        model.save(path)

        model2 = XGBoostModel()
        model2.load(path)
        preds = model2.predict(X)
        assert len(preds) == len(X)


class TestLSTMModel:
    """Tests for LSTMModel."""

    def test_train_and_predict(self, sample_featured, feature_columns):
        from alphaedge.models.lstm_model import LSTMModel

        model = LSTMModel(epochs=2, sequence_length=5)
        X = sample_featured[feature_columns]
        y = sample_featured["target"]

        model.train(X, y)
        preds = model.predict(X)

        assert preds is not None
        assert len(preds) > 0


class TestTransformerModel:
    """Tests for TransformerModel."""

    def test_train_and_predict(self, sample_featured, feature_columns):
        from alphaedge.models.transformer import TransformerModel

        model = TransformerModel(epochs=2, sequence_length=5)
        X = sample_featured[feature_columns]
        y = sample_featured["target"]

        model.train(X, y)
        preds = model.predict(X)

        assert preds is not None
        assert len(preds) > 0


class TestEnsembleModel:
    """Tests for EnsembleModel."""

    def test_predict_returns_dict(self, sample_featured, feature_columns):
        from alphaedge.models.ensemble import EnsembleModel

        ensemble = EnsembleModel()
        X = sample_featured[feature_columns]
        y = sample_featured["target"]

        # Train sub-models minimally
        ensemble.models["xgboost"].train(X, y)

        result = ensemble.predict(X)
        assert isinstance(result, dict)
        assert "predicted_price" in result or "price" in result
