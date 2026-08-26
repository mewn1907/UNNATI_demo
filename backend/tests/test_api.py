"""API contract tests including the full end-to-end golden journey."""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_crops_listed(client):
    crops = client.get("/api/crops").json()
    names = {c["name"] for c in crops}
    assert {"Tomato", "Potato", "Onion", "Wheat", "Rice"} <= names


def test_trucks_and_mandis(client):
    trucks = client.get("/api/trucks").json()
    assert len(trucks) >= 10
    t104 = next(t for t in trucks if t["id"] == "T104")
    assert t104["capacity_kg"] == 2500
    assert any(r["return_available"] for r in t104["routes"])

    mandis = client.get("/api/mandis").json()
    assert len(mandis) >= 6
    prices = client.get("/api/mandis/1/prices").json()
    tomato = next(p for p in prices if p["crop"] == "Tomato")
    assert tomato["price_per_kg"] == 48.0


def test_full_farmer_journey(client):
    """Create listing → recommend → join pool → notifications."""
    # 1. Farmer input.
    created = client.post(
        "/api/listings",
        json={
            "crop": "Tomato",
            "quantity_kg": 800,
            "latitude": 28.683,
            "longitude": 77.06,
        },
    )
    assert created.status_code == 201, created.text
    listing_id = created.json()["id"]

    # 2. Recommendation.
    rec = client.post("/api/recommendations", json={"listing_id": listing_id})
    assert rec.status_code == 200, rec.text
    body = rec.json()
    assert body["recommended"]["pool"]["farmer_count"] >= 1
    assert body["net_gain"] > 0

    # 3. Join the load.
    joined = client.post(
        f"/api/pools/{body['pool_id']}/join", json={"listing_id": listing_id}
    )
    assert joined.status_code == 200
    assert joined.json()["status"] == "JOINED"

    # 4. Notification created.
    notes = client.get("/api/notifications/1").json()
    assert any(n["type"] == "POOL_CONFIRMED" for n in notes)


def test_listing_validation(client):
    bad_crop = client.post(
        "/api/listings",
        json={"crop": "Pizza", "quantity_kg": 10, "latitude": 28.0, "longitude": 77.0},
    )
    assert bad_crop.status_code == 422

    bad_qty = client.post(
        "/api/listings",
        json={"crop": "Tomato", "quantity_kg": -5, "latitude": 28.0, "longitude": 77.0},
    )
    assert bad_qty.status_code == 422


def test_recommendation_unknown_listing(client):
    missing = client.post("/api/recommendations", json={"listing_id": 987654})
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"


def test_matching_candidates_endpoint(client):
    result = client.post("/api/matching/candidates", json={"listing_id": 1})
    assert result.status_code == 200
    payload = result.json()
    compatible_names = {f["name"] for f in payload["compatible_farmers"]}
    assert "Suresh Yadav" in compatible_names


def test_chat_conversation_flow(client):
    session_id = "pytest-chat-01"

    # Every fresh conversation starts by asking the user's role.
    r1 = client.post("/api/chat", json={
        "session_id": session_id,
        "text": "I have 800 kg tomatoes ready today from Nangloi",
    })
    assert r1.status_code == 200
    text1 = r1.json()["reply"]["text"]
    assert "farmer" in text1.lower() and "driver" in text1.lower()

    # Choosing farmer leads to the language question.
    r_role = client.post("/api/chat", json={"session_id": session_id, "text": "farmer"})
    assert "language" in r_role.json()["reply"]["text"].lower()

    r_lang = client.post("/api/chat", json={"session_id": session_id, "text": "english"})
    assert r_lang.status_code == 200
    assert "begin" in r_lang.json()["reply"]["text"].lower()

    r2 = client.post("/api/chat", json={"session_id": session_id, "text": "start over"})
    assert "Namaste" in r2.json()["reply"]["text"]

    client.post("/api/chat", json={"session_id": session_id, "text": "farmer"})
    client.post("/api/chat", json={"session_id": session_id, "text": "english"})
    r3 = client.post("/api/chat", json={"session_id": session_id, "text": "500 kg aalu Kharkhoda kal"})
    text3 = r3.json()["reply"]["text"]
    assert ("Potato" in text3) or ("kilograms" in text3) or ("option" in text3)


def test_chat_hindi_flow(client):
    session_id = "pytest-chat-hi"

    # Choosing the role first; Devanagari also sets the language.
    r1 = client.post("/api/chat", json={"session_id": session_id, "text": "किसान"})
    assert r1.status_code == 200
    assert "चलिए शुरू करें" in r1.json()["reply"]["text"]

    # A fully Devanagari message is parsed end-to-end.
    r2 = client.post("/api/chat", json={
        "session_id": session_id,
        "text": "आज नांगलोई से ८०० किलो टमाटर तैयार है",
    })
    assert r2.status_code == 200
    text2 = r2.json()["reply"]["text"]
    assert any(word in text2 for word in ("विकल्प", "किलो", "ट्रक"))

    # Joining works from the Hindi flow too.
    r3 = client.post("/api/chat", json={"session_id": session_id, "text": "1"})
    assert r3.status_code == 200


def test_chat_driver_flow(client):
    session_id = "pytest-chat-driver"

    r1 = client.post("/api/chat", json={"session_id": session_id, "text": "driver"})
    assert r1.status_code == 200
    text1 = r1.json()["reply"]["text"]
    assert "English" in text1 and ("हिंदी" in text1 or "language" in text1)

    r_lang = client.post("/api/chat", json={"session_id": session_id, "text": "english"})
    assert "truck" in r_lang.json()["reply"]["text"].lower()

    r_cap = client.post("/api/chat", json={"session_id": session_id, "text": "2500 kg"})
    assert "where" in r_cap.json()["reply"]["text"].lower() or "📍" in r_cap.json()["reply"]["text"]

    r_origin = client.post("/api/chat", json={"session_id": session_id, "text": "Nangloi"})
    summary = r_origin.json()["reply"]["text"]
    assert "₹" in summary
    assert any(w in summary.lower() for w in ("mandi", "मंडी"))


def test_chat_language_required_first(client):
    session_id = "pytest-chat-lang"

    r1 = client.post("/api/chat", json={"session_id": session_id, "text": "hello there"})
    assert r1.status_code == 200
    text = r1.json()["reply"]["text"]
    assert "farmer" in text.lower() and "driver" in text.lower()

    # Quick-reply style role choice sets the role; Hindi script sets language.
    r2 = client.post("/api/chat", json={"session_id": session_id, "text": "हिंदी किसान"})
    assert "हम हिंदी में बात करेंगे" in r2.json()["reply"]["text"]


def test_demo_reset(client):
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "reseeded"
