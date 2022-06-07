"""
    ~   Tracing    ~
    This modules containes functions and classes
    related to the console debug long or trace.
"""
from enum import Enum, auto
import time
from threading import Lock

__all__ = (
    "TraceLEVELS",
    "trace"
)

m_use_debug = None
m_lock = Lock()

class TraceLEVELS(Enum):
    """
    Info: Level of trace for debug
    """
    NORMAL = 0
    WARNING = auto()
    ERROR =  auto()

def trace(message: str,
          level:   TraceLEVELS = TraceLEVELS.NORMAL):
    """"
    Name : trace
    Param:
    - message : str          = Trace message
    - level   : TraceLEVELS = Level of the trace
    """
    if m_use_debug:
        with m_lock:
            timestruct = time.localtime()
            timestamp = "Date: {:02d}.{:02d}.{:04d} Time:{:02d}:{:02d}"
            timestamp = timestamp.format(timestruct.tm_mday,
                                        timestruct.tm_mon,
                                        timestruct.tm_year,
                                        timestruct.tm_hour,
                                        timestruct.tm_min)
            l_trace = f"{timestamp}\nTrace level: {level.name}\nMessage: {message}\n"
            print(l_trace)
