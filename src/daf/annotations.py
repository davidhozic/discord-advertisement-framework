"""
Module is responsible to adding additional annotations to some objects (for better GUI support).
"""
import datetime as dt


ANNOTATIONS = {
    dt.timedelta: {
        "days": float,
        "seconds": float,
        "microseconds": float,
        "milliseconds": float,
        "minutes": float,
        "hours": float,
        "weeks": float
    },
    dt.datetime: {
        "year": int,
        "month": int | None,
        "day": int | None,
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "tzinfo": dt.tzinfo | None,
        "fold": int
    }
}
