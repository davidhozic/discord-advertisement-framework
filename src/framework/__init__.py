"""
    ==============================================
    DISCORD ADVERTISEMENT FRAMEWORK (DAF)
    ==============================================
   +----------+-----------------------------------+
   | Author   |   David Hozic                     |
   | Copyright|   Copyright (c) 2022 David Hozic  |
   | Version  |   v1.9                            |          
   +----------+-----------------------------------+
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

#-----------------
# TODO:
#-----------------
#  Update Examples
#  Check documentation for errors
#  Add Lock objects in xGUILD (add_message, remove_message, update, advertise)