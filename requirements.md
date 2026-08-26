# Unnati — Hackathon Build Specification

> **Hackathon-first master specification for OpenCode / AI coding agents**
>
> Build a polished, believable, end-to-end MVP that demonstrates one powerful idea:
>
> **Unnati tells a farmer where to sell, who to pool with, which truck to use, how much they can gain, and how urgently they need to move the produce.**

---

# 1. THE ONE-LINE PITCH

**Unnati is an AI-powered agricultural logistics copilot that combines nearby farmer pooling, empty-return truck matching, mandi price comparison, deterministic profit calculation, and spoilage-aware recommendations to help farmers maximize their net earnings.**

The product should feel like:

> **“I tell Unnati what I harvested. It tells me what to do.”**

---

# 2. THE HACKATHON NORTH STAR

The entire product is designed around one 30-second question:

> **“What should this farmer do right now?”**

The answer must appear clearly on the screen:

```text
SELLING YOUR TOMATOES AT MANDI A
₹37,800 expected net

Unnati RECOMMENDS
Pool with 2 farmers
Use return truck T104
Sell at Mandi B

₹49,850 expected net

YOU GAIN
+₹12,050
```

Then:

```text
SPOILAGE WINDOW
18h 42m remaining
HIGH RISK
```

And:

```text
WHY?
Mandi B gives a better net return,
the truck is already returning toward your region,
and pooling reduces your transport share.
```

This is the **wow moment**.

---

# 3. HACKATHON PRIORITY ORDER

If time becomes limited, implement in this order:

```text
P0 — MUST WORK
│
├── Farmer input
├── Matching engine
├── Truck capacity
├── Mandi comparison
├── Profit calculation
├── Spoilage calculation
├── Recommendation
└── Before/after ₹ gain screen

P1 — STRONGLY RECOMMENDED
│
├── AI explanation
├── Farmer pooling
├── Return-trip truck
├── Map
└── Join-load interaction

P2 — POLISH
│
├── Notifications
├── Animations
├── Demo mode
├── Multi-language UI
└── Responsive/mobile polish

P3 — FUTURE
│
├── WhatsApp production integration
├── Live e-NAM
├── Real GPS
├── Payments
├── Authentication
└── Advanced ML
```

**Do not sacrifice P0 features to build P3 features.**

---

# 4. PRODUCT PRINCIPLES

## Principle 1 — Deterministic facts, AI explanation

The backend calculates:

- price
- revenue
- transport
- capacity
- spoilage estimate
- net gain
- route compatibility
- farmer compatibility

The LLM explains:

- why the option is recommended
- what the farmer should do
- urgency
- trade-offs
- simple-language summary

The LLM must never be the source of truth for calculations.

---

## Principle 2 — The farmer should not need logistics knowledge

Avoid technical language such as:

```text
optimization score
candidate ranking
constraint satisfaction
weighted objective
```

Instead show:

```text
Best option for you
You can earn ₹12,050 more
Truck already returning
2 nearby farmers can share the load
18 hours before estimated spoilage window
```

---

## Principle 3 — One recommendation beats ten confusing choices

The system can internally evaluate many options.

The farmer should primarily see:

```text
BEST OPTION
```

Then optionally:

```text
See 2 other options
```

---

## Principle 4 — Never fake live data

Seeded mandi prices are acceptable for a hackathon.

But clearly label:

```text
Demo / seeded market data
```

Never claim:

```text
Live e-NAM price
```

unless a real verified source is connected.

---

# 5. CORE USER STORY

A farmer has:

```text
Crop: Tomato
Quantity: 800 kg
Location: Delhi NCR
Harvested: Today 6:00 AM
```

Unnati should:

```text
1. Find compatible nearby farmers.

2. Find trucks with available capacity.

3. Prefer empty-return trips when possible.

4. Find viable mandis.

5. Calculate transport costs.

6. Estimate spoilage risk.

7. Calculate expected net earnings.

8. Compare against the baseline option.

9. Select the best valid option.

10. Ask the LLM to explain the result.

11. Show the farmer one clear recommendation.

12. Let the farmer join the load.
```

---

# 6. PRODUCT ARCHITECTURE

```text
                 ┌─────────────────────┐
                 │       FARMER        │
                 │ Web / Future WhatsApp│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      WEB APP        │
                 │ React + TypeScript  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       FASTAPI       │
                 │     Backend API     │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         Farmer Data    Truck Data    Mandi Data
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                 ┌─────────────────────┐
                 │  MATCHING ENGINE    │
                 │ Farmers + Trucks    │
                 │ Routes + Mandis     │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ CANDIDATE OPTIONS   │
                 └──────────┬──────────┘
                            ▼
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   PROFIT ENGINE      TRANSPORT ENGINE    SPOILAGE ENGINE
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                 ┌─────────────────────┐
                 │ CAPACITY + RULES    │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ RANKING ENGINE     │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ BEST VALID OPTION  │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │     LLM SERVICE     │
                 │ Explanation only    │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ RECOMMENDATION API  │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ FARMER DASHBOARD    │
                 └─────────────────────┘
```

---

# 7. RECOMMENDED TECH STACK

## Frontend

Use:

- React
- Vite
- TypeScript
- Tailwind CSS
- React Router
- TanStack Query
- Recharts
- Leaflet
- OpenStreetMap

The UI should feel modern and premium.

Do not create a generic Bootstrap-style dashboard.

---

## Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

SQLite can be supported for extremely simple local development, but PostgreSQL should be the primary database.

---

## AI

Use an OpenAI-compatible API abstraction.

The preferred configuration is:

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
```

The exact free model must remain configurable.

Never hard-code one model.

The system must work even when:

```env
LLM_ENABLED=false
```

---

## Weather

Weather should be an optional enrichment.

Architecture:

```text
Weather API
    ↓
Weather Service
    ↓
Spoilage Engine
```

Fallback:

```text
Weather API unavailable
        ↓
Seeded weather
        ↓
