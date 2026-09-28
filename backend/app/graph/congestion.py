"""分时段线路拥挤度模型：基于上海地铁公开客流资料整理估算。

数据来源：上海地铁官方发布的高峰满载率、日均客流等公开资料。
说明：非实时数据，为"线路×时段"静态估算模型，用于演示与出行参考。
"""
import csv
from datetime import datetime
from pathlib import Path

WEEKDAY_SLOTS = {  # (起始小时, 结束小时) -> 时段
    (7, 9): "早高峰",
    (9, 17): "平峰",
    (17, 19): "晚高峰",
}

def slot_for(dt: datetime) -> str:
    """按提问时刻返回时段标签（周末全天走周末档）。"""
    if dt.weekday() >= 5:
        return "周末"
    h = dt.hour
    for (s, e), slot in WEEKDAY_SLOTS.items():
        if s <= h < e:
            return slot
    return "夜间"

def load_congestion(data_dir: Path) -> dict:
    data: dict = {}
    with open(data_dir / "congestion.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data.setdefault(row["line_name"], {})[row["slot"]] = {
                "level": row["level"],
                "occupancy_pct": int(row["occupancy_pct"]),
                "note": row["note"],
            }
    return data

def query_congestion(data: dict, line: str, dt: datetime) -> dict | None:
    slot = slot_for(dt)
    line_data = data.get(line)
    if not line_data or slot not in line_data:
        return None
    info = line_data[slot]
    return {"line": line, "slot": slot,
            "time_label": dt.strftime("%H:%M"),
            "weekday_label": "工作日" if dt.weekday() < 5 else "周末",
            "level": info["level"], "occupancy_pct": info["occupancy_pct"],
            "note": info["note"]}
