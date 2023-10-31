"""
Module contains interface to run async tasks from GUI.
"""
from typing import Callable
from threading import Thread
from functools import wraps

import asyncio
import importlib
import tkinter.messagebox as msgbox


CONF_TASK_SLEEP = 0.1


class GLOBAL:
    async_thread: Thread = None
    loop: asyncio.AbstractEventLoop = None


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
                msgbox.showerror(message=f"{exc}\n(Exception in {fnc.__name__})", master=parent)

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
            result = msgbox.askyesnocancel("Confirm", "Are you sure?", master=self if self_parent else None)
            if result:
                return fnc(self, *args, **kwargs) if self is not None else fnc(*args, **kwargs)

        return wrapper

    if callable(self_parent):  # Function used as the decorator
        fnc = self_parent
        self_parent = None
        return _gui_confirm_action(fnc)

    return _gui_confirm_action
