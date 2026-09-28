"""意图路由Agent：LLM分类用户输入并结构化提取参数。"""
from app.llm.client import LLMClient, extract_json
from app.agents.prompts import ROUTER_SYSTEM
from app.graph.resolver import resolve_station

def route_intent(llm: LLMClient, user_text: str, station_names: list[str]) -> dict:
    raw = llm.chat(ROUTER_SYSTEM, user_text, json_mode=True)
    data = extract_json(raw)
    if not data or "intent" not in data:
        return {"intent": "info_query", "args": {"question": user_text}}
    intent = data.get("intent", "info_query")
    if intent == "route_plan":
        args = {
            "from": resolve_station(data.get("from", ""), station_names),
            "to": resolve_station(data.get("to", ""), station_names),
            "via": [resolve_station(v, station_names) for v in data.get("via", [])],
            "avoid": [resolve_station(v, station_names) for v in data.get("avoid", [])],
        }
        args = {k: v for k, v in args.items() if v is not None}
        return {"intent": intent, "args": args}
    if intent == "info_query":
        return {"intent": intent, "args": {"question": data.get("question", user_text)}}
    return {"intent": "chitchat", "args": {"reply": data.get("reply", "你好，我是申城智行")}}
