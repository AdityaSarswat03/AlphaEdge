"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import { TrendingUp, TrendingDown, Activity, Globe, BarChart2, Zap, Sparkles, ArrowRight } from "lucide-react";
import CountUp from "@/components/CountUp";
import { alphaApi, PredictionResponse } from "@/lib/api";
import { toast } from "@/components/Toast";
import Link from "next/link";

const GlobeScene = dynamic(() => import("@/components/GlobeScene"), { ssr: false });

const TICKER_MOCK = [
  { symbol: "RELIANCE", price: 2923.45, change: +1.23 }, { symbol: "TCS", price: 3867.10, change: -0.45 },
  { symbol: "HDFCBANK", price: 1654.80, change: +0.88 }, { symbol: "INFY", price: 1423.55, change: +2.11 },
  { symbol: "ICICIBANK", price: 1089.30, change: -0.22 }, { symbol: "SBIN", price: 782.60, change: +1.67 },
  { symbol: "HINDUNILVR", price: 2567.90, change: -0.94 }, { symbol: "BHARTIARTL", price: 1789.20, change: +3.04 },
  { symbol: "WIPRO", price: 478.35, change: -1.12 }, { symbol: "KOTAKBANK", price: 1923.70, change: +0.55 },
  { symbol: "TATAMOTORS", price: 942.15, change: +4.32 }, { symbol: "ONGC", price: 267.80, change: -0.67 },
];

const STATS = [
  { label: "Markets Monitored", value: 47, suffix: "", icon: Globe, color: "#00f0ff", desc: "Global exchanges tracked" },
  { label: "Predictions Today", value: 1284, suffix: "", icon: Zap, color: "#8b5cf6", desc: "AI signals generated" },
  { label: "Avg Confidence", value: 84.7, suffix: "%", icon: Activity, color: "#00ff88", desc: "Multi-model consensus" },
  { label: "Active Signals", value: 23, suffix: "", icon: BarChart2, color: "#ff8800", desc: "Actionable right now" },
];

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } } };

function TickerTape() {
  const items = [...TICKER_MOCK, ...TICKER_MOCK, ...TICKER_MOCK];
  return (
    <div className="overflow-hidden py-4 mb-8 separator">
      <div className="ticker-track flex gap-10 whitespace-nowrap" style={{ width: "max-content" }}>
        {items.map((t, i) => (
          <span key={i} className="flex items-center gap-2.5 text-sm">
            <span className="font-semibold text-white">{t.symbol}</span>
            <span className="mono text-xs" style={{ color: "var(--text-secondary)" }}>₹{t.price.toLocaleString("en-IN")}</span>
            <span className="mono text-xs font-semibold flex items-center gap-0.5"
              style={{ color: t.change >= 0 ? "#00ff88" : "#ff4466" }}>
              {t.change >= 0 ? "▲" : "▼"} {Math.abs(t.change).toFixed(2)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

function TopPickCard({ pick, index }: { pick: PredictionResponse; index: number }) {
  const isUp = pick.direction === "UP";
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="glass p-5 cursor-pointer relative overflow-hidden group"
    >
      {/* Top glow accent */}
      <div className="absolute top-0 left-0 right-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ background: isUp ? "linear-gradient(90deg, transparent, #00ff88, transparent)" : "linear-gradient(90deg, transparent, #ff4466, transparent)" }} />

      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="font-bold text-base">{pick.ticker}</span>
          {pick.confidence && (
            <div className="text-[10px] mono mt-0.5" style={{ color: "var(--text-muted)" }}>
              {(pick.confidence * 100).toFixed(0)}% confidence
            </div>
          )}
        </div>
        <span className={`text-[11px] px-2.5 py-1 rounded-lg font-bold ${isUp ? "badge-up" : "badge-down"}`}>
          {isUp ? "▲ BULL" : "▼ BEAR"}
        </span>
      </div>

      <div className="mono text-2xl font-bold mb-1" style={{ color: isUp ? "#00ff88" : "#ff4466" }}>
        ₹{pick.predicted_price.toFixed(2)}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          From ₹{pick.current_price.toFixed(2)}
        </span>
        <span className="mono text-xs font-bold" style={{ color: isUp ? "#00ff88" : "#ff4466" }}>
          {isUp ? "+" : ""}{Math.abs(pick.change_percent).toFixed(2)}%
        </span>
      </div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const [picks, setPicks] = useState<PredictionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    alphaApi.topPicks(8)
      .then(setPicks)
      .catch(() => toast("Could not load top picks — API may be offline", "error"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
      {/* Hero */}
      <div className="mb-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
          <div className="section-label mb-3">COMMAND CENTER</div>
          <h1 className="text-5xl font-black gradient-text mb-2 leading-tight">Market Intelligence</h1>
          <p className="text-sm max-w-lg" style={{ color: "var(--text-secondary)" }}>
            AI-powered ensemble predictions · Real-time signals across {TICKER_MOCK.length}+ NSE stocks · XGBoost + LSTM + Transformer
          </p>
        </motion.div>
      </div>

      {/* Globe */}
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2, duration: 0.8 }}>
        <GlobeScene />
      </motion.div>

      {/* Ticker */}
      <TickerTape />

      {/* Stats */}
      <motion.div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10" variants={stagger} initial="hidden" animate="show">
        {STATS.map((s) => (
          <motion.div key={s.label} variants={fadeUp} className="glass p-5 group">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${s.color}15` }}>
                <s.icon size={16} style={{ color: s.color }} />
              </div>
              <span className="section-label" style={{ fontSize: 10 }}>{s.label}</span>
            </div>
            <div className="text-3xl font-black mono" style={{ color: s.color }}>
              <CountUp end={s.value} suffix={s.suffix} decimals={s.suffix === "%" ? 1 : 0} />
            </div>
            <div className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>{s.desc}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Top Picks */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="section-label mb-1">AI-POWERED PICKS</div>
          <h2 className="text-xl font-bold">Top Predictions</h2>
        </div>
        <Link href="/predictions">
          <span className="btn-ghost flex items-center gap-2 text-sm">
            View all <ArrowRight size={14} />
          </span>
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-36 rounded-2xl" />)}
        </div>
      ) : picks.length > 0 ? (
        <motion.div className="grid grid-cols-2 lg:grid-cols-4 gap-4" variants={stagger} initial="hidden" animate="show">
          {picks.map((p, i) => <TopPickCard key={p.ticker} pick={p} index={i} />)}
        </motion.div>
      ) : (
        <div className="glass p-10 text-center">
          <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: "rgba(0,240,255,0.08)" }}>
            <Sparkles size={24} style={{ color: "#00f0ff" }} />
          </div>
          <p className="font-semibold mb-1">API Server Offline</p>
          <p className="text-sm mb-3" style={{ color: "var(--text-muted)" }}>Start the backend to see live AI picks</p>
          <code className="text-xs mono px-3 py-2 rounded-lg inline-block" style={{ background: "rgba(0,240,255,0.06)", color: "#00f0ff" }}>
            uvicorn alphaedge.api.main:app --reload
          </code>
        </div>
      )}
    </motion.div>
  );
}