Spoilage Engine
```

The hackathon demo must not fail because the weather API is unavailable.

---

# 8. REPOSITORY STRUCTURE

```text
Unnati/
│
├── README.md
├── Unnati_HACKATHON.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── base.py
│   │   │   └── seed.py
│   │
│   │   ├── models/
│   │   │   ├── farmer.py
│   │   │   ├── crop.py
│   │   │   ├── farmer_listing.py
│   │   │   ├── truck.py
│   │   │   ├── truck_route.py
│   │   │   ├── mandi.py
│   │   │   ├── mandi_price.py
│   │   │   ├── load_pool.py
│   │   │   ├── pool_member.py
│   │   │   ├── recommendation.py
│   │   │   └── notification.py
│   │
│   │   ├── schemas/
│   │   │   ├── farmer.py
│   │   │   ├── listing.py
│   │   │   ├── matching.py
│   │   │   ├── recommendation.py
│   │   │   └── notification.py
│   │
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── farmers.py
│   │   │   ├── listings.py
│   │   │   ├── trucks.py
│   │   │   ├── mandis.py
│   │   │   ├── matching.py
│   │   │   ├── recommendations.py
│   │   │   ├── weather.py
│   │   │   └── notifications.py
│   │
│   │   ├── services/
│   │   │   ├── matching_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── weather_service.py
│   │   │   ├── llm_service.py
│   │   │   └── notification_service.py
│   │
│   │   ├── engines/
│   │   │   ├── profit_engine.py
│   │   │   ├── transport_engine.py
│   │   │   ├── spoilage_engine.py
│   │   │   ├── capacity_engine.py
│   │   │   └── ranking_engine.py
│   │
│   │   └── utils/
│   │       ├── geo.py
│   │       └── time.py
│   │
│   └── tests/
│       ├── test_profit.py
│       ├── test_transport.py
│       ├── test_spoilage.py
│       ├── test_capacity.py
│       ├── test_matching.py
│       ├── test_recommendation.py
│       └── test_api.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── data/
│   ├── crops.json
│   ├── farmers.json
│   ├── listings.json
│   ├── trucks.json
│   ├── truck_routes.json
│   ├── mandis.json
│   ├── mandi_prices.json
│   └── weather.json
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEMO_SCRIPT.md
```

---

# 9. DATABASE

## 9.1 Farmer

```text
farmers

id
name
phone
village
district
state
latitude
longitude
created_at
```

---

## 9.2 Crop

```text
crops

id
name
category
unit
baseline_shelf_life_hours
temperature_sensitivity
```

Initial crops:

```text
Tomato
Potato
Onion
Cabbage
Cauliflower
Mango
Banana
Apple
Wheat
Rice
```

---

## 9.3 Farmer Listing

```text
farmer_listings

id
farmer_id
crop_id
quantity_kg
harvested_at
available_until
latitude
longitude
status
created_at
```

Statuses:

```text
AVAILABLE
POOLED
SOLD
EXPIRED
CANCELLED
```

---

## 9.4 Truck

```text
trucks

id
registration_number
capacity_kg
current_latitude
current_longitude
available_capacity_kg
status
```

Statuses:

```text
AVAILABLE
IN_TRANSIT
FULL
UNAVAILABLE
```

---

## 9.5 Truck Route

```text
truck_routes

id
truck_id
origin_name
origin_latitude
origin_longitude
destination_mandi_id
departure_at
estimated_arrival_at
return_available
return_origin_mandi_id
return_destination_region
distance_km
estimated_cost
```

This table enables the key:

> **empty-return trip matching**

---

## 9.6 Mandi

```text
mandis

id
name
city
district
state
latitude
longitude
```

---

## 9.7 Mandi Price

```text
mandi_prices

id
mandi_id
crop_id
price_per_kg
recorded_at
source
confidence
```

For demo:

```text
source = seeded_demo
```

---

## 9.8 Load Pool

```text
load_pools

id
truck_id
destination_mandi_id
total_quantity_kg
status
departure_at
created_at
```

Statuses:

```text
OPEN
CONFIRMED
DEPARTED
COMPLETED
CANCELLED
```

---

## 9.9 Pool Member

```text
pool_members

id
pool_id
farmer_listing_id
quantity_kg
transport_share
expected_profit
```

---

## 9.10 Recommendation

```text
recommendations

id
farmer_listing_id
baseline_mandi_id
recommended_mandi_id
truck_id
pool_id
baseline_profit
recommended_profit
transport_cost
spoilage_loss
net_gain
score
reasoning
created_at
```

---

## 9.11 Notification

```text
notifications

id
farmer_id
type
title
message
scheduled_for
sent_at
status
```

---

# 10. INPUT FLOW

The primary request:

```json
{
  "crop": "Tomato",
  "quantity_kg": 800,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "harvested_at": "2026-08-24T06:00:00",
  "preferred_radius_km": 40,
  "language": "en"
}
```

The farmer does not manually enter:

- mandi prices
- transport cost
- truck capacity
- spoilage percentage

The backend determines these.

---

# 11. MATCHING ENGINE

The matching engine should answer:

> **Who can I pool with, which truck can carry us, and where should we go?**

A candidate contains:

```json
{
  "farmer_ids": [1, 8, 13],
  "truck_id": "T104",
  "destination_mandi_id": 4,
  "total_quantity_kg": 2100,
  "truck_capacity_kg": 2500,
  "remaining_capacity_kg": 400
}
```

---

# 12. FARMER MATCHING

Two listings are compatible when:

```text
crop compatible
AND
distance <= max_pool_radius
AND
harvest time difference <= max_harvest_difference
AND
both can reach the truck before departure
```

Default:

```text
MAX_POOL_RADIUS_KM=40
MAX_HARVEST_TIME_DIFF_HOURS=24
```

These must be configurable.

---

# 13. EMPTY-RETURN TRUCK MATCHING

This is one of the strongest differentiators.

Prefer trucks where:

```text
return_available = true
```

Example:

```text
Truck T104

