def test_health_success_status(client):
    r = client.get("/health")
    assert r.status_code == 200
