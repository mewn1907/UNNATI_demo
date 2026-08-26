import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";

const quickActions = [
  { icon: "query_stats", title: "Market", subtitle: "Live rates", to: "/network" },
  { icon: "smart_toy", title: "AI Copilot", subtitle: "Ask anything", to: "/chat" },
];

const steps = [
  {
    number: "01",
    title: "Harvest Intent",
    description:
      "Log your expected yield and timeframe. Our system begins scanning regional markets instantly.",
    to: "/sell",
    visualizer: (
      <div className="h-24 bg-surface rounded-lg ring-1 ring-outline/10 p-3 flex items-end gap-2">
        <div className="w-1/4 bg-primary/20 h-1/3 rounded-t"></div>
        <div className="w-1/4 bg-primary/40 h-2/3 rounded-t"></div>
        <div className="w-1/4 bg-primary h-full rounded-t relative">
          <span className="absolute -top-6 left-1/2 -translate-x-1/2 font-label-mono text-[10px] text-primary">
            PEAK
          </span>
        </div>
        <div className="w-1/4 bg-primary/60 h-4/5 rounded-t"></div>
      </div>
    ),
  },
  {
    number: "02",
    title: "Logistics Matching",
    description:
      "AI identifies return trucks and load-pooling opportunities within a 50km radius to slash transport costs.",
    to: "/network",
    visualizer: (
      <div className="h-24 bg-surface rounded-lg ring-1 ring-outline/10 p-3 flex flex-col justify-center gap-3 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(78,222,163,0.1)_0%,transparent_70%)]"></div>
        <div className="flex items-center justify-between z-10">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">location_on</span>
          <div className="flex-1 border-t border-dashed border-primary/30 mx-2 relative">
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-primary rounded-full animate-ping"></span>
          </div>
          <span className="material-symbols-outlined text-primary text-sm">local_shipping</span>
        </div>
        <div className="flex items-center justify-between z-10 opacity-50">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">location_on</span>
          <div className="flex-1 border-t border-dashed border-outline/30 mx-2"></div>
          <span className="material-symbols-outlined text-on-surface-variant text-sm">local_shipping</span>
        </div>
      </div>
    ),
  },
  {
    number: "03",
    title: "See Your Gain",
    description:
      "Execute the contract with transparent pricing. Track delivery and realize your optimized profit margins.",
    to: "/chat",
    visualizer: (
      <div className="h-24 bg-surface rounded-lg ring-1 ring-outline/10 p-4 flex items-center justify-center">
        <div className="flex flex-col items-center">
          <span className="font-label-mono text-label-mono text-on-surface-variant mb-1">
            NET_PROFIT_INC
          </span>
          <span className="font-display-hero text-headline-md text-primary">+₹4,250</span>
        </div>
      </div>
    ),
  },
];

