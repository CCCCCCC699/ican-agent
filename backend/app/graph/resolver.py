"""站点/线路名解析：把用户口语站名模糊匹配到知识图谱规范站名。"""
import csv
import difflib
from pathlib import Path

# 中文数字→阿拉伯数字（先长后短，保证"十八号线"→"18号线"）
_CN_NUM = [("十八", "18"), ("十七", "17"), ("十六", "16"), ("十五", "15"),
           ("十四", "14"), ("十三", "13"), ("十二", "12"), ("十一", "11"),
           ("十", "10"), ("九", "9"), ("八", "8"), ("七", "7"), ("六", "6"),
           ("五", "5"), ("四", "4"), ("三", "3"), ("二", "2"), ("一", "1")]

def _cn_to_digits(s: str) -> str:
    for k, v in _CN_NUM:
        s = s.replace(k, v)
    return s

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

def load_line_names(data_dir: Path) -> list[str]:
    names: list[str] = []
    with open(data_dir / "lines.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names.append(row["line_name"])
    return names

def resolve_line(name: str, line_names: list[str]) -> str | None:
    name = name.strip()
    if name in line_names:
        return name
    normalized = _cn_to_digits(name)  # "一号线"→"1号线"，"十八号线"→"18号线"
    if normalized in line_names:
        return normalized
    if normalized.startswith("地铁") and normalized[2:] in line_names:
        return normalized[2:]  # "地铁1号线"→"1号线"
    matches = difflib.get_close_matches(normalized, line_names, n=1, cutoff=0.55)
    return matches[0] if matches else None
