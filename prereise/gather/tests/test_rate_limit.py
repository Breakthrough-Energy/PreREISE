import time

import pytest

from prereise.gather.rate_limit import RateLimit


@pytest.fixture
def sleepless(monkeypatch):
    class SleepCounter:
        def __init__(self):
            self.time_sleeping = 0
            self.init_time = time.time()

        def time(self):
            return self.init_time + self.time_sleeping

        def sleep(self, seconds):
            self.time_sleeping += seconds

    counter = SleepCounter()
    monkeypatch.setattr(time, "sleep", counter.sleep)
    monkeypatch.setattr(time, "time", counter.time)
    return counter


def test_default_no_limit(sleepless):
    limiter = RateLimit()
    _ = [limiter.invoke(lambda: i + 1) for i in range(10)]
    assert sleepless.time_sleeping == 0


def test_limit_takes_times(sleepless):
    limiter = RateLimit(42)
    _ = [limiter.invoke(lambda: i + 1) for i in range(10)]
    assert sleepless.time_sleeping >= 420
