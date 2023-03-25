"""
Main file of the DAF GUI.
"""
from contextlib import suppress
from typing import get_args, Iterable
from tkinter import ttk
import ttkwidgets as tw
import tkinter as tk
import asyncio

import daf


WIN_UPDATE_DELAY = 0.01
CREDITS_TEXT = \
"""
Welcome to Discord Advertisement Framework - UI mode.
The UI runs on top of Discord Advertisement Framework and allows easier usage for those who
don't want to write Python code to use the software.

Authors: David Hozic - Student at UL FE.
"""


class NewObjectWindow(tk.Toplevel):
    def __init__(self, class_, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for i, (k, v) in enumerate(class_.__init__.__annotations__.items()):
            if k == "return":
                break

            label = ttk.Label(self, text=k)
            entry_type = get_args(v)[0]

            if entry_type is bool:
                entry_type = ttk.Checkbutton, {}
            elif entry_type in {str, int}:
                entry_type = ttk.Entry, {}
            elif isinstance(entry_type, Iterable):
                entry_type = tk.Listbox, {}
            else:
                continue

            entry_type, kwargs = entry_type
            entry = entry_type(self, **kwargs)
            label.grid(row=i, column=0)
            entry.grid(row=i, column=1)

class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = tk.Tk()
        self.win_main = win_main
        screen_res = win_main.winfo_screenwidth() // 2, win_main.winfo_screenheight() // 2
        win_main.wm_title(f"Discord Advert Framework {daf.VERSION}")
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
        self.tabman_mf = ttk.Notebook(self.frame_main)
        self.tabman_mf.pack(fill=tk.BOTH, expand=True)

        # Credits tab
        self.tab_info = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_info, text="Credits")
        self.labl_credits = tk.Label(self.tab_info, text=CREDITS_TEXT)
        self.labl_credits.pack()

        # Objects tab
        self.tab_objects = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_objects, text="Objects")
        self.bnt_add_object = ttk.Button(self.tab_objects, text="Add ACCOUNT", command=lambda: NewObjectWindow(daf.ACCOUNT))
        self.bnt_add_object.pack(anchor=tk.NW, padx=5, pady=5)
        self.lb_accounts = tw.ScrolledListbox(self.tab_objects)
        self.lb_accounts.pack(fill=tk.BOTH, expand=True, side="left")

        self.bnt_tw_option = ttk.Button(self.tab_objects, text="Options")
        self.bnt_tw_option.pack(side="right", fill=tk.Y)

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
        def _():
            self.win_debug.quit()
            self.win_debug = None

        if self.win_debug is not None:
            self.win_debug.quit()

        self.win_debug = tw.DebugWindow(self.win_main, "Trace", stderr=False)
        self.win_debug.protocol("WM_DELETE_WINDOW", _)

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
