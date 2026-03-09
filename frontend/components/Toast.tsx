"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

type Listener = (toasts: Toast[]) => void;

let listeners: Listener[] = [];
let _toasts: Toast[] = [];

function notify(message: string, type: Toast["type"] = "info") {
  const id = Math.random().toString(36).slice(2);
  _toasts = [..._toasts, { id, message, type }];
  listeners.forEach((l) => l(_toasts));
  setTimeout(() => {
    _toasts = _toasts.filter((t) => t.id !== id);
    listeners.forEach((l) => l(_toasts));
  }, 4000);
}

export { notify as toast };

export default function ToastProvider() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler: Listener = (t) => setToasts([...t]);
    listeners.push(handler);
    return () => { listeners = listeners.filter((l) => l !== handler); };
  }, []);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, x: 60, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 60 }}
            className="glass px-4 py-3 flex items-center gap-3 min-w-[280px] pointer-events-auto"
            style={{
              borderColor:
                t.type === "success" ? "rgba(0,255,136,0.4)"
                : t.type === "error" ? "rgba(255,68,102,0.4)"
                : "rgba(0,240,255,0.4)",
            }}
          >
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{
              background: t.type === "success" ? "#00ff88" : t.type === "error" ? "#ff4466" : "#00f0ff"
            }} />
            <span className="text-sm flex-1">{t.message}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
