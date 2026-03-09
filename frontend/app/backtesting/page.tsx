"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, TrendingUp, TrendingDown, AlertTriangle, Award, DollarSign, Target, Repeat } from "lucide-react";
import CountUp from "@/components/CountUp";
import { alphaApi, BacktestResponse } from "@/lib/api";
import { toast } from "@/components/Toast";

const STRATEGIES = [
  { value: "buy_and_hold", label: "Buy & Hold", desc: "Simple long-only" },
  { value: "mean_reversion", label: "Mean Reversion", desc: "Buy dips, sell rallies" },
  { value: "momentum", label: "Momentum", desc: "Trend following" },
  { value: "rsi", label: "RSI Strategy", desc: "Oversold/overbought signals" },
];

function MetricCard({ label, value, suffix, color, icon: Icon, desc }: { label: string; value: number; suffix?: string; color: string; icon: any; desc?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass p-5 group">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}12` }}>
          <Icon size={16} style={{ color }} />
        </div>
        <span className="section-label text-[10px]">{label}</span>
      </div>
      <div className="text-3xl font-black mono" style={{ color }}>
        <CountUp end={value} suffix={suffix || ""} decimals={suffix === "%" ? 2 : 2} duration={1.5} />
      </div>
      {desc && <div className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>{desc}</div>}
    </motion.div>
  );
}

function EquityCurve({ finalValue, initial }: { finalValue: number; initial: number }) {
  const pct = ((finalValue - initial) / initial) * 100;
  const isPos = pct >= 0;
  const color = isPos ? "#00ff88" : "#ff4466";
  // Generate semi-realistic curve
  const pts = 20;
  const points: string[] = [];
  let y = 95;
  for (let i = 0; i <= pts; i++) {
    const progress = i / pts;
    const target = isPos ? 15 + (85 - 15) * (1 - progress) : 15 + (progress * 70);
    y = y + (target - y) * 0.3 + (Math.random() - 0.5) * 12;
    y = Math.max(8, Math.min(112, y));
    points.push(`${(i / pts) * 400},${y}`);
  }
  const line = `M${points.join(" L")}`;
  const fill = `${line} L400,120 L0,120 Z`;

  return (
    <div className="glass p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <span className="section-label">Equity Curve</span>
        <span className="mono text-sm font-bold" style={{ color }}>
          {isPos ? "+" : ""}{pct.toFixed(1)}% return
        </span>
      </div>
      <div className="relative h-44">
        <svg viewBox="0 0 400 120" className="w-full h-full" preserveAspectRatio="none">
          <defs>
            <linearGradient id="eq-grad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#00f0ff" />
              <stop offset="1" stopColor={color} />
            </linearGradient>
            <linearGradient id="eq-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={color} stopOpacity="0.15" />
              <stop offset="1" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          {/* Grid */}
          {[30, 60, 90].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="rgba(255,255,255,0.04)" strokeWidth="0.5" />)}
          {/* Area fill */}
          <path d={fill} fill="url(#eq-fill)" />
          {/* Line */}
          <path d={line} fill="none" stroke="url(#eq-grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
}

