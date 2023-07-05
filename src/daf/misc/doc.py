"""
Utility module for documentation.
"""
# Documentation
from typing import Optional, Dict
from os import environ


__all__ = (
    "doc_category",
)

DOCUMENTATION_MODE = bool(environ.get("DOCUMENTATION", False))
if DOCUMENTATION_MODE:
    cat_map: Dict[str, list] = {}


def doc_category(cat: str,
                 manual: Optional[bool] = False,
                 path: Optional[str] = None):
    """
    Used for marking under which category this should
    be put when auto generating documentation.

    Parameters
    ------------
    cat: str
        The name of the category to put this in.
    manual: Optional[bool]
        Should documentation be manually generated
    path: Optional[str]
        Custom path to the object.

    Returns
    ----------
    Decorator
        Returns decorator which marks the object
        to the category.
    """
    def _category(item):
        if DOCUMENTATION_MODE:
            cat_map[cat].append((item, manual, path))
        return item

    if DOCUMENTATION_MODE:
        if cat not in cat_map:
            cat_map[cat] = []

    return _category
