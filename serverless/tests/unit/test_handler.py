def test_health_returns_ok(api):
    status, body = api("GET", "/health")

    assert status == 200
    assert body == {"status": "ok"}


def test_unknown_route_returns_404(api):
    status, _ = api("GET", "/nope")

    assert status == 404
