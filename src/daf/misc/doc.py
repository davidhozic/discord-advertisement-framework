"""
Utility module for documentation.
"""
# Documentation
from typing import Optional, Dict, Literal
from os import environ


__all__ = (
    "doc_category",
)

DOCUMENTATION_MODE = bool(environ.get("DOCUMENTATION", False))
if DOCUMENTATION_MODE:
    cat_map: Dict[str, list] = {"Program": {}, "HTTP": {}}


def doc_category(
    cat: str,
    manual: Optional[bool] = False,
    path: Optional[str] = None,
    api_type: Literal["Program", "HTTP"] = "Program"
):
    """
    Used to mark the object for documentation.
    Objects marked with this decorator function will
    have :mod:`sphinx.ext.autodoc` directives generated automatically.

    Parameters
    ------------
    cat: str
        The name of the category to put this in.
    manual: Optional[bool]
        Generate ``function`` directives instead of ``autofunction``.
        Should be used when dealing with overloads.
    path: Optional[str]
        Custom path to the object.
    api_type: Literal["Program", "HTTP"]
        The type of API, the documented item belongs to.
        Defaults to 'Program'
    """
    def _category(item):  # item == class or function
        if DOCUMENTATION_MODE:
            cat_map[api_type][cat].append((item, manual, path))
        return item

    if DOCUMENTATION_MODE:
        if cat not in cat_map[api_type]:
            cat_map[api_type][cat] = []

    return _category
