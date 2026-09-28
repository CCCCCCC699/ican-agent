"""Neo4j存储：CSV导入与只读查询执行。"""
import csv
from neo4j import GraphDatabase

class Neo4jStore:
    def __init__(self, settings):
        self.settings = settings
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))

    def close(self):
        self._driver.close()

    def import_from_csv(self, data_dir):
        def tx(tx):
            tx.run("MATCH (n) DETACH DELETE n")
            for query in [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (ls:LineStation) REQUIRE ls.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Line) REQUIRE l.id IS UNIQUE",
            ]:
                tx.run(query)
        with self._driver.session() as s:
            s.execute_write(tx)
        with self._driver.session() as s:
            with open(data_dir / "lines.csv", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f)]
            s.run("UNWIND $rows AS r MERGE (l:Line {id: r['line_id']}) "
                  "SET l.name = r['line_name'], l.color = r['color']", rows=rows)
            with open(data_dir / "line_stations.csv", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f)]
            s.run("UNWIND $rows AS r MERGE (ls:LineStation {id: r['line_station_id']}) "
                  "SET ls.station = r['station_name'], ls.line = r['line_name'], "
                  "ls.order = toInteger(r['station_order']), ls.is_transfer = r['is_transfer']", rows=rows)
            s.run("MATCH (ls:LineStation), (l:Line) WHERE ls.line = l.name "
                  "MERGE (ls)-[:ON_LINE]->(l)")
            # 同线相邻关系
            s.run("MATCH (a:LineStation)-[:ON_LINE]->(l:Line)<-[:ON_LINE]-(b:LineStation) "
                  "WHERE a.line = b.line AND a.order = b.order - 1 "
                  "MERGE (a)-[:NEXT_STATION]->(b)")
            with open(data_dir / "transfers.csv", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f)]
            s.run("UNWIND $rows AS r MATCH (a:LineStation {id: r['from_line_station_id']}), "
                  "(b:LineStation {id: r['to_line_station_id']}) "
                  "MERGE (a)-[:TRANSFER_TO {transfer_type: r['transfer_type'], "
                  "transfer_time: toInteger(r['transfer_time'])}]->(b)", rows=rows)

    def run_read_query(self, query: str) -> list[dict]:
        with self._driver.session() as s:
            return [dict(r) for r in s.run(query)]

    def preview_subgraph(self, station: str, depth: int = 1) -> dict:
        with self._driver.session() as s:
            result = s.run(
                "MATCH p=(a:LineStation)-[*1..$d]-(b:LineStation) "
                "WHERE a.station = $station RETURN p LIMIT 100", d=depth, station=station)
            nodes, edges = {}, []
            for record in result:
                for rel in record["p"].relationships:
                    for node in (rel.start_node, rel.end_node):
                        nodes[node.element_id] = {
                            "id": node["id"], "station": node.get("station"), "line": node.get("line"),
                            "label": node.get("station") or node.get("name")}
                    edges.append({"from": nodes[rel.start_node.element_id]["id"],
                                  "to": nodes[rel.end_node.element_id]["id"],
                                  "kind": rel.type})
            return {"nodes": list(nodes.values()), "edges": edges}
