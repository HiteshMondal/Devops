from src.services.log_service import LogIndex

SAMPLE_LOGS = [
    {"timestamp": "2026-01-01T00:00:00", "message": "one"},
    {"timestamp": "2026-01-01T00:05:00", "message": "two"},
    {"timestamp": "2026-01-01T00:10:00", "message": "three"},
    {"timestamp": "2026-01-01T00:15:00", "message": "four"},
]


def test_find_from_returns_matching_and_later_entries():
    index = LogIndex(SAMPLE_LOGS)
    result = index.find_from("2026-01-01T00:10:00")
    assert [r["message"] for r in result] == ["three", "four"]


def test_find_before_returns_earlier_entries():
    index = LogIndex(SAMPLE_LOGS)
    result = index.find_before("2026-01-01T00:10:00")
    assert [r["message"] for r in result] == ["one", "two"]


def test_find_from_timestamp_before_all_entries_returns_all():
    index = LogIndex(SAMPLE_LOGS)
    assert len(index.find_from("2025-01-01T00:00:00")) == len(SAMPLE_LOGS)


def test_find_from_timestamp_after_all_entries_returns_empty():
    index = LogIndex(SAMPLE_LOGS)
    assert index.find_from("2027-01-01T00:00:00") == []