<div align="center">
  <img src="frontend/public/globe.svg" width="100" height="100" alt="AlphaEdge Logo" />
  <h1>AlphaEdge 📈</h1>
  <p><b>Your Personal AI Stock Market Analyst</b></p>
  <p>A beautifully designed, full-stack platform that uses Artificial Intelligence to predict stock prices, analyze market sentiment, and backtest trading strategies.</p>
</div>

---

## ✨ What is AlphaEdge?

AlphaEdge is not just another stock tracker. It actually tries to **predict the future** by looking at the past. Give it a stock ticker (like `RELIANCE` or `TCS`), and it will:
1. **Fetch** the last 2 years of market data.
2. **Calculate** 60+ complex technical indicators (like RSI, MACD, and Bollinger Bands).
3. **Run AI Models** (XGBoost, LSTM, and Transformer) on that data.
4. **Give you a prediction:** Where is the price going in the next few days, and how confident is the AI?

It also reads the news to gauge market mood (**Sentiment Analysis**) and lets you test if your trading ideas would have actually made money (**Backtesting**).

---

## 🚀 Key Features Explained Simply

*   🤖 **AI Price Predictions:** It uses an ensemble of 3 cutting-edge models. XGBoost is fast and runs instantly. The LSTM tracks patterns over time, and the Transformer pays attention to complex relationships. They vote together to give you the most accurate prediction possible.
*   📊 **Stunning Dashboard:** A premium, dark-mode, sci-fi themed interface built with Next.js and 3D graphics (React Three Fiber).
*   💬 **News Sentiment Analysis:** It reads financial headlines and uses an NLP (Natural Language Processing) engine to tell you if the news is Bullish (good) or Bearish (bad).
*   🎯 **Strategy Backtesting:** Want to know if "Buying when RSI is below 30" actually works? Test it against years of historical data in seconds.
*   🏢 **Company Analytics:** See the fundamental health of a company (P/E ratio, market cap, risk profile) visualised beautifully.

---

## 🏗️ How It Works Under the Hood

AlphaEdge is split into two halves that talk to each other:

1.  **The Frontend (User Interface):** Built with **Next.js 14**, React, and Tailwind CSS. This is the beautiful website you interact with. It runs on Port 3000.
2.  **The Backend (The Brain):** Built with **Python & FastAPI**. This does all the heavy lifting—fetching data from Yahoo Finance, running the PyTorch AI models, and talking to the database. It runs on Port 8000.

**The Tech Stack:**
*   **AI:** PyTorch, XGBoost, Scikit-Learn
*   **Backend:** FastAPI, Python 3.10+, Pandas, Numpy
*   **Web App:** Next.js 14, TypeScript, Tailwind CSS, Framer Motion
*   **Infrastructure:** Docker, Firebase (Database), Clerk (Authentication), Redis (Caching)

---

## 🛠️ Step-by-Step Installation Guide

Want to run this on your own machine? It's easy.

### Prerequisites
Make sure you have installed:
- **Python 3.10** or higher
- **Node.js 18** or higher

### Step 1: Clone the Code
```bash
git clone https://github.com/adityas/AlphaEdge.git
cd AlphaEdge
```

### Step 2: Setup the Python Backend
This installs the AI libraries and starts the API server.
```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # (On Windows use: .venv\Scripts\activate)

# Install requirements
pip install -e ".[dev]"

# Start the backend server!
python3 -m uvicorn alphaedge.api.main:app --reload
# It is now running at http://localhost:8000
```

### Step 3: Setup the Web Frontend
Open a **new terminal window**, and run:
```bash
cd frontend
npm install
npm run dev
# It is now running at http://localhost:3000
```

🎉 **You're done!** Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧠 Training the Full AI Intellect

By default, out of the box, AlphaEdge uses **XGBoost** to train instantly on-the-fly when you ask for a prediction. It takes 2 seconds, but it's only using 1 out of 3 models.

To unlock maximum accuracy, you need to pre-train the **LSTM** and **Transformer** neural networks on your favourite stocks.

Open a terminal in the AlphaEdge folder and run:
```bash
python3 scripts/train_models.py --tickers RELIANCE TCS INFY HDFCBANK --period 2y
```
*(Grab a coffee ☕ — neural networks take 15-30 minutes to learn 2 years of daily data!)*

Once it finishes, the model weights are saved permanently. Next time you use the app, it will combine all 3 models for a super-powered prediction!

---

## 🔐 Configuration & Security (For Production)

If you decide to put this on the real internet, AlphaEdge is fully OWASP-hardened.
1.  Copy `.env.example` and rename it to `.env`.
2.  **Firebase:** Setup a free Firebase project and put your `firebase-service-account.json` in the `config/` folder. This saves your backtest history.
3.  **Clerk:** Setup a free Clerk account and put your API keys in the `.env` to enable user logins.
4.  The app has built-in **Rate Limiting** (anti-spam) and **Security Headers**.

---

## 📁 Repository Map

If you want to explore the code, here's where everything lives:

```text
AlphaEdge/
├── frontend/                   # UI Code (Next.js, React, Tailwind)
│   ├── app/                    #  -> Dashboard, Predictions, Backtesting
│   └── components/             #  -> 3D Globes, Interactive Charts
├── src/alphaedge/              # Backend Code (Python, FastAPI)
│   ├── api/                    #  -> Web endpoints (routes, schemas)
│   ├── models/                 #  -> AI Architectures (XGBoost, LSTM, Transformer)
│   ├── features/               #  -> Technical Indicators & Candlesticks
│   ├── data/                   #  -> Yahoo Finance fetcher & NLP Sentiment
│   └── backtesting/            #  -> Trading Strategy simulators
├── scripts/                    # Tools to train the AI models
├── config/                     # Settings and Firebase credentials
└── docs/                       # Advanced technical documentation
```

<div align="center">
  <i>Built for the future of finance.</i>
</div>
