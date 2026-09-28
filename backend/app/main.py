"""FastAPI入口：/api/chat 完整Agent流水线，/api/graph/preview 子图可视化。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.config import settings
from app.graph.neo4j_store import Neo4jStore
from app.graph.planner import build_metro_graph
from app.llm.client import LLMClient
from app.orchestrator import Orchestrator

app = FastAPI(title="申城智行")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_llm = LLMClient(
    settings.llm_api_model or settings.ollama_model,
    api_base=settings.llm_api_base,
    api_key=settings.llm_api_key,
)
_store = Neo4jStore(settings)
_graph = build_metro_graph(settings.data_dir)
station_names = None  # Orchestrator 内惰性加载

def get_llm(): return _llm
def get_store(): return _store

class ChatIn(BaseModel):
    message: str

@app.post("/api/chat")
def chat(body: ChatIn):
    orch = Orchestrator(get_llm(), get_store(), _graph, settings.data_dir, station_names)
    return orch.handle(body.message)

@app.get("/api/graph/preview")
def graph_preview(station: str, depth: int = 1):
    return get_store().preview_subgraph(station, depth)

@app.get("/health")
def health():
    return {"status": "ok"}

# 前端静态托管（路由优先于静态挂载）
_frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