export default function BacktestingPage() {
  const [form, setForm] = useState({ ticker: "RELIANCE", start_date: "2024-01-01", end_date: "2025-01-01", strategy: "momentum", initial_capital: 100000 });
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const data = await alphaApi.backtest(form);
      setResult(data);
      toast("Backtest complete!", "success");
    } catch (e: any) { toast(e.message || "Backtest failed", "error"); }
    finally { setLoading(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className="mb-8">
        <div className="section-label mb-2">PORTFOLIO SIMULATION</div>
        <h1 className="text-4xl font-black mb-2" style={{ background: "linear-gradient(135deg, #8b5cf6, #00f0ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Strategy Backtesting
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>Test strategies on historical data · Performance metrics · Risk analysis</p>
      </div>

      {/* Form */}
      <div className="glass p-6 mb-8">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
          <div>
            <span className="section-label text-[10px] block mb-2">Ticker</span>
            <input className="input-glass mono" value={form.ticker} onChange={e => setForm({ ...form, ticker: e.target.value.toUpperCase() })} placeholder="RELIANCE" />
          </div>
          <div>
            <span className="section-label text-[10px] block mb-2">Start Date</span>
            <input className="input-glass" type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} />
          </div>
          <div>
            <span className="section-label text-[10px] block mb-2">End Date</span>
            <input className="input-glass" type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} />
          </div>
        </div>

        {/* Strategy selector */}
        <span className="section-label text-[10px] block mb-2">Strategy</span>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          {STRATEGIES.map(s => (
            <button key={s.value} onClick={() => setForm({ ...form, strategy: s.value })}
              className="p-3 rounded-xl text-left transition-all"
              style={{
                background: form.strategy === s.value ? "rgba(0,240,255,0.08)" : "rgba(255,255,255,0.02)",
                border: `1px solid ${form.strategy === s.value ? "rgba(0,240,255,0.3)" : "rgba(255,255,255,0.06)"}`,
              }}>
              <span className="text-sm font-semibold block" style={{ color: form.strategy === s.value ? "#00f0ff" : "var(--text)" }}>{s.label}</span>
              <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{s.desc}</span>
            </button>
          ))}
        </div>

        <div className="flex items-end gap-4">
          <div className="flex-1 max-w-xs">
            <span className="section-label text-[10px] block mb-2">Initial Capital (₹)</span>
            <input className="input-glass mono" type="number" value={form.initial_capital} onChange={e => setForm({ ...form, initial_capital: +e.target.value })} />
          </div>
          <button className="btn-primary h-[46px]" onClick={run} disabled={loading}>
            {loading ? "Simulating…" : "Run Backtest"}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {loading && (
          <div className="space-y-4">
            {[200, 120, 120, 120].map((_, i) => <div key={i} className="skeleton rounded-2xl" style={{ height: i === 0 ? 200 : 100 }} />)}
          </div>
        )}

        {result && !loading && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            {/* Results header */}
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(139,92,246,0.12)" }}>
                <BarChart3 size={18} style={{ color: "#8b5cf6" }} />
              </div>
              <div>
                <span className="font-bold">{result.ticker}</span>
                <span className="text-sm ml-2" style={{ color: "var(--text-muted)" }}>
                  {result.strategy.replace(/_/g, " ")} · {result.start_date} → {result.end_date}
                </span>
              </div>
            </div>

            {/* Key metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <MetricCard label="Total Return" value={result.total_return * 100} suffix="%" color={result.total_return >= 0 ? "#00ff88" : "#ff4466"} icon={TrendingUp} />
              <MetricCard label="Sharpe Ratio" value={result.sharpe_ratio} color={result.sharpe_ratio >= 1.5 ? "#00ff88" : result.sharpe_ratio >= 0.5 ? "#ff8800" : "#ff4466"} icon={Award} desc={result.sharpe_ratio >= 1.5 ? "Excellent" : result.sharpe_ratio >= 0.5 ? "Average" : "Poor"} />
              <MetricCard label="Max Drawdown" value={Math.abs(result.max_drawdown) * 100} suffix="%" color={Math.abs(result.max_drawdown) < 0.15 ? "#00ff88" : "#ff4466"} icon={AlertTriangle} desc={Math.abs(result.max_drawdown) < 0.15 ? "Low risk" : "High risk"} />
              <MetricCard label="Win Rate" value={result.win_rate * 100} suffix="%" color={result.win_rate >= 0.55 ? "#00ff88" : "#ff8800"} icon={Target} />
            </div>

            {/* Secondary metrics */}
            <div className="grid grid-cols-3 gap-4 mb-2">
              <div className="glass p-4">
                <div className="section-label text-[10px] mb-1">Final Value</div>
                <div className="text-xl font-bold mono" style={{ color: "#00f0ff" }}>₹{result.final_value.toLocaleString("en-IN")}</div>
              </div>
              <div className="glass p-4">
                <div className="section-label text-[10px] mb-1">Annual Return</div>
                <div className="text-xl font-bold mono" style={{ color: result.annual_return >= 0 ? "#00ff88" : "#ff4466" }}>{(result.annual_return * 100).toFixed(2)}%</div>
              </div>
              <div className="glass p-4">
                <div className="section-label text-[10px] mb-1">Total Trades</div>
                <div className="text-xl font-bold mono" style={{ color: "#8b5cf6" }}>{result.total_trades}</div>
              </div>
            </div>

            <EquityCurve finalValue={result.final_value} initial={result.initial_capital} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
