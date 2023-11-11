"""
Graphical interface for Discord Advertisement Framework.
"""
from .main import run
from .tod_extensions.loader import register_extensions, register_annotations, register_conversions
register_extensions()
register_annotations()
register_conversions()