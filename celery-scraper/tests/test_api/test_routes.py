"""Tests for API routes."""

from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestTriggerScrape:
    def test_returns_accepted_with_task_id(self):
        mock_result = Mock()
        mock_result.id = "fake-task-id-123"

        with patch("app.api.routes.run_scrape_pipeline.delay", return_value=mock_result):
            response = client.post("/api/scrape", json={"limit": 5, "min_score": 10})

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "fake-task-id-123"
        assert data["status"] == "ACCEPTED"

    def test_uses_defaults_when_no_body(self):
        mock_result = Mock()
        mock_result.id = "fake-id"

        with patch("app.api.routes.run_scrape_pipeline.delay", return_value=mock_result) as mock_delay:
            response = client.post("/api/scrape", json={})

        assert response.status_code == 200
        mock_delay.assert_called_once_with(limit=20, min_score=10)


class TestGetTaskStatus:
    def test_pending_task(self):
        mock_result = Mock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False

        with patch("app.api.routes.AsyncResult", return_value=mock_result):
            response = client.get("/api/tasks/some-id")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["result"] is None

    def test_successful_task(self):
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"file": "data/test.json", "count": 5}

        with patch("app.api.routes.AsyncResult", return_value=mock_result):
            response = client.get("/api/tasks/some-id")

        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["result"]["count"] == 5


class TestResults:
    def test_list_results_empty(self):
        with patch("app.api.routes.list_result_files", return_value=[]):
            response = client.get("/api/results")

        assert response.status_code == 200
        assert response.json() == []

    def test_latest_returns_404_when_empty(self):
        with patch("app.api.routes.get_latest_results", return_value=None):
            response = client.get("/api/results/latest")

        assert response.status_code == 404
