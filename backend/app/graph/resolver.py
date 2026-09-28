"""站点名解析：把用户口语站名模糊匹配到知识图谱规范站名。"""
import csv
import difflib
from pathlib import Path

def load_station_names(data_dir: Path) -> list[str]:
    names: list[str] = []
    with open(data_dir / "line_stations.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["station_name"] not in names:
                names.append(row["station_name"])
    return names

def resolve_station(name: str, station_names: list[str]) -> str | None:
    name = name.strip()
    if name in station_names:
        return name
    matches = difflib.get_close_matches(name, station_names, n=1, cutoff=0.55)
    return matches[0] if matches else None
