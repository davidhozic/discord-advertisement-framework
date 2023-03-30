"""
Main file of the DAF GUI.
"""
from typing import get_args, get_origin, Iterable, Awaitable, Union, Literal
from contextlib import suppress
from tkinter import ttk

import ttkwidgets as tw
import tkinter as tk
import tkinter.messagebox as tkmsg

import asyncio
import inspect
import types
import os


import daf


WIN_UPDATE_DELAY = 0.005
CREDITS_TEXT = \
"""
Welcome to Discord Advertisement Framework - UI mode.
The UI runs on top of Discord Advertisement Framework and allows easier usage for those who
don't want to write Python code to use the software.

Authors: David Hozic - Student at UL FE.
"""


class Text(tk.Text):
    def get(self) -> str:
        return super().get("1.0", tk.END)


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

    def delete(self, first: str | int, last: str | int | None = None) -> None:
        super().delete(first, last)
        if last is None:
            last = first

        for item in self._original_items[first:last + 1]:
            self._original_items.remove(item)


class ComboBoxObjects(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)

    def get(self, original = True, *args, **kwargs) -> list:
        if original:
            index = self.current()
            if index >= 0:
                return self._original_items[index]

        return super().get(*args, **kwargs)

    def __setitem__(self, key: str, value) -> None:
        if key == "values":
            self._original_items = value

        return super().__setitem__(key, value)

    def __getitem__(self, key: str):
        if key == "values":
            return self._original_items

        return super().__getitem__(key)


