"""多Agent流水线编排：路由→执行→生成，输出完整轨迹供前端展示。"""
from app.agents.router import route_intent
from app.agents.text2cypher import text_to_cypher
from app.agents.composer import compose_answer, format_plan_for_llm
from app.graph.planner import plan_route
from app.graph.resolver import load_station_names

class Orchestrator:
    def __init__(self, llm, store, graph, data_dir, station_names=None):
        self.llm, self.store, self.graph, self.data_dir = llm, store, graph, data_dir
        self.station_names = station_names or load_station_names(data_dir)

    def handle(self, message: str) -> dict:
        routed = route_intent(self.llm, message, self.station_names)
        intent = routed["intent"]
        trace = {"intent": intent, "question": message, "cypher": None,
                 "evidence": [], "answer": "", "plan": None}
        if intent == "route_plan":
            args = routed["args"]
            if "from" not in args or "to" not in args:
                trace["answer"] = "请告诉我起点和终点站，例如：从莘庄到人民广场怎么走？"
                return trace
            plan = plan_route(self.graph, args["from"], args["to"],
                              args.get("via", []), args.get("avoid", []))
            trace["plan"] = plan
            if not plan["ok"]:
                trace["answer"] = plan["error"]
                return trace
            trace["answer"] = compose_answer(self.llm, message, [{"plan": format_plan_for_llm(plan)}])
            return trace
        if intent == "info_query":
            result = text_to_cypher(self.llm, routed["args"]["question"], self.store.run_read_query)
            trace["cypher"] = result["cypher"]
            if not result["ok"]:
                trace["answer"] = f"查询失败：{result['error']}"
                return trace
            trace["evidence"] = result["records"]
            trace["answer"] = compose_answer(self.llm, routed["args"]["question"], result["records"])
            return trace
        trace["answer"] = routed["args"].get("reply", "你好，我是申城智行")
        return trace
