import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/services/api";

/** Demo user — Ramesh Kumar, farmer #1 from the seeded golden scenario. */
const DEMO_FARMER_ID = 1;

const navItems = [
  { to: "/sell", label: "Sell Produce" },
  { to: "/network", label: "Network" },
  { to: "/chat", label: "Chat Demo" },
];

export default function Layout() {
  const navigate = useNavigate();
  const [bellOpen, setBellOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data: notifications } = useQuery({
    queryKey: ["notifications", DEMO_FARMER_ID],
    queryFn: () => api.notifications(DEMO_FARMER_ID),
    staleTime: 60_000,
  });
  const { data: farmers } = useQuery({
    queryKey: ["farmers"],
    queryFn: api.farmers,
    staleTime: 60_000,
  });
  const profile = farmers?.find((f) => f.id === DEMO_FARMER_ID);

  const resetDemo = useMutation({
    mutationFn: api.resetDemo,
    onSuccess: () => {
      // Demo reset wipes listings/pools/notifications — refresh everything.
      queryClient.invalidateQueries();
    },
  });
  const resetting = resetDemo.isPending;

  return (
    <div className="min-h-screen bg-background text-on-surface radial-glow">
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-xl border-b border-primary/10">
        <div className="h-20 w-full px-container-padding flex items-center justify-between max-w-7xl mx-auto">
          <button
            className="flex items-center gap-2 text-headline-md font-headline-md cursor-pointer"
            onClick={() => navigate("/")}
          >
            <img
              src="/unnati_logo.png"
              alt="Unnati logo"
              className="h-9 w-9 rounded-full object-cover"
            />
            <span className="wordmark tracking-tight">Unnati</span>
          </button>
          <nav className="hidden md:flex items-center gap-10">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `transition-colors duration-200 ${
                    isActive
                      ? "text-primary font-bold"
                      : "text-body-md text-on-surface-variant hover:text-primary"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-6">
            {/* Mobile menu button */}
            <button
              className="md:hidden flex items-center justify-center w-10 h-10 rounded-lg ring-1 ring-primary/20 text-on-surface hover:text-primary hover:ring-primary/50 transition-colors"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Menu"
            >
              <span className="material-symbols-outlined">
                {menuOpen ? "close" : "menu"}
              </span>
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                <nav className="absolute top-full left-0 right-0 z-50 bg-surface-container border-b border-primary/20 shadow-2xl shadow-black/60 flex flex-col p-2">
                  {[{ to: "/", label: "Home" }, ...navItems].map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={() => setMenuOpen(false)}
                      className={({ isActive }) =>
                        `px-4 py-3.5 rounded-lg transition-colors duration-200 ${
                          isActive
                            ? "text-primary font-bold bg-primary/10"
                            : "text-on-surface-variant hover:text-primary hover:bg-surface-container-high/60"
                        }`
                      }
                    >
                      {item.label}
                    </NavLink>
                  ))}
                </nav>
              </>
            )}
            <div className="relative flex items-center">
              <button
                className="relative flex items-center group"
                onClick={() => setBellOpen((o) => !o)}
                aria-label="Notifications"
              >
                <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary cursor-pointer">
                  notifications
                </span>
                {(notifications?.length ?? 0) > 0 && (
                  <span className="absolute -top-1 -right-1 bg-primary text-on-primary text-[10px] font-bold px-1.5 py-0.5 rounded-full ring-2 ring-background">
                    {notifications!.length}
                  </span>
                )}
              </button>
              {bellOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setBellOpen(false)} />
                  <div className="absolute right-0 top-9 z-50 w-80 max-h-96 overflow-y-auto bg-surface-container border border-primary/20 rounded-xl shadow-2xl shadow-black/60 p-3 flex flex-col gap-2">
                    <div className="font-label-mono text-label-mono text-on-surface-variant uppercase px-1 pb-1 border-b border-outline-variant/30">
                      Notifications
                    </div>
                    {(notifications ?? []).length === 0 && (
                      <div className="font-body-md text-sm text-on-surface-variant p-2">
                        No notifications yet.
                      </div>
                    )}
                    {(notifications ?? []).map((n) => (
                      <div key={n.id} className="p-3 rounded-lg bg-surface-container-high/60 hover:bg-surface-container-high transition-colors">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-bold text-on-surface">{n.title}</span>
                          <span className="font-label-mono text-[10px] text-on-surface-variant whitespace-nowrap">
                            {new Date(n.created_at).toLocaleString("en-IN", {
                              day: "numeric",
                              month: "short",
                              hour: "numeric",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        <div className="text-xs text-on-surface-variant mt-1">{n.message}</div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
            <div className="relative flex items-center">
              <button
                className={`w-8 h-8 rounded-full bg-primary flex items-center justify-center ring-1 transition-all hover:ring-primary/60 hover:scale-105 ${
                  profileOpen ? "ring-primary/70 scale-105" : "ring-primary/20"
                }`}
                onClick={() => setProfileOpen((o) => !o)}
                aria-label="Profile"
              >
                <span className="material-symbols-outlined text-on-primary text-[18px]">
                  person
                </span>
              </button>
              {profileOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
                  <div className="absolute right-0 top-11 z-50 w-80 max-h-96 overflow-y-auto bg-surface-container border border-primary/20 rounded-xl shadow-2xl shadow-black/60 p-4 flex flex-col gap-3">
                    <div className="flex items-center gap-3 pb-3 border-b border-outline-variant/30">
                      <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center ring-1 ring-primary/30">
                        <span className="material-symbols-outlined text-primary text-[24px]">
                          person
                        </span>
                      </div>
                      <div>
                        <div className="font-headline-md text-base text-on-surface">
                          {profile?.name ?? "Loading…"}
                        </div>
                        <div className="text-xs text-on-surface-variant">
                          {profile
                            ? `${profile.village}, ${profile.district}, ${profile.state}`
                            : "—"}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      <div className="font-label-mono text-[10px] text-on-surface-variant uppercase tracking-wider">
                        My Listings ({profile?.listings.length ?? 0})
                      </div>
                      {(profile?.listings ?? []).map((l) => (
                        <div
                          key={l.id}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container-high/60"
                        >
                          <div>
                            <span className="text-sm font-bold text-on-surface capitalize">
                              {l.crop}
                            </span>
                            <span className="text-xs text-on-surface-variant ml-2">
                              {Math.round(l.quantity_kg).toLocaleString("en-IN")} kg
                            </span>
                          </div>
                          <span className="font-label-mono text-[10px] uppercase px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                            {l.status.replace("_", " ")}
                          </span>
                        </div>
                      ))}
                      {(profile?.listings.length ?? 0) === 0 && (
                        <div className="text-xs text-on-surface-variant p-1">
                          No active listings.
                        </div>
                      )}
                    </div>

                    <button
                      className="mt-1 w-full inline-flex items-center justify-center gap-2 rounded-lg border border-primary/25 bg-primary/[0.06] px-4 py-2.5 font-mono text-[11px] font-semibold uppercase tracking-widest text-emerald-200 transition-colors hover:border-primary/50 hover:bg-primary/[0.12]"
                      onClick={() => {
                        resetDemo.mutate();
                        setProfileOpen(false);
                      }}
                      disabled={resetting}
                    >
                      <span className="material-symbols-outlined text-[16px]">
                        {resetting ? "progress_activity" : "restart_alt"}
                      </span>
                      {resetting ? "Resetting…" : "Reset Demo Data"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="w-full pt-20 min-h-screen">
        <Outlet />
      </main>

      <footer className="w-full bg-surface-container-lowest py-16 border-t border-outline-variant/10 mt-auto">
        <div className="max-w-7xl mx-auto px-container-padding flex flex-col md:flex-row justify-between gap-8 text-on-surface-variant text-body-md">
          <div>
            <div className="wordmark font-headline-md text-headline-md mb-4">
              Unnati
            </div>
            <p className="max-w-xs text-sm">
              Empowering the modern farmer with AI-driven market intelligence and
              logistics.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-12">
            <div className="flex flex-col gap-3">
              <span className="text-on-surface font-bold text-sm uppercase">
                Product
              </span>
              <button className="hover:text-primary text-left" onClick={() => navigate("/sell")}>
                Sell Produce
              </button>
              <button className="hover:text-primary text-left" onClick={() => navigate("/network")}>
                Network Snapshot
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <span className="text-on-surface font-bold text-sm uppercase">
                Support
              </span>
              <button className="hover:text-primary text-left" onClick={() => navigate("/chat")}>
                Chat Assistant
              </button>
            </div>
          </div>
          <div className="w-full mt-8 pt-8 border-t border-outline-variant/10 text-center text-sm opacity-50">
            © mewn
          </div>
        </div>
      </footer>
    </div>
  );
}
