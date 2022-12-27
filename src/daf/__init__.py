"""
Discord Advertisement Framework

Version 2.4
"""
import _discord as discord
from .client import *
from .core import *
from .dtypes import *
from .guild import *
from .message import *
from .logging import *

from .misc import DOCUMENTATION_MODE
if DOCUMENTATION_MODE:
    from .misc import *