Current trip:
Mandi A → Delhi NCR

Return trip:
Mandi A → Delhi NCR

Available return capacity:
2,500 kg
```

If compatible farmers are near the return corridor, Unnati should consider this truck.

The UI should explicitly say:

```text
RETURNING EMPTY
```

or:

```text
RETURN TRIP AVAILABLE
```

This makes the concept immediately understandable to judges.

---

# 14. MANDI SELECTION

Generate 3–5 candidate mandis.

A mandi becomes a candidate when:

```text
price exists
AND
route is feasible
AND
transport cost is calculable
```

A farther mandi can still win if its net gain is sufficiently higher.

The system must optimize:

```text
NET VALUE
```

not:

```text
HIGHEST RAW PRICE
```

---

# 15. PROFIT ENGINE

Create:

```python
calculate_profit(...)
```

Inputs:

```text
quantity_kg
price_per_kg
transport_cost
spoilage_percentage
```

Calculate:

```text
sellable_quantity =
    quantity_kg * (1 - spoilage_percentage)

expected_revenue =
    sellable_quantity * price_per_kg

net_profit =
    expected_revenue - transport_cost
```

Baseline:

```text
baseline_net_profit
```

Recommendation:

```text
recommended_net_profit
```

Gain:

```text
net_gain =
    recommended_net_profit - baseline_net_profit
```

All monetary calculations must be deterministic Python code.

---

# 16. TRANSPORT ENGINE

Create:

```python
calculate_transport_cost(...)
```

MVP model:

```text
base_cost =
    fixed_cost +
    distance_km * cost_per_km
```

Farmer share:

```text
farmer_share =
    total_transport_cost
    *
    farmer_quantity
    /
    total_pool_quantity
```

For an empty-return trip, the transport cost model may provide a lower effective cost because the truck is already traveling that corridor.

This must be represented explicitly in the calculation.

---

# 17. CAPACITY ENGINE

Create:

```python
check_capacity(...)
```

Hard rule:

```text
total_quantity <= available_capacity
```

If:

```text
2100 kg <= 2500 kg
```

candidate is valid.

If:

```text
2700 kg > 2500 kg
```

candidate is invalid.

The LLM cannot override this.

---

# 18. SPOILAGE ENGINE

Create:

```python
calculate_spoilage_risk(...)
```

Inputs:

```text
crop
harvested_at
current_time
temperature
humidity
```

Output:

```json
{
  "risk_level": "HIGH",
  "risk_score": 78,
  "hours_remaining": 18,
  "estimated_loss_percentage": 12.5
}
```

Risk:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

This is an **estimate**, not a scientific guarantee.

---

# 19. SPOILAGE CLOCK

The frontend must display:

```text
18h 42m
```

and:

```text
HIGH RISK
```

The countdown should update every minute.

Show:

```text
Estimated spoilage window
```

not:

```text
Exact spoilage deadline
```

Disclaimer:

```text
Estimated using crop age and environmental conditions.
Actual spoilage may vary.
```

---

# 20. CANDIDATE RANKING

Use deterministic ranking.

Example:

```text
net_gain             40%
pooling_benefit      20%
truck_compatibility 15%
spoilage_safety      15%
route_efficiency     10%
```

Normalize:

```text
0–100
```

Then:

```text
final_score =
    weighted combination
```

The highest-scoring **valid** candidate wins.

---

# 21. HARD CONSTRAINTS

Reject candidate if:

```text
quantity <= 0
```

or:

```text
truck capacity insufficient
```

or:

```text
truck unavailable
```

or:

```text
departure after spoilage deadline
```

or:

```text
invalid route
```

or:

```text
no mandi price
```

or:

```text
farmer outside allowed pickup range
```

These are absolute.

---

# 22. RECOMMENDATION OBJECT

The recommendation API should return:

```json
{
  "recommendation_id": "REC-1001",

  "baseline": {
    "mandi": "Mandi A",
    "gross_revenue": 42000,
    "transport_cost": 2400,
    "spoilage_loss": 1800,
    "net_profit": 37800
  },

  "recommended": {
    "mandi": "Mandi B",
    "truck": "T104",

    "pool": {
      "farmer_count": 3,
      "total_quantity_kg": 2100,
      "remaining_capacity_kg": 400
    },

    "gross_revenue": 56000,
    "transport_cost": 2600,
    "spoilage_loss": 3550,
    "net_profit": 49850
  },

  "net_gain": 12050,

  "spoilage": {
    "risk": "HIGH",
    "hours_remaining": 18
  },

  "score": 87.4
}
```

---

# 23. AI'S JOB

The LLM receives validated facts.

It should explain:

```text
Why Mandi B?
Why this truck?
Why pooling?
Why now?
What is the farmer expected to gain?
```

It should not calculate anything that the backend already calculated.

---

# 24. LLM SYSTEM PROMPT

Use a system prompt conceptually equivalent to:

```text
You are Unnati's agricultural logistics explanation assistant.

Your job is to explain a recommendation generated by deterministic
software.

You MUST:
- use only the supplied facts;
- preserve all supplied numbers;
- explain the recommendation simply;
- clearly identify estimates;
- mention when data is demo/seeded;
- explain urgency when spoilage risk is relevant;
- avoid technical terminology where possible;
- never invent prices;
- never invent trucks;
- never invent farmers;
- never invent routes;
- never invent weather;
- never change profit values;
- never change quantities;
- never override capacity constraints.

You MUST NOT:
- perform alternative calculations;
- create unsupported claims;
- claim that seeded prices are live;
- claim spoilage is guaranteed;
- make financial guarantees.

If a fact is unavailable, say it is unavailable.
```

---

# 25. STRUCTURED LLM OUTPUT

Use Pydantic:

```python
class LLMExplanation(BaseModel):
    headline: str
    summary: str
    why_this_option: list[str]
    action: str
    urgency: str
    warnings: list[str]
