"""Tests for fetch tasks."""

from unittest.mock import patch, Mock

from app.tasks.fetch import fetch_top_stories, fetch_story_details


class TestFetchTopStories:
    def test_returns_limited_ids(self):
        mock_ids = list(range(500))
        mock_response = Mock()
        mock_response.json.return_value = mock_ids
        mock_response.raise_for_status = Mock()

        with patch("app.tasks.fetch.httpx.get", return_value=mock_response):
            result = fetch_top_stories(limit=10)

        assert len(result) == 10
        assert result == list(range(10))

    def test_default_limit_is_30(self):
        mock_ids = list(range(500))
        mock_response = Mock()
        mock_response.json.return_value = mock_ids
        mock_response.raise_for_status = Mock()

        with patch("app.tasks.fetch.httpx.get", return_value=mock_response):
            result = fetch_top_stories()

        assert len(result) == 30


class TestFetchStoryDetails:
    def test_returns_expected_fields(self):
        mock_story = {
            "id": 123,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 42,
            "by": "testuser",
            "time": 1234567890,
            "type": "story",
            "descendants": 5,
            "kids": [1, 2, 3],  # should be excluded from result
        }
        mock_response = Mock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = Mock()

        with patch("app.tasks.fetch.httpx.get", return_value=mock_response):
            result = fetch_story_details(123)

        assert result["id"] == 123
        assert result["title"] == "Test Story"
        assert result["score"] == 42
        assert "kids" not in result

    def test_defaults_missing_score_to_zero(self):
        mock_story = {"id": 1, "title": "No Score"}
        mock_response = Mock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = Mock()

        with patch("app.tasks.fetch.httpx.get", return_value=mock_response):
            result = fetch_story_details(1)

        assert result["score"] == 0
