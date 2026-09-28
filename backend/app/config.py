import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env（若存在），优先级低于已设置的环境变量
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

@dataclass(frozen=True)
class Settings:
    neo4j_uri: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password: str = os.environ.get("NEO4J_PASSWORD", "ican2026")
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    # OpenAI兼容云API（DeepSeek/智谱/硅基流动/百炼等通用）
    llm_api_base: str = os.environ.get("LLM_API_BASE", "")
    llm_api_key: str = os.environ.get("LLM_API_KEY", "")
    llm_api_model: str = os.environ.get("LLM_API_MODEL", "")
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

settings = Settings()