```

Example:

```json
{
  "headline": "Pool with 2 nearby farmers and use truck T104 to reach Mandi B.",
  "summary": "This option has an estimated net gain of ₹12,050 compared with the baseline.",
  "why_this_option": [
    "Mandi B has the higher expected net return.",
    "Truck T104 has enough return-trip capacity.",
    "Pooling reduces your share of transport cost."
  ],
  "action": "Join the T104 load before departure.",
  "urgency": "Your estimated spoilage window is about 18 hours.",
  "warnings": [
    "Mandi prices are seeded demo values."
  ]
}
```

---

# 26. LLM FAILURE FALLBACK

If the LLM fails:

```text
DO NOT FAIL THE RECOMMENDATION.
```

Return deterministic recommendation + generated fallback text.

Example:

```text
Unnati recommends Mandi B.

It has the highest expected net return after transport
and estimated spoilage costs.

Estimated gain:
₹12,050

Truck:
T104

Pool:
3 farmers

Estimated spoilage risk:
HIGH
```

The user should never see:

```text
LLM timeout
JSON parse failed
OpenRouter error
```

during the normal demo.

---

# 27. LLM CONFIGURATION

Use:

```env
LLM_ENABLED=true
LLM_PROVIDER=openrouter
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_TEMPERATURE=0.2
LLM_TIMEOUT_SECONDS=30
```

If the chosen provider uses a different OpenAI-compatible base URL, configure it through environment variables.

Never hard-code API keys.

---

# 28. FRONTEND DESIGN DIRECTION

The interface should look like a **modern fintech/logistics product**, not a college CRUD project.

Visual direction:

```text
Clean
Premium
Trustworthy
Minimal
Data-driven
Mobile-friendly
Agriculture-inspired
```

Avoid:

```text
excessive gradients
giant illustrations
too many cards
rainbow colors
generic admin dashboard layout
```

Use strong hierarchy.

---

# 29. COLOR SYSTEM

Use a restrained palette:

```text
Primary:
deep green

Success:
green

Warning:
amber

Danger:
red

Background:
warm off-white / very light neutral

Text:
dark charcoal
```

Use color mainly to communicate status.

---

# 30. PAGE 1 — LANDING

Hero:

```text
SELL SMARTER.
MOVE TOGETHER.

Unnati finds the best mandi,
the right truck, and nearby farmers
to help you earn more from every harvest.
```

CTA:

```text
Try Unnati
```

Secondary:

```text
See How It Works
```

Show three steps:

```text
1. Tell us what you harvested
2. We find the best logistics option
3. See your expected gain
```

---

# 31. PAGE 2 — FARMER INPUT

Heading:

```text
What are you selling today?
```

Fields:

```text
Crop
Quantity
Location
Harvested date/time
```

Optional:

```text
Search radius
Language
```

Primary CTA:

```text
Find My Best Option →
```

Use a simple form.

Do not ask for unnecessary information.

---

# 32. PAGE 3 — ANALYSIS STATE

This should feel intelligent.

Show:

```text
Finding nearby farmers...
```

Then:

```text
Checking available trucks...
```

Then:

```text
Comparing mandis...
```

Then:

```text
Calculating transport and spoilage...
```

Then:

```text
Finding your highest-value option...
```

Do not fake numerical progress.

---

# 33. PAGE 4 — RECOMMENDATION HERO

This is the most important screen.

Top:

```text
Unnati RECOMMENDS
```

Main:

```text
₹12,050 MORE
```

Subtitle:

```text
estimated net gain
```

Then:

```text
Pool with 2 farmers
Use return truck T104
Sell at Mandi B
```

CTA:

```text
Join This Load
```

Secondary:

```text
See Why
```

---

# 34. BEFORE VS AFTER

Create a strong comparison.

## Sell normally

```text
MANDI A

Revenue             ₹42,000
Transport           -₹2,400
Estimated spoilage  -₹1,800

NET                  ₹37,800
```

## Unnati

```text
MANDI B

Revenue             ₹56,000
Transport           -₹2,600
Estimated spoilage  -₹3,550

NET                  ₹49,850
```

Then:

```text
YOUR ADVANTAGE
+₹12,050
```

This should be visually dominant.

---

# 35. POOL CARD

```text
YOUR LOAD

You
800 kg

+
Ramesh
700 kg

+
Amit
600 kg

----------------

2,100 / 2,500 kg
84% truck utilization
```

Truck:

```text
T104
RETURN TRIP AVAILABLE
```

Departure:

```text
Today · 7:00 PM
```

CTA:

```text
Join This Load
```

---

# 36. MANDI COMPARISON

Display:

```text
Mandi A
₹48/kg
45 km
₹37,800 net

Mandi B
₹63/kg
72 km
₹49,850 net
RECOMMENDED

Mandi C
₹58/kg
60 km
₹44,300 net
```

Important:

```text
Price is not the same as profit.
```

This is a strong judge-facing concept.

---

# 37. SPOILAGE CARD

```text
SPOILAGE CLOCK

HIGH RISK

18h 42m

████████████░░░░

Move before the estimated
risk window closes.
```

Show:

```text
Temperature: 31°C
Crop age: 15h
Estimated loss: 12.5%
```

Label:

```text
Estimated — not guaranteed.
```

---

# 38. AI EXPLANATION CARD

Header:

```text
WHY Unnati CHOSE THIS
```

Example:

```text
Mandi B offers the strongest expected net return
after transport and estimated spoilage.

Truck T104 is already returning toward your region,
so you can use available return capacity instead of
booking a dedicated trip.

Pooling with 2 farmers also reduces your transport share.

