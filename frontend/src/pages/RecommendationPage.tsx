import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/services/api";
import type { JoinPoolResponse, OptionEconomics, SpoilageInfo } from "@/types";
import { formatINR, formatTime, useCountdown } from "@/utils/format";

function DemoBadge() {
  return (
    <span className="bg-tertiary text-on-tertiary font-label-mono text-[10px] px-1.5 py-0.5 rounded-sm">
      Demo
    </span>
  );
}

function DemoDataBadge() {
  return (
    <span className="bg-tertiary text-on-tertiary font-label-mono text-[10px] px-2 py-0.5 rounded-sm">
      Demo Data
    </span>
  );
}

function SpoilageTimer({ hoursRemaining }: { hoursRemaining: number }) {
  const { h, m } = useCountdown(hoursRemaining);
  return (
    <span className="font-data-lg text-on-surface-variant text-lg">
      {h > 0 ? `${h}h ${m}m left` : `${m}m left`}
    </span>
  );
}

function riskColor(level: SpoilageInfo["risk_level"]) {
  if (level === "LOW") return "text-primary";
  if (level === "MEDIUM") return "text-tertiary";
  return "text-error";
}

export default function RecommendationPage() {
  const { listingId } = useParams<{ listingId: string }>();
  const navigate = useNavigate();
  const [joining, setJoining] = useState(false);
  const [joined, setJoined] = useState<JoinPoolResponse | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);

  const { data: rec, isLoading, error } = useQuery({
    queryKey: ["recommendation", listingId],
    queryFn: () => api.latestRecommendation(Number(listingId)),
    enabled: !!listingId,
  });

  async function handleJoin() {
    if (!rec?.pool_id || !listingId) return;
    setJoining(true);
    setJoinError(null);
    try {
      const result = await api.joinPool(rec.pool_id, Number(listingId));
      setJoined(result);
    } catch (err) {
      setJoinError(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setJoining(false);
    }
  }

  if (isLoading) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center gap-4 px-container-padding">
        <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin"></div>
        <span className="font-label-mono text-label-mono text-on-surface-variant uppercase">
          Loading recommendation…
        </span>
      </div>
    );
  }

  if (error || !rec) {
    const apiError = error instanceof ApiError ? error : null;
    return (
      <div className="w-full min-h-[60vh] flex items-center justify-center px-container-padding">
        <div className="max-w-md bg-surface-container/60 backdrop-blur-md border border-error/40 rounded-2xl p-8 text-center flex flex-col gap-4">
          <h1 className="font-headline-md text-headline-md text-on-surface">
            No recommendation available
          </h1>
          <p className="font-body-md text-on-surface-variant">
            {apiError?.message ?? "Something went wrong. Please try again."}
          </p>
          {apiError?.suggestions && (
            <ul className="text-left font-body-md text-sm text-on-surface-variant list-disc pl-6">
              {apiError.suggestions.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          )}
          <button className="btn-primary" onClick={() => navigate("/sell")}>
            Start a New Listing
          </button>
        </div>
      </div>
    );
  }

  const { recommended, baseline, spoilage, explanation } = rec;
  const pool = recommended.pool;
  const priceDelta =
    baseline.price_per_kg > 0
      ? Math.round(
          ((recommended.price_per_kg - baseline.price_per_kg) / baseline.price_per_kg) * 100,
        )
      : 0;
  const transportSavingsPct =
    baseline.transport_cost > 0
      ? Math.max(
          0,
          Math.round((1 - recommended.transport_cost / baseline.transport_cost) * 100),
        )
      : 0;

  const rankedMarkets = [
    {
      rank: 1,
      name: recommended.mandi_name,
      distance_km: recommended.distance_km,
      price_per_kg: recommended.price_per_kg,
      selected: true,
    },
    ...rec.alternatives.map((a, i) => ({
      rank: i + 2,
      name: a.mandi_name,
      distance_km: a.distance_km,
      price_per_kg: a.price_per_kg,
      selected: false,
    })),
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-container-padding py-8 flex flex-col gap-4">
      {/* Hero Recommends Panel */}
      <section className="relative w-full rounded-2xl bg-surface-container/60 backdrop-blur-xl border border-primary/20 overflow-hidden shadow-2xl p-8 md:p-12 mt-6">
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(78,222,163,0.1)_0%,transparent_70%)]"></div>
        <div className="relative z-10 flex flex-col items-center text-center">
          <div className="flex items-center gap-3 mb-6">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(78,222,163,0.8)]"></span>
            <span className="font-label-mono text-label-mono text-primary tracking-widest uppercase">
              Unnati Recommends
            </span>
            <DemoDataBadge />
          </div>
          <div className="font-display-hero text-display-hero md:text-[80px] md:leading-[88px] font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-primary via-primary-fixed to-secondary-fixed mb-6 drop-shadow-[0_0_24px_rgba(78,222,163,0.3)] tabular-nums">
            {rec.net_gain >= 0 ? "+" : ""}
            {formatINR(rec.net_gain)}
          </div>
          <p className="text-headline-md font-headline-md text-on-surface-variant max-w-2xl mx-auto mb-4 leading-snug">
            {pool && (
              <>
                Pool with <span className="text-on-surface">{pool.farmer_count} farmers</span> ·{" "}
              </>
            )}
            {recommended.truck_registration && (
              <>
                Return truck{" "}
                <span className="text-on-surface font-data-lg">
                  {recommended.truck_id}
                </span>{" "}
                ·{" "}
              </>
            )}
            Sell at <span className="text-on-surface">{recommended.mandi_name}</span>
          </p>
          <p className="font-body-md text-on-surface-variant max-w-xl mx-auto mb-10">
            {explanation.headline} — {explanation.summary}
          </p>

          {joined ? (
            <div className="flex flex-col items-center gap-3 bg-primary/10 border border-primary/40 rounded-xl px-8 py-5 max-w-lg">
              <div className="flex items-center gap-2 text-primary font-headline-md">
                <span className="material-symbols-outlined">check_circle</span>
                You're on the load!
              </div>
              <p className="font-body-md text-sm text-on-surface-variant">
                {joined.message} Truck {joined.truck_id} → {joined.destination_mandi},
                departing {new Date(joined.departure_at).toLocaleString("en-IN")} ·{" "}
                {Math.round(joined.quantity_kg).toLocaleString("en-IN")} kg total.
              </p>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto justify-center">
              <button
                className="bg-gradient-to-r from-secondary to-primary text-on-primary font-headline-md text-base px-8 py-4 rounded-lg shadow-[0_0_20px_rgba(78,222,163,0.3)] hover:shadow-[0_0_30px_rgba(78,222,163,0.5)] transition-all duration-300 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:pointer-events-none"
                onClick={handleJoin}
                disabled={joining || !rec.pool_id}
              >
                {joining ? "JOINING…" : rec.pool_id ? "JOIN THIS LOAD" : "POOL UNAVAILABLE"}
                {!joining && (
                  <span className="material-symbols-outlined transition-transform duration-300 group-hover:translate-x-1">
                    arrow_forward
                  </span>
                )}
              </button>
              <button
                className="bg-surface-container-high/50 text-on-surface border border-primary/20 px-8 py-4 rounded-lg font-headline-md text-base hover:bg-surface-container-highest transition-colors duration-300 flex items-center justify-center gap-2"
                onClick={() =>
                  document.getElementById("why-section")?.scrollIntoView({ behavior: "smooth" })
                }
              >
                <span className="material-symbols-outlined text-[20px]">analytics</span>
                See Why
              </button>
            </div>
          )}
          {joinError && (
            <p className="mt-4 text-sm text-error font-body-md">{joinError}</p>
          )}
        </div>
      </section>

      {/* Status Strip */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-surface-container/60 backdrop-blur-md rounded-xl p-6 border border-outline-variant/30 relative flex flex-col justify-between">
          <DemoBadge />
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
              local_shipping
            </span>
            <span className="font-label-mono text-label-mono text-on-surface-variant uppercase">
              Truck Capacity
            </span>
          </div>
          <div className="flex items-end justify-between">
            <span className="font-data-lg text-data-lg text-on-surface text-3xl">
              {pool?.utilization_percent ?? 0}%
            </span>
            <div className="w-24 h-2 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full shadow-[0_0_8px_rgba(78,222,163,0.5)]"
                style={{ width: `${pool?.utilization_percent ?? 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-surface-container/60 backdrop-blur-md rounded-xl p-6 border border-outline-variant/30 relative flex flex-col justify-between">
          <DemoBadge />
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
              group
            </span>
            <span className="font-label-mono text-label-mono text-on-surface-variant uppercase">
              Pooled Volume
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-data-lg text-data-lg text-on-surface text-3xl">
              {pool ? Math.round(pool.total_quantity_kg).toLocaleString("en-IN") : "—"}
            </span>
            <span className="font-label-mono text-on-surface-variant">kg</span>
          </div>
          {pool && pool.remaining_capacity_kg > 0 && (
            <p className="text-sm text-primary mt-1 flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
              +{Math.round(pool.remaining_capacity_kg).toLocaleString("en-IN")}
              kg needed for full load
            </p>
          )}
        </div>

        <div className="bg-surface-container/60 backdrop-blur-md rounded-xl p-6 border border-outline-variant/30 relative flex flex-col justify-between">
          <DemoBadge />
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
              thermostat
            </span>
            <span className="font-label-mono text-label-mono text-on-surface-variant uppercase">
              Spoilage Risk
            </span>
          </div>
          <div className="flex items-baseline gap-3">
            <span
              className={`font-headline-md text-2xl uppercase tracking-wider ${riskColor(spoilage.risk_level)}`}
            >
              {spoilage.risk_level.toLowerCase()}
            </span>
            <SpoilageTimer hoursRemaining={spoilage.hours_remaining} />
          </div>
          <p className="text-xs text-on-surface-variant mt-2">
            Est. spoilage loss {spoilage.estimated_loss_percentage.toFixed(1)}% if delayed
          </p>
        </div>
      </section>

      {/* Demo-data labels from the API — seeded prices/weather must stay clearly labelled */}
      {Object.keys(rec.data_labels).length > 0 && (
        <section className="flex flex-wrap items-center gap-2 mt-2">
          <span className="material-symbols-outlined text-tertiary text-[16px]">info</span>
          {Object.entries(rec.data_labels).map(([key, label]) => (
            <span
              key={key}
              className="bg-tertiary/10 border border-tertiary/30 text-tertiary font-label-mono text-[10px] px-2 py-0.5 rounded-sm"
            >
              {label}
            </span>
          ))}
        </section>
      )}

      {/* Comparison */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
        <EconomicsCard label="Sell Normally (Local)" economics={baseline} muted />
        <EconomicsCard
          label="With Unnati"
          economics={recommended}
          truckLabel={
            recommended.is_return_trip
              ? `Return trip${recommended.departure_at ? ` · departs ${formatTime(recommended.departure_at)}` : ""}`
              : undefined
          }
          transportSavingsPct={transportSavingsPct}
          priceDelta={priceDelta}
        />
      </section>

      {/* Details Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Route Summary */}
          <div className="bg-surface-container/60 backdrop-blur-md border border-outline-variant/30 rounded-2xl overflow-hidden relative min-h-[180px] p-6">
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_80%_0%,rgba(78,222,163,0.08)_0%,transparent_60%)]"></div>
            <div className="relative z-10 flex justify-between items-start">
              <div>
                <div className="font-label-mono text-[10px] text-on-surface-variant uppercase mb-1">
                  Optimal Route Generated
                </div>
                <div className="font-data-lg text-primary">
                  {Math.round(rec.recommended.distance_km)} km to{" "}
                  {recommended.mandi_name}
                  {recommended.departure_at &&
                    ` · ${new Date(recommended.departure_at).toLocaleString("en-IN", {
                      day: "numeric",
                      month: "short",
                      hour: "numeric",
                      minute: "2-digit",
                    })}`}
                </div>
                <div className="mt-4 flex items-center gap-3 font-body-md text-sm text-on-surface-variant">
                  <span className="material-symbols-outlined text-primary">location_on</span>
                  Pickup
                  <div className="flex-1 border-t border-dashed border-primary/40 min-w-[60px] relative">
                    <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-primary rounded-full animate-ping"></span>
                  </div>
                  <span className="material-symbols-outlined text-primary">
                    local_shipping
                  </span>
                  <div className="flex-1 border-t border-dashed border-outline/30 min-w-[60px]"></div>
                  <span className="material-symbols-outlined text-primary">storefront</span>
                  {recommended.mandi_name}
                </div>
              </div>
              <DemoBadge />
            </div>
          </div>

          {/* Ranked Mandis */}
          <div className="bg-surface-container/60 backdrop-blur-md rounded-2xl border border-outline-variant/30 p-6">
            <h3 className="font-headline-md text-xl mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">storefront</span>
              Target Markets Analysis
            </h3>
            <div className="flex flex-col gap-3">
              {rankedMarkets.map((m) =>
                m.selected ? (
                  <div
                    key={m.name}
                    className="bg-primary/10 border border-primary/30 rounded-lg p-4 flex items-center justify-between relative overflow-hidden group"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div className="flex items-center gap-4 relative z-10">
                      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                        {m.rank}
                      </div>
                      <div>
                        <div className="font-bold text-on-surface flex items-center gap-2">
                          {m.name}
                          <span className="text-[10px] bg-primary text-on-primary px-1.5 py-0.5 rounded-sm uppercase tracking-wider font-label-mono">
                            Selected
                          </span>
                        </div>
                        <div className="text-sm text-on-surface-variant">
                          Distance: {Math.round(m.distance_km)}km
                        </div>
                      </div>
                    </div>
                    <div className="text-right relative z-10 flex flex-col items-end">
                      <div className="font-data-lg text-primary text-xl">
                        ₹{m.price_per_kg.toFixed(0)}/kg
                      </div>
                      <DemoBadge />
                    </div>
                  </div>
                ) : (
                  <div
                    key={m.name}
                    className={`bg-surface-container-low border border-outline-variant/10 rounded-lg p-4 flex items-center justify-between ${
                      m.price_per_kg === 0 ? "opacity-40" : "opacity-70 hover:opacity-100"
                    } transition-opacity`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center text-on-surface-variant font-bold">
                        {m.rank}
                      </div>
                      <div>
                        <div className="font-bold text-on-surface">{m.name}</div>
                        <div className="text-sm text-on-surface-variant">
                          Distance: {Math.round(m.distance_km)}km
                        </div>
                      </div>
                    </div>
                    <div className="text-right flex flex-col items-end">
                      <div className="font-data-lg text-on-surface-variant text-xl">
                        ₹{m.price_per_kg.toFixed(0)}/kg
                      </div>
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-6" id="why-section">
          {/* AI Reasoning — facts validated by the engines, explained by the LLM */}
          <div className="bg-surface-container/60 backdrop-blur-md rounded-2xl border border-outline-variant/30 p-6 relative">
            <div className="absolute top-4 right-4"><DemoBadge /></div>
            <h3 className="font-headline-md text-lg mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">psychology</span>
              Why this recommendation?
              {!rec.llm_powered && (
                <span className="font-label-mono text-[9px] text-on-surface-variant uppercase">
                  (offline mode)
                </span>
              )}
            </h3>
            <ul className="space-y-4">
              {explanation.why_this_option.map((reason, i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="material-symbols-outlined text-primary text-[18px] mt-0.5">
                    check_circle
                  </span>
                  <div className="text-xs text-on-surface-variant mt-0.5">{reason}</div>
                </li>
              ))}
            </ul>
            {explanation.warnings.length > 0 && (
              <ul className="space-y-2 mt-4 pt-4 border-t border-outline-variant/20">
                {explanation.warnings.map((w, i) => (
                  <li key={i} className="flex gap-3 items-start">
                    <span className="material-symbols-outlined text-tertiary text-[18px] mt-0.5">
                      warning
                    </span>
                    <div className="text-xs text-tertiary mt-0.5">{w}</div>
                  </li>
                ))}
              </ul>
            )}
            {explanation.action && (
              <div className="mt-4 pt-4 border-t border-outline-variant/20 flex items-start gap-2">
                <span className="material-symbols-outlined text-primary text-[18px]">
                  bolt
                </span>
                <p className="text-sm text-on-surface font-medium">{explanation.action}</p>
              </div>
            )}
          </div>

          {/* Pool Members */}
          <div className="bg-surface-container/60 backdrop-blur-md rounded-2xl border border-outline-variant/30 p-6 relative flex-grow">
            <div className="absolute top-4 right-4"><DemoBadge /></div>
            <h3 className="font-headline-md text-lg mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-on-surface-variant">
                diversity_3
              </span>
              Pool Composition
            </h3>
            {!pool || pool.members.length === 0 ? (
              <p className="font-body-md text-sm text-on-surface-variant">
                Shipping solo for now — no nearby farmers are pooling on this truck yet.
              </p>
            ) : (
              <div className="space-y-4">
                {pool.members.map((member, i) => {
                  const share = pool.total_quantity_kg
                    ? Math.round((member.quantity_kg / pool.total_quantity_kg) * 100)
                    : 0;
                  const isUser = i === 0;
                  return isUser ? (
                    <div
                      key={`${member.farmer_name}-${i}`}
                      className="flex items-center justify-between p-3 bg-surface-container-highest rounded-lg border border-primary/10"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
                          <span className="material-symbols-outlined text-primary text-[16px]">
                            person
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-bold text-primary flex items-center gap-2">
                            You
                            <span className="bg-primary/20 text-primary text-[9px] uppercase px-1 rounded-sm">
                              Initiator
                            </span>
                          </div>
                          <div className="text-xs text-on-surface-variant">
                            {rec.crop_name} ·{" "}
                            {Math.round(member.quantity_kg).toLocaleString("en-IN")}kg
                          </div>
                        </div>
                      </div>
                      <div className="font-data-lg text-sm">{share}%</div>
                    </div>
                  ) : (
                    <div
                      key={`${member.farmer_name}-${i}`}
                      className="flex items-center justify-between p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center border border-outline-variant">
                          <span className="text-xs font-bold text-on-surface-variant">
                            {member.farmer_name
                              .split(" ")
                              .map((p) => p[0])
                              .slice(0, 2)
                              .join("")}
                          </span>
                        </div>
                        <div>
                          <div className="text-sm text-on-surface">{member.farmer_name}</div>
                          <div className="text-xs text-on-surface-variant">
                            {member.village} Village ·{" "}
                            {Math.round(member.quantity_kg).toLocaleString("en-IN")}kg ·{" "}
                            {Math.round(member.distance_km)}km away
                          </div>
                        </div>
                      </div>
                      <div className="font-data-lg text-sm text-on-surface-variant">
                        {share}%
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function EconomicsCard({
  label,
  economics,
  muted = false,
  transportSavingsPct,
  priceDelta,
  truckLabel,
}: {
  label: string;
  economics: OptionEconomics;
  muted?: boolean;
  transportSavingsPct?: number;
  priceDelta?: number;
  truckLabel?: string;
}) {
  return (
    <div
      className={`${
        muted
          ? "bg-surface-container-low opacity-80 grayscale-[30%]"
          : "bg-surface-container/80 backdrop-blur-lg border border-primary/40 shadow-[0_0_30px_rgba(78,222,163,0.15)] transform md:scale-105 z-10 overflow-hidden"
      } p-8 rounded-2xl border ${
        muted ? "border-outline-variant/20" : ""
      } relative flex flex-col justify-center items-center text-center`}
    >
      {!muted && (
        <>
          <div className="absolute top-4 right-4 z-20">
            <DemoBadge />
          </div>
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none"></div>
        </>
      )}
      <span
        className={`font-label-mono text-label-mono uppercase tracking-widest mb-4 flex items-center gap-2 ${
          muted ? "text-on-surface-variant" : "text-primary"
        }`}
      >
        {!muted && (
          <span className="material-symbols-outlined text-[16px]">verified</span>
        )}
        {label}
      </span>
      <div
        className={`font-data-lg text-4xl mb-2 tabular-nums ${
          muted ? "text-on-surface-variant line-through decoration-error/50 decoration-2" : "text-primary text-5xl font-bold"
        }`}
      >
        {formatINR(economics.net_profit)}
      </div>
      {muted ? (
        <p className="text-sm text-on-surface-variant max-w-xs mt-2">
          Direct sale at your nearest mandi ({economics.mandi_name},{" "}
          {Math.round(economics.distance_km)}km).
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-2 w-full max-w-xs text-left">
          {truckLabel && (
            <div className="flex justify-between text-sm border-b border-outline-variant/20 pb-1">
              <span className="text-on-surface-variant">Truck</span>
              <span className="text-primary font-data-lg">{truckLabel}</span>
            </div>
          )}
          {transportSavingsPct !== undefined && (
            <div className="flex justify-between text-sm border-b border-outline-variant/20 pb-1">
              <span className="text-on-surface-variant">Transport Cost</span>
              <span className="text-primary font-data-lg">
                -{transportSavingsPct}% (Pooled)
              </span>
            </div>
          )}
          {priceDelta !== undefined && (
            <div className="flex justify-between text-sm">
              <span className="text-on-surface-variant">Sale Price</span>
              <span className="text-primary font-data-lg">
                {priceDelta >= 0 ? "+" : ""}
                {priceDelta}% ({economics.mandi_name})
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
