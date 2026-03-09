"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import dynamic from "next/dynamic";
import { MessageSquare, Send, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { alphaApi } from "@/lib/api";
import { toast } from "@/components/Toast";

const SentimentSphere = dynamic(() => import("@/components/SentimentSphere"), { ssr: false });

interface SentimentResult { positive?: number; negative?: number; neutral?: number; compound?: number; text?: string; score?: number; label?: string; }

function ScoreBar({ value, color, label }: { value: number; color: string; label: string }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1.5">
        <span style={{ color: "var(--text-secondary)" }}>{label}</span>
        <span className="mono font-semibold" style={{ color }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <motion.div
          initial={{ width: 0 }} animate={{ width: `${Math.min(value * 100, 100)}%` }}
          transition={{ duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}80, ${color})` }}
        />
      </div>
    </div>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const icon = sentiment === "positive" ? ArrowUpRight : sentiment === "negative" ? ArrowDownRight : Minus;
  const Icon = icon;
  const cls = sentiment === "positive" ? "badge-up" : sentiment === "negative" ? "badge-down" : "badge-neutral";
  const lbl = sentiment === "positive" ? "Bullish" : sentiment === "negative" ? "Bearish" : "Neutral";
  return (
    <span className={`inline-flex items-center gap-1 ${cls}`}>
      <Icon size={12} /> {lbl}
    </span>
  );
}

export default function SentimentPage() {
  const [text, setText] = useState("");
  const [results, setResults] = useState<SentimentResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [aggregate, setAggregate] = useState<{ positive: number; negative: number; neutral: number; compound: number } | null>(null);

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const lines = text.split("\n").filter(l => l.trim());
      const data = await alphaApi.sentiment({ texts: lines.length > 1 ? lines : undefined, text: lines.length === 1 ? text : undefined });
      setResults(data);
      if (data.length > 0) {
        const avg = (key: string) =>
          data.reduce((s: number, r: Record<string, any>) => s + (typeof r[key] === "number" ? (r[key] as number) : 0), 0) / data.length;
        setAggregate({ positive: avg("positive"), negative: avg("negative"), neutral: avg("neutral"), compound: avg("compound") });
      }
      toast("Sentiment analysis complete!", "success");
    } catch (e: any) { toast(e.message || "Analysis failed", "error"); }
    finally { setLoading(false); }
  };

  const sentiment = !aggregate ? "neutral" : aggregate.compound > 0.1 ? "positive" : aggregate.compound < -0.1 ? "negative" : "neutral";
  const intensity = aggregate ? Math.min(Math.abs(aggregate.compound) + 0.3, 1) : 0.3;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className="mb-8">
        <div className="section-label mb-2">NLP ENGINE</div>
        <h1 className="text-4xl font-black mb-2 gradient-text-warm">Sentiment Analyzer</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>Financial NLP · VADER + domain-tuned · One headline or hundreds</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {/* Input */}
          <div className="glass p-6">
            <span className="section-label text-[10px] block mb-3">Headlines / Financial Text</span>
            <textarea
              className="input-glass resize-none mb-4"
              rows={7}
              placeholder={`Reliance Industries Q3 profits surge 23%\nRBI holds rates steady amid inflation concerns\nTCS wins $500M deal with European bank\nAdani stocks fall on rising debt worries`}
              value={text}
              onChange={e => setText(e.target.value)}
              style={{ lineHeight: 1.6 }}
            />
            <div className="flex items-center justify-between">
              <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                {text.split("\n").filter(l => l.trim()).length} line{text.split("\n").filter(l => l.trim()).length !== 1 ? "s" : ""} · {text.length} chars
              </span>
              <button className="btn-primary flex items-center gap-2" onClick={analyze} disabled={loading || !text.trim()}>
                <Send size={14} /> {loading ? "Analyzing…" : "Analyze"}
              </button>
            </div>
          </div>

          {/* Aggregate */}
          <AnimatePresence>
            {aggregate && (
              <motion.div className="glass p-6" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex items-center justify-between mb-5">
                  <span className="font-semibold">Overall Sentiment</span>
                  <SentimentBadge sentiment={sentiment} />
                </div>
                <ScoreBar value={aggregate.positive} color="#00ff88" label="Positive" />
                <ScoreBar value={aggregate.negative} color="#ff4466" label="Negative" />
                <ScoreBar value={aggregate.neutral} color="#8b5cf6" label="Neutral" />
                <div className="separator mt-4 pt-3 flex items-center justify-between">
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Compound Score</span>
                  <span className="mono text-lg font-bold" style={{ color: aggregate.compound >= 0 ? "#00ff88" : "#ff4466" }}>
                    {aggregate.compound >= 0 ? "+" : ""}{aggregate.compound.toFixed(4)}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="space-y-6">
          {/* 3D Sphere */}
          <div className="glass p-4">
            <div className="text-center mb-2 section-label text-[10px]">SENTIMENT FIELD</div>
            <SentimentSphere sentiment={sentiment as any} intensity={intensity} />
            <div className="text-center mt-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
              {sentiment === "positive" ? "Particles expand ↑ (bullish energy)" : sentiment === "negative" ? "Particles contract ↓ (bearish pressure)" : "Particles orbit calmly (neutral)"}
            </div>
          </div>

          {/* Results */}
          {results.length > 0 && (
            <motion.div className="glass p-5" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <span className="font-semibold text-sm block mb-3">Per-Item Results ({results.length})</span>
              <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
                {results.map((r, i) => {
                  const lbl = r.label || (typeof r.compound === "number" ? (r.compound > 0.1 ? "positive" : r.compound < -0.1 ? "negative" : "neutral") : "neutral");
                  return (
                    <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                      className="flex items-center justify-between p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.025)" }}>
                      <span className="text-sm flex-1 mr-3 truncate" style={{ color: "var(--text-secondary)" }}>{r.text || `Item ${i + 1}`}</span>
                      <SentimentBadge sentiment={lbl} />
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
