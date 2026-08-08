import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_system import RAGSystem


def test_rag_system_registers_search_and_outline_tools() -> None:
    config = SimpleNamespace(
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        CHROMA_PATH="unused",
        EMBEDDING_MODEL="unused",
        MAX_RESULTS=5,
        ANTHROPIC_API_KEY="unused",
        ANTHROPIC_MODEL="unused",
        MAX_HISTORY=2,
    )

    with (
        patch("rag_system.DocumentProcessor"),
        patch("rag_system.VectorStore"),
        patch("rag_system.AIGenerator"),
        patch("rag_system.SessionManager"),
    ):
        rag_system = RAGSystem(config)

    definitions = rag_system.tool_manager.get_tool_definitions()

    assert [definition["name"] for definition in definitions] == [
        "search_course_content",
        "get_course_outline",
    ]
