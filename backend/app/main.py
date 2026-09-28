"""FastAPI入口：/api/chat 完整Agent流水线，/api/graph/preview 子图可视化。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import settings
from app.graph.neo4j_store import Neo4jStore
from app.graph.planner import build_metro_graph
from app.llm.client import LLMClient
from app.orchestrator import Orchestrator

app = FastAPI(title="申城智行")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_llm = LLMClient(settings.ollama_model)
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
