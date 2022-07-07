"""
    DISCORD ADVERTISEMENT FRAMEWORK (DAF)
    Author      :: David Hozic
    Copyright   :: Copyright (c) 2022 David Hozic
    Version     :: V1.9
"""
import _discord as discord
from .client import *
from .const import *
from .core import *
from .dtypes import *
from .guild import *
from .message import *
from .tracing import *
from .sql import *
from .exceptions import *

# TODO:
# . Edit docstrings
# . Implement .update() method for inherited message objects
# . Implement .update() method for BaseGUILD and inherited guild objects
# . Documentation