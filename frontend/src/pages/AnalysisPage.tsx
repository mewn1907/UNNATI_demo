import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { api, ApiError } from "@/services/api";

const STEPS = [
  { title: "Finding nearby farmers", meta: "SCANNING POOLING RADIUS", icon: "group" },
  { title: "Checking return trucks", meta: "EMPTY-TRIP PREFERENCE ON", icon: "local_shipping" },
  { title: "Comparing Mandi prices", meta: "LIVE DEMO PRICE FEED", icon: "query_stats" },
  { title: "Calculating spoilage risk", meta: "TEMP / HUMIDITY VARIANCES", icon: "thermostat" },
  { title: "Picking best profit option", meta: "YIELD OPTIMIZATION", icon: "account_balance_wallet" },
];

export default function AnalysisPage() {
  const { listingId } = useParams<{ listingId: string }>();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!listingId || startedRef.current) return;
    startedRef.current = true;

    // Advance the visual checklist while the deterministic engines run.
    const timers = [
      setTimeout(() => setStep(1), 700),
      setTimeout(() => setStep(2), 1400),
      setTimeout(() => setStep(3), 2200),
      setTimeout(() => setStep(4), 2900),
    ];

    api
      .recommend(Number(listingId))
      .then(() => {
        // Wait for the checklist to reach the last step before revealing.
        setTimeout(() => navigate(`/recommendation/${listingId}`), 3200);
      })
      .catch((err: unknown) => {
        timers.forEach(clearTimeout);
        setError(
          err instanceof ApiError
            ? err
            : new ApiError("INTERNAL_ERROR", "Something went wrong. Please try again."),
        );
      });

    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  if (error) {
    return (
      <div className="w-full min-h-[70vh] flex items-center justify-center px-container-padding">
        <div className="max-w-lg w-full bg-surface-container/60 backdrop-blur-md border border-error/40 rounded-2xl p-8 text-center flex flex-col gap-4">
          <span className="material-symbols-outlined text-error text-4xl mx-auto">
            error
          </span>
          <h1 className="font-headline-md text-headline-md text-on-surface">
            We couldn't find a profitable route
          </h1>
          <p className="font-body-md text-on-surface-variant">{error.message}</p>
          {error.suggestions && error.suggestions.length > 0 && (
            <ul className="text-left font-body-md text-sm text-on-surface-variant list-disc pl-6">
              {error.suggestions.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          )}
          <div className="flex gap-3 justify-center mt-2">
            <button className="btn-primary" onClick={() => navigate("/sell")}>
              Edit Listing
            </button>
            <button className="btn-secondary" onClick={() => window.location.reload()}>
              Retry Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full py-16 px-container-padding flex justify-center overflow-hidden">
      {/* Ambient Background FX */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-20 flex items-center justify-center">
        <div className="w-[800px] h-[800px] rounded-full bg-primary-fixed/30 blur-[120px] mix-blend-screen animate-pulse-soft"></div>
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-[1000px] max-h-[1000px] opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at center, rgba(78,222,163,0.8) 0%, transparent 60%)",
          }}
        ></div>
      </div>

      {/* Central Glass Container */}
      <div className="w-full max-w-lg relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4 px-4 py-1.5 rounded-full bg-surface-container-high/80 border border-primary/20 shadow-[0_0_15px_rgba(78,222,163,0.15)]">
            <span
              className="material-symbols-outlined text-primary text-sm animate-spin"
              style={{ animationDuration: "3s" }}
            >
              drive_file_rename
            </span>
            <span className="font-label-mono text-label-mono text-primary tracking-widest uppercase">
              Processing
            </span>
          </div>
          <h1 className="font-display-hero text-display-hero text-on-surface mb-2">
            Analysis in Progress
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-sm mx-auto">
            Unnati AI is calculating optimal logistics and market routing for your
            load.
          </p>
        </div>

        {/* Checklist Container with scan line */}
        <div className="flex flex-col gap-4 relative overflow-hidden rounded-xl">
          {/* Scanning sweep across the checklist */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-full z-20">
            <div className="h-16 w-full bg-gradient-to-b from-transparent via-primary/10 to-transparent animate-scan"></div>
          </div>
          {/* Connection Line */}
          <div className="absolute left-7 top-8 bottom-8 w-[2px] bg-outline-variant/30 z-0 hidden sm:block"></div>
          <div
            className="absolute left-7 top-8 w-[2px] bg-primary shadow-[0_0_8px_rgba(78,222,163,0.6)] z-0 hidden sm:block transition-all duration-1000"
            style={{ height: `${(Math.min(step, STEPS.length - 1) / STEPS.length) * 100}%` }}
          ></div>

          {STEPS.map((s, i) => {
            const done = i < step;
            const active = i === step;
            if (done) {
              return (
                <div
                  key={s.title}
                  className="relative z-10 flex items-center gap-4 p-4 rounded-xl bg-surface-container/60 backdrop-blur-md border border-primary/15 shadow-sm transform transition-all hover:scale-[1.02] hover:bg-surface-container/80 group"
                >
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center border border-primary/40 shadow-[0_0_12px_rgba(78,222,163,0.3)] shrink-0 group-hover:shadow-[0_0_20px_rgba(78,222,163,0.5)] transition-shadow">
                    <span className="material-symbols-outlined text-primary text-[20px]">
                      check
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-data-lg text-data-lg text-on-surface truncate">
                      {s.title}
                    </h3>
                    <p className="font-label-mono text-label-mono text-on-surface-variant/70 mt-1">
                      {s.meta}
                    </p>
                  </div>
                  <span className="shrink-0 hidden sm:block font-label-mono text-label-mono text-primary opacity-80 uppercase tracking-wider">
                    Done
                  </span>
                </div>
              );
            }
            if (active) {
              const pct = Math.round(((i + 0.68) / STEPS.length) * 100);
              return (
                <div
                  key={s.title}
                  className="relative z-10 flex items-center gap-4 p-4 rounded-xl bg-surface-container-high backdrop-blur-xl border border-primary/40 shadow-[0_0_30px_rgba(78,222,163,0.1)] transform transition-all scale-[1.03]"
                >
                  <div className="w-10 h-10 rounded-full bg-transparent flex items-center justify-center relative shrink-0">
                    <div className="absolute inset-0 rounded-full border-2 border-primary/20"></div>
                    <div className="absolute inset-0 rounded-full border-2 border-t-primary border-r-primary border-b-transparent border-l-transparent animate-spin shadow-[0_0_15px_rgba(78,222,163,0.8)]"></div>
                    <span className="material-symbols-outlined text-primary text-[18px] animate-pulse">
                      query_stats
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-data-lg text-data-lg text-primary truncate">
                      {s.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="h-1 flex-1 bg-surface-container-lowest rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-700 relative"
                          style={{ width: `${pct}%` }}
                        >
                          <div className="absolute top-0 right-0 bottom-0 w-8 bg-gradient-to-r from-transparent to-white/50 animate-pulse-soft"></div>
                        </div>
                      </div>
                      <span className="font-label-mono text-label-mono text-primary">
                        {pct}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            }
            return (
              <div
                key={s.title}
                className="relative z-10 flex items-center gap-4 p-4 rounded-xl bg-surface-container-low/40 backdrop-blur-sm border border-outline-variant/30 opacity-60"
              >
                <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center border border-outline-variant shrink-0">
                  <span className="material-symbols-outlined text-outline text-[20px]">
                    {s.icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-data-lg text-data-lg text-on-surface-variant truncate">
                    {s.title}
                  </h3>
                  <p className="font-label-mono text-label-mono text-on-surface-variant/50 mt-1">
                    {s.meta}
                  </p>
                </div>
                <span className="shrink-0 hidden sm:block font-label-mono text-label-mono text-outline uppercase tracking-wider">
                  Pending
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-12 text-center opacity-80">
          <div className="inline-flex items-start gap-3 text-left max-w-sm bg-surface-container-lowest/50 p-4 rounded-lg border border-outline-variant/20">
            <span className="material-symbols-outlined text-secondary-fixed text-[20px] mt-0.5">
              lightbulb
            </span>
            <p className="font-body-md text-body-md text-on-surface-variant text-sm">
              <strong className="text-on-surface">Pro Tip:</strong> Every number you'll
              see next is computed by our deterministic logistics engine — the AI only
              explains it.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
