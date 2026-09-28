"""LLM客户端：封装Ollama调用；测试时注入fake。"""
import json
import re
from typing import Optional

class LLMClient:
    def __init__(self, model: str, _ollama=None):
        self.model = model
        self._ollama = _ollama

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        if self._ollama is None:
            import ollama as ollama_pkg
            self._ollama = ollama_pkg
        resp = self._ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            format="json" if json_mode else None,
        )
        return resp["message"]["content"]

def extract_json(text: str) -> Optional[dict]:
    """从模型输出中稳健提取JSON对象（容忍```json围栏与前后废话）。"""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
