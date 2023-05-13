"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from asyncio import Queue, Task

from daf import trace, TraceLEVELS

import ttkbootstrap.dialogs.dialogs as tkdiag

CONF_TASK_SLEEP = 0.1


class GLOBAL:
    tasks_to_run: Queue = None
    running = False
    async_task: Task = None


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


def gui_confirm_action(fnc: Callable):
    """
    Decorator that asks the user to confirm the action before calling the
    targeted function (fnc).
    """
    def wrapper(*args, **kwargs):
        result = tkdiag.Messagebox.show_question("Are you sure?", "Confirm")
        if result == "Yes":
            return fnc(*args, **kwargs)

    return wrapper


async def dummy_task():
    "Dummy task for force waking async_runner()"
    pass


async def async_runner():
    """
    Executes coroutines from async queue.
    """
    GLOBAL.tasks_to_run = Queue()
    while GLOBAL.running:
        awaitable, callback, parent_window = await GLOBAL.tasks_to_run.get()  # Coroutine and function to call at end
        try:
            result = await awaitable
            if callback is not None:
                callback(result)
        except Exception as exc:
            if parent_window is not None:
                tkdiag.Messagebox.show_error(
                    f"{exc}\n(Error while running coroutine: {awaitable.__name__})",
                    "Coroutine error",
                    parent_window
                )
            else:
                trace(f"Error while running coroutine: {awaitable.__name__}", TraceLEVELS.ERROR, exc)


async def async_stop():
    """
    Stops the async queue executor.
    """
    GLOBAL.running = False
    async_execute(dummy_task())  # Force wakeup
    await GLOBAL.async_task


def async_start(loop):
    """
    Starts the async queue executor.
    """
    GLOBAL.running = True
    GLOBAL.async_task = loop.create_task(async_runner())


def async_execute(coro: Coroutine, callback: Callable = None, parent_window = None):
    """
    Puts the coroutine into async queue to execue.

    Parameters
    ---------------
    coro: Coroutine
        The coro to run.
    callback: Callable
        Callback function to call with result afer coro has finished.
    parent: window
        The window to show exceptions.
    """
    GLOBAL.tasks_to_run.put_nowait((coro, callback, parent_window))
