"""helper methods for other modules."""

import time
from functools import wraps
from datetime import timedelta


def duration(func):
    """Decorator to measure time used by a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """This is a wrapper function."""
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        end_time = time.monotonic()
        print(f'Time elapsed: {timedelta(seconds = end_time - start_time)}')
        return result
    return wrapper
