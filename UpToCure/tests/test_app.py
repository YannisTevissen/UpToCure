def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"UpToCure" in res.data
    assert b"Sample Disease" in res.data


def test_security_headers(client):
    res = client.get("/healthz")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "Referrer-Policy" in res.headers


def test_reports_list(client):
    res = client.get("/api/reports?lang=en")
    assert res.status_code == 200
    body = res.get_json()
    assert body["error"] is False
    assert body["count"] == 1
    assert body["reports"][0]["slug"] == "sample-disease"
    # Listing should not include the full HTML body
    assert "content" not in body["reports"][0]


def test_reports_list_invalid_language(client):
    res = client.get("/api/reports?lang=xx")
    assert res.status_code == 400


def test_report_detail(client):
    res = client.get("/api/reports/en/sample-disease")
    assert res.status_code == 200
    body = res.get_json()
    assert body["report"]["title"] == "Sample Disease"
    assert "content" in body["report"]


def test_report_detail_404(client):
    res = client.get("/api/reports/en/not-a-real-disease")
    assert res.status_code == 404


def test_request_report_success(client, tmp_reports_dir, tmp_path):
    res = client.post("/api/request-report", json={"disease": "Pompe Disease"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True

    from src import app as app_module
    saved = list(app_module.REQUESTS_DIR.glob("request_*.json"))
    assert len(saved) == 1


def test_request_report_validation(client):
    assert client.post("/api/request-report", json={}).status_code == 400
    assert client.post("/api/request-report", json={"disease": ""}).status_code == 400
    assert client.post("/api/request-report", json={"disease": "x"}).status_code == 400
    assert client.post(
        "/api/request-report",
        json={"disease": "<script>alert(1)</script>"},
    ).status_code == 400


def test_request_report_rate_limit(client):
    for _ in range(5):
        assert client.post("/api/request-report", json={"disease": "Test Disease"}).status_code == 200
    res = client.post("/api/request-report", json={"disease": "Test Disease"})
    assert res.status_code == 429
