# Unnati — Project Handoff Brief

Give this entire document to an AI assistant before asking questions about the project.

---

## 1. What Unnati Is

Unnati is an **AI-powered agricultural logistics copilot** built as a hackathon MVP.
Pitch: *"I tell Unnati what I harvested. It tells me what to do."*

A farmer enters produce details; **deterministic Python engines** compute pooling,
transport cost, spoilage risk, and net profit across nearby mandis (markets); the
**LLM only explains** the validated result in plain language. The core answer is:
"Which mandi should I sell at, with which truck, pooled with whom — and how much
more will I earn?"

**Source of truth:** `requirements.md` (~3,600 lines). `AGENTS.md` condenses rules.

### Non-negotiable rules (from AGENTS.md)
1. Recommendation numbers are NEVER hard-coded — they must come from engines.
2. The LLM never does arithmetic or overrides constraints; it explains validated facts and must fail gracefully to `build_fallback_explanation`.
3. Secrets live only in backend env, never exposed to frontend.
4. Seeded prices/weather are always labelled demo data in UI/API (`source: seeded_demo`, labels attached).
5. Capacity/spoilage/route hard constraints are enforced BEFORE ranking.

---

## 2. Architecture & Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2, Python 3.12. SQLite by default (`backend/Unnati.db`), optional MySQL/PostgreSQL via `DATABASE_URL`. Runs on port 8000; seeds demo data on startup when `DEMO_MODE=true`.
- **Frontend**: React 18 + TypeScript + Vite + Tailwind + TanStack Query + React Router + Leaflet maps + Recharts. Dev server 5173 proxies `/api → :8000`. Build = `tsc && vite build`.
- **Single-service deploy**: backend serves the built frontend from `frontend/dist` with SPA fallback (deployed on Render via `render.yaml`; free plan; build = pip install + npm build).
- **LLM**: any OpenAI-compatible API; default OpenRouter (`openrouter/auto`, temp 0.2). Key via env (`LLM_API_KEY` / legacy `OPENROUTER_API_KEY`). Bundled key is expired → app runs in rule-based fallback mode, which is fully functional.
- **Weather**: open-meteo live fetch optional (`WEATHER_ENABLED=false`); falls back to seeded regional data (Delhi 31°C/62%, Haryana 32°C/58%, UP 33°C/60%).

```
backend/app/
  main.py                  app factory, startup seeding, error envelope, SPA serving
  api/                     13 routers (health, crops, farmers, listings, trucks, mandis,
                           matching, recommendations, pools, weather, notifications, demo, chat)
  engines/                 PURE deterministic math, no DB/LLM:
                           transport_engine, capacity_engine, spoilage_engine,
                           profit_engine, ranking_engine
  services/                matching_service, recommendation_service (orchestration),
                           llm_service, chat_service, weather_service, notification_service
  models/                  11 SQLAlchemy models
  schemas/                 Pydantic: listing.py, recommendation.py, chat.py
  db/                      database.py, base.py, seed.py (loads data/*.json)
  core/config.py           pydantic-settings knobs
  utils/                   geo.py (haversine), time.py
data/                      crops.json, farmers.json, mandis.json, trucks.json, weather.json
frontend/src/
  pages/                   LandingPage, SellPage, AnalysisPage, RecommendationPage,
                           NetworkPage, ChatPage (+7 static HTML design mockups)
  components/Layout.tsx    header/nav/footer shell, notifications bell, profile, reset-demo
  services/api.ts          typed fetch client, ApiError carries backend code+suggestions
tests/ (backend/tests)     ~40 pytest tests across api/capacity/llm/matching/profit/
                           recommendation/spoilage/transport
```

---

## 3. Engine Formulas (exact)

### Transport (`transport_engine.py`)
- `base_cost = ₹500 fixed + distance_km × ₹18/km`
- Return-trip discount: `effective_total = base_cost × (1 − 0.35)` (35% off)
- Pool share: `farmer_share = effective_total × farmer_qty / pool_qty`

### Profit (`profit_engine.py`)
- `sellable_qty = qty × (1 − spoilage%)`, `gross_revenue = sellable_qty × price`
- `spoilage_loss = qty × spoilage% × price`
- **`net_profit = gross_revenue − transport_cost`**
- `net_gain = recommended_net_profit − baseline_net_profit`

