import axios from "axios";

const api = axios.create({
  baseURL: typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    : "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Response interceptor for error normalisation
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err?.response?.data?.detail || err?.message || "Request failed";
    return Promise.reject(new Error(msg));
  }
);

// ── Typed API calls ─────────────────────────────────────────────

export interface PredictionResponse {
  ticker: string;
  current_price: number;
  predicted_price: number;
  change_percent: number;
  direction: "UP" | "DOWN";
  confidence?: number;
  lower_bound?: number;
  upper_bound?: number;
  timestamp: string;
  model_version: string;
}

export interface BacktestResponse {
  ticker: string;
  strategy: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
}

export interface SentimentResult {
  positive: number;
  negative: number;
  neutral: number;
  compound: number;
}

export const alphaApi = {
  predict: (ticker: string, horizon = 1) =>
    api.post<PredictionResponse>("/v1/predict", {
      ticker,
      horizon,
      include_confidence: true,
    }).then((r) => r.data),

  topPicks: (topN = 10) =>
    api.get<PredictionResponse[]>(`/v1/top-picks?top_n=${topN}&min_confidence=0.5`).then((r) => r.data),

  backtest: (params: {
    ticker: string;
    start_date: string;
    end_date: string;
    strategy: string;
    initial_capital: number;
  }) =>
    api.post<BacktestResponse>("/v1/backtest", params).then((r) => r.data),

  sentiment: (payload: { text?: string; texts?: string[] }) =>
    api.post<SentimentResult[]>("/v1/sentiment", payload).then((r) => r.data),

  analytics: (ticker: string) =>
    api.get(`/v1/analytics/${ticker}`).then((r) => r.data),
};

export default api;
