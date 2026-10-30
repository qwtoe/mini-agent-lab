import json
from types import SimpleNamespace

from mmagent import query_llm
from tools import TOOL_DEFINITIONS, read_file, run_tests


def test_workspace_read_rejects_parent_paths():
    assert not read_file("../../mmagent.py")["ok"]
    assert "def average" in read_file("calculator.py")["content"]


def test_example_returns_a_failing_test_result():
    result = run_tests()
    assert result["exit_code"] == 1
    assert "test_average" in result["stdout"]


def test_agent_passes_tool_result_back_to_model():
    class Message:
        def __init__(self, content, calls):
            self.role = "assistant"
            self.content = content
            self.tool_calls = calls

        def model_dump(self, exclude_none=True):
            calls = []
            for call in self.tool_calls or []:
                calls.append({"id": call.id, "function": {"name": call.function.name, "arguments": call.function.arguments}})
            return {"role": self.role, "content": self.content, "tool_calls": calls}

    call = SimpleNamespace(id="call-1", function=SimpleNamespace(name="read_file", arguments='{"path":"calculator.py"}'))
    replies = iter([Message(None, [call]), Message("The bug is floor division.", None)])
    requests = []

    def create(**kwargs):
        requests.append(list(kwargs["messages"]))
        return SimpleNamespace(choices=[SimpleNamespace(message=next(replies))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert query_llm("Find the bug", TOOL_DEFINITIONS, client) == "The bug is floor division."
    tool_message = requests[1][-1]
    assert tool_message["tool_call_id"] == "call-1"
    assert "//" in json.loads(tool_message["content"])["content"]
