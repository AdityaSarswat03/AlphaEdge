"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import dynamic from "next/dynamic";
import { Search, TrendingUp, TrendingDown, Clock, Shield, Layers } from "lucide-react";
import CountUp from "@/components/CountUp";
import { alphaApi, PredictionResponse } from "@/lib/api";
import { toast } from "@/components/Toast";

const PriceBarsScene = dynamic(() => import("@/components/PriceBarsScene"), { ssr: false });

const NSE_STOCKS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "WIPRO", "TATAMOTORS", "ONGC", "NTPC", "POWERGRID", "LTIM", "SUNPHARMA", "MARUTI", "BAJFINANCE", "ADANIENT", "ULTRACEMCO"];
const HORIZONS = [1, 2, 3, 4, 5];

const fadeUp = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

export default function PredictionsPage() {
  const [ticker, setTicker] = useState("");
  const [horizon, setHorizon] = useState(1);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [history, setHistory] = useState<PredictionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleInput = (v: string) => {
    setTicker(v.toUpperCase());
    setSuggestions(v.length > 0 ? NSE_STOCKS.filter(s => s.startsWith(v.toUpperCase())).slice(0, 6) : []);
  };

  const predict = async (sym?: string) => {
    const t = sym || ticker;
    if (!t) return;
    setLoading(true); setSuggestions([]);
    try {
      const data = await alphaApi.predict(t, horizon);
      setResult(data);
      setHistory(prev => [data, ...prev.filter(p => p.ticker !== data.ticker || p.timestamp !== data.timestamp)].slice(0, 10));
      toast(`${t} prediction ready`, "success");
    } catch (e: any) { toast(e.message || "Prediction failed", "error"); }
    finally { setLoading(false); }
  };

  const isUp = result?.direction === "UP";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className="mb-8">
        <div className="section-label mb-2">MULTI-MODEL ENSEMBLE</div>
        <h1 className="text-4xl font-black gradient-text-green mb-2">Price Predictions</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>XGBoost + LSTM + Transformer · Confidence intervals · 1-5 day horizons</p>
      </div>

      {/* Search card */}
      <div className="glass p-6 mb-6">
        <div className="flex gap-3 mb-5">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: "var(--text-muted)" }} />
            <input className="input-glass pl-11 mono" placeholder="RELIANCE" value={ticker}
              onChange={e => handleInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && predict()} />
            {suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 glass-static rounded-xl overflow-hidden z-30 py-1" style={{ background: "rgba(14,14,22,0.95)" }}>
                {suggestions.map(s => (
                  <button key={s} onClick={() => { setTicker(s); setSuggestions([]); }}
                    className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 transition-colors mono flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" /> {s}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button className="btn-primary" onClick={() => predict()} disabled={loading || !ticker}>
            {loading ? "Analyzing…" : "Predict"}
          </button>
        </div>
        <div>
          <span className="section-label block mb-2">Horizon</span>
          <div className="seg-control" style={{ maxWidth: 300 }}>
            {HORIZONS.map(h => (
              <button key={h} className={`seg-btn ${horizon === h ? "active" : ""}`} onClick={() => setHorizon(h)}>{h} Day{h > 1 ? "s" : ""}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" className="glass p-8 space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {[240, 180, 60, 60].map((w, i) => <div key={i} className="skeleton rounded-xl" style={{ height: i === 0 ? 340 : 40, maxWidth: w === 240 ? "100%" : w }} />)}
              </motion.div>
            ) : result ? (
              <motion.div key={result.ticker + result.timestamp} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="glass p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h2 className="text-3xl font-black">{result.ticker}</h2>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{horizon}-day forecast · {result.model_version}</span>
                  </div>
                  <span className={`px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-1.5 ${isUp ? "badge-up" : "badge-down"}`}>
                    {isUp ? <TrendingUp size={15} /> : <TrendingDown size={15} />}
                    {isUp ? "BULLISH" : "BEARISH"}
                  </span>
                </div>

                {/* 3D Bars */}
                <PriceBarsScene currentPrice={result.current_price} predictedPrice={result.predicted_price} isUp={!!isUp} />

                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
                  {[
                    { label: "Current", value: result.current_price, color: "#00f0ff", prefix: "₹" },
                    { label: "Predicted", value: result.predicted_price, color: isUp ? "#00ff88" : "#ff4466", prefix: "₹" },
                    { label: "Change", value: result.change_percent, color: isUp ? "#00ff88" : "#ff4466", suffix: "%" },
                    { label: "Confidence", value: result.confidence ? result.confidence * 100 : 0, color: "#8b5cf6", suffix: "%" },
                  ].map(m => (
                    <div key={m.label} className="p-4 rounded-xl" style={{ background: "rgba(255,255,255,0.025)" }}>
                      <div className="section-label text-[10px] mb-1">{m.label}</div>
                      <div className="mono text-xl font-bold" style={{ color: m.color }}>
                        {m.prefix || ""}<CountUp end={m.value} decimals={2} duration={1} />{m.suffix || ""}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Confidence interval */}
                {result.lower_bound && result.upper_bound && (
                  <div className="mt-4 p-4 rounded-xl flex items-center gap-3" style={{ background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.15)" }}>
                    <Shield size={16} style={{ color: "#8b5cf6" }} />
                    <div>
                      <span className="text-xs font-semibold" style={{ color: "#8b5cf6" }}>95% Confidence Interval</span>
                      <div className="mono text-sm mt-0.5">₹{result.lower_bound.toFixed(2)} — ₹{result.upper_bound.toFixed(2)}</div>
                    </div>
                  </div>
                )}

                <div className="mt-3 text-[11px]" style={{ color: "var(--text-muted)" }}>
                  {new Date(result.timestamp).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                </div>
              </motion.div>
            ) : (
              <div className="glass p-16 text-center">
                <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center float" style={{ background: "rgba(0,240,255,0.06)" }}>
                  <Layers size={28} style={{ color: "#00f0ff" }} />
                </div>
                <p className="font-semibold mb-1">Enter a Ticker Symbol</p>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>Search any NSE stock to get AI-powered predictions</p>
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* History */}
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={15} style={{ color: "#8b5cf6" }} />
            <span className="font-semibold text-sm">Recent Predictions</span>
          </div>
          {history.length === 0 ? (
            <p className="text-sm text-center py-10" style={{ color: "var(--text-muted)" }}>Predictions will appear here</p>
          ) : (
            <div className="space-y-2">
              {history.map((h, i) => {
                const up = h.direction === "UP";
                return (
                  <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                    className="flex items-center justify-between p-3 rounded-xl cursor-pointer hover:bg-white/[0.03] transition-colors"
                    onClick={() => setResult(h)}>
                    <div>
                      <div className="font-semibold text-sm">{h.ticker}</div>
                      <div className="text-[11px] mono" style={{ color: "var(--text-muted)" }}>₹{h.predicted_price.toFixed(2)}</div>
                    </div>
                    <div className="text-right">
                      <span className="mono text-xs font-bold" style={{ color: up ? "#00ff88" : "#ff4466" }}>
                        {up ? "+" : ""}{h.change_percent.toFixed(2)}%
                      </span>
                      <div className="w-1.5 h-1.5 rounded-full ml-auto mt-1 glow-dot" style={{ color: up ? "#00ff88" : "#ff4466", background: up ? "#00ff88" : "#ff4466" }} />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
