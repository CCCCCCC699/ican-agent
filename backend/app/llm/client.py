"""LLM客户端：支持Ollama本地推理与OpenAI兼容云API（DeepSeek/智谱/硅基流动/百炼等）。"""
import json
import re
from typing import Optional

class LLMClient:
    def __init__(self, model: str, _ollama=None, api_base: str = "", api_key: str = ""):
        self.model = model
        self._ollama = _ollama
        self.api_base = api_base
        self.api_key = api_key

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if self.api_key:
            return self._chat_openai_compatible(messages, json_mode)
        if self._ollama is None:
            import ollama as ollama_pkg
            self._ollama = ollama_pkg
        resp = self._ollama.chat(
            model=self.model,
            messages=messages,
            format="json" if json_mode else None,
        )
        return resp["message"]["content"]

    def _chat_openai_compatible(self, messages: list[dict], json_mode: bool) -> str:
        import httpx
        payload: dict = {"model": self.model, "messages": messages}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = httpx.post(
            f"{self.api_base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

def extract_json(text: str) -> Optional[dict]:
    """从模型输出中稳健提取JSON对象（容忍```json围栏与前后废话）。"""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
