"""
This sub-package contains the message definitions.
It is a separate package to reduce number of lines per file."""
from .base import *
from .text_based import *

try:
    from .voice_based import *
except ModuleNotFoundError:
    pass