Because your tomatoes are already harvested,
we recommend moving the load before the estimated
spoilage window becomes critical.
```

Show:

```text
AI-assisted explanation
```

---

# 39. MAP

Use:

```text
Leaflet + OpenStreetMap
```

Show:

```text
Farmer
Nearby farmers
Truck
Recommended mandi
Alternative mandis
Route
```

The map should support the story:

```text
farmer → pooled pickup → truck → Mandi B
```

Do not spend hours creating advanced GIS functionality.

A clean route visualization is enough.

---

# 40. JOIN LOAD INTERACTION

When user clicks:

```text
Join This Load
```

Change:

```text
AVAILABLE
```

to:

```text
JOINED
```

Then show:

```text
Your 800 kg has been added to the T104 pooled load.

Departure:
Today · 7:00 PM

Destination:
Mandi B
```

Then notification:

```text
Load confirmed.
```

This makes the demo feel like a real product.

---

# 41. NOTIFICATIONS

MVP notification examples:

```text
Truck T104 departs in 3 hours.

Your estimated spoilage window closes in 18 hours.

Your pooled load is now confirmed.

Mandi B currently has the best expected net return.
```

These can be simulated.

---

# 42. FUTURE WHATSAPP ARCHITECTURE

Do not implement production WhatsApp integration during the core MVP.

Design the service layer so that:

```text
WebNotificationProvider
```

can later become:

```text
WhatsAppProvider
```

Future interaction:

```text
Farmer:
What should I do with 800kg tomato?

Unnati:
Mandi B can give you an estimated ₹12,050 more.

You can join truck T104 with 2 nearby farmers.

Estimated spoilage window: 18 hours.

Reply:
1 - Join load
2 - Other options
```

Mention this as a **future scalability vision**, not as a fake current integration.

---

# 43. DEMO DATA

The application must include a carefully designed golden demo.

## Farmer

```text
Name:
Ramesh Kumar

Crop:
Tomato

Quantity:
800 kg

Location:
Delhi NCR

Harvest:
Today, 6:00 AM
```

## Nearby farmers

```text
Suresh
700 kg
Tomato

Amit
600 kg
Tomato
```

## Truck

```text
T104

Capacity:
2,500 kg

Available:
2,500 kg

Return trip:
Yes

Route:
Mandi A → Delhi NCR
```

## Mandis

```text
Mandi A
₹48/kg

Mandi B
₹63/kg

Mandi C
₹58/kg
```

These numbers are illustrative demo data.

---

# 44. GOLDEN DEMO RESULT

The seed data should produce a compelling recommendation.

Target narrative:

```text
Baseline:
~₹37,800 net

Recommended:
~₹49,850 net

Gain:
~₹12,050
```

Exact values must come from the deterministic calculation engine.

Never hard-code:

```text
net_gain = 12050
```

The data should cause the calculation to produce the result.

---

# 45. DEMO DATA DISCLAIMER

Where prices appear:

```text
Demo price · seeded prototype data
```

Where weather appears:

```text
Demo weather · used for prototype spoilage estimation
```

This protects credibility.

---

# 46. API ENDPOINTS

## Health

```http
GET /api/health
```

---

## Crops

```http
GET /api/crops
```

---

## Farmers

```http
POST /api/farmers
GET /api/farmers/{id}
```

---

## Listings

```http
POST /api/listings
GET /api/listings/{id}
```

---

## Trucks

```http
GET /api/trucks
GET /api/trucks/{id}
```

---

## Mandis

```http
GET /api/mandis
GET /api/mandis/{id}/prices
```

---

## Candidate Matching

```http
POST /api/matching/candidates
```

Request:

```json
{
  "listing_id": 1
}
```

---

## Recommendation

```http
POST /api/recommendations
```

Request:

```json
{
  "listing_id": 1
}
```

---

## Join Pool

```http
POST /api/pools/{pool_id}/join
```

Request:

```json
{
  "listing_id": 1
}
```

---

## Weather

```http
GET /api/weather
```

---

## Notifications

```http
GET /api/notifications/{farmer_id}
```

---

# 47. ERROR HANDLING

Use meaningful error codes.

```text
INVALID_INPUT
NO_COMPATIBLE_FARMERS
NO_AVAILABLE_TRUCK
NO_VALID_ROUTE
NO_VALID_MANDI
NO_VALID_MATCH
WEATHER_UNAVAILABLE
LLM_UNAVAILABLE
INTERNAL_ERROR
```

Example:

```json
{
  "error": {
    "code": "NO_VALID_MATCH",
    "message": "No suitable truck and mandi combination was found before the estimated spoilage window."
  }
}
```

Never expose stack traces to users.

---

# 48. FRONTEND ERROR EXPERIENCE

If no truck exists:

```text
We couldn't find a suitable truck right now.

Try:
• increasing your pickup radius
• checking another departure
• viewing other mandis
```

If LLM fails:

Do not tell the farmer.

Simply show:

```text
Why we recommend this

