"""
Module contains interface to run async tasks from GUI.
"""
from typing import Callable
from functools import wraps

import importlib
from .messagebox import Messagebox


__all__ = (
    "import_class",
    "gui_except",
    "gui_confirm_action",
    "issubclass_noexcept",
)


def import_class(path: str):
    """
    Imports the class provided by it's ``path``.
    """
    path = path.split(".")
    module_path, class_name = '.'.join(path[:-1]), path[-1]
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # Fall back for older versions, try to import from package instead of module
        module_path = module_path.split('.')[0]
        module = importlib.import_module(module_path)

    class_ = getattr(module, class_name)
    return class_


def gui_except(parent = None):
    """
    Propagate any exceptions to the ``parent`` window.
    """
    def decorator(fnc: Callable):
        """
        Decorator that catches exceptions and displays them in GUI.
        """
        @wraps(fnc)
        def wrapper(*args, **kwargs):
            try:
                return fnc(*args, **kwargs)
            except Exception as exc:
                Messagebox.show_error(f"Exception in {fnc.__name__}", str(exc), parent=parent)

        return wrapper

    if callable(parent):  # Assume no parameters given
        fnc = parent
        parent = None
        return decorator(fnc)

    return decorator


def gui_confirm_action(self_parent = False):
    def _gui_confirm_action(fnc: Callable):
        """
        Decorator that asks the user to confirm the action before calling the
        targeted function (fnc).
        """
        def wrapper(self = None, *args, **kwargs):
            result = Messagebox.yesnocancel("Confirm", "Are you sure?", parent=self if self_parent else None)
            if result:
                return fnc(self, *args, **kwargs) if self is not None else fnc(*args, **kwargs)

        return wrapper

    if callable(self_parent):  # Function used as the decorator
        fnc = self_parent
        self_parent = None
        return _gui_confirm_action(fnc)

    return _gui_confirm_action


def issubclass_noexcept(*args):
    try:
        return issubclass(*args)
    except Exception:
        return False
