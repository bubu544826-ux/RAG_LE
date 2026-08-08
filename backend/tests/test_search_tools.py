import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search_tools import CourseOutlineTool, CourseSearchTool
from vector_store import SearchResults


def make_results(
    *,
    document: str = "Lesson content",
    course_title: str = "Building AI Agents",
    lesson_number: int | None = 2,
) -> SearchResults:
    metadata = {"course_title": course_title}
    if lesson_number is not None:
        metadata["lesson_number"] = lesson_number

    return SearchResults(
        documents=[document],
        metadata=[metadata],
        distances=[0.1],
    )


def test_format_results_links_lesson_citation_without_showing_url() -> None:
    store = MagicMock()
    store.get_lesson_link.return_value = "https://example.com/courses/agents/lesson-2"
    tool = CourseSearchTool(store)

    tool._format_results(make_results())

    assert tool.last_sources == [
        '<a href="https://example.com/courses/agents/lesson-2" '
        'target="_blank" rel="noopener noreferrer">'
        "Building AI Agents - Lesson 2</a>"
    ]
    store.get_lesson_link.assert_called_once_with("Building AI Agents", 2)


def test_format_results_escapes_link_and_visible_label() -> None:
    store = MagicMock()
    store.get_lesson_link.return_value = (
        'https://example.com/watch?lesson=2&name="agents"'
    )
    tool = CourseSearchTool(store)

    tool._format_results(make_results(course_title="Agents & <Tools>"))

    assert tool.last_sources == [
        '<a href="https://example.com/watch?lesson=2&amp;name=&quot;agents&quot;" '
        'target="_blank" rel="noopener noreferrer">'
        "Agents &amp; &lt;Tools&gt; - Lesson 2</a>"
    ]


def test_format_results_without_lesson_link_keeps_plain_text_source() -> None:
    store = MagicMock()
    store.get_lesson_link.return_value = None
    tool = CourseSearchTool(store)

    tool._format_results(make_results())

    assert tool.last_sources == ["Building AI Agents - Lesson 2"]


def test_format_results_without_lesson_metadata_keeps_plain_text_source() -> None:
    store = MagicMock()
    tool = CourseSearchTool(store)

    formatted = tool._format_results(
        make_results(document="Course overview", lesson_number=None)
    )

    assert formatted == "[Building AI Agents]\nCourse overview"
    assert tool.last_sources == ["Building AI Agents"]
    store.get_lesson_link.assert_not_called()


def test_format_results_keeps_model_context_unchanged() -> None:
    store = MagicMock()
    store.get_lesson_link.return_value = "https://example.com/lesson-2"
    tool = CourseSearchTool(store)

    formatted = tool._format_results(
        make_results(document="Retrieval context sent to the model")
    )

    assert formatted == (
        "[Building AI Agents - Lesson 2]\n" "Retrieval context sent to the model"
    )


def test_outline_tool_definition_requires_course_title() -> None:
    tool = CourseOutlineTool(MagicMock())

    definition = tool.get_tool_definition()

    assert definition["name"] == "get_course_outline"
    assert definition["input_schema"]["properties"]["course_title"]["type"] == (
        "string"
    )
    assert definition["input_schema"]["required"] == ["course_title"]


def test_outline_tool_returns_complete_ordered_outline() -> None:
    store = MagicMock()
    store.get_course_outline.return_value = {
        "title": "Building AI Agents",
        "course_link": "https://example.com/courses/agents",
        "lessons": [
            {"lesson_number": 2, "lesson_title": "Tools"},
            {"lesson_number": 1, "lesson_title": "Introduction"},
        ],
    }
    tool = CourseOutlineTool(store)

    result = tool.execute("AI Agents")

    assert result == (
        "Course Title: Building AI Agents\n"
        "Course Link: https://example.com/courses/agents\n"
        "Lesson 2: Tools\n"
        "Lesson 1: Introduction"
    )
    store.get_course_outline.assert_called_once_with("AI Agents")


def test_outline_tool_marks_missing_link_unavailable() -> None:
    store = MagicMock()
    store.get_course_outline.return_value = {
        "title": "Building AI Agents",
        "course_link": None,
        "lessons": [],
    }
    tool = CourseOutlineTool(store)

    result = tool.execute("AI Agents")

    assert result == ("Course Title: Building AI Agents\n" "Course Link: Unavailable")


def test_outline_tool_reports_no_matching_course() -> None:
    store = MagicMock()
    store.get_course_outline.return_value = None
    tool = CourseOutlineTool(store)

    assert tool.execute("Unknown Course") == (
        "No course found matching 'Unknown Course'."
    )
