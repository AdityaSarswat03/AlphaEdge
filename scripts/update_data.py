#!/usr/bin/env python3
"""
Update local data cache for all tracked tickers.

Usage:
    python scripts/update_data.py
"""
import argparse
import sys
import pathlib
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from alphaedge.config import settings
from alphaedge.logger import logger
from alphaedge.data.fetcher import DataFetcher
from alphaedge.data.processor import DataProcessor


def load_tickers(config_path: str = "config/tickers.yaml") -> list[str]:
    path = pathlib.Path(config_path)
    if path.exists():
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("tickers", [])
    return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]


def update(tickers: list[str], period: str = "1y", exchange: str = "nse") -> None:
    fetcher = DataFetcher()
    processor = DataProcessor()
    data_dir = pathlib.Path(settings.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        logger.info(f"Updating data for {ticker} …")
        try:
            raw = fetcher.fetch_stock_data(ticker, period=period, exchange=exchange)
            if raw is None or raw.empty:
                logger.warning(f"No data for {ticker}")
                continue

            processed = processor.process(raw)
            out = data_dir / f"{ticker}.csv"
            processed.to_csv(out)
            logger.info(f"  Saved {len(processed)} rows → {out}")
        except Exception as exc:
            logger.error(f"Failed for {ticker}: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Update data cache")
    parser.add_argument("--period", default="1y")
    parser.add_argument("--exchange", default="nse")
    args = parser.parse_args()

    tickers = load_tickers()
    logger.info(f"Updating {len(tickers)} tickers")
    update(tickers, args.period, args.exchange)
    logger.info("Data update complete.")


if __name__ == "__main__":
    main()
