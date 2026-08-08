import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vector_store import VectorStore


def make_store() -> VectorStore:
    """Create a VectorStore without initializing ChromaDB or embeddings."""
    store = VectorStore.__new__(VectorStore)
    store.course_catalog = MagicMock()
    store._resolve_course_name = MagicMock(return_value="Building AI Agents")
    return store


def test_get_course_outline_resolves_title_and_parses_lessons() -> None:
    store = make_store()
    lessons = [
        {
            "lesson_number": 1,
            "lesson_title": "Introduction",
            "lesson_link": "https://example.com/lesson-1",
        },
        {
            "lesson_number": 2,
            "lesson_title": "Tools",
            "lesson_link": "https://example.com/lesson-2",
        },
    ]
    store.course_catalog.get.return_value = {
        "metadatas": [
            {
                "title": "Building AI Agents",
                "course_link": "https://example.com/courses/agents",
                "lessons_json": json.dumps(lessons),
            }
        ]
    }

    outline = store.get_course_outline("AI Agents")

    assert outline == {
        "title": "Building AI Agents",
        "course_link": "https://example.com/courses/agents",
        "lessons": lessons,
    }
    store._resolve_course_name.assert_called_once_with("AI Agents")
    store.course_catalog.get.assert_called_once_with(ids=["Building AI Agents"])


def test_get_course_outline_returns_none_when_title_does_not_resolve() -> None:
    store = make_store()
    store._resolve_course_name.return_value = None

    assert store.get_course_outline("Unknown Course") is None
    store.course_catalog.get.assert_not_called()


def test_get_course_outline_returns_none_for_empty_metadata() -> None:
    store = make_store()
    store.course_catalog.get.return_value = {"metadatas": []}

    assert store.get_course_outline("AI Agents") is None


def test_get_course_outline_returns_none_without_lesson_metadata() -> None:
    store = make_store()
    store.course_catalog.get.return_value = {
        "metadatas": [{"title": "Building AI Agents"}]
    }

    assert store.get_course_outline("AI Agents") is None
