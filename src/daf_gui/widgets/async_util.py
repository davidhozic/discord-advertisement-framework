"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from asyncio import Queue, Task

from daf import trace, TraceLEVELS

import ttkbootstrap.dialogs.dialogs as tkdiag

CONF_TASK_SLEEP = 0.1

class GLOBAL:
    tasks_to_run: Queue = Queue()
    running = False
    async_task: Task = None


async def async_runner():
    """
    Executes coroutines from async queue.
    """
    while GLOBAL.running:
        awaitable, callback, parent_window = await GLOBAL.tasks_to_run.get()  # Coroutine and function to call at end
        try:
            result = await awaitable
            if callback is not None:
                callback(result)
        except Exception as exc:
            if parent_window is not None:
                tkdiag.Messagebox.show_error(
                    f"Error while running coroutine: {awaitable} ({exc})",
                    "Coroutine error",
                    parent_window
                )
            else:
                trace(f"Error while running coroutine: {awaitable}", TraceLEVELS.ERROR, exc)


async def async_stop():
    """
    Stops the async queue executor.
    """
    GLOBAL.running = False
    async def dummy():
        pass

    async_execute(dummy())  # Force wakeup
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
