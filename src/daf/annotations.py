"""
Module is responsible to adding additional annotations to some objects (for better GUI support).
"""
import datetime as dt


class timedelta(dt.timedelta):
    __module__ = dt.__name__

    def __init__(cls, days: float = 0, seconds: float = 0, microseconds: float = 0, milliseconds: float = 0, minutes: float = 0, hours: float = 0, weeks: float = 0):
        return super().__init__()


class datetime(dt.datetime):
    __module__ = dt.__name__

    def __init__(cls, year: int, month: int | None=None, day: int | None=None, hour: int=0, minute: int=0, second: int=0, microsecond: int=0, tzinfo: dt.tzinfo | None = None, *, fold: int=0):
        return super().__init__()


dt.timedelta = timedelta
dt.datetime = datetime
