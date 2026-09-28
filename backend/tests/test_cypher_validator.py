from app.safety.cypher_validator import validate_cypher

def test_allow_read_query():
    ok, reason = validate_cypher("MATCH (s:Station {name:'人民广场'}) RETURN s")
    assert ok, reason

def test_reject_write_query():
    ok, _ = validate_cypher("MATCH (s:Station) DELETE s")
    assert not ok

def test_reject_non_match_start():
    ok, _ = validate_cypher("RETURN 1")
    assert not ok

def test_reject_comments():
    ok, _ = validate_cypher("MATCH (s:Station)//comment\nRETURN s")
    assert not ok

def test_reject_call_apoc():
    ok, _ = validate_cypher("MATCH (s) CALL apoc.load.json('file:///etc/passwd') YIELD x RETURN x")
    assert not ok

def test_reject_empty():
    ok, _ = validate_cypher("")
    assert not ok
