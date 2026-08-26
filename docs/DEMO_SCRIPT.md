# Unnati — Judge Demo Script (2 minutes)

## 0:00–0:15 — The problem
> "Farmers don't just lose money because of low prices. They lose money
> because they can't efficiently combine their produce, trucks, timing, and
> market opportunities."

## 0:15–0:30 — Launch the golden scenario
Landing page → click **⚡ TRY LIVE DEMO** (no typing needed).
The analysis pipeline lights up: nearby farmers → trucks → mandis → spoilage →
highest-value option.

## 0:30–1:00 — The wow moment
Reveal in order:
- **₹37,652** — selling normally at Azadpur (nearest mandi)
- **₹49,955** — Unnati plan
- **+₹12,304 YOUR ADVANTAGE**

> "Instead of picking the highest-priced mandi, Unnati calculates what the
> farmer actually takes home after transport and estimated spoilage."

## 1:00–1:30 — Why it works
Point at the cards:
- 👨‍🌾 **Pool card**: Ramesh 800 + Suresh 700 + Amit 600 = **2,100 / 2,500 kg (84%)**
- 🚚 **Truck T104** with **🔁 RETURN TRIP AVAILABLE** badge — "this truck is
  already returning toward their region; its spare capacity costs less."
- 🏛️ **Mandi comparison**: "Price is not profit" — Rohtak pays ₹58/kg vs
  Baraut ₹63/kg but net realisation decides.
- ⏱ **Spoilage clock**: "~14h · MEDIUM RISK — estimated, not guaranteed."

## 1:30–1:45 — AI's role
Open **Why Unnati chose this**:
> "The LLM isn't doing the math. Our deterministic engines calculate economics
> and enforce constraints. The LLM turns those validated facts into simple
> language. If it fails or is disabled, a rule-based explanation appears —
> the demo never breaks." (Badge shows Rule-based/LLM honestly.)

## 1:45–2:00 — Close the loop
Click **JOIN THIS LOAD → ✓ JOINED — LOAD CONFIRMED**, notification bell shows
*"Load confirmed."* Then open the **WhatsApp-style Demo** and type:

```
I have 800 kg tomato ready today from Nangloi
```

The bot replies with the same recommendation; press quick-reply **1 - Join load**
to confirm inside chat.

---

## Backup answers for judges

- **"Where does the data come from?"** — Seeded demo dataset shaped like real
  e-NAM/APMC structures, clearly labelled everywhere; swap-in points exist for
  live price/weather/logistics APIs.
- **"Why not ML?"** — The core problem is constrained optimisation over
  structured logistics/market data, not prediction. Deterministic rules give a
  reliable MVP today; historical data can power ML later.
- **"What if no truck matches?"** — Honest NO_VALID_MATCH screen listing what
  was checked with suggestions (radius, timing, other mandis). We never
  fabricate an option.
- **"WhatsApp?"** — Chat simulator runs on the same engine; production
  WhatsApp Business API is a provider swap behind the notification/chat layer.
