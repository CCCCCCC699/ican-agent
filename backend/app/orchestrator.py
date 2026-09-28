"""多Agent流水线编排：路由→执行→生成，输出前端契约的完整轨迹。

响应契约（与前端index.html约定）：
{intent: 中文意图标签, question, cypher, answer,
 evidence: [{type: 站点|线路|关系, name}], graph: {nodes,edges}|None,
 elapsed_ms: int, intent_key: 内部英文意图}
"""
import time

from app.agents.router import route_intent
from app.agents.text2cypher import text_to_cypher
from app.agents.composer import compose_answer, format_plan_for_llm
from app.graph.planner import plan_route
from app.graph.resolver import load_station_names

INTENT_ROUTE = "路线规划"
INTENT_CONSTRAINT = "约束路线规划"
INTENT_LINE = "线路信息查询"
INTENT_TRANSFER = "换乘查询"
INTENT_CHAT = "闲聊"

ROUTE_CYPHER_HINT = ("确定性图算法：Dijkstra最短路 + 途经点分段 + 避让站剔除（NetworkX）· "
                     "不经过LLM生成，从机制上杜绝编造路线")


def _intent_label(intent_key: str, question: str, args: dict) -> str:
    if intent_key == "route_plan":
        return INTENT_CONSTRAINT if (args.get("via") or args.get("avoid")) else INTENT_ROUTE
    if intent_key == "info_query":
        return INTENT_TRANSFER if ("换乘" in question or "换成" in question or "几条线" in question) else INTENT_LINE
    return INTENT_CHAT


def _route_evidence(plan: dict) -> list[dict]:
    ev = []
    stations = plan["path"]
    if stations:
        ev.append({"type": "站点", "name": stations[0]})
        if len(stations) > 1:
            ev.append({"type": "站点", "name": stations[-1]})
    parts = [p for seg in plan["segments"] for p in seg.get("line_parts", [])]
    seen_lines = []
    for p in parts:
        if p["line"] not in seen_lines:
            seen_lines.append(p["line"])
            ev.append({"type": "线路", "name": p["line"]})
    next_n = sum(len(p["stations"]) - 1 for p in parts)
    if next_n:
        ev.append({"type": "关系", "name": f"NEXT_STATION×{next_n}"})
    transfers = len(parts) - len(plan["segments"])
    if transfers > 0:
        ev.append({"type": "关系", "name": f"TRANSFER_TO×{transfers}"})
    return ev


def _route_graph(plan: dict) -> dict:
    """由规划结果构造图谱载荷：节点id=站名（供证据芯片点击高亮）。"""
    parts = [p for seg in plan["segments"] for p in seg.get("line_parts", [])]
    line_of = {}
    for p in parts:
        for s in p["stations"]:
            line_of.setdefault(s, p["line"])
    transfer_set = {s for s in line_of
                    if any(s in p["stations"] and p["line"] != line_of[s] for p in parts)}
    nodes = [{"id": s, "label": s, "line": line_of[s], "transfer": s in transfer_set}
             for s in plan["path"]]
    edges = []
    for p in parts:
        for a, b in zip(p["stations"], p["stations"][1:]):
            edges.append({"from": a, "to": b, "label": ""})
    return {"nodes": nodes, "edges": edges}


def _info_evidence(records: list[dict]) -> list[dict]:
    ev = []
    for r in records:
        for k, v in r.items():
            if v is None:
                continue
            if k in ("line", "line_name"):
                item = {"type": "线路", "name": str(v)}
            elif k in ("station", "station_name"):
                item = {"type": "站点", "name": str(v)}
            else:
                item = {"type": "关系", "name": f"{k}={v}"}
            if item not in ev:
                ev.append(item)
    return ev


def _info_graph(store, question: str, station_names: list[str], evidence: list[dict]):
    station = next((e["name"] for e in evidence if e["type"] == "站点"), None)
    if not station:
        # 证据中无站点时，从问题文本匹配站名（取最长匹配，避免"上海南站"误配"上海"）
        station = max((n for n in station_names if n in question), key=len, default=None)
    if not station:
        return None
    try:
        g = store.preview_subgraph(station, 1)
    except Exception:
        return None
    id_to_station = {}
    for n in g["nodes"]:
        name = n.get("station") or n.get("label")
        if name:
            id_to_station[n["id"]] = name
    nodes, seen = [], set()
    for n in g["nodes"]:
        name = n.get("station") or n.get("label")
        if name and name not in seen:
            seen.add(name)
            nodes.append({"id": name, "label": name, "line": n.get("line")})
    edges = []
    for e in g["edges"]:
        src, dst = id_to_station.get(e["from"]), id_to_station.get(e["to"])
        if src and dst:
            edges.append({"from": src, "to": dst,
                          "label": "换乘" if e["kind"] == "TRANSFER_TO" else "",
                          "dashes": e["kind"] == "TRANSFER_TO"})
    return {"nodes": nodes, "edges": edges}


class Orchestrator:
    def __init__(self, llm, store, graph, data_dir, station_names=None):
        self.llm, self.store, self.graph, self.data_dir = llm, store, graph, data_dir
        self.station_names = station_names or load_station_names(data_dir)

    def handle(self, message: str) -> dict:
        t0 = time.time()
        routed = route_intent(self.llm, message, self.station_names)
        intent_key = routed["intent"]
        args = routed["args"]
        trace = {"intent": _intent_label(intent_key, message, args),
                 "intent_key": intent_key, "question": message,
                 "cypher": None, "evidence": [], "answer": "", "graph": None}
        if intent_key == "route_plan":
            if "from" not in args or "to" not in args:
                trace["answer"] = "请告诉我起点和终点站，例如：从莘庄到人民广场怎么走？"
            else:
                plan = plan_route(self.graph, args["from"], args["to"],
                                  args.get("via", []), args.get("avoid", []))
                if not plan["ok"]:
                    trace["answer"] = plan["error"]
                else:
                    trace["cypher"] = ROUTE_CYPHER_HINT
                    trace["evidence"] = _route_evidence(plan)
                    trace["graph"] = _route_graph(plan)
                    evidence_text = format_plan_for_llm(plan)
                    constraints = []
                    if args.get("via"):
                        constraints.append(f"途经{'、'.join(args['via'])}")
                    if args.get("avoid"):
                        constraints.append(f"避开{'、'.join(args['avoid'])}")
                    if constraints:
                        evidence_text += "\n已满足约束：" + "；".join(constraints)
                    trace["answer"] = compose_answer(self.llm, message, [{"plan": evidence_text}])
        elif intent_key == "info_query":
            result = text_to_cypher(self.llm, args["question"], self.store.run_read_query)
            trace["cypher"] = result["cypher"]
            if not result["ok"]:
                trace["answer"] = f"查询失败：{result['error']}"
            else:
                trace["evidence"] = _info_evidence(result["records"])
                trace["graph"] = _info_graph(self.store, args["question"],
                                             self.station_names, trace["evidence"])
                trace["answer"] = compose_answer(self.llm, args["question"], result["records"])
        else:
            trace["answer"] = args.get("reply", "你好，我是申城智行")
        trace["elapsed_ms"] = int((time.time() - t0) * 1000)
        return trace
