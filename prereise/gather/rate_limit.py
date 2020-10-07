import time
from datetime import timedelta


class RateLimit:
    def __init__(self, interval=None):
        self.interval = interval
        self.last_run_at = time.time()

    def invoke(self, action):
        if self.interval is None:
            return action()
        elapsed = time.time() - self.last_run_at
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        result = action()
        self.last_run_at = time.time()
        return result