Mandi B has the highest expected net return
after transport and estimated spoilage.
```

---

# 49. TESTING

## Profit tests

Test:

```text
normal calculation
spoilage-adjusted calculation
negative/invalid inputs
baseline comparison
```

## Transport tests

Test:

```text
fixed + distance cost
pool sharing
return-trip adjustment
```

## Capacity tests

Test:

```text
within capacity
exact capacity
over capacity
```

## Spoilage tests

Test:

```text
fresh produce
old produce
hot weather
cool weather
```

## Matching tests

Test:

```text
near farmer
far farmer
compatible crop
incompatible crop
compatible timing
incompatible timing
```

## Recommendation tests

Test:

```text
best valid candidate
invalid candidate rejection
no candidate
```

## LLM tests

Test:

```text
valid structured output
invalid JSON
LLM timeout
LLM disabled
fallback explanation
```

---

# 50. DEMO MODE

Add:

```env
DEMO_MODE=true
```

When enabled:

- seeded data is available;
- demo scenario is easy to launch;
- external APIs are optional;
- prices are clearly marked;
- weather can use seeded values.

Add:

```http
POST /api/demo/reset
```

only for development/demo mode.

---

# 51. ONE-CLICK DEMO

The landing page should have:

```text
TRY LIVE DEMO
```

This should load the golden farmer scenario.

Do not force judges to manually type:

```text
crop
quantity
coordinates
date
```

during the presentation.

The manual input flow should still exist.

---

# 52. JUDGE DEMO SCRIPT

## 0:00–0:15

Say:

> “Farmers don't just lose money because of low prices. They lose money because they can't efficiently combine their produce, trucks, timing, and market opportunities.”

---

## 0:15–0:30

Show:

```text
800 kg Tomato
```

Click:

```text
Find My Best Option
```

---

## 0:30–0:45

Show analysis:

```text
Nearby farmers found
Return truck found
Mandis compared
Spoilage calculated
```

---

## 0:45–1:15

Reveal:

```text
₹37,800
```

then:

```text
₹49,850
```

then:

```text
+₹12,050
```

Say:

> “Instead of simply choosing the mandi with the highest price, Unnati calculates what the farmer actually takes home after transport and estimated spoilage.”

---

## 1:15–1:40

Show:

```text
2 nearby farmers
Truck T104
2,100 / 2,500 kg
Return trip
Mandi B
```

Say:

> “The system found two nearby farmers and an empty-return truck with enough capacity.”

---

## 1:40–2:00

Show:

```text
18h 42m
HIGH RISK
```

Say:

> “It also knows this isn't just a price decision. Produce is perishable, so timing matters.”

---

## 2:00–2:20

Show AI explanation.

Say:

> “The AI isn't doing the math. Our deterministic engines calculate the economics and constraints. The LLM turns those facts into a simple recommendation the farmer can understand.”

---

## 2:20–2:40

Click:

```text
Join This Load
```

Show:

```text
Load confirmed
```

---

# 53. JUDGE-FACING ARCHITECTURE SLIDE

Use this architecture in the presentation:

```text
              FARMER INPUT
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
             LLM EXPLANATION
                   ↓
            FARMER DECISION
```

Key sentence:

> **“AI explains the decision; deterministic engines protect its correctness.”**

---

# 54. WHAT MAKES THIS DIFFERENT

Do not pitch:

> “We made an AI chatbot for farmers.”

Pitch:

> **“We built a farmer-side logistics decision engine.”**

The differentiated combination is:

```text
Farmer pooling
+
Empty-return truck matching
+
Mandi comparison
+
Net-profit calculation
+
Spoilage-aware timing
+
AI explanation
```

---

# 55. BUSINESS MODEL

Keep this simple for the presentation.

Potential models:

## Transaction take-rate

Take a small percentage of incremental value created.

Example:

```text
Farmer gains ₹10,000
Platform charges a small success-based fee
```

---

## FPO SaaS

FPOs can use Unnati to coordinate:

```text
farmers
trucks
mandis
load pools
```

---

## Logistics partnership

Truck operators can receive:

```text
return-load opportunities
```

This reduces empty kilometers.

---

# 56. SCALABILITY STORY

Do not claim the MVP already supports millions of farmers.

Say:

> “The MVP is a modular monolith. The matching engine can later become a dedicated service, while the same recommendation object can power web, WhatsApp, and mobile interfaces.”

Future:

```text
Web
WhatsApp
Mobile
     ↓
Recommendation API
     ↓
Matching Service
     ↓
Optimization
     ↓
Market + Weather + Logistics data
```

---

# 57. WHY NOT CUSTOM ML?

Expected judge question:

> “Why aren't you training an ML model?”

Answer:

> “At this stage, the core problem is constrained optimization over structured logistics and market data, not prediction alone. We can make the MVP reliable with deterministic calculations and rules, while using an LLM for natural-language reasoning. As we collect historical data, ML can later improve demand, price, and spoilage prediction.”

This is a stronger answer than pretending to have trained a model.

---

# 58. WHY LLM?

Expected judge question:

> “Where exactly is the AI?”

Answer:

> “The LLM receives validated candidate options and deterministic calculations, then converts them into an actionable recommendation in farmer-friendly language. It can also later support multilingual and conversational interfaces.”

The LLM is therefore:

```text
Reasoning + explanation + future conversational interface
```

not:

```text
calculator
```

---

# 59. WHY FARMER POOLING?

Expected judge question:

> “Why can't farmers just hire trucks themselves?”

Answer:

> “The problem is fragmented supply. One farmer may not have enough volume to justify an efficient trip. Unnati aggregates compatible nearby loads and matches them with existing or empty-return capacity.”

---

# 60. WHY EMPTY-RETURN TRIPS?

Expected judge question:

> “Why focus on return trips?”

Answer:

> “A truck that is already traveling back with unused capacity represents logistics capacity that would otherwise be wasted. Matching farmers to that capacity can reduce effective transport cost without requiring a new dedicated trip.”

---

# 61. SPOILAGE CLAIMS

Never claim:

```text
We predict exactly when tomatoes will spoil.
```

Say:

> “We provide an estimated spoilage-risk window using crop type, harvest age, and environmental conditions.”

This keeps the claim credible.

---

# 62. DATA STRATEGY

For the hackathon:

```text
Seeded mandi prices
+
Seeded truck routes
+
Seeded farmer listings
+
Optional weather API
```

Clearly label demo data.

Future:

```text
e-NAM
APMC data
weather APIs
logistics providers
FPO data
historical transactions
```

---

# 63. SECURITY

Minimum requirements:

- API keys only in `.env`
- `.env` in `.gitignore`
- no secrets in frontend
- validate all API input
- restrict CORS
- avoid logging private phone numbers
- do not expose database credentials

Authentication is optional for the hackathon.

Do not spend critical hackathon time building a complex authentication system.

---

# 64. PERFORMANCE

Target:

```text
API calculation:
< 500 ms ideally

