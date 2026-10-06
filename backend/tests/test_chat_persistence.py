from app.api.v1 import chat
from app.schemas.chat import AnswerOut, CitationOut


def test_dynamic_web_citations_are_not_written_to_local_source_fk(monkeypatch) -> None:
    class FakeDb:
        def __init__(self) -> None:
            self.added: list[object] = []
            self.commits = 0

        def add(self, row: object) -> None:
            self.added.append(row)

        def commit(self) -> None:
            self.commits += 1

        def rollback(self) -> None:
            raise AssertionError("web citations should be skipped before persistence")

    db = FakeDb()
    monkeypatch.setattr(chat, "_save_message", lambda *args, **kwargs: "msg_test")
    result = AnswerOut(
        answer_markdown="DeepSeek 归纳结果",
        status="DONE",
        response_tier="live_rag",
        citations=[
            CitationOut(
                source_id="web:abc123",
                chunk_id="web_abc123",
                title="网页搜索结果",
                public_url="https://example.org/result",
            )
        ],
    )

    message_id = chat._persist_answer(
        db, session_id="chat_test", result=result, question="测试问题"
    )

    assert message_id == "msg_test"
    assert db.added == []
    assert db.commits == 0
