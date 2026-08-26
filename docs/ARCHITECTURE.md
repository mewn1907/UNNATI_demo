# Unnati Architecture

## Flow (specification §53)

```
              FARMER INPUT  (web form / chat simulator)
                   ↓
             FASTAPI BACKEND
                   ↓
           MATCHING + CANDIDATES
                   ↓
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    PROFIT       TRANSPORT    SPOILAGE
       │            │            │
       └────────────┼────────────┘
                    ↓
              HARD CONSTRAINTS
                    ↓
              RANKING ENGINE
                    ↓
              BEST VALID PLAN
                    ↓
              LLM EXPLANATION   (fallback-safe)
                    ↓
              FARMER DECISION   (Join This Load)
```

**"AI explains the decision; deterministic engines protect its correctness."**

## Layers

### Engines (`backend/app/engines/`) — pure functions, no I/O
| Engine | Responsibility |
|---|---|
| `profit_engine` | revenue, spoilage loss, net profit, net gain |
| `transport_engine` | fixed + per-km cost, return-trip discount (~35%), pool-share split |
| `capacity_engine` | hard `total ≤ available` validation |
| `spoilage_engine` | shelf-life × harvest-age × temperature/humidity → risk level/score/window/loss % |
| `ranking_engine` | weighted score: net_gain 40% · pooling 20% · truck fit 15% · spoilage safety 15% · route efficiency 10% |

### Services (`backend/app/services/`)
- **matching_service** — compatible-listing discovery (same crop, ≤40 km,
  ≤24 h harvest gap), greedy pool assembly, truck-route candidate generation,
  hard-constraint filtering.
- **recommendation_service** — orchestrates baseline vs candidates, ranking,
  persistence (`recommendations`, `load_pools`), LLM explanation, join-pool
  transaction (member row, truck capacity decrement, notification).
- **llm_service** — OpenAI-compatible chat client. Two jobs: structured
  explanation (Pydantic-validated) and free-text field extraction for chat.
  Every path degrades to deterministic fallbacks.
- **chat_service** — WhatsApp-style state machine: extraction (LLM → Hinglish
  rule fallback) → one-question-at-a-time slot filling → recommendation →
  join/alternatives controls.
- **weather_service** — live provider when configured, seeded demo otherwise.
- **notification_service** — WebNotificationProvider (WhatsAppProvider swap
  point for the future).

## Data model
11 tables per specification §9: farmers, crops, farmer_listings, trucks,
truck_routes (empty-return flags), mandis, mandi_prices, load_pools,
pool_members, recommendations, notifications.

## Why the golden scenario is robust
Seed departures are anchored **relative to seeding time**, so the demo
produces identical economics whether a judge launches it at 10 AM or 11 PM:
golden trio harvested ~8 h ago, truck T104 departs ~4 h later, arrival ≈ 14.5 h
post-harvest — MEDIUM spoilage risk and ≈ ₹12k gain every run.

## Security posture
- Keys only in `.env` (gitignored); frontend receives zero secrets.
- CORS restricted to `CORS_ORIGINS`.
- All API input validated via Pydantic; errors return `{error:{code,message}}`
  envelopes — stack traces never reach users.
- No phone-number logging in the request path.

## Performance
Recommendation pipeline measured at ~50–130 ms on SQLite with the full seed;
LLM adds network latency but is wrapped by `LLM_TIMEOUT_SECONDS=30`.