Full recommendation:
< 5 seconds ideally
```

LLM latency may vary.

Use:

```text
deterministic recommendation
+
LLM explanation
```

so the core recommendation remains reliable.

---

# 65. OBSERVABILITY

Log:

```text
recommendation_id
candidate_count
valid_candidate_count
selected_candidate
calculation_time
llm_time
total_time
```

Do not log:

```text
API keys
full phone numbers
unnecessary personal data
```

---

# 66. ENVIRONMENT VARIABLES

Create `.env.example`:

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/Unnati

LLM_ENABLED=true
LLM_PROVIDER=openrouter
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_TEMPERATURE=0.2
LLM_TIMEOUT_SECONDS=30

WEATHER_ENABLED=false
WEATHER_API_KEY=

CORS_ORIGINS=http://localhost:5173

DEMO_MODE=true

MAX_POOL_RADIUS_KM=40
MAX_HARVEST_TIME_DIFF_HOURS=24
MIN_LISTING_QUANTITY_KG=50
```

---

# 67. DOCKER

Use Docker Compose for PostgreSQL:

```text
PostgreSQL
```

Do not unnecessarily containerize the entire application.

The goal is:

```text
easy setup
easy debugging
easy demo
```

---

# 68. BACKEND SETUP

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

---

# 69. FRONTEND SETUP

```bash
cd frontend
npm install
npm run dev
```

---

# 70. DATABASE SETUP

Use Alembic:

```bash
alembic upgrade head
```

Seed:

```bash
python -m app.db.seed
```

Expected:

```text
Seed complete.

Farmers: 10+
Listings: 10+
Trucks: 10+
Mandis: 6+
Routes: 10+
Price records: 30+
```

---

# 71. API DOCUMENTATION

FastAPI must expose:

```text
/docs
/redoc
```

Important endpoints should have:

- descriptions
- request examples
- response examples
- error responses

---

# 72. CODE QUALITY

Follow:

```text
PEP 8
Type hints
Small functions
Clear names
Single responsibility
No duplicated business logic
```

Avoid:

```text
business logic in React components
database queries scattered across routers
LLM calls inside calculation functions
magic numbers
hard-coded recommendation results
```

---

# 73. FRONTEND COMPONENTS

Create:

```text
Navbar
HeroSection
FarmerInputForm
CropSelector
QuantityInput
LocationPicker
HarvestDatePicker

AnalysisLoader

RecommendationHero
GainComparison
MandiComparison
PoolCard
TruckCard
SpoilageClock
AISummary
RouteMap
EvidenceCard
NotificationPanel

ErrorState
EmptyState
LoadingState
```

---

# 74. RESPONSIVE DESIGN

Prioritize:

```text
Mobile
Tablet
Desktop
```

On mobile, keep these visible early:

```text
₹ gain
recommended mandi
truck
spoilage clock
join load button
```

---

# 75. ACCESSIBILITY

Use:

- semantic HTML
- labels
- keyboard navigation
- accessible buttons
- clear focus states
- readable font sizes
- meaningful errors

---

# 76. NO-MATCH EXPERIENCE

If no valid option exists:

```text
No safe load found right now.
```

Then explain:

```text
We checked:
• nearby farmers
• available trucks
• mandi routes
• capacity
• estimated spoilage timing
```

Suggestions:

```text
Increase pickup radius
View another mandi
Try another departure time
```

Do not fabricate an option.

---

# 77. FALLBACK MAP

If map tiles/API fail:

Do not break the dashboard.

Show:

```text
Route summary

Farmer pickup
↓
Delhi NCR
↓
Truck T104
↓
Mandi B
```

The map is a visualization, not a core dependency.

---

# 78. DEVELOPMENT PHASES

## PHASE 1 — Foundation

Implement:

- repository
- FastAPI
- database
- models
- migrations
- seed data
- health endpoint

---

## PHASE 2 — Deterministic Brain

Implement:

- profit
- transport
- capacity
- spoilage
- distance
- ranking

Write tests immediately.

---

## PHASE 3 — Matching

Implement:

- farmer compatibility
- truck compatibility
- return-trip matching
- mandi candidate generation

---

## PHASE 4 — Recommendation

Implement:

```text
listing
→ candidates
→ calculations
→ ranking
→ best option
```

This must work without AI.

---

## PHASE 5 — LLM

Implement:

```text
validated recommendation
→ LLM
→ structured JSON
→ validation
→ explanation
```

Add fallback.

---

## PHASE 6 — Frontend

Build:

```text
landing
→ input
→ analysis
→ recommendation
```

---

## PHASE 7 — Hackathon UX

Add:

```text
pool card
truck card
mandi comparison
spoilage clock
map
join load
notification
```

---

## PHASE 8 — Polish

Add:

```text
animations
mobile layout
loading states
error states
demo mode
micro-interactions
```

---

## PHASE 9 — Final Testing

Test:

```text
golden scenario
no truck
over capacity
no mandi
expired produce
LLM disabled
LLM timeout
invalid input
```

---

# 79. DEFINITION OF DONE

The project is complete only when:

## Core

- [ ] Farmer can enter produce.
- [ ] Backend receives real data.
- [ ] Database stores listings.
- [ ] Matching engine finds compatible farmers.
- [ ] Truck matching works.
- [ ] Return-trip matching works.
- [ ] Mandi comparison works.
- [ ] Profit calculation works.
- [ ] Spoilage estimate works.
- [ ] Capacity validation works.
- [ ] Recommendation ranking works.

## AI

- [ ] LLM receives structured facts.
- [ ] LLM output is validated.
- [ ] LLM cannot alter calculations.
- [ ] LLM failure has fallback.
- [ ] Demo works with AI enabled.
- [ ] Demo works with AI disabled.

## UI

- [ ] Farmer input page works.
- [ ] Analysis screen works.
- [ ] Recommendation hero works.
- [ ] ₹ gain is obvious.
- [ ] Before/after comparison works.
- [ ] Pool card works.
- [ ] Truck card works.
- [ ] Mandi cards work.
- [ ] Spoilage clock works.
- [ ] AI explanation works.
- [ ] Join load works.
- [ ] Notification works.
- [ ] Mobile layout works.

## Demo

