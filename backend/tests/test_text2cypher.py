from app.agents.text2cypher import text_to_cypher
from app.llm.client import LLMClient

class FakeLLM:
    def __init__(self, reply): self.reply = reply
    def chat(self, model=None, messages=None, format=None, **kw):
        return {"message": {"content": self.reply}}

def test_valid_cypher_executed():
    llm = LLMClient("fake", _ollama=FakeLLM('{"cypher": "MATCH (ls:LineStation {station:\'人民广场\'}) RETURN ls.line AS line"}'))
    calls = []
    def executor(q):
        calls.append(q)
        return [{"line": "1号线"}, {"line": "2号线"}]
    r = text_to_cypher(llm, "人民广场可以换乘哪几条线？", executor)
    assert r["ok"] and len(r["records"]) == 2 and len(calls) == 1

def test_invalid_cypher_rejected():
    llm = LLMClient("fake", _ollama=FakeLLM('{"cypher": "MATCH (s) DELETE s"}'))
    def executor(q): raise AssertionError("不应执行")
    r = text_to_cypher(llm, "删掉所有节点", executor)
    assert not r["ok"] and "校验" in r["error"]

def test_garbage_output_rejected():
    llm = LLMClient("fake", _ollama=FakeLLM("呃……"))
    def executor(q): raise AssertionError("不应执行")
    r = text_to_cypher(llm, "随便问", executor)
    assert not r["ok"]
