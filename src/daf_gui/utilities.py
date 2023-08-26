"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from threading import Thread, current_thread

from .dpi import dpi_scaled

import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap as ttk

import asyncio
import sys

import daf


CONF_TASK_SLEEP = 0.1


class GLOBAL:
    async_thread: Thread = None
    loop: asyncio.AbstractEventLoop = None


def gui_except(parent = None):
    """
    Propagate any exceptions to the ``parent`` window.
    """
    def decorator(fnc: Callable):
        """
        Decorator that catches exceptions and displays them in GUI.
        """
        def wrapper(*args, **kwargs):
            try:
                return fnc(*args, **kwargs)
            except Exception as exc:
                tkdiag.Messagebox.show_error(f"{exc}\n(Exception in {fnc.__name__})", parent=parent)

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
            result = tkdiag.Messagebox.show_question("Are you sure?", "Confirm", parent=self if self_parent else None)
            if result == "Yes":
                return fnc(self, *args, **kwargs) if self is not None else fnc(*args, **kwargs)

        return wrapper

    if callable(self_parent):  # Function used as the decorator
        fnc = self_parent
        self_parent = None
        return _gui_confirm_action(fnc)

    return _gui_confirm_action
