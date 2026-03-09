# AlphaEdge 📈

**AI-Powered Stock Market Prediction Platform** — a multi-model ensemble (XGBoost + LSTM + Transformer) with a premium Next.js frontend, backtesting engine, sentiment analysis, and real-time analytics. Built for NSE/BSE stocks.

---

## What It Does

AlphaEdge fetches live stock data, engineers 60+ features, and runs an ensemble of 3 ML models to predict prices 1–5 days ahead. It also lets you backtest trading strategies, analyze financial sentiment, and explore company fundamentals — all through a polished, sci-fi-themed web interface.

```
┌──────────────────┐      ┌───────────────────┐      ┌─────────────────────┐
│   Next.js App    │─────▸│   FastAPI Backend  │─────▸│   ML Ensemble       │
│   (Port 3000)    │◂─────│   (Port 8000)     │◂─────│   XGBoost/LSTM/     │
│                  │      │                   │      │   Transformer       │
└──────────────────┘      └───────────────────┘      └─────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
               Firebase    Yahoo Finance    Redis
               (Database)  (Market Data)   (Cache)
```

---

## Tech Stack

### Backend

| Component | Technology |
|-----------|-----------|
| API Framework | **FastAPI** + Uvicorn |
| ML Models | **XGBoost**, **PyTorch LSTM**, **PyTorch Transformer** (weighted ensemble) |
| Feature Engineering | 60+ features — RSI, MACD, Bollinger Bands, ADX, candlestick patterns, momentum, volatility |
| Sentiment Analysis | VADER (financial NLP) |
| Database | **Firebase Firestore** (NoSQL, serverless) |
| Authentication | **Clerk** (JWT-based, social/email/passwordless) |
| Cache | **Redis** (optional, in-memory fallback) |
| DNS & CDN | **Cloudflare** (proxied DNS, SSL, DDoS protection) |
| Language | Python 3.10+ |

### Frontend

| Component | Technology |
|-----------|-----------|
| Framework | **Next.js 14+** (App Router, TypeScript) |
| Styling | **Tailwind CSS** |
| 3D Graphics | **React Three Fiber** + Drei + Postprocessing |
| Animations | **Framer Motion** |
| Icons | Lucide React |
| HTTP Client | Axios |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions (lint → test → build) |
| Process Manager | Gunicorn (production) |

---

## Features

### 🤖 AI Predictions
- **3-model ensemble** — XGBoost (gradient boosting), LSTM (sequence memory), Transformer (attention)
- Quick-train fallback when no pre-trained models exist (XGBoost on-the-fly)
- Confidence intervals and directional signals (bullish/bearish/neutral)
- Batch predictions and "top picks" endpoint

### 📊 Technical Analysis
- 25+ technical indicators (RSI, MACD, Bollinger Bands, ADX, Stochastic, CCI, OBV, Ichimoku, VWAP, etc.)
- 9 candlestick pattern detectors (Doji, Hammer, Engulfing, etc.)
- Custom price, volume, momentum, and volatility features

### 🎯 Backtesting Engine
- 4 strategies: Buy & Hold, Mean Reversion, Momentum, RSI
- Metrics: total return, Sharpe ratio, max drawdown, win rate, annual return
- Configurable date range and initial capital

### 💬 Sentiment Analysis
- Financial NLP using VADER with domain tuning
- Analyze single headlines or batch process hundreds
- Aggregate positive/negative/neutral/compound scores

### 📈 Company Analytics
- Fundamental data from Yahoo Finance (P/E, market cap, 52-week range, beta, etc.)
- Risk profiling and valuation metrics

### 🔒 Security (OWASP Hardened)
- Rate limiting — 60 req/min per IP, 180/min for authenticated users
- Strict input validation via Pydantic schemas (`extra="forbid"`, regex constraints)
- Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- API keys loaded from environment variables, never hard-coded
- Swagger/ReDoc disabled in production
- User ID validation to prevent path traversal/SSRF

### 🎨 Frontend Design
- Dark glassmorphic theme (`#0a0a0f` base, cyan `#00f0ff` / green `#00ff88` / purple `#8b5cf6` accents)
- 3D visualizations: spinning globe (Dashboard), sentiment particle sphere, risk icosahedron
- Animated ticker tape, staggered card animations, gradient text
- Collapsible sidebar, custom cursor glow, responsive layout

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Docker** (optional, for Redis)

### 1. Clone & Install Backend

```bash
git clone https://github.com/adityas/AlphaEdge.git && cd AlphaEdge
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Install Frontend

```bash
cd frontend
npm install
cd ..
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env — fill in your credentials (see Configuration section below)
```

### 4. Run

**Start the API server:**
```bash
python3 -m uvicorn alphaedge.api.main:app --reload
# → http://localhost:8000
```

**Start the frontend (in a separate terminal):**
```bash
cd frontend && npm run dev
# → http://localhost:3000
```

**Optional — start Redis for caching:**
```bash
docker run -d --name alphaedge-redis -p 6379:6379 redis:7-alpine
# Set ENABLE_REDIS_CACHE=true in .env
```

**Docker (full stack):**
```bash
docker-compose up -d
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the following:

