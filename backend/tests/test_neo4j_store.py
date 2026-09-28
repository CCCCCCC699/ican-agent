import pytest
from neo4j import GraphDatabase
from app.config import settings
from app.graph.neo4j_store import Neo4jStore

def _available() -> bool:
    try:
        with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as d:
            d.verify_connectivity()
        return True
    except Exception:
        return False

pytestmark = pytest.mark.skipif(not _available(), reason="Neo4j未启动")

def test_import_and_query():
    store = Neo4jStore(settings)
    store.import_from_csv(settings.data_dir)
    records = store.run_read_query(
        "MATCH (ls:LineStation {station:'人民广场'}) RETURN DISTINCT ls.line AS line")
    lines = {r["line"] for r in records}
    assert "1号线" in lines and "2号线" in lines

def test_preview_subgraph():
    store = Neo4jStore(settings)
    g = store.preview_subgraph("人民广场", depth=1)
    assert g["nodes"] and g["edges"]
