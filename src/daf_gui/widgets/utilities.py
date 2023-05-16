"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from asyncio import Queue, Task, Semaphore, Lock

from daf import trace, TraceLEVELS

from .dpi import dpi_scaled

import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap as ttk

import asyncio


CONF_TASK_SLEEP = 0.1


class GLOBAL:
    tasks_to_run = Queue()
    running = False
    async_task: Task = None


class ExecutingAsyncWindow(ttk.Toplevel):
    """
    Window that hovers while executing async methods.
    """
    def __init__(self, awaitable: Coroutine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Async execution window")
        self.resizable(False, False)
        self.geometry(f"{dpi_scaled(500)}x{dpi_scaled(100)}")
        dpi_10 = dpi_scaled(10)
        frame_main = ttk.Frame(self, padding=(dpi_10, dpi_10))
        frame_main.pack(fill=ttk.BOTH, expand=True)

        ttk.Label(frame_main, text=f"Executing async {awaitable.__name__}").pack(fill=ttk.X)
        gauge = ttk.Floodgauge(frame_main)
        gauge.start()
        gauge.pack(fill=ttk.BOTH)


async def wait_for_mutexes(obj: object):
    "Waits for all mutexes the ``obj`` has to become available."
    mutexes = []
    for item in obj.__slots__ if hasattr(obj, "__slots__") else vars(obj):
        if isinstance((value := getattr(obj, item)), (Semaphore, Lock)):
            mutexes.append(value)

    for mutex in mutexes:
        await mutex.acquire()

    for mutex in mutexes:
        mutex.release()


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
            executor_win = ExecutingAsyncWindow(awaitable, topmost=True, master=parent_window)
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

        finally:
            executor_win.destroy()


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
