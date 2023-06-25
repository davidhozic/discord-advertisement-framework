"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from asyncio import Queue, Task

from daf import trace, TraceLEVELS

from .dpi import dpi_scaled

import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap as ttk

import sys
import daf


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
        dpi_10 = dpi_scaled(10)
        frame_main = ttk.Frame(self, padding=(dpi_10, dpi_10))
        frame_main.pack(fill=ttk.BOTH, expand=True)

        frame_stdout = ttk.Frame(frame_main)
        frame_stdout.pack(fill=ttk.BOTH, expand=True)
        self.status_var = ttk.StringVar()
        ttk.Label(frame_stdout, text="Last status: ").grid(row=0, column=0)
        ttk.Label(frame_stdout, textvariable=self.status_var).grid(row=0, column=1)

        ttk.Label(frame_main, text=f"Executing {awaitable.__name__}").pack(fill=ttk.X)
        gauge = ttk.Floodgauge(frame_main)
        gauge.start()
        gauge.pack(fill=ttk.BOTH)

        self.old_stdout = sys.stdout
        sys.stdout = self

        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.grab_set()

    def flush(self):
        pass

    def write(self, text: str):
        if text == "\n":
            return

        text = text.replace("\033[0m", "")
        for r in daf.tracing.TRACE_COLOR_MAP.values():
            text = text.replace(r, "")

        self.status_var.set(text)
        self.old_stdout.write(text)

    def destroy(self) -> None:
        sys.stdout = self.old_stdout
        return super().destroy()


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
            tkdiag.Messagebox.show_error(
                f"{exc}\n(Error while running coroutine: {awaitable.__name__})\nType: {exc.__class__}",
                "Coroutine error",
                executor_win
            )
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
