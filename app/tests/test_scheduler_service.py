from src.models.task import Task
from src.services.scheduler_service import TaskScheduler


def test_pop_next_returns_highest_priority_first():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="low", priority=9))
    scheduler.submit(Task(name="urgent", priority=0))
    scheduler.submit(Task(name="medium", priority=5))

    first = scheduler.pop_next()
    second = scheduler.pop_next()
    third = scheduler.pop_next()

    assert [first.name, second.name, third.name] == ["urgent", "medium", "low"]


def test_equal_priority_is_fifo():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="a", priority=3))
    scheduler.submit(Task(name="b", priority=3))

    assert scheduler.pop_next().name == "a"
    assert scheduler.pop_next().name == "b"


def test_pop_next_on_empty_queue_returns_none():
    scheduler = TaskScheduler()
    assert scheduler.pop_next() is None


def test_len_reflects_pending_count():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="a", priority=1))
    scheduler.submit(Task(name="b", priority=2))
    assert len(scheduler) == 2
    scheduler.pop_next()
    assert len(scheduler) == 1