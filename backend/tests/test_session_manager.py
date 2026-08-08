import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from session_manager import SessionManager


def test_delete_session_removes_messages_and_session() -> None:
    manager = SessionManager()
    session_id = manager.create_session()
    manager.add_exchange(session_id, "Question", "Answer")

    assert manager.delete_session(session_id) is True
    assert session_id not in manager.sessions
    assert manager.get_conversation_history(session_id) is None


def test_delete_session_is_safe_for_unknown_session() -> None:
    manager = SessionManager()

    assert manager.delete_session("unknown-session") is False
