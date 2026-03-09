"use client";
import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, BarChart3,
  MessageSquare, PieChart, ChevronLeft, Zap
} from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/predictions", label: "Predictions", icon: TrendingUp },
  { href: "/backtesting", label: "Backtesting", icon: BarChart3 },
  { href: "/sentiment", label: "Sentiment", icon: MessageSquare },
  { href: "/analytics", label: "Analytics", icon: PieChart },
];

export default function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const path = usePathname();

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="fixed left-0 top-0 h-full z-40 flex flex-col"
      style={{
        background: "rgba(10,10,20,0.7)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderRight: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 p-5 mb-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "linear-gradient(135deg, #00f0ff, #8b5cf6)" }}>
          <Zap size={16} color="#000" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}
              className="font-bold text-lg tracking-tight"
              style={{ color: "#00f0ff", whiteSpace: "nowrap" }}
            >
              AlphaEdge
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 mt-4" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href;
          return (
            <Link key={href} href={href}>
              <motion.div
                whileHover={{ x: 2 }}
                className="flex items-center gap-3 px-3 rounded-xl cursor-pointer transition-all"
                style={{ padding: "14px 12px" ,
                  background: active ? "rgba(0,240,255,0.1)" : "transparent",
                  borderLeft: active ? "2px solid #00f0ff" : "2px solid transparent",
                  color: active ? "#00f0ff" : "#9ca3af",
                }}
              >
                <Icon size={20} className="flex-shrink-0" />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="text-sm font-medium whitespace-nowrap"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Toggle */}
      <button
        onClick={onToggle}
        className="m-4 p-2 rounded-lg flex items-center justify-center transition-colors"
        style={{ background: "rgba(255,255,255,0.05)", color: "#6b7280" }}
      >
        <motion.div animate={{ rotate: collapsed ? 180 : 0 }} transition={{ duration: 0.3 }}>
          <ChevronLeft size={18} />
        </motion.div>
      </button>
    </motion.aside>
  );
}
