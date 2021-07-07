import pytest

from prereise.gather.request_util import retry


class CustomError(Exception):
    pass


def test_max_times_reached():
    @retry(max_attempts=3, allowed_exceptions=CustomError)
    def no_fail(x=[]):
        x.append(len(x))
        raise CustomError()

    counts = []
    no_fail(counts)
    assert len(counts) == 3


def test_raises_after_max_attempts():
    @retry(max_attempts=3, raises=True, allowed_exceptions=CustomError)
    def func():
        raise CustomError()

    with pytest.raises(CustomError):
        func()


def test_return_value():
    @retry()
    def return_something():
        return 42

    assert 42 == return_something()


def test_decorate_without_call():
    @retry
    def still_works():
        return 42

    assert 42 == still_works()


def test_unhandled_exception():
    @retry()
    def fail():
        raise Exception()

    with pytest.raises(Exception):
        fail()


def test_counter_attribute():
    limit = 3

    @retry(max_attempts=limit, allowed_exceptions=CustomError)
    def best_attempt():
        x = best_attempt.retry_count
        if best_attempt.retry_count < limit:
            raise CustomError
        return x

    assert limit == best_attempt()
