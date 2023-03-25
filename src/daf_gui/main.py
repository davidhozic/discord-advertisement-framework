"""
Main file of the DAF GUI.
"""
from contextlib import suppress
from tkinter import ttk
from ttkwidgets import DebugWindow
import tkinter as tk
import asyncio

import daf

WIN_UPDATE_DELAY = 0.1


class Application():
    def __init__(self) -> None:

        # Window initialization
        win_main = tk.Tk()
        self.win_main = win_main
        screen_res = win_main.winfo_screenwidth() // 2, win_main.winfo_screenheight() // 2
        win_main.wm_title("Discord Advert Framework")
        win_main.wm_minsize(*screen_res)
        win_main.protocol("WM_DELETE_WINDOW", self.close_window)

        # Console initialization
        self.win_debug = None

        # Toolbar
        self.frame_toolbar = ttk.Frame(self.win_main)
        self.frame_toolbar.pack(fill=tk.X, side="top", padx=5, pady=5)
        self.bnt_toolbar_open_debug = ttk.Button(self.frame_toolbar, command=self.open_console, text="Console")
        self.bnt_toolbar_open_debug.pack(side="left")
        self.bnt_toolbar_start_daf = ttk.Button(self.frame_toolbar, text="Start", command=self.start_daf)
        self.bnt_toolbar_start_daf.pack(side="left")
        self.bnt_toolbar_stop_daf = ttk.Button(self.frame_toolbar, text="Stop", state="disabled", command=self.stop_daf)
        self.bnt_toolbar_stop_daf.pack(side="left")

        # Main Frame
        self.frame_main = ttk.Frame(self.win_main)
        self.frame_main.pack(expand=True, fill=tk.BOTH, side="bottom")

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # Tasks
        self._daf_task = None
        self._async_queue = asyncio.Queue()

    @property
    def opened(self) -> bool:
        return self._window_opened

    def open_console(self):
        return DebugWindow(self.win_main, "Trace", stderr=False)

    def start_daf(self):
        self.bnt_toolbar_start_daf.configure(state="disabled")
        self.bnt_toolbar_stop_daf.configure(state="enabled")
        self._daf_running = True
        self._daf_task = asyncio.create_task(daf.initialize())

    def stop_daf(self):
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")
        self._async_queue.put_nowait(daf.shutdown())

    def close_window(self):
        self._window_opened = False
        if self._daf_running:
            self.stop_daf()

        self.win_main.destroy()

    async def _process(self):
        self.win_main.update()
        with suppress(asyncio.QueueEmpty):
            await self._async_queue.get_nowait()


if __name__ == "__main__":
    win_main = Application()

    async def update_task():
        while win_main.opened:
            await win_main._process()
            await asyncio.sleep(WIN_UPDATE_DELAY)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(update_task())
