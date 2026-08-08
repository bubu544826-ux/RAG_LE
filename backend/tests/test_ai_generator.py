import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_generator import AIGenerator


def test_system_prompt_routes_outline_queries_and_requires_complete_output() -> None:
    prompt = AIGenerator.SYSTEM_PROMPT

    assert "search_course_content" in prompt
    assert "get_course_outline" in prompt
    assert "course title, course link, and every lesson number and title" in prompt
    assert "do not summarize, reorder, or omit lessons" in prompt