### Spoilage (`spoilage_engine.py`)
- Reference: 25°C / 60% RH. Aging factor `= 1 + max(0,T−25)×crop_sensitivity + 0.15×((H−60)/100)`, clamped [0.5, 4.0].
- `effective_age = real_age_hours × factor`; `life_used = effective_age/shelf_life` (clamped 0–1.6)
- **loss_pct = clamp((life_used − 0.5) × 40, 0, 60)** — loss starts after half of shelf life consumed
- Risk score = life_used×100; levels <25 LOW, <50 MEDIUM, <75 HIGH, else CRITICAL
- Crop params (shelf_life_h / temp sensitivity): Tomato 40h/0.06, Potato 720h/0.01, Onion 480h/0.01, Cabbage 96h/0.05, Cauliflower 72h/0.05, Mango 120h/0.07, Banana 84h/0.07, Apple 240h/0.03, Wheat/Rice 8760h/0.002

### Ranking (`ranking_engine.py`)
Weights: **net_gain 0.40, pooling_benefit 0.20, truck_compatibility 0.15, spoilage_safety 0.15, route_efficiency 0.10**. Min-max normalization per component across candidates (0–100). Truck score = `clamp(100×(1−|util−0.85|/0.85)) × 0.85 + 15 if return_trip`. Ideal utilization = 85%.

### Matching constraints (`matching_service.py`)
- Road km = haversine × 1.25; travel time at 30 km/h avg speed.
- Compatible farmers: same crop, ≥50 kg, harvest-time diff ≤24 h, within 40 km radius; greedy nearest-first pool fill up to truck capacity (target always included).
- Hard constraints applied per candidate (marked invalid with reason, never ranked):
  - no positive price at destination mandi;
  - farmer >80 km from truck route origin;
  - solo load exceeds truck capacity;
  - departure after spoilage window closes;
  - estimated spoilage loss at arrival ≥60%.
- Baseline = nearest priced mandi, solo transport (no discount), full cost on farmer.

---

## 4. Golden Scenario (demo-critical)

Listing 1 = Ramesh Kumar, Nangloi, 800 kg tomato harvested ~8h ago.

| | Sell normally (baseline) | With Unnati (recommended) |
|---|---|---|
| Mandi | Azadpur (₹48/kg) | Baraut (₹63/kg) |
| Truck | solo, 13.8 km | **T104** "HR-26-T-1044", return trip, 72 km |
| Pool | none | 3 farmers: Ramesh 800 + Suresh Yadav/Mundka 700 + Amit Chauhan/Bawana 600 = **2,100 / 2,500 kg (84%)** |
| Net profit | **₹37,652** | **₹49,955** |
| Gain | — | **+₹12,304**, score ≈92 |

If this breaks, check `data/*.json` offsets and engine math first. Test asserts T104, return trip, pool of 3 @2100 kg, gain >₹8,000.

