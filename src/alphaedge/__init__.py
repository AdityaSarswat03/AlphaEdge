"""
AlphaEdge - Advanced Stock Market Prediction Platform
=====================================================

A production-grade stock market prediction platform combining
multi-model ensemble (XGBoost, LSTM, Transformer), real-time
predictions, sentiment analysis, technical analysis, backtesting,
and an interactive dashboard.

Version: 1.0.0
Author: Aditya
"""

__version__ = "1.0.0"
__author__ = "Aditya"
__app_name__ = "AlphaEdge"

from alphaedge.core.predictor import AlphaEdge  # noqa: F401

__all__ = ["AlphaEdge"]