export default function LandingPage() {
  const navigate = useNavigate();
  const { data: prices } = useQuery({ queryKey: ["prices"], queryFn: api.prices });
  const { data: trucks } = useQuery({ queryKey: ["trucks"], queryFn: api.trucks });

  const feed = (prices ?? []).slice(0, 2);
  const availableTrucks = (trucks ?? []).filter((t) => t.available_capacity_kg > 0).length;

  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="relative w-full pt-32 pb-24 px-container-padding overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] mix-blend-screen opacity-50"></div>
          <div className="absolute top-1/2 right-1/4 w-[400px] h-[400px] bg-secondary/10 rounded-full blur-[80px] mix-blend-screen opacity-50"></div>
        </div>
        <div className="max-w-7xl mx-auto relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column */}
          <div className="col-span-1 lg:col-span-7 flex flex-col gap-8">
            <div className="inline-flex items-center self-start px-3 py-1.5 rounded-full bg-tertiary/20 text-tertiary font-label-mono text-label-mono shadow-sm shadow-tertiary/10 ring-1 ring-tertiary/30">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary mr-2 animate-pulse"></span>
              AI-POWERED AGRICULTURAL LOGISTICS COPILOT
            </div>
            <h1 className="font-display-hero text-display-hero text-on-surface tracking-tighter">
              SELL SMARTER.
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary-fixed to-primary">
                MOVE TOGETHER.
              </span>
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl leading-relaxed">
              Pool loads, find return trucks, and maximize your mandi profits with
              AI. Join the digital agronomy revolution designed for high-pressure
              logistics.
            </p>
            <div className="flex flex-wrap items-center gap-6 mt-4">
              <button
                className="group relative inline-flex items-center justify-center px-8 py-4 font-label-mono text-label-mono font-bold text-surface bg-gradient-to-r from-secondary-fixed to-primary rounded-lg transition-transform hover:scale-105 overflow-hidden"
                onClick={() => navigate("/sell")}
              >
                <span className="relative flex items-center gap-2">
                  Try Unnati
                  <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">
                    arrow_forward
                  </span>
                </span>
                <span className="absolute -inset-1 bg-primary blur-md opacity-0 group-hover:opacity-30 transition-opacity pointer-events-none"></span>
              </button>
              <button
                className="relative inline-flex items-center justify-center px-8 py-4 font-label-mono text-label-mono font-bold text-primary bg-surface/60 backdrop-blur-md rounded-lg ring-1 ring-primary/20 hover:bg-surface/80 transition-colors shadow-sm shadow-primary/5"
                onClick={() => navigate("/chat")}
              >
                <span className="mr-2">⚡</span> Try Live Demo
              </button>
            </div>
          </div>
          {/* Right Column: Live market feed from seeded demo data */}
          <div className="col-span-1 lg:col-span-5 relative">
            <div className="relative w-full aspect-square max-h-[480px] rounded-2xl bg-surface-container/60 backdrop-blur-xl ring-1 ring-primary/15 shadow-xl shadow-surface-container-lowest overflow-hidden flex flex-col p-6">
              <div className="absolute inset-0 bg-[linear-gradient(rgba(110,231,183,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(110,231,183,0.03)_1px,transparent_1px)] [background-size:20px_20px]"></div>
              <div className="relative z-10 flex justify-between items-center mb-6">
                <span className="font-label-mono text-label-mono text-on-surface-variant">
                  LIVE_MARKET_FEED · DEMO DATA
                </span>
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-primary/40"></span>
                  <span className="w-2 h-2 rounded-full bg-primary/40"></span>
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                </div>
              </div>
              <div className="relative z-10 flex-1 flex flex-col gap-4" id="hero-data-feed">
                {feed.length === 0 && (
                  <div className="bg-surface/80 rounded-lg p-4 ring-1 ring-outline/20 font-label-mono text-label-mono text-on-surface-variant animate-pulse">
                    LOADING MARKET PRICES…
                  </div>
                )}
                {feed.map((p) => (
                  <div
                    key={`${p.mandi_id}-${p.crop}`}
                    className="bg-surface/80 rounded-lg p-4 ring-1 ring-outline/20 transform transition-all translate-y-0 opacity-100"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-data-lg text-primary text-sm uppercase">
                        {p.crop} @ {p.mandi}
                      </span>
                      <span className="font-label-mono text-tertiary text-[10px] bg-tertiary/10 px-2 py-0.5 rounded">
                        DEMO
                      </span>
                    </div>
                    <div className="flex justify-between items-end">
                      <span className="font-headline-md text-on-surface">
                        ₹{p.price_per_quintal.toLocaleString("en-IN")}/q
                      </span>
                      <span className="font-label-mono text-on-surface-variant text-[10px]">
                        {p.source}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="absolute bottom-4 right-4 p-3 bg-surface-container/90 backdrop-blur-md rounded-lg ring-1 ring-primary/30 flex items-center gap-3 shadow-lg shadow-black/50">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-[18px]">
                      local_shipping
                    </span>
                  </div>
                  <div>
                    <div className="font-label-mono text-on-surface-variant text-[10px]">
                      ACTIVE POOL
                    </div>
                    <div className="font-data-lg text-on-surface text-sm">
                      {availableTrucks} TRUCKS AVL
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Actions (mobile-first pattern) */}
      <section className="w-full pb-16 px-container-padding lg:hidden">
        <h3 className="font-headline-md text-headline-md text-on-surface flex items-center gap-2 mb-6">
          <span className="material-symbols-outlined text-primary">bolt</span> Quick Actions
        </h3>
        <div className="grid grid-cols-2 gap-card-gap">
          <button
            className="flex flex-col items-start gap-4 bg-gradient-to-br from-primary to-primary-container text-on-primary p-4 rounded-xl shadow-lg shadow-primary/20 active:scale-95 transition-transform"
            onClick={() => navigate("/sell")}
          >
            <span className="w-10 h-10 rounded-full bg-on-primary/10 flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary">local_shipping</span>
            </span>
            <span className="flex flex-col items-start text-left">
              <span className="font-bold text-lg">Sell Produce</span>
              <span className="text-xs opacity-90">Start pooling</span>
            </span>
          </button>
          <div className="flex flex-col gap-card-gap">
            {quickActions.map((action) => (
              <button
                key={action.title}
                className={`flex items-center gap-3 bg-surface-container/80 backdrop-blur-md border border-primary/15 text-on-surface p-3 rounded-xl active:bg-surface-container-high transition-colors ${
                  action.title === "AI Copilot"
                    ? "relative overflow-hidden"
                    : ""
                }`}
                onClick={() => navigate(action.to)}
              >
                {action.title === "AI Copilot" && (
                  <span className="absolute inset-0 bg-primary/5 animate-pulse pointer-events-none"></span>
                )}
                <span
                  className={`material-symbols-outlined relative z-10 ${
                    action.title === "AI Copilot" ? "text-secondary" : "text-tertiary"
                  }`}
                >
                  {action.icon}
                </span>
                <span className="flex flex-col items-start text-left relative z-10">
                  <span className="font-bold text-sm">{action.title}</span>
                  <span className="text-xs text-on-surface-variant">{action.subtitle}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="w-full py-12 px-container-padding bg-surface-container-low/50 border-t border-b border-primary/5">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { value: "₹12,000+", label: "Typical Gain/Month" },
            { value: "84%", label: "Truck Utilisation" },
            { value: "35%", label: "Cheaper Return Trips" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col items-center text-center p-6 bg-surface-container/30 rounded-xl ring-1 ring-primary/10 shadow-sm transition-transform hover:-translate-y-1 hover:bg-surface-container/50"
            >
              <span className="font-display-hero text-headline-lg text-primary mb-2">
                {stat.value}
              </span>
              <span className="font-label-mono text-label-mono text-on-surface-variant tracking-wider uppercase">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="w-full py-24 px-container-padding relative">
        <div className="max-w-7xl mx-auto flex flex-col gap-16">
          <div className="flex flex-col items-center text-center gap-4">
            <h2 className="font-headline-lg text-headline-lg text-on-surface">
              Precision Execution Pipeline
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-xl">
              Our AI aligns your harvest schedule with regional transport logistics
              to eliminate deadhead runs and maximize profit margins.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent -translate-y-1/2 z-0"></div>
            {steps.map((step) => (
              <div
                key={step.number}
                className="relative z-10 bg-[rgba(16,24,20,0.6)] backdrop-blur-xl rounded-2xl p-8 ring-1 ring-primary/15 shadow-xl shadow-surface-container-lowest flex flex-col gap-6 group hover:ring-primary/40 transition-colors cursor-pointer"
                onClick={() => navigate(step.to)}
              >
                <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center ring-1 ring-outline/20 group-hover:bg-primary/10 transition-colors">
                  <span className="font-data-lg text-primary">{step.number}</span>
                </div>
                <div className="flex flex-col gap-2">
                  <h3 className="font-headline-md text-headline-md text-on-surface text-xl">
                    {step.title}
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant text-sm">
                    {step.description}
                  </p>
                </div>
                {step.visualizer}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full py-24 px-container-padding flex justify-center">
        <div className="max-w-4xl w-full bg-surface-container-high/80 backdrop-blur-xl rounded-3xl p-12 ring-1 ring-primary/20 shadow-2xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/4 pointer-events-none"></div>
          <div className="flex flex-col gap-4 relative z-10 max-w-md">
            <h2 className="font-headline-lg text-headline-lg text-on-surface">
              Ready to optimize?
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Talk to our AI assistant to see how Unnati can route your next
              harvest for maximum return.
            </p>
          </div>
          <button
            className="relative z-10 flex-shrink-0 group inline-flex items-center justify-center px-8 py-4 bg-surface text-on-surface rounded-xl ring-1 ring-primary/30 hover:ring-primary/60 transition-all shadow-lg hover:shadow-primary/20 gap-3"
            onClick={() => navigate("/chat")}
          >
            <span className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center group-hover:bg-primary/40 transition-colors">
              <span className="material-symbols-outlined text-primary text-[18px]">
                smart_toy
              </span>
            </span>
            <span className="font-label-mono text-label-mono font-bold tracking-widest uppercase">
              Chat with AI
            </span>
          </button>
        </div>
      </section>
    </div>
  );
}
