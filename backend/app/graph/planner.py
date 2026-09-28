"""多约束路径规划：确定性图算法（Dijkstra），支持途经点与避让站。"""
import csv
from pathlib import Path
from typing import Optional

import networkx as nx

ADJACENT_MINUTES = 3  # 相邻站间约3分钟（简化）

def build_metro_graph(data_dir: Path) -> nx.Graph:
    G = nx.Graph()
    with open(data_dir / "line_stations.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        G.add_node(
            row["line_station_id"],
            station=row["station_name"], line=row["line_name"], order=int(row["station_order"]),
        )
    by_line: dict[str, list] = {}
    for row in rows:
        by_line.setdefault(row["line_id"], []).append(row)
    for line_id, stations in by_line.items():
        stations.sort(key=lambda r: int(r["station_order"]))
        for a, b in zip(stations, stations[1:]):
            G.add_edge(a["line_station_id"], b["line_station_id"], kind="adjacent", minutes=ADJACENT_MINUTES)
    with open(data_dir / "transfers.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if G.has_node(row["from_line_station_id"]) and G.has_node(row["to_line_station_id"]):
                G.add_edge(row["from_line_station_id"], row["to_line_station_id"],
                           kind="transfer", minutes=int(row["transfer_time"] or 5))
    return G

def _nodes_by_station(G, name: str):
    return [n for n, d in G.nodes(data=True) if d["station"] == name]

def _shortest(G, start_node: str, end_node: str) -> tuple[Optional[list], Optional[int]]:
    try:
        path = nx.shortest_path(G, start_node, end_node, weight="minutes")
        total = int(sum(G[u][v]["minutes"] for u, v in zip(path, path[1:])))
        return path, total
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, None

def _line_summary(G, node_path):
    """把节点路径按线路切段：[(线路名, [站名...]), ...]。"""
    parts = []
    for n in node_path:
        line = G.nodes[n]["line"]
        station = G.nodes[n]["station"]
        if parts and parts[-1][0] == line:
            parts[-1][1].append(station)
        else:
            parts.append([line, [station]])
    return [{"line": line, "stations": stations} for line, stations in parts]

def _plan_pair(G, start_name: str, end_name: str, banned_names: set[str]):
    H = G.copy()
    for node, d in G.nodes(data=True):
        if d["station"] in banned_names:
            H.remove_node(node)
    best: Optional[tuple] = None
    for sn in _nodes_by_station(H, start_name):
        for en in _nodes_by_station(H, end_name):
            path, total = _shortest(H, sn, en)
            if path is not None and (best is None or total < best[1]):
                best = (path, total, sn, en)
    if best is None:
        return None
    path, total, sn, en = best
    stations = [G.nodes[n]["station"] for n in path]
    return {"node_path": path, "stations": stations, "total": total,
            "line_parts": _line_summary(G, path)}

def plan_route(G, start: str, end: str, via: list[str] = [], avoid: list[str] = []) -> dict:
    banned = set(avoid) - {start, end}  # 避让站与起终点冲突时自动忽略
    stops = [start] + list(via) + [end]
    segments = []
    for a, b in zip(stops, stops[1:]):
        if not _nodes_by_station(G, b):
            return {"ok": False, "error": f"未找到站点「{b}」，请确认站名"}
        seg = _plan_pair(G, a, b, banned)
        if seg is None:
            return {"ok": False, "error": f"在避开{banned or '无'}的约束下，「{a}」到「{b}」之间没有可行路线"}
        segments.append(seg)
    path = segments[0]["stations"]
    for seg in segments[1:]:
        path += seg["stations"][1:]
    # 压缩连续重复站名（换乘站跨线同名）
    compressed = [path[0]]
    for s in path[1:]:
        if s != compressed[-1]:
            compressed.append(s)
    total_time = sum(s["total"] for s in segments)
    return {"ok": True, "path": compressed, "total_time": total_time, "segments": segments}
