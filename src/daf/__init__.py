"""
Discord Advertisement Framework
"""
import _discord as discord

from . import misc
from . import events

from .client import *
from .core import *
from .dtypes import *
from .guild import *
from .message import *
from .logging import *
from .web import *
from .convert import *
from .remote import *

import sys
import warnings


VERSION = "3.2.0"

if sys.version_info.minor == 12 and sys.version_info.major == 3:
    warnings.warn(
        "DAF's support on Python 3.12 is limited. Web browser features and"
        " SQL logging are not supported in Python 3.12. Please install Python 3.11 instead."
        " Additional GUI may be unstable on Python 3.12"
    )
