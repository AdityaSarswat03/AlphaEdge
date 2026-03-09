"use client";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import { PieChart, Search, TrendingUp, TrendingDown, Building2 } from "lucide-react";
import { alphaApi } from "@/lib/api";
import { toast } from "@/components/Toast";

function IcosahedronViz({ volatility }: { volatility: number }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.x = clock.getElapsedTime() * 0.3;
    ref.current.rotation.y = clock.getElapsedTime() * 0.4;
  });
  const color = volatility > 30 ? "#ff4466" : volatility > 15 ? "#ff8800" : "#00ff88";
  return (
    <group>
      <mesh ref={ref}>
        <icosahedronGeometry args={[2, 3]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.35} roughness={0.3} metalness={0.7} />
      </mesh>
      <mesh ref={ref}>
        <icosahedronGeometry args={[2.05, 3]} />
        <meshStandardMaterial color={color} wireframe transparent opacity={0.1} />
      </mesh>
    </group>
  );
}

function IcosaScene({ volatility }: { volatility: number }) {
  return (
    <div style={{ width: "100%", height: "280px" }}>
      <Canvas camera={{ position: [0, 0, 6] }}>
        <ambientLight intensity={0.25} />
        <pointLight position={[5, 5, 5]} intensity={1.2} color="#00f0ff" />
        <pointLight position={[-5, -3, -3]} intensity={0.5} color="#8b5cf6" />
        <IcosahedronViz volatility={volatility} />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
        <EffectComposer>
          <Bloom luminanceThreshold={0.3} intensity={0.7} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}

function FundamentalCard({ label, value, color = "#e8eaf0" }: { label: string; value: any; color?: string }) {
  const display = typeof value === "number"
    ? value > 1e12 ? `₹${(value / 1e12).toFixed(2)}T`
    : value > 1e9 ? `₹${(value / 1e9).toFixed(2)}B`
    : value > 1e6 ? `₹${(value / 1e6).toFixed(2)}M`
    : value > 100 ? value.toFixed(0)
    : value.toFixed(2)
    : String(value ?? "—");
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass p-4 group">
      <div className="section-label text-[10px] mb-1.5">{label}</div>
      <div className="font-bold mono text-lg truncate" style={{ color }}>{display}</div>
    </motion.div>
  );
}

const LABEL_COLORS: Record<string, string> = {
  market_cap: "#00f0ff", pe_ratio: "#8b5cf6", pb_ratio: "#8b5cf6",
  dividend_yield: "#00ff88", eps: "#00ff88", revenue: "#00f0ff",
  fifty_two_week_high: "#00ff88", fifty_two_week_low: "#ff4466",
  beta: "#ff8800", debt_to_equity: "#ff4466", roe: "#00ff88", roa: "#00ff88",
  profit_margin: "#00ff88", operating_margin: "#00ff88",
};

export default function AnalyticsPage() {
  const [ticker, setTicker] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    try {
      const res = await alphaApi.analytics(ticker.toUpperCase());
      setData(res);
      toast(`Analytics loaded for ${ticker.toUpperCase()}`, "success");
    } catch (e: any) { toast(e.message || "Fetch failed", "error"); }
    finally { setLoading(false); }
  };

  const fundamentals = data?.fundamentals || {};
  const beta = fundamentals.beta || 1;
  const volatility = Math.abs(beta) * 20;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className="mb-8">
        <div className="section-label mb-2">FUNDAMENTAL ANALYSIS</div>
        <h1 className="text-4xl font-black mb-2" style={{ background: "linear-gradient(135deg, #ff8800, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Company Analytics
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>Key ratios · Valuation metrics · Risk indicators</p>
      </div>

      {/* Search */}
      <div className="glass p-5 mb-8 flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: "var(--text-muted)" }} />
          <input className="input-glass pl-11 mono" placeholder="RELIANCE" value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === "Enter" && load()} />
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={load} disabled={loading || !ticker}>
          <Building2 size={15} /> {loading ? "Loading…" : "Analyze"}
        </button>
      </div>

      <AnimatePresence mode="wait">
        {loading && (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-24 rounded-2xl" />)}
          </motion.div>
        )}

        {data && !loading && (
          <motion.div key="data" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 3D Vis */}
              <div className="glass p-5">
                <div className="text-center section-label text-[10px] mb-2">RISK PROFILE</div>
                <IcosaScene volatility={volatility} />
                <div className="text-center mt-2 space-y-1">
                  <div className="text-sm font-bold">{data.ticker || ticker}</div>
                  <div className="mono text-xs" style={{ color: "var(--text-muted)" }}>
                    Beta: <span style={{ color: beta > 1.2 ? "#ff4466" : beta < 0.8 ? "#00ff88" : "#ff8800" }}>{beta.toFixed(2)}</span>
                    <span className="mx-2">·</span>
                    Risk: <span style={{ color: volatility > 30 ? "#ff4466" : volatility > 15 ? "#ff8800" : "#00ff88" }}>
                      {volatility > 30 ? "High" : volatility > 15 ? "Medium" : "Low"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Fundamentals grid */}
              <div className="lg:col-span-2">
                <div className="section-label text-[10px] mb-3">KEY METRICS</div>
                {Object.keys(fundamentals).length === 0 ? (
                  <div className="glass p-10 text-center" style={{ color: "var(--text-muted)" }}>
                    No fundamentals available for this ticker
                  </div>
                ) : (
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(fundamentals).map(([k, v]) => (
                      <FundamentalCard
                        key={k}
                        label={k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                        value={v}
                        color={LABEL_COLORS[k] || "#00f0ff"}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {!data && !loading && (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="glass p-16 text-center">
              <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center float" style={{ background: "rgba(139,92,246,0.08)" }}>
                <PieChart size={28} style={{ color: "#8b5cf6" }} />
              </div>
              <p className="font-semibold mb-1">Enter a Ticker</p>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Search any NSE stock to view fundamentals and risk profile</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
