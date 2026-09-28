from fastapi.testclient import TestClient
import app.main as main

class FakeLLM:
    def chat(self, system, user, json_mode=False):
        if "意图路由" in system:
            return '{"intent":"info_query","question":"人民广场可以换乘哪几条线？"}'
        if "Schema" in system:
            return '{"cypher": "MATCH (ls:LineStation {station:\'人民广场\'}) RETURN DISTINCT ls.line AS line"}'
        return "1号线和2号线。"

class FakeStore:
    def __init__(self): self.queries = []
    def run_read_query(self, q):
        self.queries.append(q)
        return [{"line": "1号线"}, {"line": "2号线"}]
    def preview_subgraph(self, station, depth=1):
        return {"nodes": [], "edges": []}

main.get_llm = lambda: FakeLLM()
main.get_store = lambda: FakeStore()
main.station_names = ["人民广场"]

client = TestClient(main.app)

def test_chat_pipeline():
    r = client.post("/api/chat", json={"message": "人民广场可以换乘哪几条线？"})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "info_query"
    assert data["answer"] and data["cypher"] and data["evidence"]

def test_chat_route_plan():
    r = client.post("/api/chat", json={"message": "从莘庄去人民广场"})
    assert r.status_code == 200

def test_health():
    assert client.get("/health").json() == {"status": "ok"}
