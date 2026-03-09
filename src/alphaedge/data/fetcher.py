"""
Data fetching from multiple sources (yfinance, news APIs).
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from alphaedge.logger import log


class DataFetcher:
    """Fetch stock data from various sources."""

    # ── Historical OHLCV ─────────────────────────────────────────
    def fetch_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        market: str = "NSE",
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.

        Args:
            ticker:     Stock ticker symbol (e.g. "RELIANCE").
            start_date: Start date  YYYY-MM-DD.
            end_date:   End date    YYYY-MM-DD.
            market:     Market suffix – NSE or BSE.

        Returns:
            DataFrame with OHLCV data + Symbol column.
        """
        try:
            # Resolve market suffix for Indian exchanges
            if market == "NSE" and not ticker.endswith(".NS"):
                symbol = f"{ticker}.NS"
            elif market == "BSE" and not ticker.endswith(".BO"):
                symbol = f"{ticker}.BO"
            else:
                symbol = ticker

            log.info(f"Fetching data for {symbol}: {start_date} → {end_date}")

            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
            )

            if df.empty:
                log.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Flatten multi-level columns that yfinance sometimes returns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.reset_index(inplace=True)

            # Standardise column names
            col_map = {
                "Adj Close": "Adj_Close",
            }
            df.rename(columns=col_map, inplace=True)

            df["Symbol"] = ticker
            log.info(f"Fetched {len(df)} rows for {ticker}")
            return df

        except Exception as e:
            log.error(f"Failed to fetch data for {ticker}: {e}")
            return pd.DataFrame()

    # ── Batch fetch ──────────────────────────────────────────────
    def fetch_multiple(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        market: str = "NSE",
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers.

        Returns:
            Dict mapping ticker → DataFrame.
        """
        results: Dict[str, pd.DataFrame] = {}
        for t in tickers:
            df = self.fetch_stock_data(t, start_date, end_date, market)
            if not df.empty:
                results[t] = df
        return results

    # ── Fundamentals ─────────────────────────────────────────────
    def fetch_fundamentals(self, ticker: str, market: str = "NSE") -> Dict[str, Any]:
        """Fetch fundamental data for a ticker."""
        try:
            suffix = ".NS" if market == "NSE" else ".BO"
            stock = yf.Ticker(f"{ticker}{suffix}")
            info = stock.info
            return {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            log.error(f"Failed to fetch fundamentals for {ticker}: {e}")
            return {}

    # ── News sentiment ─────────────────────────────────────────────
    def fetch_news_sentiment(self, ticker: str, days: int = 7) -> pd.DataFrame:
        """
        Fetch news articles and compute sentiment scores.

        Uses NewsAPI (newsapi.org) when NEWS_API_KEY is configured.
        Returns a DataFrame with columns: date, headline, source, sentiment_score.
        Falls back to an empty DataFrame if the API key is missing or on error.
        """
        from alphaedge.config import settings

        if not settings.news_api_key:
            log.debug(f"NEWS_API_KEY not set — skipping news sentiment for {ticker}")
            return pd.DataFrame(columns=["date", "headline", "source", "sentiment_score"])

        try:
            from datetime import datetime, timedelta
            from alphaedge.data.sentiment import SentimentAnalyzer

            analyzer = SentimentAnalyzer()
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")

            import httpx
            # OWASP: Pass API key in header, NOT query params.
            # Query params leak in server logs, Referer headers, and proxy caches.
            resp = httpx.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": ticker,
                    "from": from_date,
                    "to": to_date,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 50,
                },
                headers={"X-Api-Key": settings.news_api_key},
                timeout=15,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])

            if not articles:
                log.info(f"No news articles found for {ticker}")
                return pd.DataFrame(columns=["date", "headline", "source", "sentiment_score"])

            rows = []
            for article in articles:
                headline = article.get("title", "")
                if not headline:
                    continue
                score = analyzer.analyze(headline)
                rows.append({
                    "date": article.get("publishedAt", "")[:10],
                    "headline": headline,
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "sentiment_score": score["compound"],
                })

            df = pd.DataFrame(rows)
            log.info(f"Fetched {len(df)} news articles with sentiment for {ticker}")
            return df

        except Exception as e:
            log.warning(f"News sentiment fetch failed for {ticker}: {e}")
            return pd.DataFrame(columns=["date", "headline", "source", "sentiment_score"])
