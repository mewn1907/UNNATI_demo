# Unnati 🌾

**AI-powered agricultural logistics copilot — hackathon MVP.**

> *"I tell Unnati what I harvested. It tells me what to do."*

Unnati tells a farmer **where to sell, who to pool with, which truck to
use, how much they can gain, and how urgently they need to move the produce.**

---

## The 30-second demo

| | |
|---|---|
| **Sell normally** (Azadpur, solo truck) | ₹37,652 net |
| **Unnati** (pool 3 farmers · return truck T104 · Baraut) | ₹49,955 net |
| **You gain** | **+₹12,304** |

Every number above is computed live by deterministic Python engines from seeded
demo data — nothing is hard-coded.

## Quick start

### Backend (Python 3.12+, from `backend/`)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload        # seeds demo data on startup
```

- API: http://localhost:8000 · Docs: http://localhost:8000/docs
- Tests: `python -m pytest tests -q` (40 tests)

### Frontend (Node 18+, from `frontend/`)

```powershell
npm install
npm run dev                          # http://localhost:5173  (proxies /api → :8000)
```

Optional PostgreSQL instead of SQLite: `docker compose up -d db`, then set
`DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/Unnati`
in `backend/.env`. Re-seed anytime with `POST /api/demo/reset`.

## What's inside

```text
backend/app/
├── engines/      profit · transport · capacity · spoilage · ranking   ← all money math
├── services/     matching · recommendation · llm · weather · chat · notifications
├── api/          health crops farmers listings trucks mandis matching
│                 recommendations pools weather notifications demo chat
└── db/           SQLAlchemy models + idempotent golden-scenario seeder

frontend/src/
├── pages/        Landing · Sell form · Analysis · Recommendation hero ·
│                 WhatsApp-style chat · Network overview
└── components/   SpoilageClock GainComparison PoolCard TruckCard
                  MandiComparison AISummary RouteMap(Leaflet + fallback) …
data/             crops farmers mandis trucks weather (seeded demo data)
```

## Architecture in one line

```
Farmer input → FastAPI → Matching engine → Profit/Transport/Spoilage engines
→ Hard constraints → Ranking → Best valid plan → LLM explanation (fallback-safe)
→ Farmer decision (Join This Load)
```

**The LLM never calculates anything.** It receives validated facts and explains
them in farmer-friendly language. If the LLM is disabled, unreachable, or
returns garbage, a deterministic fallback explanation is used automatically —
the demo never breaks and never fakes success.

## AI configuration (`backend/.env`, see `.env.example` at repo root)

```env
LLM_ENABLED=true
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-...            # any OpenAI-compatible endpoint works
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openrouter/auto
```

> ⚠️ Note: the OpenRouter key bundled in this workspace's `.env` returns
> HTTP 401 ("User not found") — it appears expired/revoked. The app still runs
> perfectly using rule-based explanations; supply your own key for LLM text.

## Honest-data policy

- Mandi prices: `Demo price · seeded prototype data` labels everywhere.
- Weather: optional live API, else `Demo weather` seeded values.
- Chat page is labelled a *WhatsApp-style demo simulator*; production WhatsApp
  integration is intentionally future work (provider-swap architecture).

## Demo script (60 seconds)

1. Landing → click **⚡ TRY LIVE DEMO**
2. Watch the analysis pipeline light up
3. Hero shows **+₹12,304 estimated net gain** — before/after comparison below
4. Point out: pool card (2,100/2,500 kg), 🔁 RETURN TRIP badge, mandi table
   (“price ≠ profit”), spoilage clock, AI explanation, route map
5. Click **JOIN THIS LOAD** → confirmation + notification 🔔
6. Open **WhatsApp-style Demo** → type *"I have 800 kg tomato ready today"*
   → recommendation in chat → reply **1** to join

See `docs/DEMO_SCRIPT.md` for the judge-facing walkthrough.