- [ ] One-click demo works.
- [ ] Golden scenario works.
- [ ] No fake calculation is used.
- [ ] Seeded data is labeled.
- [ ] End-to-end flow works.
- [ ] No critical console errors.
- [ ] No critical backend errors.

---

# 80. OPEN-CODE / CODING AGENT MASTER INSTRUCTIONS

You are the principal engineer implementing Unnati for a hackathon.

Your goal is NOT to build an unnecessarily large production system.

Your goal is to build a:

```text
polished
credible
functional
end-to-end
hackathon MVP
```

that demonstrates the product's core value in under 30 seconds.

---

## Before coding

1. Inspect the entire repository.
2. Read this document completely.
3. Identify what already exists.
4. Run the current application.
5. Do not delete working code.
6. Do not restart the project from scratch if an implementation already exists.
7. Create a short implementation plan.
8. Implement incrementally.
9. Test after each major subsystem.

---

## If the repository is empty

Build in this order:

```text
1. Backend foundation
2. Database
3. Seed data
4. Deterministic engines
5. Tests
6. Matching engine
7. Recommendation API
8. LLM service
9. Frontend
10. Recommendation dashboard
11. Map
12. Join-load interaction
13. Notifications
14. Polish
15. Final testing
```

---

# 81. ABSOLUTE CODING RULES

## Rule 1

Do not hard-code the final recommendation.

Bad:

```python
return {"net_gain": 12050}
```

Good:

```text
database
→ matching
→ calculation
→ ranking
→ recommendation
```

---

## Rule 2

Do not make the LLM responsible for arithmetic.

Bad:

```text
LLM calculates profit
```

Good:

```text
Python calculates profit
LLM explains profit
```

---

## Rule 3

Do not let the LLM violate constraints.

Bad:

```text
Truck capacity = 2500 kg
LLM recommends 3200 kg
```

Good:

```text
3200 kg candidate rejected before LLM
```

---

## Rule 4

Never fake a successful API call.

If an API fails:

```text
fallback
```

not:

```text
fake success
```

---

## Rule 5

Never expose secrets.

---

## Rule 6

Do not introduce unnecessary libraries.

---

## Rule 7

Do not spend hackathon time on advanced authentication.

---

## Rule 8

Do not build WhatsApp production integration unless all P0/P1 requirements are already complete.

---

## Rule 9

Do not build ML models for the MVP.

---

## Rule 10

Always prioritize:

```text
working demo
>
architecture complexity
```

---

# 82. FINAL END-TO-END ACCEPTANCE TEST

Run this exact scenario:

```text
Crop:
Tomato

Quantity:
800 kg

Location:
Delhi NCR

Harvest:
Today at 6:00 AM
```

System must:

```text
1. Find compatible farmers.

2. Find truck T104 or another valid truck.

3. Check available capacity.

4. Find candidate mandis.

5. Calculate baseline.

6. Calculate alternatives.

7. Calculate transport.

8. Calculate spoilage.

9. Reject invalid candidates.

10. Rank valid candidates.

11. Select the best candidate.

12. Calculate net gain.

13. Generate AI explanation.

14. Validate AI response.

15. Display recommendation.

16. Allow Join This Load.

17. Update pool state.

18. Display confirmation.
```

---

# 83. FINAL DEMO SCREEN

The final recommendation should visually communicate:

```text
┌───────────────────────────────────────────┐
│                                           │
│          Unnati RECOMMENDS            │
│                                           │
│             ₹12,050 MORE                 │
│              estimated gain               │
│                                           │
│        Mandi B · Truck T104               │
│        Pool with 2 farmers                │
│                                           │
│       ┌─────────────────────────┐         │
│       │    JOIN THIS LOAD →     │         │
│       └─────────────────────────┘         │
│                                           │
├───────────────────────────────────────────┤
│                                           │
│  NORMAL SALE          Unnati          │
│  ₹37,800              ₹49,850             │
│                                           │
│             +₹12,050                     │
│                                           │
├───────────────────────────────────────────┤
│                                           │
│  🚚 RETURN TRIP AVAILABLE                 │
│  T104 · 400 kg capacity remaining         │
│                                           │
│  👨‍🌾 3 FARMERS · 2,100 / 2,500 kg        │
│                                           │
│  ⏱ HIGH SPOILAGE RISK · 18h 42m           │
│                                           │
├───────────────────────────────────────────┤
│                                           │
│  WHY THIS OPTION?                         │
│                                           │
│  Mandi B offers the strongest expected    │
│  net return after transport and estimated │
│  spoilage. The truck is already returning │
│  toward your region, and pooling reduces  │
│  your transport share.                    │
│                                           │
└───────────────────────────────────────────┘
```

The exact numbers come from the backend.

---

# 84. FINAL PRODUCT STATEMENT

Unnati should ultimately demonstrate:

```text
FARMER INPUT
      ↓
WHAT DO I HAVE?
      ↓
WHERE CAN I SELL?
      ↓
WHO CAN I POOL WITH?
      ↓
WHICH TRUCK SHOULD I USE?
      ↓
WHAT WILL I ACTUALLY EARN?
      ↓
HOW MUCH TIME DO I HAVE?
      ↓
WHAT SHOULD I DO?
```

And the answer should be one clear action:

> **“Pool these farmers, take this return truck, sell at this mandi, and you could gain ₹X more.”**

---

# 85. FINAL HACKATHON PHILOSOPHY

Do not try to prove that Unnati has solved Indian agricultural logistics.

Prove something much more valuable:

> **A farmer can make a significantly better logistics decision when market price, transportation capacity, nearby supply, and perishability are considered together.**

The MVP only needs to make that idea undeniable.

The winning demo is not:

```text
Look at our 20 screens.
```

It is:

```text
Here is a farmer.
Here is their produce.

Without Unnati:
₹37,800.

With Unnati:
₹49,850.

Here's the truck.
Here's the farmer pool.
Here's the spoilage clock.
Here's why.

And the farmer can join the load.
```

That is Unnati.