class NewObjectWindow(tk.Toplevel):
    class ObjectInfo:
        def __init__(self, class_, data: dict) -> None:
            self.class_ = class_
            self.data = data

        def __str__(self) -> str:
            _ret: str = self.class_.__name__ + "("
            for k, v in self.data.items():
                _ret += f"{k}={str(v)}, "

            return _ret.rstrip(", ") + ")"

    open_widgets = {}

    def __init__(self, class_, return_widget: tk.Listbox, parent = None, object_ = None, *args, **kwargs):
        self.class_ = class_
        self.return_widget = return_widget
        self._map = {}
        self.parent = parent
        self.edit = object_ is not None

        opened_widget = type(self).open_widgets.get(class_)
        if opened_widget is not None:
            opened_widget._cleanup()

        super().__init__(parent, *args, **kwargs)
        type(self).open_widgets[class_] = self

        frame_toolbar = ttk.Frame(self, padding=(5, 5))
        bnt_save = ttk.Button(frame_toolbar, text="Save", command=self.save)
        bnt_save.pack(anchor=tk.W)
        frame_toolbar.pack(fill=tk.X)

        frame_main = ttk.Frame(self, padding=(5, 5))
        frame_main.pack(expand=True, fill=tk.BOTH)

        if class_ is str:
            w = Text(frame_main)
            w.pack(fill=tk.X)
            self._map[None] = (w, class_)
        elif class_ in {int, float}:
            w = ttk.Spinbox(frame_main, from_=-9999, to=9999)
            w.pack(fill=tk.X)
            self._map[None] = (w, class_)
        elif get_origin(class_) in {list, Iterable} or "Iterable" in str(class_):
            w = ListBoxObjects(frame_main)
            frame_edit_remove = ttk.Frame(frame_main)
            menubtn = ttk.Menubutton(frame_edit_remove, text="Add object")
            menu = tk.Menu(menubtn)
            menubtn.configure(menu=menu)
            menubtn.pack()
            ttk.Button(frame_edit_remove, text="Remove", command=self.listbox_delete_selected(w)).pack()
            ttk.Button(frame_edit_remove, text="Edit", command=self.listbox_edit_selected(w)).pack()

            w.pack(side="left", fill=tk.BOTH, expand=True)
            frame_edit_remove.pack(side="right")

            args = get_args(class_)
            if get_origin(args[0]) is Union:
                args = get_args(args[0])

            for arg in args:
                # ttk.Button(frame, text=f"Add {arg.__name__}", command=_(arg, w)).pack(fill=tk.X)
                menu.add_radiobutton(label=arg.__name__, command=self.new_object_window(arg, w))

            self._map[None] = (w, list)
        elif hasattr(class_.__init__, "__annotations__"):
            # Do not allow Y resize to keep layout clean
            self.resizable(True, False)

            annotations = class_.__init__.__annotations__
            if annotations is None:
                annotations = {}

            for row, (k, v) in enumerate(annotations.items()):
                if k == "return":
                    break

                frame_annotated = ttk.Frame(frame_main, padding=(5, 5))
                frame_annotated.pack(fill=tk.BOTH, expand=True)

                entry_types = v
                ttk.Label(frame_annotated, text=k, width=15).pack(side="left")

                if isinstance(entry_types, str):
                    _ = __builtins__.get(entry_types)
                    if _ is None:
                        try:
                            entry_types = eval(entry_types, inspect.getmodule(class_).__dict__)
                        except Exception:
                            entry_types = type(None)
                    else:
                        entry_types = _

                while get_origin(entry_types) in {Union, types.UnionType}:
                    entry_types = get_args(entry_types)

                if not isinstance(entry_types, tuple):
                    entry_types = (entry_types,)

                bnt_menu = ttk.Menubutton(frame_annotated)
                menu = tk.Menu(bnt_menu)
                bnt_menu.configure(menu=menu)
                w = combo = ComboBoxObjects(frame_annotated)
                bnt_menu.pack(side="right")
                combo.pack(fill=tk.X, side="right", expand=True, padx=5, pady=5)

                editable_types = []
                for entry_type in entry_types:
                    if get_origin(entry_type) is Literal:
                        combo["values"] = get_args(entry_type)
                    elif entry_type is bool:
                        combo["values"] = list(combo["values"]) + [True]
                        combo["values"] = list(combo["values"]) + [False]
                    elif entry_type is type(None):
                        if bool not in entry_types:
                            combo["values"] = list(combo["values"]) + [None]
                    else:  # Type not supported, try other types
                        menu.add_radiobutton(label=f"New {entry_type.__name__}", command=self.new_object_window(entry_type, combo))
                        editable_types.append(entry_type)

                menu.add_radiobutton(label="Edit selected", command=self.combo_edit_selected(w, editable_types))
                self._map[k] = (w, entry_types)
        else:
            tkmsg.showerror("Load error", "This object cannot be edited.", parent=self)
            self._cleanup()
            return

        self.protocol("WM_DELETE_WINDOW", self._cleanup)
        self.title(f"New {class_.__name__} object")

        if self.edit:
            self.load(object_)

    def load(self, object_):
        for attr, (widget, types_) in self._map.items():
            try:
                val = object_[attr] if attr is not None else object_  # Single value type
            except Exception:
                continue

            if isinstance(widget, ComboBoxObjects):
                if val not in widget["values"]:
                    widget["values"] = widget["values"] + [val]

                widget.set(str(val))

            elif isinstance(widget, ListBoxObjects):
                widget.insert(tk.END, *object_)

            elif isinstance(widget, tk.Text):
                widget.insert(tk.END, object_)

            elif isinstance(widget, ttk.Spinbox):
                widget.set(object_)

    def new_object_window(self, class_, widget):
        def __():
            return NewObjectWindow(class_, widget, self)

        return __

    def listbox_delete_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection):
                lb.delete(*selection)
            else:
                tkmsg.showerror("Empty list!", "Select atleast one item!", parent=self)

        return __

    def listbox_edit_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection):
                object_: NewObjectWindow.ObjectInfo = lb.get()[selection[0]]
                return NewObjectWindow(object_.class_, lb, self, object_.data)
            else:
                tkmsg.showerror("Empty list!", "Select atleast one item!", parent=self)

        return __

    def combo_edit_selected(self, combo: ComboBoxObjects, types: list):
        def __():
            selection = combo.get()

            if isinstance(selection, list):
                return NewObjectWindow(Union[tuple(types)], combo, self, selection)
            elif isinstance(selection, NewObjectWindow.ObjectInfo):
                return NewObjectWindow(selection.class_, combo, self, selection.data)
            else:
                return NewObjectWindow(type(selection), combo, self, selection)

        return __

    def _cleanup(self):
        del type(self).open_widgets[self.class_]
        self.destroy()
        self.quit()

    def save(self):
        try:
            map_ = {}
            for attr, (widget, type_) in self._map.items():
                value = widget.get()

                if not isinstance(type_, Iterable):
                    type_ = (type_, )

                if isinstance(value, str):  # Ignore empty values
                    if not len(value):
                        continue

                    for type__ in type_:
                        with suppress(Exception):
                            map_[attr] = type__(value)
                            break
                    else:
                        map_[attr] = value  # Could not cast value, use as it is
                else:
                    map_[attr] = value

            single_value = map_.get(None)
            if single_value is not None:
                object_ = single_value
            else:
                object_ = NewObjectWindow.ObjectInfo(self.class_, map_)
                self.convert_to_objects(object_)  # Tries to create instances to check for errors

            if isinstance(self.return_widget, tk.Listbox):
                self.return_widget.insert(tk.END, object_)
            else:
                self.return_widget["values"] = list(self.return_widget["values"]) + [object_]

            self._cleanup()
        except Exception as exc:
            tkmsg.showerror("Saving error", f"Could not save the object.\n\n{exc}", parent=self)

    @classmethod
    def convert_to_objects(cls, d: ObjectInfo):
        data_conv = {}
        for k, v in d.data.items():
            if isinstance(v, NewObjectWindow.ObjectInfo):
                v = cls.convert_to_objects(v)

            elif isinstance(v, list):
                for i, subv in enumerate(v):
                    if isinstance(subv, NewObjectWindow.ObjectInfo):
                        v[i] = cls.convert_to_objects(subv)

            data_conv[k] = v

        return d.class_(**data_conv)


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = tk.Tk()
        path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        win_main.iconphoto(True, tk.PhotoImage(file=path))

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
        self.bnt_edit_object = ttk.Button(self.tab_objects, text="Edit")
        self.bnt_remove_object = ttk.Button(self.tab_objects, text="Remove", command=self.list_del_account)
        # self.bnt_tw_option.option_add()
        self.bnt_add_object.pack(anchor=tk.NW, fill=tk.X)
        self.bnt_edit_object.pack(anchor=tk.NW, fill=tk.X)
        self.bnt_remove_object.pack(anchor=tk.NW, fill=tk.X)
        self.lb_accounts.pack(fill=tk.BOTH, expand=True)

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # Tasks
        self._async_queue = asyncio.Queue()

    @property
    def opened(self) -> bool:
        return self._window_opened

    def list_del_account(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            self.lb_accounts.delete(*selection)
        else:
            tkmsg.showerror("Empty list!", "Select atleast one item!")

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
        self._async_queue.put_nowait([daf.add_object(NewObjectWindow.convert_to_objects(account)) for account in self.lb_accounts.get()])

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


def run():
    win_main = Application()

    async def update_task():
        while win_main.opened:
            await win_main._process()
            await asyncio.sleep(WIN_UPDATE_DELAY)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(update_task())


if __name__ == "__main__":
    run()
