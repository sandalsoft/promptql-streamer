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


def test_initial_prompt_sent_only_if_user_supplied(monkeypatch):
    # Simulate user-supplied prompt
    monkeypatch.setattr(sys, "argv", ["main.py", "Hello AI!"])
    prompt = get_initial_prompt()
    assert prompt == "Hello AI!"
    # Simulate default prompt
    monkeypatch.setattr(sys, "argv", ["main.py"])
    prompt2 = get_initial_prompt()
    assert prompt2 == "Tell me what you can do"

    # Now test the logic for sending the prompt
    # We'll patch interactive_conversation to capture its arguments
    called_args = {}

    def fake_interactive_conversation(conv, initial_prompt=None):
        called_args['initial_prompt'] = initial_prompt
    # Patch interactive_conversation in main's module
    import main as main_mod
    orig_interactive = main_mod.interactive_conversation
    main_mod.interactive_conversation = fake_interactive_conversation

    # Patch PromptQLClient and conversation
    class DummyConv:
        def __init__(self):
            self.interactions = []

        def send_message(self, prompt, stream=False):
            class Resp:
                message = f"Response to: {prompt}"
            return Resp()

    class DummyClient:
        def create_conversation(self, **kwargs):
            return DummyConv()
    monkeypatch.setattr(main_mod, "PromptQLClient",
                        lambda *a, **k: DummyClient())
    monkeypatch.setattr(main_mod, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "process_artifacts", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "HasuraLLMProvider", lambda *a, **k: None)
    # Test with user-supplied prompt
    monkeypatch.setattr(sys, "argv", ["main.py", "Hello AI!"])
    called_args.clear()
    main_mod.main()
    # Should not pass initial_prompt to interactive_conversation
    assert called_args['initial_prompt'] is None
    # Test with default prompt
    monkeypatch.setattr(sys, "argv", ["main.py"])
    called_args.clear()
    main_mod.main()
    # Should not pass initial_prompt to interactive_conversation
    assert called_args['initial_prompt'] is None
    # Restore
    main_mod.interactive_conversation = orig_interactive
