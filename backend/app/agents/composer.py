"""答案生成Agent：基于图数据证据合成自然语言回答。"""
from app.llm.client import LLMClient
from app.agents.prompts import COMPOSER_SYSTEM

def format_plan_for_llm(plan: dict) -> str:
    lines = [f"规划路线：{' → '.join(plan['path'])}", f"预计总耗时：约{plan['total_time']}分钟"]
    for i, seg in enumerate(plan["segments"], 1):
        lines.append(f"第{i}段（约{seg['total']}分钟）：")
        for part in seg.get("line_parts", []):
            lines.append(f"  {part['line']}：{' → '.join(part['stations'])}")
    return "\n".join(lines)

def compose_answer(llm: LLMClient, question: str, evidence: list[dict]) -> str:
    evidence_text = "\n".join(str(e) for e in evidence[:30]) or "（无数据）"
    user = f"用户问题：{question}\n\n知识图谱查询结果：\n{evidence_text}"
    return llm.chat(COMPOSER_SYSTEM, user).strip()
