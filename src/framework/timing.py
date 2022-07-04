import time


def timeit(num: int):
    """~ Profiling function ~
    - @Info: Prints average time to execute specific function
    - @Param: 
        - num ~ Number of samples to take for average"""
    def _timeit(fnc):
        sum = 0
        ct = 0
        def __timeit(*args, **kwargs):
            nonlocal sum
            nonlocal ct

            start = time.time()
            ret = fnc(*args, **kwargs)
            end = time.time()
            ms = (end-start)*1000
            
            sum += ms
            ct  += 1
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


class TIMER:
    """ ~ class ~
    - @Info ~ Used in MESSAGE objects as a send timer
    """
    __slots__ = (
        "running",
        "startms"
    )

    def __init__(self):
        self.running = False
        self.startms = 0

    def start(self):
        """ ~ method ~
        - @Info: Start the timer"""
        if not self.running:
            self.running = True
            self.startms = time.time()

    def elapsed(self):
        """ ~ method ~
        - @Info: Returns the elapsed time in seconds"""
        if self.running:
            return time.time() - self.startms
        self.start()
        return 0

    def reset (self):
        """ ~ method ~
        - @Info: Resets the timer"""
        self.running = False