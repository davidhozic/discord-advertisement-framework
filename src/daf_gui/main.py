"""
Main file of the DAF GUI.
"""
from contextlib import suppress
from typing import get_args, get_origin, Iterable, Awaitable, Union, Literal, Optional
from tkinter import ttk
import ttkwidgets as tw
import tkinter as tk
import tkinter.messagebox as tkmsg
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


class ListBoxObjects(tk.Listbox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)

    def get(self, original = True, *args, **kwargs) -> list:
        if original:
            return self._original_items

        return super().get(*args, **kwargs)

    def insert(self, index: str | int, *elements: str | float) -> None:
        _ret = super().insert(index, *elements)
        self._original_items.extend(elements)
        return _ret


class NewObjectWindow(tk.Toplevel):
    open_widgets = {}

    def __init__(self, class_, return_listbox: tk.Listbox, *args, **kwargs):
        self.class_ = class_
        self.return_listbox = return_listbox
        self._map = {}

        opened_widget = type(self).open_widgets.get(class_)
        if opened_widget is not None:
            opened_widget._cleanup()

        super().__init__(*args, **kwargs)
        type(self).open_widgets[class_] = self

        frame_toolbar = ttk.Frame(self, padding=(5, 5))
        bnt_save = ttk.Button(frame_toolbar, text="Save", command=self.save)
        bnt_save.pack(anchor=tk.W)
        frame_toolbar.pack(fill=tk.X)

        frame_main = ttk.Frame(self)
        frame_main.pack(fill=tk.BOTH, expand=True)
        if class_ is bool:
            w = tk.BooleanVar(value=False)
            self.bnt = ttk.Checkbutton(frame_main, variable=w)
            self.bnt.pack()
            self._map[None] = (w, class_)
        elif class_ in {str, int}:
            w = ttk.Entry(frame_main)
            w.pack()
            self._map[None] = (w, class_)
        else:
            for row, (k, v) in enumerate(class_.__init__.__annotations__.items()):
                if k == "return":
                    break

                widgets = []
                widgets.append(ttk.Label(frame_main, text=k, padding=(5, 5)))
                entry_types = v
                while get_origin(entry_types) is Union:
                    entry_types = get_args(entry_types)

                if not isinstance(entry_types, tuple):
                    entry_types = (entry_types,)

                for entry_type in entry_types:
                    if get_origin(entry_type) is Literal:
                        w = tk.StringVar()
                        opts = get_args(entry_type)
                        widgets.append(ttk.OptionMenu(frame_main, w, opts[0], *opts))
                        break

                    elif entry_type is bool:
                        w = tk.BooleanVar(value=False)
                        widgets.append(ttk.Checkbutton(frame_main, variable=w))
                        break
                    elif entry_type in {str, int}:
                        widgets.append(w := ttk.Entry(frame_main))
                        break

                    elif isinstance(entry_type, Iterable):
                        widgets.append(w := ListBoxObjects(frame_main))
                        args = get_args(entry_type)
                        if get_origin(args[0]) is Union:
                            args = get_args(args[0])

                        entry_type = list

                        def _(class_, widget):
                            def __():
                                return NewObjectWindow(class_, widget)

                            return __

                        for arg in args:
                            if arg.__module__.split(".", 1)[0] != "_discord":
                                frame = ttk.Frame(frame_main)
                                b = ttk.Button(frame, text=f"Add {arg.__name__}", command=_(arg, w))
                                b.pack(fill=tk.X)
                                b = ttk.Button(frame, text=f"Remove {arg.__name__}")
                                b.pack(fill=tk.X)
                                widgets.append(frame)

                        break
                    else:
                        continue

                self._map[k] = (w, entry_types)
                for column, widget in enumerate(widgets):
                    widget.grid(row=row, column=column)

        self.protocol("WM_DELETE_WINDOW", self._cleanup)
        self.title(f"New {class_.__name__} object")

    def _cleanup(self):
        del type(self).open_widgets[self.class_]
        self.destroy()
        self.quit()

    def save(self):
        try:
            map_ = {}
            for attr, (widget, type_) in self._map.items():
                value = widget.get()

                if isinstance(value, list):
                    map_[attr] = value
                    continue

                if not isinstance(type_, Iterable):
                    type_ = [type_]

                for type__ in type_:
                    try:
                        map_[attr] = type__(value)
                        break
                    except Exception:
                        continue


            map_ = {k:v for k, v in map_.items() if type(v) is bool or v}
            single_value = map_.get(None)
            if single_value is not None:
                object_ = single_value
            else:
                object_ = self.class_(**map_)

            self.return_listbox.insert(tk.END, object_)
            self._cleanup()
        except Exception as exc:
            tkmsg.showerror("Saving error", f"Could not save the object.\n\n{exc}")


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

        # Menubar
        self.menubar_main = tk.Menu(self.win_main)
        self.menubar_file = tk.Menu(self.menubar_main)
        self.menubar_main.add_cascade(label="File", menu=self.menubar_file)
        self.win_main.configure(menu=self.menubar_main)

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
        self.tabman_mf.add(self.tab_objects, text="Objects template")
        self.lb_accounts = ListBoxObjects(self.tab_objects)
        self.bnt_add_object = ttk.Button(self.tab_objects, text="Add ACCOUNT", command=lambda: NewObjectWindow(daf.ACCOUNT, self.lb_accounts))
        self.bnt_add_object.pack(anchor=tk.NW, padx=5, pady=5)
        self.lb_accounts.pack(fill=tk.BOTH, expand=True, side="left")

        self.bnt_tw_option = ttk.Button(self.tab_objects, text="Options")
        self.bnt_tw_option.pack(side="right", fill=tk.Y)

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # Tasks
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
        self._async_queue.put_nowait(daf.initialize())
        self._async_queue.put_nowait([daf.add_object(account) for account in self.lb_accounts.get()])

    def stop_daf(self):
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")
        self._async_queue.put_nowait(daf.shutdown())

    def close_window(self):
        self._window_opened = False
        if self._daf_running:
            self.stop_daf()

        self.win_main.destroy()

    async def _run_coro_gui_errors(self, coro: Awaitable):
        try:
            await coro
        except asyncio.QueueEmpty:
            raise
        except Exception as exc:
            tkmsg.showerror("Coroutine error", str(exc))

    async def _process(self):
        self.win_main.update()
        try:
            t = self._async_queue.get_nowait()
            if isinstance(t, Iterable):
                for c in t:
                    asyncio.create_task(self._run_coro_gui_errors(c))
            else:
                await self._run_coro_gui_errors(t)
        except asyncio.QueueEmpty:
            pass


if __name__ == "__main__":
    win_main = Application()

    async def update_task():
        while win_main.opened:
            await win_main._process()
            await asyncio.sleep(WIN_UPDATE_DELAY)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(update_task())
