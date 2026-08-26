# AGENTS.md — Unnati

## What this is
Unnati is an AI-powered agricultural logistics copilot for a hackathon MVP.
Farmers enter produce; deterministic engines compute pooling, transport,
spoilage and profit; the LLM only explains the result.

## Source of truth
`requirements.md` — the full build specification. Read it before changing
architecture or product behaviour.

## Commands

Backend (from `backend/`, Python 3.12+):

```powershell
..\.venv\Scripts\Activate.ps1        # or create: python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload         # seeds demo data on startup
python -m pytest tests -q             # 40 tests
```

Frontend (from `frontend/`, Node 18+):

```powershell
npm install
npm run dev                           # http://localhost:5173 (proxies /api -> :8000)
npm run build                         # typecheck + production build
```

## Non-negotiable rules

1. Never hard-code recommendation numbers — they must come from the engines.
2. The LLM never performs arithmetic or overrides constraints; it explains
   validated facts and must fail gracefully to `build_fallback_explanation`.
3. Never expose secrets to the frontend; keys live only in backend env.
4. Seeded prices/weather must stay clearly labelled as demo data in the UI.
5. Capacity/spoilage/route hard constraints are enforced before ranking.

## Golden scenario
Listing 1 (Ramesh, 800 kg tomato, Nangloi) must produce:
Azadpur baseline ≈ ₹37.6k net → Baraut via return truck T104 ≈ ₹49.9k net →
gain ≈ ₹12k, pool of 3 farmers at 2,100/2,500 kg. If this breaks, the demo is
broken — check `data/*.json` offsets and engine math first.
