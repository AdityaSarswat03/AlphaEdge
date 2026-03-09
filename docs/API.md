# AlphaEdge API Reference

Base URL: `http://localhost:8000` (local) / `https://api.alphaedge.ai` (production via Cloudflare)

## Authentication

AlphaEdge uses **Clerk** for authentication. Include a Clerk-issued JWT in the `Authorization` header:

```
Authorization: Bearer <clerk-jwt-token>
```

Auth is **optional** in development (`ENABLE_CLERK_AUTH=false`) and **required** in production.

---

## Health

### `GET /`
Returns app info including auth and database status.

**Response:**
```json
{
  "message": "Welcome to AlphaEdge API",
  "version": "1.0.0",
  "docs": "/docs",
  "auth": "Clerk",
  "database": "Firebase Firestore",
  "dns": "Cloudflare (alphaedge.ai)"
}
```

### `GET /health`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "firebase": "connected",
  "auth": "clerk"
}
```

---

## Predictions

### `POST /api/v1/predict`
**Auth:** Optional (user_id logged if authenticated)

**Request:**
```json
{
  "ticker": "RELIANCE",
  "exchange": "nse",
  "horizon": 1
}
```
**Response:**
```json
{
  "ticker": "RELIANCE",
  "current_price": 2450.00,
  "predicted_price": 2478.50,
  "direction": "UP",
  "confidence": 72.5,
  "change_percent": 1.16
}
```

Predictions are automatically persisted to Firebase Firestore.

### `GET /api/v1/predict/{ticker}`
Quick prediction for a single ticker.

### `POST /api/v1/predict/batch`
```json
{
  "tickers": ["RELIANCE", "TCS", "INFY"],
  "exchange": "nse"
}
```

### `GET /api/v1/top-picks`
Returns Top 5 picks sorted by predicted upside.

---

## Backtesting

### `POST /api/v1/backtest`
```json
{
  "ticker": "RELIANCE",
  "strategy": "momentum",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000,
  "commission": 0.001
}
```
**Response:** Metrics (Sharpe, drawdown, return …), trade log, equity curve.

Results are persisted to Firebase.

### `GET /api/v1/strategies`
Lists available strategy names.

---

## Analytics

### `GET /api/v1/analytics/{ticker}`
Feature statistics and model info.

### `POST /api/v1/sentiment`
```json
{ "text": "Reliance shares surge on strong earnings!" }
```
**Response:**
```json
{
  "positive": 0.85,
  "negative": 0.05,
  "neutral": 0.10,
  "compound": 0.80
}
```
