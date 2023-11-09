"""
Graphical interface for Discord Advertisement Framework.
"""
from .tod_extensions.loader import register_extensions
register_extensions()
from .main import run
