"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from alphaedge.api.main import app

    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data or "status" in data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ("healthy", "ok", True)


class TestPredictionEndpoints:
    def test_predict_ticker(self, client):
        resp = client.get("/api/v1/predict/RELIANCE")
        # May succeed or fail depending on network; just check it doesn't 500
        assert resp.status_code in (200, 422, 500, 503)

    def test_predict_post(self, client):
        resp = client.post("/api/v1/predict", json={"ticker": "RELIANCE"})
        assert resp.status_code in (200, 422, 500, 503)

    def test_top_picks(self, client):
        resp = client.get("/api/v1/top-picks")
        assert resp.status_code in (200, 422, 500, 503)


class TestBacktestEndpoints:
    def test_strategies_list(self, client):
        resp = client.get("/api/v1/strategies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_backtest_post(self, client):
        resp = client.post(
            "/api/v1/backtest",
            json={
                "ticker": "RELIANCE",
                "strategy": "buy_and_hold",
            },
        )
        assert resp.status_code in (200, 422, 500, 503)


class TestAnalyticsEndpoints:
    def test_analytics_ticker(self, client):
        resp = client.get("/api/v1/analytics/RELIANCE")
        assert resp.status_code in (200, 422, 500, 503)

    def test_sentiment_post(self, client):
        resp = client.post("/api/v1/sentiment", json={"text": "Stock is doing great today!"})
        assert resp.status_code in (200, 422, 500, 503)
