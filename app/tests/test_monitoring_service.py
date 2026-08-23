from src.services.monitoring_service import LRUCache, MonitoringService


def test_lru_cache_evicts_least_recently_used():
    cache = LRUCache[str, int](capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # touch 'a' so 'b' becomes least-recently-used
    cache.put("c", 3)  # should evict 'b'

    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_lru_cache_rejects_non_positive_capacity():
    import pytest

    with pytest.raises(ValueError):
        LRUCache(capacity=0)


def test_monitoring_service_records_and_reads_status():
    service = MonitoringService(capacity=10)
    service.record_status("server-1", "HEALTHY")
    assert service.get_cached_status("server-1") == "HEALTHY"
    assert service.get_cached_status("unknown") is None