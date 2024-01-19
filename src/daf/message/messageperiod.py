from abc import ABC, abstractmethod
from datetime import datetime, timedelta, time
from random import randrange


__all__ = (
    "BaseMessagePeriod",
    "DurationPeriod",
    "EveryXPeriod",
    "FixedDurationPeriod",
    "RandomizedDurationPeriod",
    "DailyPeriod",
)


class BaseMessagePeriod(ABC):
    """
    Interface for implementing message periods.
    Subclasses can be passed to ``xMESSAGE``'s ``period`` parameter.
    """
    @abstractmethod
    def get(self) -> timedelta:
        "Returns the message (sendoing) period."
        pass

    @abstractmethod
    def adjust(self, minimum: timedelta) -> None:
        """
        Adjust the period to always be greater than the ``minimum``.
        """
        pass


class DurationPeriod(BaseMessagePeriod):
    """
    Interface for duration-like message periods.
    """
    pass


class EveryXPeriod(BaseMessagePeriod):
    """
    Interface for every-x-like message periods.
    The X can be Day, Month, Year, ...
    """
    pass


class FixedDurationPeriod(DurationPeriod):
    """
    A fixed message (sending) period.

    Parameter
    ---------------
    duration: timedelta
        The period duration (how much time to wait after every send).
    """
    def __init__(self, duration: timedelta) -> None:
        self.duration = duration

    def get(self):
        return self.duration
    
    def adjust(self, minimum: timedelta) -> None:
        self.duration = max(minimum, self.duration)


class RandomizedDurationPeriod(DurationPeriod):
    """
    A randomized message (sending) period.
    After every send, the message will wait a different randomly
    chosen period within ``minimum`` and ``maximum``.

    Parameters
    --------------
    minimum: timedelta
        Bottom limit of the randomized period.
    maximum: timedelta
        Upper limit of the randomized period.
    """
    def __init__(self, minimum: timedelta, maximum: timedelta) -> None:
        self.minimum = minimum
        self.maximum = maximum
    
    def get(self):
        return timedelta(seconds=randrange(*self.minimum.total_seconds(), self.maximum.total_seconds()))

    def adjust(self, minimum: timedelta) -> None:
        if self.minimum >= minimum:
            return
        
        self.maximum = minimum + (self.maximum - self.minimum)  # Preserve the period band's width
        self.minimum = minimum


class DailyPeriod(EveryXPeriod):
    """
    Represents a daily send period.
    Messages will be sent every day at ``time``.
    """
    def __init__(self, time: time) -> None:
        if time.tzinfo is None:
            time = time.replace(tzinfo=datetime.now().astimezone().tzinfo)

        self.time = time
    
    def get(self) -> timedelta:
        now = datetime.now().astimezone()
        now_time = now.timetz()
        self_time = self.time
        if now_time >= self_time:
            next_datetime = (now + timedelta(days=1))  # Go to next day
        else:
            next_datetime = now

        # Replace the hour of either today / next day and then calculate
        # the difference from current datetime
        delta = next_datetime.replace(
            hour=self_time.hour,
            minute=self_time.minute,
            second=self_time.second,
            microsecond=self_time.microsecond
        ) - now

        return delta

    def adjust(self, minimum: timedelta) -> None:
        pass  # Slow-mode can be max 6 hours. EveryDayPeriod will be 24 hours.
