from datetime import datetime, timedelta, time
from abc import ABC, abstractmethod
from random import randrange
from typing import Union


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
    Base for implementing message periods.
    Subclasses can be passed to ``xMESSAGE``'s ``period`` parameter.
    """
    def __init__(self, next_send_time: Union[datetime, timedelta]) -> None:
        if next_send_time is None:
            next_send_time = datetime.now()
        elif isinstance(next_send_time, timedelta):
            next_send_time = datetime.now() + next_send_time

        next_send_time = next_send_time.astimezone()
        self.next_send_time: datetime = next_send_time
        self.defer(next_send_time)  # Correct the next time to confirm with the period type

    @abstractmethod
    def defer(self, dt: datetime):
        """
        Defers advertising until ``dt``
        This should be used for overriding the normal next datetime
        the message was supposed to be sent on.
        """
        pass

    def get(self) -> datetime:
        "Returns the next datetime the message is going to be sent."
        return self.next_send_time

    @abstractmethod
    def calculate(self) -> datetime:
        "Calculates the next datetime the message is going to be sent."
        pass

    @abstractmethod
    def adjust(self, minimum: timedelta) -> None:
        """
        Adjust the period to always be greater than the ``minimum``.
        """
        pass


class DurationPeriod(BaseMessagePeriod):
    """
    Base for duration-like message periods.
    """    
    @abstractmethod
    def _get_period(self) -> timedelta:
        "Get's the calculated relative period (offset) from previous scheduled time."
        pass

    def defer(self, dt: datetime):
        while (self.next_send_time) < dt:
            self.calculate()

    def calculate(self):
        current_stamp = datetime.now().astimezone()
        duration = self._get_period()
        while self.next_send_time < current_stamp:
            self.next_send_time += duration

        return self.next_send_time


class EveryXPeriod(BaseMessagePeriod):
    """
    Base for every-x-like message periods.
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
    def __init__(self, duration: timedelta, next_send_time: Union[datetime, timedelta]  = None) -> None:
        self.duration = duration
        super().__init__(next_send_time)

    def _get_period(self):
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
    def __init__(
        self,
        minimum: timedelta,
        maximum: timedelta,
        next_send_time: Union[datetime, timedelta]  = None
    ) -> None:
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(next_send_time)

    
    def _get_period(self):
        return timedelta(seconds=randrange(self.minimum.total_seconds(), self.maximum.total_seconds()))

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
    def __init__(
        self,
        time: time,
        next_send_time: Union[datetime, timedelta]  = None
    ) -> None:
        if time.tzinfo is None:
            time = time.replace(tzinfo=datetime.now().astimezone().tzinfo)

        self.time = time
        super().__init__(next_send_time)

    def defer(self, dt: datetime):
        self.next_send_time = dt
        self.calculate()

    def calculate(self):
        # In case of deferral, the next_send_time will be greater,
        # thus next send time should be relative to that instead of now.
        now = max(datetime.now().astimezone(), self.next_send_time)
        now_time = now.timetz()
        self_time = self.time
        if now_time >= self_time:
            next_datetime = (now + timedelta(days=1))  # Go to next day
        else:
            next_datetime = now

        # Replace the hour of either today / next day and then calculate
        # the difference from current datetime
        next_datetime = next_datetime.replace(
            hour=self_time.hour,
            minute=self_time.minute,
            second=self_time.second,
            microsecond=self_time.microsecond + 100  # + 100 to prevent instant refire
        )
        self.next_send_time = next_datetime
        return next_datetime

    def adjust(self, minimum: timedelta) -> None:
        pass  # Slow-mode can be max 6 hours. EveryDayPeriod will be 24 hours.
