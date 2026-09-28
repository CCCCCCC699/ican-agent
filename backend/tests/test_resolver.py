from app.config import settings
from app.graph.resolver import load_station_names, resolve_station

def test_exact_match():
    names = ["人民广场", "徐家汇", "虹桥火车站"]
    assert resolve_station("徐家汇", names) == "徐家汇"

def test_fuzzy_match():
    names = ["人民广场", "徐家汇", "虹桥火车站"]
    assert resolve_station("徐家汇站", names) == "徐家汇"

def test_no_match():
    names = ["人民广场", "徐家汇"]
    assert resolve_station("不存在的站", names) is None

def test_load_from_csv():
    names = load_station_names(settings.data_dir)
    assert "人民广场" in names
    assert len(names) > 100
