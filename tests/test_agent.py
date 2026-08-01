from __future__ import annotations

import copy
from typing import Any

from ragmod.agent.loop import ask


class ScriptedClient:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []
        self.responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": '{"path":"answer.py","start":1,"end":2}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {"choices": [{"message": {"content": "The answer is implemented in answer.py."}}]},
    ]

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(copy.deepcopy(payload))
        return self.responses.pop(0)


def test_agent_executes_tool_and_returns_citations(tmp_path):
    (tmp_path / "answer.py").write_text("VALUE = 42\nprint(VALUE)\n", encoding="utf-8")
    client = ScriptedClient()

    answer = ask("Where is the answer?", tmp_path, client=client, model="test-model")

    assert answer["text"] == "The answer is implemented in answer.py."
    assert answer["citations"] == [{"path": "answer.py", "start": 1, "end": 2}]
    assert answer["turns"] == 2
    bootstrap_message = client.payloads[0]["messages"][-1]
    assert bootstrap_message["role"] == "tool"
    assert bootstrap_message["content"].startswith("# tool_result search_repo")
    tool_message = client.payloads[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["content"].startswith("# tool_result read_file")
