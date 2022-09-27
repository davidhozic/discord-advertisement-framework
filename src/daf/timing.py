"""
Module contains definitions that are related to time.
"""

import time


def timeit(num: int):
    """
    Decorator that prints average time to execute specific function.

    Parameters
    ------------
    num: int
        Number of samples to take for average
    """
    def _timeit(fnc):
        sum = 0
        ct = 0
        async def __timeit(*args, **kwargs):
            nonlocal sum
            nonlocal ct

            start = time.time()
            ret = await fnc(*args, **kwargs)
            end = time.time()
            ms = (end-start)*1000

            sum += ms
            ct += 1
            if ct == num:
                print(f"{fnc.__name__} took {sum/ct} ms on average")
                ct = 0
                sum = 0
            return ret
        return __timeit

    if callable(num): # is a function (function was used as decorator)
        tmp = num
        num = 1
        return _timeit(tmp)
    return _timeit

# Deprecated
class TIMER:
    """
    Used in MESSAGE objects as a send timer.

    .. deprecated:: v2.1
        Since v2.1, absolute timestamp is used.
    """
    __slots__ = (
        "running",
        "startms"
    )

    def __init__(self):
        self.running = False
        self.startms = 0

    def start(self):
        """
        Start the timer.
        """
        if not self.running:
            self.running = True
            self.startms = time.time()

    def elapsed(self):
        """
        Returns the elapsed time in seconds.
        """
        if self.running:
            return time.time() - self.startms
        self.start()
        return 0

    def reset (self):
        """
        Resets the timer.
        """
        self.running = False
