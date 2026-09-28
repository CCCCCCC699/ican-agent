"""Text2Cypher Agent：自然语言→只读Cypher→执行，带安全校验。"""
from app.llm.client import LLMClient, extract_json
from app.agents.prompts import TEXT2CYPHER_SYSTEM
from app.safety.cypher_validator import validate_cypher

def text_to_cypher(llm: LLMClient, question: str, executor) -> dict:
    raw = llm.chat(TEXT2CYPHER_SYSTEM, question, json_mode=True)
    data = extract_json(raw)
    if not data or "cypher" not in data:
        return {"ok": False, "cypher": None, "records": [], "error": "模型未生成有效查询"}
    query = data["cypher"]
    ok, reason = validate_cypher(query)
    if not ok:
        return {"ok": False, "cypher": query, "records": [], "error": f"查询未通过安全校验：{reason}"}
    try:
        records = executor(query)
        return {"ok": True, "cypher": query, "records": records, "error": None}
    except Exception as e:  # 图数据库异常兜底
        return {"ok": False, "cypher": query, "records": [], "error": f"查询执行失败：{e}"}
