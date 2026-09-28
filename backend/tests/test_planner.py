from app.config import settings
from app.graph.planner import build_metro_graph, plan_route

G = build_metro_graph(settings.data_dir)

def test_direct_route():
    r = plan_route(G, "莘庄", "人民广场")
    assert r["ok"], r.get("error")
    assert r["path"][0] == "莘庄" and r["path"][-1] == "人民广场"
    assert r["total_time"] > 0

def test_route_with_via():
    r = plan_route(G, "莘庄", "五角场", via=["徐家汇"])
    assert r["ok"], r.get("error")
    i = r["path"].index("徐家汇")
    assert 0 < i < len(r["path"]) - 1

def test_route_with_avoid():
    r = plan_route(G, "莘庄", "人民广场", avoid=["徐家汇"])
    assert r["ok"], r.get("error")
    assert "徐家汇" not in r["path"]

def test_unknown_station():
    r = plan_route(G, "莘庄", "不存在的站")
    assert not r["ok"]
    assert "不存在的站" in r["error"]
