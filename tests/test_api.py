from datetime import date


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"HealthTrack" in res.data


def test_about_page(client):
    res = client.get("/about")
    assert res.status_code == 200
    assert b"About \xe2\x80\x94 HealthTrack" in res.data or b"HealthTrack" in res.data
    assert b"Vijay Rajesh R" in res.data
    assert b"Aiden AI" in res.data
    assert b"https://github.com/vijayrajeshr" in res.data



def test_create_symptom_success(client):
    today_str = date.today().isoformat()
    payload = {
        "user_id": "test_user",
        "symptom": "Migraine",
        "severity": 8,
        "date": today_str,
    }
    res = client.post("/api/symptoms", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["user_id"] == "test_user"
    assert data["symptom"] == "migraine"
    assert data["severity"] == 8
    assert data["date"] == today_str
    assert len(data["id"]) == 12
    assert "timestamp" in data


def test_create_symptom_validation_error(client):
    res = client.post("/api/symptoms", json={})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data
    assert "details" in data
    assert "symptom" in data["details"]
    assert "severity" in data["details"]


def test_create_symptom_invalid_json(client):
    res = client.post("/api/symptoms", data="not json", content_type="application/json")
    assert res.status_code == 400
    data = res.get_json()
    assert "valid JSON" in data["error"]


def test_create_symptom_oversized_body(client):
    huge_data = {"user_id": "test", "symptom": "x" * 20000}
    res = client.post("/api/symptoms", json=huge_data)
    assert res.status_code == 413
    data = res.get_json()
    assert "large" in data["error"]


def test_get_symptoms_requires_user_id(client):
    res = client.get("/api/symptoms")
    assert res.status_code == 400
    data = res.get_json()
    assert "user_id" in data["details"]


def test_get_symptoms_unknown_user_empty(client):
    res = client.get("/api/symptoms?user_id=ghost")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == 0
    assert data["symptoms"] == []


def test_get_symptoms_with_filter(client):
    today = date.today()
    today_str = today.isoformat()

    client.post("/api/symptoms", json={
        "user_id": "filter_user",
        "symptom": "fever",
        "severity": 7,
        "date": today_str,
    })

    # Valid filter
    res = client.get(f"/api/symptoms?user_id=filter_user&start={today_str}&end={today_str}")
    assert res.status_code == 200
    assert res.get_json()["count"] == 1

    # Invalid range (start > end)
    res_err = client.get("/api/symptoms?user_id=filter_user&start=2026-10-15&end=2026-10-01")
    assert res_err.status_code == 400
    assert "range" in res_err.get_json()["details"]


def test_get_insights_flow(client):
    today_str = date.today().isoformat()
    client.post("/api/symptoms", json={
        "user_id": "insight_user",
        "symptom": "joint pain",
        "severity": 6,
        "date": today_str,
    })

    res = client.get("/api/insights?user_id=insight_user")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_entries"] == 1
    assert data["average_severity"] == 6.0
    assert len(data["most_common"]) == 1


def test_delete_symptom_flow(client):
    today_str = date.today().isoformat()
    res_create = client.post("/api/symptoms", json={
        "user_id": "del_user",
        "symptom": "nausea",
        "severity": 4,
        "date": today_str,
    })
    record_id = res_create.get_json()["id"]

    # Wrong user -> 404
    res_del_wrong = client.delete(f"/api/symptoms/{record_id}?user_id=other_user")
    assert res_del_wrong.status_code == 404

    # Owner delete -> 204
    res_del = client.delete(f"/api/symptoms/{record_id}?user_id=del_user")
    assert res_del.status_code == 204

    # Already deleted -> 404
    res_del_again = client.delete(f"/api/symptoms/{record_id}?user_id=del_user")
    assert res_del_again.status_code == 404


def test_json_error_handlers(client):
    # 404 Not Found as JSON
    res_404 = client.get("/api/nonexistent_route")
    assert res_404.status_code == 404
    assert res_404.is_json
    assert res_404.get_json()["error"] == "Not found."

    # 405 Method Not Allowed as JSON
    res_405 = client.post("/api/insights?user_id=demo")
    assert res_405.status_code == 405
    assert res_405.is_json
    assert res_405.get_json()["error"] == "Method not allowed."


def test_delete_missing_user_id(client):
    res = client.delete("/api/symptoms/some_id")
    assert res.status_code == 400
    data = res.get_json()
    assert "user_id" in data["details"]


def test_get_insights_missing_user_id(client):
    res = client.get("/api/insights")
    assert res.status_code == 400
    data = res.get_json()
    assert "user_id" in data["details"]


def test_get_insights_invalid_range(client):
    res = client.get("/api/insights?user_id=demo&start=2026-10-20&end=2026-10-10")
    assert res.status_code == 400
    data = res.get_json()
    assert "range" in data["details"]


def test_create_symptom_string_severity_saved_as_int(client):
    today_str = date.today().isoformat()
    res = client.post("/api/symptoms", json={
        "user_id": "demo",
        "symptom": "nausea",
        "severity": "7",
        "date": today_str,
    })
    assert res.status_code == 201
    record = res.get_json()
    assert record["severity"] == 7
    assert isinstance(record["severity"], int)


def test_get_symptoms_invalid_date_format(client):
    res = client.get("/api/symptoms?user_id=demo&start=bad-date")
    assert res.status_code == 400
    data = res.get_json()
    assert "start" in data["details"]

