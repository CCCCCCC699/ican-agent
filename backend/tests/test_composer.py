from app.agents.composer import compose_answer, format_plan_for_llm
from app.llm.client import LLMClient

def test_compose_passes_evidence():
    class Fake:
        def chat(self, system, user, json_mode=False):
            assert "人民广场" in user
            return "1号线和2号线都在人民广场换乘。"
    r = compose_answer(LLMClient("fake", _ollama=Fake()), "人民广场能换乘哪几条线？", [{"line": "1号线"}, {"line": "2号线"}])
    assert "换乘" in r

def test_format_plan():
    plan = {"ok": True, "path": ["莘庄", "人民广场"], "total_time": 60,
            "segments": [{"stations": ["莘庄", "人民广场"], "total": 60}]}
    text = format_plan_for_llm(plan)
    assert "莘庄" in text and "60" in text
