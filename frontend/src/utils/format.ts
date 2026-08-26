import { useEffect, useState } from "react";

export function formatINR(value: number, decimals = 0): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatKg(value: number): string {
  return `${new Intl.NumberFormat("en-IN").format(value)} kg`;
}

export function formatTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export function relativeDay(iso: string): string {
  const target = new Date(iso);
  const today = new Date();
  const diff = Math.round(
    (new Date(target.toDateString()).getTime() -
      new Date(today.toDateString()).getTime()) /
      86400000,
  );
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  if (diff === -1) return "Yesterday";
  return target.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

/** Ticking countdown to a target ISO timestamp; updates every second. */
export function useCountdown(hoursRemaining: number): { h: number; m: number } {
  const [target] = useState(() => Date.now() + hoursRemaining * 3600_000);
  const [remaining, setRemaining] = useState(hoursRemaining * 3600);

  useEffect(() => {
    setRemaining(Math.max(0, target - Date.now()) / 1000);
    const timer = setInterval(() => {
      setRemaining(Math.max(0, target - Date.now()) / 1000);
    }, 30_000);
    return () => clearInterval(timer);
  }, [target]);

  const totalMinutes = Math.floor(remaining / 60);
  return { h: Math.floor(totalMinutes / 60), m: totalMinutes % 60 };
}