Seed data highlights: 6 mandis (Azadpur #1, Baraut #2, Rohtak #3, Panipat #4, Meerut #5, Hapur #6) with full price matrix for 10 crops; 12 trucks / 8 routes (T103→Rohtak 1800kg non-return, T201→Hapur 2200kg, etc.); tomato prices Azadpur 48 → Baraut 63 → Rohtak 58 → Panipat 56 → Meerut 54 → Hapur 52.

---

## 5. API Surface (all under `/api`)

- `GET /health`, `POST /demo/reset` (403 unless DEMO_MODE)
- `GET /crops`; `POST /listings` (farmer pinned to id 1; available_until = harvest+3d); `GET /listings/{id}`
- `GET /farmers[/{id}]`; `GET /trucks[/{id}]`; `GET /mandis`, `/mandis/prices` (adds quintal price + demo label)
- `POST /matching/candidates` — transparency endpoint: all candidates incl. invalid + rejection_reason
- `POST /recommendations {listing_id}` → full response: baseline, recommended, ≤2 alternatives, net_gain, spoilage info, score, LLM explanation, `llm_powered` flag, `data_labels` (demo notices), `map_points`, `calculation_ms`. Errors: 404 NOT_FOUND / NO_VALID_MATCH (+suggestions), 500 INTERNAL_ERROR.
- `GET /recommendations/latest/{listing_id}`
- `POST /pools/{pool_id}/join {listing_id}` — adds member, decrements truck capacity (floor 0), sets pool CONFIRMED + listing POOLED, creates POOL_CONFIRMED notification
- `GET /weather?latitude&longitude&state`; `GET /notifications/{farmer_id}` (≤30)
- `POST /chat {session_id?, text}` → WhatsApp-style conversational flow

Error envelope everywhere: `{error:{code,message}}`.

### Chat flow (chat_service.py)
In-memory sessions. Field extraction: LLM first (if enabled), else rule-based Hinglish parser (crop synonyms like tamatar/aalu/pyaz; quintal ×100, tonne ×1000; village/location matching against seed data; harvest phrases like aaj/kal/"in 3 din"). Asks one missing field at a time → creates listing → runs the SAME recommendation engine → formats reply with quick replies (1-Join / 2-Other options / Start over).

### LLM guardrails (llm_service.py)
System prompt mandates JSON `{headline, summary, why_this_option[], action, urgency, warnings[]}` using ONLY supplied facts, preserving numbers exactly, never inventing entities or recalculating. Any failure (network, bad JSON, schema violation) → deterministic `build_fallback_explanation` template with identical facts. Response includes honest `llm_powered` flag.

---

## 6. Frontend Flow & Pages

Route flow: `/` Landing → `/sell` form → `/analysis/:id` (animated 5-step pipeline while POSTing recommendation) → `/recommendation/:id` (hero screen) → Join Load → confirmation card + notification.

- **LandingPage**: hero, LIVE_MARKET_FEED demo panel (prices+trucks queries), stats strip, CTAs.
- **SellPage**: crop select, quantity ≥50 kg, freshness bucket → back-computed harvested_at, pickup hub chips (Nangloi/Mundka/Bawana/Kharkhoda hardcoded coords), radius slider 10–80 km.
- **AnalysisPage**: fires recommend once (StrictMode-guarded), timer-driven checklist animation, then navigates.
- **RecommendationPage**: giant net_gain figure, JOIN THIS LOAD CTA, utilization bar, ticking spoilage countdown, data-labels chips verbatim, before/after economics cards, ranked mandis, AI reasoning card (shows "(offline mode)" when llm_powered=false), pool composition list.
- **NetworkPage**: dashboard — stat cards, crop-switchable CSS bar chart of prices, sortable trucks list (return trips highlighted), farmer listings table.
- **ChatPage**: phone-frame WhatsApp simulator; server-driven quick replies; inline link to recommendation; join action.
- **Layout.tsx**: header nav, notification bell (farmer id=1), profile dropdown with listings + Reset Demo Data button, footer with "© mewn". Brand logo `public/unnati_logo.png` used in navbar, favicon, and chat avatars.
- State: TanStack Query (retry 1, staleTime 30s); imperative fetch where sequencing matters. Tailwind dark theme: neon mint #4EDEA3 primary, Space Grotesk headlines, JetBrains Mono data font.

---

## 7. Tests (all 40 pass)

Golden test asserts listing 1 ⇒ T104 return trip, pool of 3 @2100 kg, baseline Azadpur, gain >₹8,000, explanation present with "seeded" warning. Others cover: capacity edge cases, transport math/discount/split, spoilage aging vs temperature, profit validation, LLM fallback on network/bad-JSON/schema failure, extraction sanitization, full API journey (create→recommend→join→notification), chat parsing, 404/validation errors. conftest isolates env (LLM off, DEMO_MODE on, temp SQLite).

---

## 8. Deployment & Ops

- Render (`render.yaml`): python runtime web service, free plan, health check `/api/health`, build = pip install + frontend npm build, start = uvicorn from backend/. Env: PYTHON_VERSION 3.12, NODE_VERSION 20, sqlite DATABASE_URL, DEMO_MODE true, OPENROUTER_API_KEY sync:false.
- Local: `.venv`, `uvicorn app.main:app --reload` seeds demo data; `python -m pytest tests -q`; frontend `npm run dev` / `npm run build`.
- Re-seed anytime via `POST /api/demo/reset`.

## 9. Known Quirks

- Bundled OpenRouter key expired (HTTP 401) → explanations run in offline/rule-based mode by design; still correct.
- Static HTML mockups in `frontend/src/pages/*.html` are design comps only, not routed.
- Chat sessions are in-memory (lost on restart) — acceptable for demo.
- `@app.on_event("startup")` deprecation warnings in tests are cosmetic.
