#!/usr/bin/env python3
"""
Evaluate trained models on held-out test data.

Usage:
    python scripts/evaluate_models.py --ticker RELIANCE
"""
import argparse
import sys
import pathlib
import json
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from alphaedge.config import settings
from alphaedge.logger import logger
from alphaedge.data.fetcher import DataFetcher
from alphaedge.data.processor import DataProcessor
from alphaedge.features.engineer import FeatureEngineer
from alphaedge.models.xgboost_model import XGBoostModel
from alphaedge.models.lstm_model import LSTMModel
from alphaedge.models.transformer import TransformerModel
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate(ticker: str, period: str = "2y", exchange: str = "nse") -> dict:
    fetcher = DataFetcher()
    processor = DataProcessor()
    engineer = FeatureEngineer()

    raw = fetcher.fetch_stock_data(ticker, period=period, exchange=exchange)
    if raw is None or raw.empty:
        logger.error(f"No data for {ticker}")
        return {}

    processed = processor.process(raw)
    featured = engineer.transform(processed)

    feature_cols = [c for c in featured.columns
                    if c not in ("Open", "High", "Low", "Close", "Volume", "target")]
    X = featured[feature_cols].dropna()
    y = featured.loc[X.index, "target"]
    mask = y.notna()
    X, y = X[mask], y[mask]

    # Use last 20% as test
    split = int(len(X) * 0.8)
    X_test, y_test = X.iloc[split:], y.iloc[split:]

    results = {}
    model_dir = pathlib.Path(settings.MODEL_DIR)

    model_map = {
        "xgboost": (XGBoostModel, f"{ticker}_xgboost.json"),
        "lstm": (LSTMModel, f"{ticker}_lstm.pt"),
        "transformer": (TransformerModel, f"{ticker}_transformer.pt"),
    }

    for name, (cls, filename) in model_map.items():
        path = model_dir / filename
        if not path.exists():
            logger.warning(f"Model file not found: {path}")
            continue
        try:
            model = cls()
            model.load(str(path))
            preds = model.predict(X_test)
            if preds is None or len(preds) == 0:
                continue
            y_true = y_test.values[:len(preds)]
            results[name] = {
                "mae": float(mean_absolute_error(y_true, preds)),
                "rmse": float(np.sqrt(mean_squared_error(y_true, preds))),
                "r2": float(r2_score(y_true, preds)),
                "samples": len(preds),
            }
            logger.info(f"  {name}: MAE={results[name]['mae']:.2f}  RMSE={results[name]['rmse']:.2f}  R²={results[name]['r2']:.4f}")
        except Exception as exc:
            logger.error(f"  {name} evaluation failed: {exc}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate models")
    parser.add_argument("--ticker", default="RELIANCE")
    parser.add_argument("--period", default="2y")
    parser.add_argument("--exchange", default="nse")
    args = parser.parse_args()

    logger.info(f"Evaluating models for {args.ticker}")
    results = evaluate(args.ticker, args.period, args.exchange)

    if results:
        out_path = pathlib.Path(settings.MODEL_DIR) / f"{args.ticker}_evaluation.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved → {out_path}")
    else:
        logger.warning("No evaluation results produced.")


if __name__ == "__main__":
    main()
