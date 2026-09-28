from fastapi.testclient import TestClient
import app.main as main

class FakeLLM:
    def chat(self, system, user, json_mode=False):
        if "意图路由" in system:
            if "从" in user and ("到" in user or "去" in user):
                return '{"intent":"route_plan","from":"莘庄","to":"人民广场","via":[],"avoid":[]}'
            if "路线" in user:
                return '{"intent":"route_plan","from":"","to":""}'
            if "挤" in user or "人多" in user:
                return '{"intent":"congestion_query","line":"1号线"}'
            if "换乘" in user:
                return '{"intent":"info_query","question":"人民广场可以换乘哪几条线？"}'
            return '{"intent":"info_query","question":"' + user + '"}'
        if "Schema" in system:
            return '{"cypher": "MATCH (ls:LineStation {station:\'人民广场\'}) RETURN DISTINCT ls.line AS line"}'
        return "**1号线**和**2号线**。"

class FakeStore:
    def __init__(self): self.queries = []
    def run_read_query(self, q):
        self.queries.append(q)
        return [{"line": "1号线"}, {"line": "2号线"}]
    def preview_subgraph(self, station, depth=1):
        return {"nodes": [{"id": "LS_L01_x", "station": "人民广场", "line": "1号线"},
                          {"id": "LS_L02_x", "station": "人民广场", "line": "2号线"}],
                "edges": [{"from": "LS_L01_x", "to": "LS_L02_x", "kind": "TRANSFER_TO"}]}

main.get_llm = lambda: FakeLLM()
main.get_store = lambda: FakeStore()
main.station_names = ["人民广场", "莘庄"]

client = TestClient(main.app)

def test_chat_info_pipeline():
    r = client.post("/api/chat", json={"message": "人民广场可以换乘哪几条线？"})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "换乘查询"
    assert data["answer"] and data["cypher"] and data["evidence"]
    assert data["evidence"][0]["type"] == "线路"
    assert data["graph"]["nodes"]  # 换乘站有子图
    assert isinstance(data["elapsed_ms"], int)

def test_chat_route_plan():
    r = client.post("/api/chat", json={"message": "从莘庄去人民广场怎么走"})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "路线规划"
    assert data["graph"] and data["graph"]["nodes"]
    assert data["graph"]["nodes"][0]["id"] == "莘庄"

def test_chat_route_plan_missing_station():
    r = client.post("/api/chat", json={"message": "帮我规划一条路线"})
    assert r.status_code == 200
    assert "起点和终点" in r.json()["answer"]

def test_chat_congestion():
    r = client.post("/api/chat", json={"message": "现在1号线挤不挤？"})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "拥挤查询"
    assert data["answer"] and data["evidence"]
    assert any(e["type"] == "线路" and e["name"] == "1号线" for e in data["evidence"])

def test_health():
    assert client.get("/health").json() == {"status": "ok"}
