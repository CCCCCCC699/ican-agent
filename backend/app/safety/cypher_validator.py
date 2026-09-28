"""只读Cypher白名单校验：LLM生成的查询必须通过此校验才能执行。"""
import re

FORBIDDEN = re.compile(
    r"\b(CREATE|DELETE|SET|MERGE|DROP|REMOVE|DETACH|CALL|LOAD|UNWIND|FOREACH|APOC|bolt|file:)\b",
    re.IGNORECASE,
)
COMMENT = re.compile(r"//|/\*|\*/")
MAX_LENGTH = 1000

def validate_cypher(query: str) -> tuple[bool, str]:
    if not query or not isinstance(query, str):
        return False, "查询为空"
    if len(query) > MAX_LENGTH:
        return False, "查询过长"
    if COMMENT.search(query):
        return False, "包含注释，存在注入风险"
    if FORBIDDEN.search(query):
        return False, "包含被禁止的关键字"
    stripped = query.strip().rstrip(";").strip()
    if not re.match(r"^(MATCH|OPTIONAL MATCH)", stripped, re.IGNORECASE):
        return False, "仅允许MATCH开头的只读查询"
    return True, "ok"
