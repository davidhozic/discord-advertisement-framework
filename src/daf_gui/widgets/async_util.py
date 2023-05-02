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