### Firebase (required for data persistence)
1. Go to [Firebase Console](https://console.firebase.google.com/) → Create project
2. Enable **Firestore Database** (Native mode)
3. Generate a service-account key → save as `config/firebase-service-account.json`
4. Set `FIREBASE_PROJECT_ID` and `FIREBASE_CREDENTIALS_PATH` in `.env`

### Clerk (required for authentication)
1. Sign up at [clerk.com](https://clerk.com) → Create application
2. Copy `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, and `CLERK_DOMAIN` into `.env`
3. Set `ENABLE_CLERK_AUTH=true` for production

### Cloudflare (optional, for DNS management)
1. Add your domain to [Cloudflare](https://dash.cloudflare.com)
2. Create an API token (Zone:DNS:Edit)
3. Set `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`, and `DOMAIN_NAME` in `.env`

---

## Project Structure

```
AlphaEdge/
├── frontend/                   # Next.js 14 frontend
│   ├── app/                    # App Router pages
│   │   ├── page.tsx            #   Dashboard (3D globe, ticker tape, stats)
│   │   ├── predictions/        #   AI price predictions
│   │   ├── backtesting/        #   Strategy backtesting
│   │   ├── sentiment/          #   Sentiment analysis
│   │   └── analytics/          #   Company fundamentals
│   ├── components/             # Reusable UI components
│   │   ├── Sidebar.tsx         #   Collapsible nav sidebar
│   │   ├── GlassCard.tsx       #   Glassmorphism card
│   │   ├── MeshBackground.tsx  #   3D animated background
│   │   ├── SentimentSphere.tsx #   3D particle sphere
│   │   └── ...                 #   CountUp, Toast, StatCard, etc.
│   └── lib/api.ts              # Typed API client (Axios)
│
├── src/alphaedge/              # Core Python package
│   ├── api/                    # FastAPI app + routes
│   │   ├── main.py             #   App setup, middleware, CORS
│   │   ├── routes/             #   predictions, backtesting, analytics
│   │   ├── middleware.py       #   Rate limiting, security headers
│   │   └── schemas.py          #   Pydantic request/response models
│   ├── core/predictor.py       # Main prediction orchestrator
│   ├── models/                 # ML model implementations
│   │   ├── xgboost_model.py    #   XGBoost regressor
│   │   ├── lstm_model.py       #   PyTorch LSTM
│   │   ├── transformer_model.py#   PyTorch Transformer
│   │   └── ensemble.py         #   Weighted ensemble combiner
│   ├── features/               # Feature engineering
│   │   ├── technical.py        #   25+ technical indicators (via `ta`)
│   │   ├── patterns.py         #   Candlestick pattern detection
│   │   └── engineer.py         #   Full pipeline orchestrator
│   ├── data/                   # Data handling
│   │   ├── fetcher.py          #   Yahoo Finance data fetcher
│   │   ├── processor.py        #   OHLCV cleanup and validation
│   │   └── sentiment.py        #   VADER sentiment scorer
│   ├── backtesting/            # Backtesting engine
│   │   ├── engine.py           #   Core backtester
│   │   └── strategies.py       #   Strategy implementations
│   ├── auth/                   # Clerk JWT authentication
│   ├── analytics/              # SHAP explainer + Plotly visualiser
│   ├── utils/                  # Firebase DB, Cloudflare DNS, cache
│   └── config.py               # Centralised settings (Pydantic)
│
├── tests/                      # Pytest test suite
├── scripts/                    # Training & evaluation scripts
├── config/                     # YAML configs + Firebase credentials
├── docs/                       # API, deployment, model documentation
├── .github/workflows/          # GitHub Actions CI/CD
├── Dockerfile                  # Production container
├── docker-compose.yml          # Full-stack orchestration
├── gunicorn.conf.py            # Production server config
└── pyproject.toml              # Python package definition
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check (Firebase, version, environment) |
| POST | `/api/v1/predict` | Optional | Predict price for a single ticker |
| GET | `/api/v1/predict/{ticker}` | Optional | Quick single-ticker prediction |
| POST | `/api/v1/predict/batch` | Optional | Batch predictions for multiple tickers |
| GET | `/api/v1/top-picks` | Optional | AI-ranked top stock picks |
| POST | `/api/v1/backtest` | No | Run a strategy backtest |
| GET | `/api/v1/strategies` | No | List available strategies |
| GET | `/api/v1/analytics/{ticker}` | No | Company fundamentals |
| POST | `/api/v1/sentiment` | No | Analyze text sentiment |

Full API docs available at `http://localhost:8000/docs` (development only).

---

## Training Models

Train the full ensemble (XGBoost + LSTM + Transformer) for better predictions:

```bash
python scripts/train_models.py --tickers RELIANCE TCS INFY --period 2y
```

Without pre-trained models, the platform falls back to a quick on-the-fly XGBoost fit.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Deployment

1. **DNS** — Point `api.alphaedge.ai` and `app.alphaedge.ai` to your server via Cloudflare
2. **Auth** — Set `ENABLE_CLERK_AUTH=true` in production
3. **Security** — Change `SECRET_KEY` from the default (enforced in production)
4. **Database** — Firestore is serverless, no infra to manage
5. **CI/CD** — Push to `main` triggers GitHub Actions (lint → test → Docker build)

See `docs/DEPLOYMENT.md` for the full production checklist.

---

## License

MIT
