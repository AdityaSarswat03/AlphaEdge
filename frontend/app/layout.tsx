"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import dynamic from "next/dynamic";
import Sidebar from "@/components/Sidebar";
import ToastProvider from "@/components/Toast";
import "./globals.css";

const MeshBackground = dynamic(() => import("@/components/MeshBackground"), { ssr: false });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const cursorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (cursorRef.current) {
        cursorRef.current.style.left = e.clientX + "px";
        cursorRef.current.style.top = e.clientY + "px";
      }
    };
    window.addEventListener("mousemove", move);
    return () => window.removeEventListener("mousemove", move);
  }, []);

  const sidebarWidth = collapsed ? 72 : 240;

  return (
    <html lang="en">
      <head>
        <title>AlphaEdge — AI Stock Prediction</title>
        <meta name="description" content="Advanced AI-powered stock market prediction platform with ensemble ML models." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body style={{ background: "#0a0a0f" }}>
        {/* Cursor glow */}
        <div id="cursor-glow" ref={cursorRef} />

        {/* Background */}
        <MeshBackground />

        {/* Sidebar */}
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

        {/* Main */}
        <motion.main
          animate={{ paddingLeft: sidebarWidth }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          style={{ minHeight: "100vh", position: "relative", zIndex: 10 }}
        >
          <div style={{ padding: "32px" }}>
            {children}
          </div>
        </motion.main>

        {/* Toasts */}
        <ToastProvider />
      </body>
    </html>
  );
}
