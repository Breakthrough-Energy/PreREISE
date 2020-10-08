import functools
import time
from datetime import timedelta
from urllib.error import HTTPError


class RateLimit:
    """Provides a way to call an arbitrary function at most once per interval.

    :param int/float interval: the amount of time in seconds to wait between actions
    """

    def __init__(self, interval=None):
        """Constructor"""
        self.interval = interval
        self.last_run_at = time.time()

    def invoke(self, action):
        """Call the action and return its value, waiting if necessary

        :param callable action: the thing to do
        :return: (*Any*) -- the return value of the action
        """
        if self.interval is None:
            return action()
        elapsed = time.time() - self.last_run_at
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        result = action()
        self.last_run_at = time.time()
        return result


def retry(retry_count=5, interval=None, allowed_exceptions=(HTTPError)):
    """Creates a decorator to handle retry logic.

    :param int retry_count: the max number of retries
    :param int/float interval: minimum spacing between retries
    :param tuple allowed_exceptions: exceptions for which the function will be retried, all others will be surfaced to the caller

    :return: (*Any*) -- the return value of the decorated function
    """

    def decorator(func):
        limiter = RateLimit(interval)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(retry_count):
                try:
                    return limiter.invoke(lambda: func(*args, **kwargs))
                except allowed_exceptions as e:
                    print(str(e))
                    pass
            print("Max retries reached!!")

        return wrapper

    return decorator
