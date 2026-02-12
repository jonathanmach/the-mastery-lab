"""Tests for process task."""

from app.tasks.process import process_stories


class TestProcessStories:
    def test_filters_below_min_score(self):
        stories = [
            {"title": "Low score", "score": 5},
            {"title": "High score", "score": 50},
        ]
        result = process_stories(stories, min_score=10)
        assert len(result) == 1
        assert result[0]["title"] == "High score"

    def test_sorts_by_score_descending(self):
        stories = [
            {"title": "A", "score": 10},
            {"title": "B", "score": 100},
            {"title": "C", "score": 50},
        ]
        result = process_stories(stories, min_score=0)
        assert [s["title"] for s in result] == ["B", "C", "A"]

    def test_adds_rank_field(self):
        stories = [{"title": "Story", "score": 42}]
        result = process_stories(stories, min_score=0)
        assert result[0]["rank"] == 1

    def test_filters_none_entries(self):
        stories = [None, {"title": "Valid", "score": 20}, None]
        result = process_stories(stories, min_score=0)
        assert len(result) == 1

    def test_filters_stories_without_title(self):
        stories = [
            {"score": 100},
            {"title": "Has title", "score": 50},
        ]
        result = process_stories(stories, min_score=0)
        assert len(result) == 1
        assert result[0]["title"] == "Has title"
