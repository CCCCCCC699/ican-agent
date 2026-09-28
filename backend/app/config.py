from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ican2026"
    ollama_model: str = "qwen3:8b"
    ollama_base_url: str = "http://localhost:11434"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

settings = Settings()
