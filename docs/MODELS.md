# AlphaEdge Model Documentation

## Architecture Overview

AlphaEdge uses a **weighted ensemble** of three complementary model families:

| Model | Weight | Strength |
|-------|--------|----------|
| XGBoost | 45% | Tabular feature interactions, fast inference |
| LSTM | 30% | Sequential dependencies, trend memory |
| Transformer | 25% | Long-range attention, complex patterns |

---

## XGBoost

- **Type:** Gradient-boosted decision trees (XGBRegressor)
- **Features:** All engineered features (technical indicators, patterns, price/volume/momentum/volatility/time)
- **Scaling:** StandardScaler on input features
- **Hyper-parameters:**
  - `n_estimators`: 300
  - `max_depth`: 6
  - `learning_rate`: 0.01
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8

## LSTM

- **Type:** PyTorch 2-layer LSTM with dropout
- **Input:** Sliding windows of `sequence_length=20` time steps
- **Scaling:** MinMaxScaler [0, 1]
- **Architecture:** Input → LSTM(64, 2 layers, dropout=0.2) → Linear → 1 output
- **Training:** MSE loss, Adam optimizer, lr=0.001

## Transformer

- **Type:** Custom encoder-only Transformer with positional encoding
- **Architecture:** PosEncoding → 2× TransformerEncoderLayer(d=64, heads=4) → mean pool → Linear
- **Scaling:** MinMaxScaler [0, 1]
- **Training:** MSE loss, Adam optimizer, lr=0.0005

---

## Ensemble Strategy

Final prediction is a weighted average:

$$\hat{y} = 0.45 \cdot \hat{y}_{xgb} + 0.30 \cdot \hat{y}_{lstm} + 0.25 \cdot \hat{y}_{tfm}$$

Confidence is calculated from prediction agreement and individual model certainty.

---

## Feature Engineering

25+ technical indicators computed via the `ta` library:

- **Trend:** SMA(20, 50), EMA(20), MACD, ADX, Ichimoku
- **Momentum:** RSI, Stochastic K/D, Williams %R, CCI
- **Volatility:** Bollinger Bands, ATR
- **Volume:** OBV, CMF, VWAP

Plus candlestick patterns: Doji, Hammer, Engulfing, Morning/Evening Star, etc.

---

## Explainability

SHAP TreeExplainer is used on the XGBoost model to compute feature importances, viewable in the Analytics dashboard page and via the `/analytics/{ticker}` API endpoint.
