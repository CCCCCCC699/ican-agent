from app.llm.client import LLMClient

class FakeOllama:
    def __init__(self, reply): self.reply = reply; self.calls = []
    def chat(self, model, messages, format=None):
        self.calls.append((model, messages, format))
        return {"message": {"content": self.reply}}

def test_chat_passes_messages():
    fake = FakeOllama("你好")
    c = LLMClient(model="fake-model", _ollama=fake)
    out = c.chat("sys", "user")
    assert out == "你好"
    model, messages, fmt = fake.calls[0]
    assert model == "fake-model"
    assert messages[0] == {"role": "system", "content": "sys"}
    assert messages[1] == {"role": "user", "content": "user"}

def test_json_mode_sets_format():
    fake = FakeOllama('{"a": 1}')
    c = LLMClient(model="m", _ollama=fake)
    c.chat("s", "u", json_mode=True)
    assert fake.calls[0][2] == "json"
