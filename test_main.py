import sys
import io
import pytest
from contextlib import redirect_stdout

# Import functions from main
from main import get_initial_prompt, process_artifacts, interactive_conversation


class FakeChunk:
    def __init__(self, message):
        self.message = message


class FakeConversation:
    def __init__(self, artifacts=None):
        self.artifacts = artifacts or []

    def send_message(self, prompt, stream=True):
        # Return a generator yielding one FakeChunk with a fake message.
        def generator():
            yield FakeChunk("Fake response to: " + prompt)
        return generator()


class DummyArtifact:
    def __init__(self, data):
        self.data = data


def test_get_initial_prompt_default(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py"])
    prompt = get_initial_prompt()
    assert prompt == "Tell me what you can do"


def test_get_initial_prompt_custom(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "Hello World"])
    prompt = get_initial_prompt()
    assert prompt == "Hello World"


def test_process_artifacts_list(monkeypatch, capsys):
    # Prepare a fake conversation with artifacts as a list of dicts.
    artifact = DummyArtifact(data=[{"col1": "value1", "col2": "value2"}])

    class FakeConversationWithArtifact:
        artifacts = [artifact]
    process_artifacts(FakeConversationWithArtifact())
    captured = capsys.readouterr().out
    assert "value1" in captured


def test_interactive_conversation_exit(monkeypatch, capsys):
    # Test interactive_conversation function with exit input immediately.
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    fake_conv = FakeConversation()
    # Capture output (will include spinner output, so we just check for the exit message)
    with redirect_stdout(io.StringIO()) as f:
        interactive_conversation(fake_conv, "Initial prompt")
    output = f.getvalue()
    assert "Exiting conversation." in output
