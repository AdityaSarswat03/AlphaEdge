#!/usr/bin/env python3
"""
Train all AlphaEdge models on configured tickers.

Usage:
    python scripts/train_models.py --tickers RELIANCE TCS INFY --period 2y
"""

import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from alphaedge.config import settings
from alphaedge.logger import logger
from alphaedge.data.fetcher import DataFetcher
from alphaedge.data.processor import DataProcessor
from alphaedge.features.engineer import FeatureEngineer
from alphaedge.models.xgboost_model import XGBoostModel
from alphaedge.models.lstm_model import LSTMModel
from alphaedge.models.transformer import TransformerModel


def train(tickers: list[str], period: str = "2y", exchange: str = "nse") -> None:
    fetcher = DataFetcher()
    processor = DataProcessor()
    engineer = FeatureEngineer()

    model_dir = pathlib.Path(settings.MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        logger.info(f"Training models for {ticker} …")
        try:
            raw = fetcher.fetch_stock_data(ticker, period=period, exchange=exchange)
            if raw is None or raw.empty:
                logger.warning(f"No data for {ticker}, skipping.")
                continue

            processed = processor.process(raw)
            featured = engineer.transform(processed)

            feature_cols = [
                c
                for c in featured.columns
                if c not in ("Open", "High", "Low", "Close", "Volume", "target")
            ]
            X = featured[feature_cols].dropna()
            y = featured.loc[X.index, "target"]
            mask = y.notna()
            X, y = X[mask], y[mask]

            if len(X) < 50:
                logger.warning(f"Insufficient data for {ticker} ({len(X)} rows), skipping.")
                continue

            # XGBoost
            xgb = XGBoostModel()
            xgb.train(X, y)
            xgb.save(str(model_dir / f"{ticker}_xgboost.json"))
            logger.info("  ✓ XGBoost saved")

            # LSTM
            lstm = LSTMModel(epochs=20)
            lstm.train(X, y)
            lstm.save(str(model_dir / f"{ticker}_lstm.pt"))
            logger.info("  ✓ LSTM saved")

            # Transformer
            tfm = TransformerModel(epochs=20)
            tfm.train(X, y)
            tfm.save(str(model_dir / f"{ticker}_transformer.pt"))
            logger.info("  ✓ Transformer saved")

            logger.success(f"All models trained for {ticker}")

        except Exception as exc:
            logger.error(f"Failed training {ticker}: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Train AlphaEdge models")
    parser.add_argument("--tickers", nargs="+", default=["RELIANCE", "TCS", "INFY", "HDFCBANK"])
    parser.add_argument("--period", default="2y")
    parser.add_argument("--exchange", default="nse")
    args = parser.parse_args()

    logger.info(f"Starting training for {len(args.tickers)} tickers")
    train(args.tickers, args.period, args.exchange)
    logger.info("Training complete.")


if __name__ == "__main__":
    main()
