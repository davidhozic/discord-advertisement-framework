"""
Module contains interface to run async tasks from GUI.
"""
from typing import Coroutine, Callable
from asyncio import Queue, Task
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


class ExecutingAsyncWindow(ttk.Toplevel):
    """
    Window that hovers while executing async methods.
    """
    def __init__(self, awaitable: Coroutine, callback = None, *args, **kwargs):
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

        self.awaitable = awaitable
        self.callback = callback
        self.current_thread = current_thread()
        self.future = future = asyncio.run_coroutine_threadsafe(awaitable, GLOBAL.loop)
        future.add_done_callback(self.destroy)

    def flush(self):
        pass

    def write(self, text: str):
        if current_thread() is not self.current_thread:
            self.after_idle(self.write, text)
            return

        if text == "\n":
            return

        text = text.replace("\033[0m", "")
        for r in daf.tracing.TRACE_COLOR_MAP.values():
            text = text.replace(r, "")

        self.status_var.set(text)
        self.old_stdout.write(text)

    def destroy(self, future: asyncio.Future = None) -> None:
        if future is not None and (exc := future.exception()) is not None:
            self.after_idle(
                tkdiag.Messagebox.show_error,        
                f"{exc}\n(Error while running coroutine: {self.awaitable.__name__})\nType: {exc.__class__}",
                "Coroutine error",
                self
            )

        sys.stdout = self.old_stdout
        if self.callback is not None:
            self.callback()

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


def async_stop():
    "Stops the async queue executor"
    GLOBAL.loop.call_soon_threadsafe(GLOBAL.loop.stop)
    GLOBAL.async_thread.join()
    return GLOBAL.loop

def async_start():
    """
    Starts the async queue executor.
    """
    loop = asyncio.new_event_loop()
    GLOBAL.loop = loop
    GLOBAL.async_thread = Thread(target=loop.run_forever)
    GLOBAL.async_thread.start()


def async_execute(coro: Coroutine, parent_window = None, callback: Callable = None):
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
    ExecutingAsyncWindow(coro, master=parent_window, callback=callback).wait_window()
