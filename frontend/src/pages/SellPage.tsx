import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/services/api";

const HUBS = [
  { name: "Nangloi", latitude: 28.683, longitude: 77.06 },
  { name: "Mundka", latitude: 28.6808, longitude: 76.9791 },
  { name: "Bawana", latitude: 28.7985, longitude: 77.0374 },
  { name: "Kharkhoda", latitude: 28.8825, longitude: 76.9063 },
];

const FRESHNESS_OPTIONS = [
  { value: "0-6", label: "Harvested 0-6 hours ago", hours: 3 },
  { value: "6-12", label: "Harvested 6-12 hours ago", hours: 9 },
  { value: "12-24", label: "Harvested 12-24 hours ago", hours: 18 },
  { value: "24+", label: "Harvested > 24 hours ago (Cold Stored)", hours: 30 },
];

const RADIUS_MIN = 10;
const RADIUS_MAX = 80;

export default function SellPage() {
  const navigate = useNavigate();
  const { data: crops, isLoading: cropsLoading } = useQuery({
    queryKey: ["crops"],
    queryFn: api.crops,
  });

  const [crop, setCrop] = useState("");
  const [quantityKg, setQuantityKg] = useState<number | "">("");
  const [freshness, setFreshness] = useState("");
  const [hub, setHub] = useState<string>(HUBS[0].name);
  const [radiusKm, setRadiusKm] = useState(45);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<{ message: string; suggestions?: string[] } | null>(
    null,
  );

  const selectedHub = useMemo(
    () => HUBS.find((h) => h.name === hub) ?? HUBS[0],
    [hub],
  );

  const radiusPercent =
    ((radiusKm - RADIUS_MIN) / (RADIUS_MAX - RADIUS_MIN)) * 100;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!crop) return setError({ message: "Please select your crop." });
    if (!quantityKg || quantityKg < 50)
      return setError({
        message: "Please enter a quantity of at least 50 kg.",
      });
    if (!freshness)
      return setError({
        message: "Please select when the crop was harvested.",
      });

    const freshnessOption =
      FRESHNESS_OPTIONS.find((f) => f.value === freshness) ?? FRESHNESS_OPTIONS[0];
    const harvestedAt = new Date(
      Date.now() - freshnessOption.hours * 3600_000,
    ).toISOString();

    setSubmitting(true);
    try {
      const { id } = await api.createListing({
        crop,
        quantity_kg: Number(quantityKg),
        latitude: selectedHub.latitude,
        longitude: selectedHub.longitude,
        harvested_at: harvestedAt,
        preferred_radius_km: radiusKm,
      });
      navigate(`/analysis/${id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? { message: err.message, suggestions: err.suggestions }
          : { message: "Something went wrong. Please try again." },
      );
      setSubmitting(false);
    }
  }

  const fieldClass =
    "w-full bg-surface-container-highest border border-[rgba(110,231,183,0.15)] rounded-lg p-4 font-body-md text-body-md text-on-surface appearance-none focus:outline-none focus:border-primary transition-colors cursor-pointer pr-12 disabled:opacity-60";
  const inputClass =
    "w-full bg-surface-container-highest border border-[rgba(110,231,183,0.15)] rounded-lg p-4 font-data-lg text-data-lg text-primary appearance-none focus:outline-none focus:border-primary transition-colors placeholder:text-outline/50 tabular-nums text-right pr-16";

  return (
    <div className="relative w-full py-16 px-container-padding flex justify-center overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 -left-1/4 w-1/2 h-1/2 bg-primary/10 rounded-full blur-[120px] mix-blend-screen"></div>
        <div className="absolute bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-secondary/10 rounded-full blur-[120px] mix-blend-screen"></div>
      </div>
      <div className="w-full max-w-2xl bg-[rgba(16,24,20,0.6)] backdrop-blur-[12px] border border-[rgba(110,231,183,0.15)] rounded-2xl p-8 md:p-12 relative shadow-2xl flex flex-col gap-10">
        <div className="absolute -top-4 right-8 bg-tertiary text-on-tertiary font-label-mono text-label-mono px-3 py-1 rounded-full shadow-lg">
          LIVE MARKET · DEMO DATA
        </div>
        <div className="flex flex-col gap-2 text-center">
          <h1 className="font-display-hero text-display-hero text-primary tracking-tight">
            Sell Produce
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-md mx-auto">
            Enter your crop details to instantly connect with verified buyers and
            optimize your logistics.
          </p>
        </div>
        <form className="flex flex-col gap-8 w-full" onSubmit={handleSubmit}>
          <div className="flex flex-col md:flex-row gap-8 w-full">
            <div className="flex flex-col gap-3 w-full md:w-1/2 group relative">
              <label className="font-label-mono text-label-mono text-primary uppercase tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                Crop Type
              </label>
              <div className="relative">
                <select
                  className={fieldClass}
                  value={crop}
                  onChange={(e) => setCrop(e.target.value)}
                  disabled={cropsLoading}
                >
                  <option value="" disabled>
                    {cropsLoading ? "Loading crops…" : "Select Crop"}
                  </option>
                  {(crops ?? []).map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name} ({c.category})
                    </option>
                  ))}
                </select>
                <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-primary pointer-events-none">
                  expand_more
                </span>
              </div>
            </div>
            <div className="flex flex-col gap-3 w-full md:w-1/2 group relative">
              <label className="font-label-mono text-label-mono text-primary uppercase tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary/50"></span>
                Quantity (kg)
              </label>
              <div className="relative">
                <input
                  className={inputClass}
                  min={50}
                  placeholder="0"
                  step={50}
                  type="number"
                  value={quantityKg}
                  onChange={(e) =>
                    setQuantityKg(e.target.value === "" ? "" : Number(e.target.value))
                  }
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 font-label-mono text-label-mono text-on-surface-variant pointer-events-none">
                  KG
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full group relative">
            <label className="font-label-mono text-label-mono text-primary uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary/50"></span>
              Freshness / Harvest Time
            </label>
            <div className="relative">
              <select
                className={fieldClass}
                value={freshness}
                onChange={(e) => setFreshness(e.target.value)}
              >
                <option value="" disabled>
                  Select Freshness
                </option>
                {FRESHNESS_OPTIONS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-primary pointer-events-none">
                schedule
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-4 w-full">
            <div className="flex justify-between items-end">
              <label className="font-label-mono text-label-mono text-primary uppercase tracking-widest flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">
                  location_on
                </span>
                Pickup Hub
              </label>
              <span className="font-label-mono text-[10px] text-on-surface-variant">
                SELECT NEAREST
              </span>
            </div>
            <div className="flex flex-wrap gap-3" id="hub-chips">
              {HUBS.map((h) => {
                const selected = hub === h.name;
                return (
                  <button
                    key={h.name}
                    type="button"
                    data-selected={selected}
                    onClick={() => setHub(h.name)}
                    className={`px-5 py-2.5 rounded-full border ${
                      selected
                        ? "bg-primary/20 border-primary text-primary"
                        : "bg-surface-container-highest border-[rgba(110,231,183,0.15)] text-on-surface"
                    } hover:border-primary transition-all duration-300 flex items-center gap-2`}
                  >
                    {h.name}
                    {selected && (
                      <span className="material-symbols-outlined text-[16px]">check</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col gap-6 w-full pt-4 border-t border-[rgba(110,231,183,0.1)]">
            <div className="flex justify-between items-center w-full">
              <label className="font-label-mono text-label-mono text-primary uppercase tracking-widest flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">radar</span>
                Search Radius
              </label>
              <div
                className="font-data-lg text-data-lg text-primary tabular-nums tracking-tighter"
                id="radius-val"
              >
                {radiusKm}{" "}
                <span className="text-sm text-on-surface-variant font-normal">KM</span>
              </div>
            </div>
            <div
              className="relative w-full h-8 flex items-center cursor-pointer group"
              id="radius-container"
            >
              <div className="absolute w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="h-full bg-primary/30 w-full"></div>
              </div>
              <div
                className="absolute h-1.5 bg-gradient-to-r from-[#6ffbbe] to-[#4edea3] rounded-full shadow-[0_0_10px_rgba(78,222,163,0.5)] transition-all duration-150 ease-out"
                id="radius-track"
                style={{ width: `${radiusPercent}%` }}
              ></div>
              <input
                aria-label="Search radius in kilometres"
                className="absolute w-full opacity-0 cursor-pointer h-full z-10"
                id="radius-slider"
                max={RADIUS_MAX}
                min={RADIUS_MIN}
                type="range"
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
              />
              <div
                className="absolute w-6 h-6 bg-surface border-2 border-primary rounded-full shadow-[0_0_15px_rgba(78,222,163,0.8)] flex items-center justify-center -ml-3 transition-all duration-150 ease-out z-20 pointer-events-none group-hover:scale-110"
                id="radius-thumb"
                style={{ left: `${radiusPercent}%` }}
              >
                <div className="w-2 h-2 bg-primary rounded-full"></div>
              </div>
            </div>
            <div className="flex justify-between font-label-mono text-xs text-on-surface-variant/50">
              <span>{RADIUS_MIN} KM</span>
              <span>{RADIUS_MAX} KM</span>
            </div>
          </div>

          {error && (
            <div className="bg-error-container/40 border border-error/40 text-error rounded-lg px-4 py-3 text-sm font-body-md flex flex-col gap-1">
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">error</span>
                {error.message}
              </span>
              {error.suggestions && error.suggestions.length > 0 && (
                <ul className="list-disc list-inside text-on-error-container/90 pl-1">
                  {error.suggestions.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <button
            className="mt-4 w-full relative group overflow-hidden rounded-xl bg-gradient-to-r from-primary-fixed to-primary-fixed-dim p-[2px] transition-all duration-300 hover:shadow-[0_0_40px_rgba(78,222,163,0.3)] hover:scale-[1.01] active:scale-[0.99] disabled:opacity-60 disabled:pointer-events-none"
            type="submit"
            disabled={submitting}
          >
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out z-0"></div>
            <div className="relative w-full h-full bg-black/10 backdrop-blur-sm rounded-[10px] px-8 py-5 flex items-center justify-center gap-3 z-10 text-[#002113] font-headline-md text-headline-md font-bold">
              {submitting ? (
                <>
                  <span className="material-symbols-outlined animate-spin">refresh</span>{" "}
                  Processing…
                </>
              ) : (
                <>
                  Find My Best Option
                  <span className="material-symbols-outlined transition-transform duration-300 group-hover:translate-x-2">
                    arrow_forward
                  </span>
                </>
              )}
            </div>
          </button>
        </form>
      </div>
    </div>
  );
}
