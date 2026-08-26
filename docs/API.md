# Unnati API

Interactive docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.

All errors use the envelope:

```json
{ "error": { "code": "NO_VALID_MATCH", "message": "…", "suggestions": ["…"] } }
```

Codes: `INVALID_INPUT`, `NO_COMPATIBLE_FARMERS`, `NO_AVAILABLE_TRUCK`,
`NO_VALID_ROUTE`, `NO_VALID_MANDI`, `NO_VALID_MATCH`, `WEATHER_UNAVAILABLE`,
`LLM_UNAVAILABLE` (internal only — users see fallback text), `INTERNAL_ERROR`,
`NOT_FOUND`, `FORBIDDEN`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness |
| GET | `/api/crops` | supported crops + shelf-life params |
| POST | `/api/farmers` | register farmer |
| GET | `/api/farmers` · `/api/farmers/{id}` | network view / details |
| POST | `/api/listings` | create produce listing (crop, qty, lat/lng, harvested_at) |
| GET | `/api/listings/{id}` | listing details |
| GET | `/api/trucks` · `/api/trucks/{id}` | trucks with routes & return flags |
| GET | `/api/mandis` | mandi directory |
| GET | `/api/mandis/prices` | full seeded price grid (labelled demo) |
| GET | `/api/mandis/{id}/prices` | one mandi's prices |
| POST | `/api/matching/candidates` | transparent raw candidates for a listing |
| POST | `/api/recommendations` | **core**: full pipeline → best plan + explanation |
| GET | `/api/recommendations/latest/{listing_id}` | recompute/return latest |
| POST | `/api/pools/{pool_id}/join` | join pooled load (confirms pool, updates truck, notifies) |
| GET | `/api/weather?lat&lng&state` | conditions used by spoilage engine (labelled) |
| GET | `/api/notifications/{farmer_id}` | recent notifications |
| POST | `/api/demo/reset` | reseed golden scenario (DEMO_MODE only) |
| POST | `/api/chat` | WhatsApp-style conversational turn |

## Recommendation response shape (abridged)

```json
{
  "recommendation_id": "REC-1001",
  "pool_id": 7,
  "baseline":   { "mandi_name": "Azadpur Mandi", "net_profit": 37652, "...": "..." },
  "recommended": {
    "mandi_name": "Baraut Mandi", "truck_id": "T104",
    "is_return_trip": true, "net_profit": 49955,
    "pool": { "farmer_count": 3, "total_quantity_kg": 2100,
               "remaining_capacity_kg": 400, "utilization_percent": 84,
               "members": [ { "farmer_name": "Ramesh Kumar", "quantity_kg": 800 } ] }
  },
  "alternatives": [ { "mandi_name": "Rohtak Mandi", "net_profit": 43996, "...": "..." } ],
  "net_gain": 12304,
  "spoilage": { "risk_level": "MEDIUM", "hours_remaining": 14.85 },
  "score": 92.26,
  "explanation": { "headline": "…", "summary": "…", "why_this_option": ["…"],
                    "action": "…", "urgency": "…", "warnings": ["…"] },
  "llm_powered": false,
  "map_points": { "farmer": { }, "truck_origin": { }, "recommended_mandi": { } }
}
```

## Chat example

```bash
POST /api/chat
{ "session_id": "abc123", "text": "I have 800 kg tomato ready today from Nangloi" }

→ { "reply": { "text": "Got it! 🍅 …🏆 Best option for you: Sell at Baraut Mandi…
      Reply 1️⃣ Join this load or 2️⃣ Other options.",
      "quick_replies": [ {"label":"1 - Join load","value":"1"} ] } }

POST /api/chat  { "session_id": "abc123", "text": "1" }
→ "✅ Load confirmed! … 🚚 Truck T104 …"
```
