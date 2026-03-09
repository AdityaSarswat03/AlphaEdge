"use client";
import { useEffect, useRef, useState } from "react";

interface Props { end: number; duration?: number; prefix?: string; suffix?: string; decimals?: number; }

export default function CountUp({ end, duration = 1.5, prefix = "", suffix = "", decimals = 2 }: Props) {
  const [value, setValue] = useState(0);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    startRef.current = null;
    const animate = (ts: number) => {
      if (!startRef.current) startRef.current = ts;
      const progress = Math.min((ts - startRef.current) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(end * eased);
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [end, duration]);

  return (
    <span className="mono">
      {prefix}{value.toFixed(decimals)}{suffix}
    </span>
  );
}
