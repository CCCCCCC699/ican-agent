from datetime import datetime
from app.config import settings
from app.graph.congestion import slot_for, load_congestion, query_congestion

DATA = load_congestion(settings.data_dir)

def test_slot_weekday_boundaries():
    assert slot_for(datetime(2026, 9, 28, 7, 0)) == "早高峰"    # 周一
    assert slot_for(datetime(2026, 9, 28, 8, 59)) == "早高峰"
    assert slot_for(datetime(2026, 9, 28, 9, 0)) == "平峰"
    assert slot_for(datetime(2026, 9, 28, 16, 59)) == "平峰"
    assert slot_for(datetime(2026, 9, 28, 17, 0)) == "晚高峰"
    assert slot_for(datetime(2026, 9, 28, 18, 59)) == "晚高峰"
    assert slot_for(datetime(2026, 9, 28, 19, 0)) == "夜间"
    assert slot_for(datetime(2026, 9, 28, 6, 0)) == "夜间"

def test_slot_weekend():
    assert slot_for(datetime(2026, 9, 26, 10, 0)) == "周末"    # 周六
    assert slot_for(datetime(2026, 9, 27, 8, 0)) == "周末"     # 周日早高峰也走周末档

def test_query_peak():
    info = query_congestion(DATA, "1号线", datetime(2026, 9, 28, 8, 0))
    assert info["slot"] == "早高峰"
    assert info["level"] == "非常拥挤"
    assert info["occupancy_pct"] > 100

def test_query_offpeak():
    info = query_congestion(DATA, "16号线", datetime(2026, 9, 28, 22, 30))
    assert info["slot"] == "夜间"
    assert info["occupancy_pct"] < 60

def test_query_unknown_line():
    assert query_congestion(DATA, "不存在的线", datetime(2026, 9, 28, 8, 0)) is None

def test_all_lines_have_all_slots():
    for line, slots in DATA.items():
        assert {"早高峰", "平峰", "晚高峰", "夜间", "周末"} == set(slots.keys()), line
