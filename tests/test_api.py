import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


@pytest.fixture()
def client():
    return TestClient(create_app(db_path=":memory:", autorun=False))


def tele(sm=20.0, **k):
    return {"node_id": "n1", "zone": "zone1", "soil_moisture": sm, "air_temp": 31.0,
            "humidity": 55.0, "battery": 3.9, **k}


def test_status(client):
    j = client.get("/api/status").json()
    assert j["ok"] and "policy" in j


def test_ingest_and_latest(client):
    assert client.post("/api/telemetry", json=tele()).json()["stored"]
    assert client.get("/api/latest?zone=zone1").json()["soil_moisture"] == 20.0
    assert client.get("/api/latest?zone=none").status_code == 404


def test_validation_rejects_bad_humidity(client):
    assert client.post("/api/telemetry", json=tele(humidity=150)).status_code == 422


def test_agent_run_makes_decision_and_command(client, monkeypatch):
    for v in (19.5, 20.0, 20.5, 19.8):
        client.post("/api/telemetry", json=tele(v))
    d = client.post("/api/agent/run?zone=zone1").json()
    assert d["zone"] == "zone1" and "explanation" in d
    assert len(client.get("/api/decisions").json()) == 1
    # a second non-forced run within 20 h is skipped
    assert "skipped" in client.post("/api/agent/run?zone=zone1&force=false").json()


def test_manual_valve_delivered_once_via_http_reply(client):
    client.post("/api/valve", json={"zone": "zone1", "minutes": 30})
    r = client.post("/api/telemetry", json=tele()).json()
    assert r["commands"] == [{"minutes": 30}]
    assert client.post("/api/telemetry", json=tele()).json()["commands"] == []


def test_valve_limit(client):
    assert client.post("/api/valve", json={"zone": "z", "minutes": 999}).status_code == 422


def test_api_key_enforced(monkeypatch):
    monkeypatch.setenv("API_KEY", "s3cret")
    c = TestClient(create_app(db_path=":memory:", autorun=False))
    assert c.post("/api/telemetry", json=tele()).status_code == 401
    assert c.post("/api/telemetry", json=tele(), headers={"x-api-key": "s3cret"}).status_code == 200


def test_no_data_agent_withholds(client):
    d = client.post("/api/agent/run?zone=ghost").json()
    assert d["approved_mm"] == 0 and d["alerts"]


def test_mango_feasibility_endpoint(client):
    client.post("/api/telemetry", json=tele(nitrogen=150, phosphorus=30, potassium=200, ph=6.8, soil_type="Laterite Soil"))
    res = client.get("/api/mango-feasibility?zone=zone1").json()
    assert "recommendations" in res
    assert len(res["recommendations"]) >= 5
    assert res["current_parameters"]["soil_type"] == "Laterite Soil"
    # Alphonso should score well on Laterite soil with optimal pH
    alphonso = next(r for r in res["recommendations"] if r["id"] == "alphonso")
    assert alphonso["score"] >= 80


def test_chat_endpoint(client):
    client.post("/api/telemetry", json=tele(soil_moisture=19.5, ph=6.5, nitrogen=140))
    # Query in Hindi / Hinglish
    r_hi = client.post("/api/chat", json={"message": "Kaun sa aam lagana chahiye mere mitti mein?", "zone": "zone1"}).json()
    assert "reply" in r_hi and len(r_hi["reply"]) > 20
    # Query in English
    r_en = client.post("/api/chat", json={"message": "What is the feasibility for Alphonso?", "zone": "zone1"}).json()
    assert "Alphonso" in r_en["reply"]
