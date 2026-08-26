import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/services/api";

const MANDI_COLORS = [
  "#4edea3",
  "#ffb95f",
  "#62dcad",
  "#7aa2ff",
  "#ff8fa3",
  "#c792ea",
];

export default function NetworkPage() {
  const { data: trucks } = useQuery({ queryKey: ["trucks"], queryFn: api.trucks });
  const { data: prices } = useQuery({ queryKey: ["prices"], queryFn: api.prices });
  const { data: priceHistory } = useQuery({
    queryKey: ["priceHistory"],
    queryFn: () => api.pricesHistory(7),
  });
  const { data: farmers } = useQuery({ queryKey: ["farmers"], queryFn: api.farmers });

  const [priceCrop, setPriceCrop] = useState<string | null>(null);
  const [priceView, setPriceView] = useState<"trend" | "today">("trend");
  const [truckSort, setTruckSort] = useState<"departure" | "capacity">("departure");
  const [showAllFarmers, setShowAllFarmers] = useState(false);

  const cropsWithPrices = useMemo(() => {
    const set = new Set((prices ?? []).map((p) => p.crop));
    return [...set];
  }, [prices]);

  const activeCrop = priceCrop ?? cropsWithPrices[0] ?? "";

  const mandiBars = useMemo(() => {
    const rows = (prices ?? []).filter((p) => p.crop === activeCrop);
    if (rows.length === 0) return [];
    const max = Math.max(...rows.map((r) => r.price_per_kg), 1);
    return rows
      .map((r) => ({
        label: r.mandi,
        price_per_kg: r.price_per_kg,
        heightPct: Math.round((r.price_per_kg / max) * 100),
        isMax: r.price_per_kg === max,
      }))
      .sort((a, b) => b.price_per_kg - a.price_per_kg);
  }, [prices, activeCrop]);

  const trend = useMemo(() => {
    const rows = (priceHistory ?? []).filter((p) => p.crop === activeCrop);
    if (rows.length === 0) return { series: [], mandis: [] as string[] };
    const mandis: string[] = [];
    const byDay = new Map<number, { ts: number; day: string } & Record<string, number | string>>();
    for (const r of rows) {
      if (!mandis.includes(r.mandi)) mandis.push(r.mandi);
      const d = new Date(r.recorded_at);
      const key = d.getTime();
      let entry = byDay.get(key);
      if (!entry) {
        entry = {
          ts: key,
          day: d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
        } as { ts: number; day: string } & Record<string, number | string>;
        byDay.set(key, entry);
      }
      entry[r.mandi] = r.price_per_kg;
    }
    return {
      series: [...byDay.values()].sort((a, b) => a.ts - b.ts),
      mandis,
    };
  }, [priceHistory, activeCrop]);

  const priceStats = useMemo(() => {
    const current = mandiBars[0] ?? null;
    let topGainer: { mandi: string; changePct: number } | null = null;
    for (const m of trend.mandis) {
      const values = trend.series
        .map((s) => s[m])
        .filter((v): v is number => typeof v === "number");
      if (values.length < 2) continue;
      const first = values[0];
      const last = values[values.length - 1];
      const changePct = ((last - first) / first) * 100;
      if (!topGainer || changePct > topGainer.changePct) {
        topGainer = { mandi: m, changePct };
      }
    }
    const avg =
      mandiBars.length > 0
        ? mandiBars.reduce((a, b) => a + b.price_per_kg, 0) / mandiBars.length
        : 0;
    return { best: current, topGainer, avg };
  }, [mandiBars, trend]);

  const avgPriceSpike = useMemo(() => {
    // Max deviation of any single mandi price above the crop average (demo data).
    let spike = 0;
    const byCrop = new Map<string, number[]>();
    for (const p of prices ?? []) {
      const list = byCrop.get(p.crop) ?? [];
      list.push(p.price_per_kg);
      byCrop.set(p.crop, list);
    }
    for (const list of byCrop.values()) {
      const avg = list.reduce((a, b) => a + b, 0) / list.length;
      for (const v of list) spike = Math.max(spike, v - avg);
    }
    return Math.round(spike);
  }, [prices]);

  // Seeded prices are demo data — keep their source label visible (project rule).
  const priceSourceLabel = prices?.[0]?.label ?? "Demo price · seeded prototype data";

  const activeTrucks = (trucks ?? []).length;
  const farmersOnline = (farmers ?? []).length;

  const truckRows = (trucks ?? [])
    .flatMap((t) =>
      t.routes.map((r) => ({
        truckId: t.id,
        registration: t.registration_number,
        capacityT: Math.round(t.available_capacity_kg / 1000),
        departureAt: new Date(r.departure_at).getTime(),
        departure: new Date(r.departure_at).toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
        origin: r.origin_name,
        destination: r.destination_mandi ?? r.return_destination_region,
        isReturn: r.return_available,
      })),
    )
    .sort((a, b) =>
      truckSort === "departure"
        ? a.departureAt - b.departureAt
        : b.capacityT - a.capacityT,
    );

  const farmerRows = (farmers ?? []).flatMap((f) =>
    f.listings.map((l) => ({ farmer: f, listing: l })),
  );
  const visibleFarmerRows = showAllFarmers ? farmerRows : farmerRows.slice(0, 6);

  return (
    <div className="w-full max-w-7xl mx-auto px-container-padding flex flex-col gap-8 pb-16">
      {/* Header */}
      <section className="flex flex-col space-y-4 pt-8">
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-primary shadow-[0_0_12px_rgba(78,222,163,0.8)] animate-pulse"></div>
          <h1 className="text-headline-lg font-headline-lg text-primary tracking-tight uppercase">
            Delhi NCR · live snapshot
          </h1>
        </div>
        <p className="text-body-md font-body-md text-on-surface-variant max-w-2xl">
          Aggregate data across major transit corridors and local mandi markets.
          Mandi prices and weather shown here are{" "}
          <span className="font-label-mono text-label-mono text-tertiary uppercase">
            demo data
          </span>
          .
        </p>
      </section>

      {/* Stat Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-card-gap">
        <div className="relative bg-surface-container/60 backdrop-blur-xl rounded-xl p-6 overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="flex justify-between items-start mb-6">
            <span className="text-on-surface-variant font-label-mono text-label-mono uppercase">
              Active Trucks
            </span>
            <span className="material-symbols-outlined text-primary">local_shipping</span>
          </div>
          <div className="text-display-hero font-display-hero text-primary">{activeTrucks}</div>
          <div className="flex items-center gap-2 mt-4 text-secondary text-sm">
            <span className="material-symbols-outlined text-[16px]">route</span>
            <span className="font-label-mono text-label-mono">Live network</span>
          </div>
        </div>

        <div className="relative bg-surface-container/60 backdrop-blur-xl rounded-xl p-6 overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-tertiary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="absolute top-0 right-0 w-24 h-24 bg-tertiary/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="flex justify-between items-start mb-6">
            <span className="text-on-surface-variant font-label-mono text-label-mono uppercase">
              Farmers Online
            </span>
            <span className="material-symbols-outlined text-tertiary">groups</span>
          </div>
          <div className="text-display-hero font-display-hero text-tertiary">
            {farmersOnline}
          </div>
          <div className="flex items-center gap-2 mt-4 text-tertiary text-sm">
            <span className="material-symbols-outlined text-[16px]">wifi</span>
            <span className="font-label-mono text-label-mono">Connected</span>
          </div>
        </div>

        <div className="relative bg-surface-container/60 backdrop-blur-xl rounded-xl p-6 overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-error/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="absolute top-0 right-0 w-24 h-24 bg-error/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="flex justify-between items-start mb-6">
            <span className="text-on-surface-variant font-label-mono text-label-mono uppercase">
              Avg Price Spike
            </span>
            <span className="material-symbols-outlined text-error">query_stats</span>
          </div>
          <div className="text-display-hero font-display-hero text-error">₹{avgPriceSpike}</div>
          <div className="flex items-center gap-2 mt-4 text-error text-sm">
            <span className="material-symbols-outlined text-[16px]">warning</span>
            <span className="font-label-mono text-label-mono">vs crop average · demo</span>
          </div>
        </div>

        <div className="relative bg-surface-container/60 backdrop-blur-xl rounded-xl p-6 overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="absolute top-0 right-0 w-24 h-24 bg-secondary/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div className="flex justify-between items-start mb-6">
            <span className="text-on-surface-variant font-label-mono text-label-mono uppercase">
              Return Trips
            </span>
            <span className="material-symbols-outlined text-secondary">eco</span>
          </div>
          <div className="text-display-hero font-display-hero text-secondary">
            {(trucks ?? []).reduce(
              (acc, t) => acc + t.routes.filter((r) => r.return_available).length,
              0,
            )}
          </div>
          <div className="flex items-center gap-2 mt-4 text-secondary text-sm">
            <span className="material-symbols-outlined text-[16px]">arrow_downward</span>
            <span className="font-label-mono text-label-mono">Empty-run savings</span>
          </div>
        </div>
      </section>

      {/* Price Chart + Trucks */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-card-gap">
        <div className="lg:col-span-2 bg-surface-container/80 backdrop-blur-md rounded-xl p-8 relative flex flex-col justify-between">
          <div className="absolute right-4 top-4 flex items-center gap-2">
            <span className="bg-tertiary/20 text-tertiary px-3 py-1 rounded font-label-mono text-label-mono shadow-[0_0_8px_rgba(255,185,95,0.3)]">
              DEMO DATA
            </span>
            <span className="hidden md:inline font-label-mono text-[10px] text-on-surface-variant/70 uppercase max-w-40 truncate">
              {priceSourceLabel}
            </span>
          </div>
          <div className="mb-10">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h2 className="text-headline-md font-headline-md text-on-surface mb-2 capitalize">
                  {activeCrop || "…"} Pricing Indices
                </h2>
                <p className="text-label-mono font-label-mono text-on-surface-variant uppercase">
                  ₹/kg across NCR Mandis · 7-day trend
                </p>
              </div>
              <div
                className="flex items-center rounded-full p-0.5 bg-surface-container-high/80"
                style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.15)" }}
              >
                {(["trend", "today"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setPriceView(mode)}
                    className={`px-3 py-1 rounded-full font-label-mono text-[10px] uppercase tracking-wider transition-colors ${
                      priceView === mode
                        ? "bg-primary/20 text-primary"
                        : "text-on-surface-variant hover:text-primary"
                    }`}
                  >
                    {mode === "trend" ? "7d Trend" : "Today"}
                  </button>
                ))}
              </div>
            </div>
            {cropsWithPrices.length > 1 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {cropsWithPrices.map((c) => (
                  <button
                    key={c}
                    onClick={() => setPriceCrop(c)}
                    className={`px-3 py-1 rounded-full border font-label-mono text-[10px] uppercase tracking-wider transition-colors ${
                      c === activeCrop
                        ? "bg-primary/20 border-primary text-primary"
                        : "border-outline-variant/40 text-on-surface-variant hover:border-primary/50"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
            {priceStats.best && (
              <div className="flex flex-wrap gap-2 mt-4">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/30 font-label-mono text-[10px] uppercase text-primary">
                  <span className="material-symbols-outlined text-[13px]">trending_up</span>
                  Best now · {priceStats.best.label} ₹{priceStats.best.price_per_kg.toFixed(0)}/kg
                </span>
                {priceStats.topGainer && (
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-label-mono text-[10px] uppercase border ${
                      priceStats.topGainer.changePct >= 0
                        ? "bg-secondary/10 border-secondary/30 text-secondary"
                        : "bg-error/10 border-error/30 text-error"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[13px]">query_stats</span>
                    Top mover 7d · {priceStats.topGainer.mandi}{" "}
                    {priceStats.topGainer.changePct >= 0 ? "+" : ""}
                    {priceStats.topGainer.changePct.toFixed(1)}%
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-high border border-outline-variant/30 font-label-mono text-[10px] uppercase text-on-surface-variant">
                  <span className="material-symbols-outlined text-[13px]">functions</span>
                  Avg ₹{priceStats.avg.toFixed(1)}/kg
                </span>
              </div>
            )}
          </div>
          {priceView === "trend" ? (
            <div className="relative h-64 w-full pb-2">
              {trend.series.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend.series} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                    <CartesianGrid stroke="rgba(134,148,138,0.12)" vertical={false} />
                    <XAxis
                      dataKey="day"
                      tick={{ fill: "#bbcabf", fontSize: 10 }}
                      stroke="rgba(134,148,138,0.25)"
                    />
                    <YAxis
                      tick={{ fill: "#bbcabf", fontSize: 10 }}
                      stroke="rgba(134,148,138,0.25)"
                      domain={["auto", "auto"]}
                      tickFormatter={(v: number) => `₹${v}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1c211e",
                        border: "1px solid rgba(110,231,183,0.2)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      labelStyle={{ color: "#dfe4df" }}
                      formatter={(value: number | string) => [`₹${Number(value).toFixed(2)}/kg`, ""]}
                    />
                    <Legend wrapperStyle={{ fontSize: 11 }} iconType="plainline" />
                    {trend.mandis.map((m, i) => (
                      <Line
                        key={m}
                        type="monotone"
                        dataKey={m}
                        stroke={MANDI_COLORS[i % MANDI_COLORS.length]}
                        strokeWidth={2}
                        dot={{ r: 2.5, strokeWidth: 0, fill: MANDI_COLORS[i % MANDI_COLORS.length] }}
                        activeDot={{ r: 4 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex items-center justify-center font-label-mono text-label-mono text-on-surface-variant animate-pulse">
                  LOADING PRICE HISTORY…
                </div>
              )}
            </div>
          ) : (
          <div className="relative h-64 w-full flex items-end justify-around gap-4 px-4 pb-8">
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="w-full h-px bg-outline/10"></div>
              ))}
            </div>
            {mandiBars.map((bar) => (
              <div
                key={bar.label}
                className="relative flex flex-col items-center group w-full max-w-[80px]"
                title={`${bar.label}: ₹${bar.price_per_kg.toFixed(0)}/kg · ${priceSourceLabel}`}
              >
                <div
                  className={`absolute -top-8 font-data-lg text-data-lg opacity-0 group-hover:opacity-100 transition-opacity ${
                    bar.isMax ? "text-primary" : "text-on-surface-variant"
                  }`}
                >
                  ₹{bar.price_per_kg.toFixed(0)}
                </div>
                <div
                  className={`w-full rounded-t-md transition-colors ${
                    bar.isMax
                      ? "bg-primary shadow-[0_0_15px_rgba(78,222,163,0.4)] hover:bg-primary-fixed"
                      : bar.heightPct > 85
                        ? "bg-error shadow-[0_0_15px_rgba(255,180,171,0.3)]"
                        : "bg-primary/50 hover:bg-primary"
                  }`}
                  style={{ height: `${Math.max(bar.heightPct, 6)}%` }}
                ></div>
                <div className="absolute -bottom-8 font-label-mono text-label-mono text-on-surface-variant truncate w-full text-center uppercase">
                  {bar.label}
                </div>
              </div>
            ))}
            {mandiBars.length === 0 && (
              <div className="w-full text-center font-label-mono text-label-mono text-on-surface-variant pb-16 animate-pulse">
                LOADING PRICE FEED…
              </div>
            )}
          </div>
          )}
        </div>

        {/* Available Trucks */}
        <div className="bg-surface-container/80 backdrop-blur-md rounded-xl p-6 flex flex-col h-[450px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-data-lg font-data-lg text-on-surface">Available Trucks</h3>
            <button
              className="flex items-center gap-1 text-on-surface-variant hover:text-primary transition-colors"
              onClick={() =>
                setTruckSort((s) => (s === "departure" ? "capacity" : "departure"))
              }
              title={`Sorted by ${truckSort === "departure" ? "departure time" : "available capacity"} — click to change`}
            >
              <span
                className={`font-label-mono text-[10px] uppercase tracking-wider hidden sm:inline ${
                  truckSort === "capacity" ? "text-primary" : ""
                }`}
              >
                {truckSort === "departure" ? "By time" : "By load"}
              </span>
              <span
                className={`material-symbols-outlined text-[20px] cursor-pointer ${
                  truckSort === "capacity" ? "text-primary" : ""
                }`}
              >
                filter_list
              </span>
            </button>
          </div>
          <div className="overflow-y-auto pr-2 space-y-4 flex-1">
            {truckRows.map((row) => (
              <div
                key={`${row.truckId}-${row.departure}-${row.destination}`}
                className={`bg-surface p-4 rounded-lg flex items-center justify-between group hover:bg-surface-bright transition-colors cursor-pointer relative overflow-hidden ${
                  row.capacityT === 0 ? "opacity-50" : ""
                }`}
                title={`${row.truckId} → ${row.destination}${row.isReturn ? " (return trip)" : ""}`}
              >
                {!row.isReturn && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-error"></div>
                )}
                <div className="flex items-center gap-4">
                  <div
                    className={`w-10 h-10 rounded flex items-center justify-center ${
                      row.isReturn
                        ? "bg-primary/10 text-primary"
                        : "bg-error/10 text-error"
                    }`}
                  >
                    <span className="material-symbols-outlined">local_shipping</span>
                  </div>
                  <div>
                    <div className="font-data-lg text-data-lg text-on-surface">
                      {row.registration}
                    </div>
                    <div className="font-label-mono text-label-mono text-on-surface-variant">
                      DEP: {row.departure} · {row.origin.toUpperCase()} →{" "}
                      {row.destination.toUpperCase()}
                      {row.isReturn && " · RETURN"}
                    </div>
                  </div>
                </div>
                <div
                  className={`px-2 py-1 rounded font-label-mono text-label-mono whitespace-nowrap ${
                    row.capacityT >= 10
                      ? "bg-secondary/20 text-secondary"
                      : row.capacityT > 0
                        ? "bg-tertiary/20 text-tertiary"
                        : "bg-surface-container-highest text-on-surface-variant"
                  }`}
                >
                  {row.capacityT}T
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Farmer Listings Table */}
      <section className="bg-surface-container/60 backdrop-blur-xl rounded-xl p-8 relative">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h3 className="text-headline-md font-headline-md text-on-surface">
              Active Farmer Listings
            </h3>
            <p className="text-label-mono font-label-mono text-on-surface-variant uppercase mt-1">
              Live Feed — Demo Network
            </p>
          </div>
          <button
            className="bg-primary hover:bg-primary-fixed text-on-primary font-label-mono text-label-mono px-6 py-2 rounded uppercase tracking-wider transition-colors shadow-[0_0_10px_rgba(78,222,163,0.3)] disabled:opacity-50"
            disabled={farmerRows.length <= 6}
            onClick={() => setShowAllFarmers((v) => !v)}
          >
            {showAllFarmers ? "Show Less" : "View All"}
          </button>
        </div>
        <div className="w-full overflow-x-auto" id="farmer-table">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline/10 text-on-surface-variant font-label-mono text-label-mono uppercase">
                <th className="py-4 px-2 font-medium">Farmer ID</th>
                <th className="py-4 px-2 font-medium">Name</th>
                <th className="py-4 px-2 font-medium">Crop</th>
                <th className="py-4 px-2 font-medium">Weight</th>
                <th className="py-4 px-2 font-medium">Village/District</th>
                <th className="py-4 px-2 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="font-data-lg text-data-lg text-on-surface">
              {visibleFarmerRows.map(({ farmer: f, listing: l }) => (
                <tr
                  key={l.id}
                  className="border-b border-outline/5 hover:bg-surface/50 transition-colors cursor-pointer"
                >
                  <td className="py-5 px-2 text-primary">#FRM-{String(f.id * 1000 + l.id)}</td>
                  <td className="py-5 px-2 font-body-md text-body-md">{f.name}</td>
                  <td className="py-5 px-2 capitalize">{l.crop}</td>
                  <td className="py-5 px-2">
                    {l.quantity_kg.toLocaleString("en-IN")} kg
                  </td>
                  <td className="py-5 px-2 font-body-md text-body-md text-on-surface-variant">
                    {f.village}, {f.state}
                  </td>
                  <td className="py-5 px-2 text-right">
                    <div className="inline-flex items-center gap-2 bg-primary/10 px-3 py-1 rounded-full">
                      <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                      <span className="font-label-mono text-label-mono text-primary uppercase">
                        {l.status.replace("_", " ")}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
              {(farmers ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center font-label-mono text-label-mono text-on-surface-variant animate-pulse">
                    LOADING NETWORK…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
