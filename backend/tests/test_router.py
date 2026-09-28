from app.agents.router import route_intent
from app.llm.client import LLMClient

NAMES = ["莘庄", "人民广场", "徐家汇", "陆家嘴", "五角场", "虹桥火车站"]

def fake_llm(reply):
    class Fake:
        def chat(self, model=None, messages=None, format=None, **kw):
            return {"message": {"content": reply}}
    return LLMClient(model="fake", _ollama=Fake())

def test_route_plan_intent():
    reply = '{"intent":"route_plan","from":"虹桥火车站","to":"陆家嘴","via":["徐家汇"],"avoid":["人民广场"]}'
    r = route_intent(fake_llm(reply), "从虹桥火车站去陆家嘴，经过徐家汇，避开人民广场", NAMES)
    assert r["intent"] == "route_plan"
    assert r["args"]["from"] == "虹桥火车站"
    assert r["args"]["via"] == ["徐家汇"]

def test_info_query_intent():
    reply = '{"intent":"info_query","question":"2号线经过哪些换乘站"}'
    r = route_intent(fake_llm(reply), "2号线经过哪些换乘站？", NAMES)
    assert r["intent"] == "info_query"

def test_llm_garbage_output_falls_back():
    reply = "抱歉我不会"
    r = route_intent(fake_llm(reply), "2号线经过哪些换乘站？", NAMES)
    assert r["intent"] == "info_query"  # 解析失败兜底为信息查询

def test_congestion_intent():
    reply = '{"intent":"congestion_query","line":"1号线"}'
    r = route_intent(fake_llm(reply), "现在1号线挤不挤？", NAMES, ["1号线", "2号线", "磁浮线"])
    assert r["intent"] == "congestion_query"
    assert r["args"]["line"] == "1号线"

def test_congestion_intent_chinese_numeral():
    reply = '{"intent":"congestion_query","line":"一号线"}'
    r = route_intent(fake_llm(reply), "一号线人多不多？", NAMES, ["1号线", "2号线"])
    assert r["args"]["line"] == "1号线"
