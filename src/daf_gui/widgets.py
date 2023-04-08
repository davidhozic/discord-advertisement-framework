from __future__ import annotations
from typing import get_args, get_origin, get_type_hints, Iterable, Union, Literal, Any
from collections.abc import Iterable as ABCIterable
from contextlib import suppress
from enum import Enum

from daf import VERSION as DAF_VERSION, FILE as DAFFile, LoggerJSON, LoggerCSV
from _discord._version import __version__ as PYCORD_VERSION
from _discord import Embed as DiscordEmbed, Colour as DiscordColor

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag
import tkinter.filedialog as tkfile

import webbrowser
import types
import datetime as dt


__all__ = (
    "Text",
    "ListBoxObjects",
    "ComboBoxObjects",
    "ObjectEditWindow",
    "NewObjectFrame",
    "SpinBoxText",
    "ComboBoxText",
    "ObjectInfo",
    "convert_to_objects",
    "convert_to_json",
    "convert_from_json",
)


HELP_URLS = {
    "daf": f"https://daf.davidhozic.com/en/{DAF_VERSION}/?rtd_search={{}}",
    "_discord": f"https://docs.pycord.dev/en/v{PYCORD_VERSION}/search.html?q={{}}",
    "builtins": "https://docs.python.org/3/search.html?q={}"
}

ADDITIONAL_ANNOTATIONS = {
    dt.timedelta: {
        "days": float,
        "seconds": float,
        "microseconds": float,
        "milliseconds": float,
        "minutes": float,
        "hours": float,
        "weeks": float
    },
    dt.datetime: {
        "year": int,
        "month": int | None,
        "day": int | None,
        "hour": int,
        "minute": int,
        "second": int,
        "microsecond": int,
        "tzinfo": dt.tzinfo | None,
        "fold": int
    },
    DiscordEmbed: {
        "title": str,
        "url": str,
        "description": str
    },
}


class AdditionalWidget:
    def __init__(self, widget_class, setup_cmd, *args, **kwargs) -> None:
        self.widget_class = widget_class
        self.args = args
        self.kwargs = kwargs
        self.setup_cmd = setup_cmd


def setup_additional_widget_datetime(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        date = tkdiag.Querybox.get_date(window, title="Select the date")
        for attr in {"year", "month", "day"}:
            widget, types_ = window._map.get(attr)
            value = getattr(date, attr)
            if value not in widget["values"]:
                widget.insert(tk.END, value)

            widget.set(value)

    w.configure(command=_callback)


def setup_additional_widget_color_picker(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        widget, types = window._map.get("value")
        _ = tkdiag.Querybox.get_color(window, "Choose color")
        if _ is None:
            return

        rgb, hsl, hex_ = _
        color = int(hex_.removeprefix("#"), base=16)
        if color not in widget["values"]:
            widget.insert(tk.END, color)

        widget.set(color)

    w.configure(command=_callback)


def setup_additional_widget_file_chooser(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        file = tkfile.askopenfile(parent=window)
        if file is None:  # File not opened
            return

        filename = None
        with file:
            filename = file.name

        filename_combo = window._map.get("filename")[0]
        filename_combo.insert(tk.END, filename)
        filename_combo.set(filename)

    w.configure(command=_callback)


def setup_additional_widget_file_chooser_logger(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        path = tkfile.askdirectory(parent=window)
        if path == "":
            return

        filename_combo = window._map.get("path")[0]
        filename_combo.insert(tk.END, path)
        filename_combo.set(path)

    w.configure(command=_callback)


ADDITIONAL_WIDGETS = {
    dt.datetime: [AdditionalWidget(ttk.Button, setup_additional_widget_datetime, text="Select date")],
    DiscordColor: [AdditionalWidget(ttk.Button, setup_additional_widget_color_picker, text="Color picker")],
    DAFFile: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
    LoggerJSON: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    LoggerCSV: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
}


def issubclass_noexcept(*args):
    try:
        return issubclass(*args)
    except Exception:
        return False


class ObjectInfo:
    """
    Describes Python objects' parameters.
    """
    CHARACTER_LIMIT = 200

    def __init__(self, class_, data: dict) -> None:
        self.class_ = class_
        self.data = data

    def __repr__(self) -> str:
        _ret: str = self.class_.__name__ + "("
        for k, v in self.data.items():
            v = f'"{v}"' if isinstance(v, str) else str(v)
            _ret += f"{k}={v}, "

        _ret = _ret.rstrip(", ") + ")"
        if len(_ret) > self.CHARACTER_LIMIT:
            _ret = _ret[:self.CHARACTER_LIMIT] + "...)"

        return _ret

    @classmethod
    def disable_limit(cls):
        cls.CHARACTER_LIMIT = 99999999999999999

    @classmethod
    def enable_limit(cls):
        cls.CHARACTER_LIMIT = 200


def convert_to_objects(d: ObjectInfo):
    data_conv = {}
    for k, v in d.data.items():
        if isinstance(v, ObjectInfo):
            v = convert_to_objects(v)

        elif isinstance(v, list):
            v = v.copy()
            for i, subv in enumerate(v):
                if isinstance(subv, ObjectInfo):
                    v[i] = convert_to_objects(subv)

        data_conv[k] = v

    return d.class_(**data_conv)


def convert_to_json(d: ObjectInfo):
    data_conv = {}
    for k, v in d.data.items():
        if isinstance(v, ObjectInfo):
            v = convert_to_json(v)

        elif isinstance(v, list):
            v = v.copy()
            for i, subv in enumerate(v):
                if isinstance(subv, ObjectInfo):
                    v[i] = convert_to_json(subv)

        data_conv[k] = v

    return {"type": f"{d.class_.__module__}.{d.class_.__name__}", "data": data_conv}


def convert_from_json(d: dict | list[dict] | Any) -> ObjectInfo:
    if isinstance(d, list):
        result = []
        for item in d:
            result.append(convert_from_json(item))

        return result

    elif isinstance(d, dict):
        type_: str = d["type"]
        data: dict = d["data"]
        type_split = type_.split('.')
        module = type_split[:len(type_split) - 1]
        type_ = type_split[-1]
        module_ = __import__(module[0])
        module.pop(0)
        for i, m in enumerate(module):
            module_ = getattr(module_, module[i])

        type_ = getattr(module_, type_)
        for k, v in data.items():
            if isinstance(v, list) or isinstance(v, dict) and v.get("type") is not None:
                v = convert_from_json(v)
                data[k] = v

        return ObjectInfo(type_, data)

    else:
        return d


class Text(tk.Text):
    def get(self) -> str:
        return super().get("1.0", tk.END).removesuffix("\n")


class SpinBoxText(ttk.Frame):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Label(self, text=text).pack(fill=tk.X, expand=True)
        self.spinbox = ttk.Spinbox(self)
        self.spinbox.pack(fill=tk.X, expand=True)


class ComboBoxText(ttk.Frame):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Label(self, text=text).pack(fill=tk.X, expand=True)
        self.combo = ComboBoxObjects(self)
        self.combo.pack(fill=tk.X, expand=True)


class ListBoxObjects(tk.Listbox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)
        self.configure(selectmode=tk.EXTENDED)

    def get(self, original = True, *args, **kwargs) -> list:
        if original:
            return self._original_items

        return super().get(*args, **kwargs)

    def insert(self, index: str | int, *elements: str | float) -> None:
        _ret = super().insert(index, *elements)
        self._original_items.extend(elements)
        return _ret

    def delete(self, *indexes: int) -> None:
        if indexes[-1] == "end":
            indexes = range(indexes[0], len(self._original_items))

        indexes = sorted(indexes, reverse=True)
        for index in indexes:
            super().delete(index)
            del self._original_items[index]


class ComboBoxObjects(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)

    def get(self, *args, **kwargs) -> list:
        index = self.current()
        if isinstance(index, int) and index >= 0:
            return self._original_items[index]

        return super().get(*args, **kwargs)

    def delete(self, index: int) -> None:
        self["values"].pop(index)
        super().delete(index)
        self["values"] = self["values"]  # Update the text list, NOT a code mistake

    def insert(self, index: int | str, element: Any) -> None:
        if index == tk.END:
            self._original_items.append(element)
            index = len(self._original_items)
        else:
            self._original_items.insert(index, element)

        self["values"] = self._original_items

    def __setitem__(self, key: str, value) -> None:
        if key == "values":
            self._original_items = list(value)
            value = [str(x)[:200] for x in value]

        return super().__setitem__(key, value)

    def __getitem__(self, key: str):
        if key == "values":
            return self._original_items

        return super().__getitem__(key)


class ObjectEditWindow(ttk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closed = False

        # Elements
        self.opened_frames = []
        self.frame_main = ttk.Frame(self, padding=(5, 5))
        self.frame_toolbar = ttk.Frame(self, padding=(5, 5))
        ttk.Button(self.frame_toolbar, text="Close", command=self.close_object_edit_frame).pack(side="left")
        ttk.Button(self.frame_toolbar, text="Save", command=self.save_object_edit_frame).pack(side="left")

        self.frame_toolbar.pack(expand=True, fill=tk.X)
        self.frame_main.pack(expand=True, fill=tk.BOTH)
        self.frame_main.rowconfigure(0, weight=1)
        self.frame_main.columnconfigure(0, weight=1)

        var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.frame_toolbar,
            text="Keep on top",
            variable=var,
            command=lambda: self.attributes("-topmost", var.get()),
            bootstyle="round-toggle"
        ).pack(side="right")
        self.attributes("-topmost", var.get())

        # Window initialization
        NewObjectFrame.set_origin_window(self)
        self.protocol("WM_DELETE_WINDOW", self.close_object_edit_frame)

    @property
    def closed(self) -> bool:
        return self._closed

    def open_object_edit_frame(self, *args, **kwargs):
        prev_frame = None
        if len(self.opened_frames):
            prev_frame = self.opened_frames[-1]

        self.opened_frames.append(frame := NewObjectFrame(parent=self.frame_main, *args, **kwargs))
        frame.pack(fill=tk.BOTH, expand=True)
        frame.update_window_title()
        if prev_frame is not None:
            prev_frame.pack_forget()

    def close_object_edit_frame(self):
        self.opened_frames[-1].close_frame()

    def save_object_edit_frame(self):
        self.opened_frames[-1].save()

    def clean_object_edit_frame(self):
        self.opened_frames.pop().destroy()
        opened_frames_len = len(self.opened_frames)

        if opened_frames_len:
            frame = self.opened_frames[-1]
            frame.pack(fill=tk.BOTH, expand=True)  # (row=0, column=0)
            frame.update_window_title()
        else:
            self._closed = True
            self.destroy()


class NewObjectFrame(ttk.Frame):
    origin_window: ObjectEditWindow = None

    def __init__(self, class_, return_widget: ComboBoxObjects | ListBoxObjects, parent = None, old: ObjectInfo = None, *args, **kwargs):
        def convert_types(types_in):
            while get_origin(types_in) in {Union, types.UnionType}:
                types_in = get_args(types_in)

            if not isinstance(types_in, list):
                if isinstance(types_in, tuple):
                    types_in = list(types_in)
                else:
                    types_in = [types_in, ]

            subtypes = []
            for t in types_in:
                if hasattr(t, "__subclasses__") and t.__module__.split('.', 1)[0] in {"_discord", "daf"}:
                    for st in t.__subclasses__():
                        subtypes.extend(convert_types(st))

            return types_in + subtypes

        self.class_ = class_
        self.return_widget = return_widget
        self._map = {}
        self.parent = parent
        self.old_object_info = old  # Edit requested

        super().__init__(
            master=parent,
            *args,
            **kwargs
        )

        frame_toolbar = ttk.Frame(self)


        package = class_.__module__.split(".", 1)[0]
        help_url = HELP_URLS.get(package)
        if help_url is not None:
            def cmd():
                webbrowser.open(help_url.format(class_.__name__))

            ttk.Button(frame_toolbar, text="Help", command=cmd).pack(side="left")

        add_widgets = ADDITIONAL_WIDGETS.get(class_)
        if add_widgets is not None:
            for add_widg in add_widgets:
                setup_cmd = add_widg.setup_cmd
                add_widg = add_widg.widget_class(frame_toolbar, *add_widg.args, **add_widg.kwargs)
                add_widg.pack(side="right")
                setup_cmd(add_widg, self)

        frame_toolbar.pack(fill=tk.X)
        frame_main = ttk.Frame(self)
        frame_main.pack(expand=True, fill=tk.BOTH)

        # Additional annotations defined in daf to support more types
        try:
            annotations = get_type_hints(class_.__init__, include_extras=True)
        except NameError:
            annotations = {}
        additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_)
        if additional_annotations is not None:
            annotations = {**annotations, **additional_annotations}

        def init_frame_str():
            w = Text(frame_main)
            w.pack(fill=tk.BOTH, expand=True)
            self._map[None] = (w, class_)

        def init_frame_num():
            w = ttk.Spinbox(frame_main, from_=-9999, to=9999)
            w.pack(fill=tk.X)
            self._map[None] = (w, class_)

        def init_frame_list():
            w = ListBoxObjects(frame_main)
            frame_edit_remove = ttk.Frame(frame_main)
            menubtn = ttk.Menubutton(frame_edit_remove, text="Add object")
            menu = tk.Menu(menubtn)
            menubtn.configure(menu=menu)
            menubtn.pack()
            ttk.Button(frame_edit_remove, text="Remove", command=self.listbox_delete_selected(w)).pack(fill=tk.X)
            ttk.Button(frame_edit_remove, text="Edit", command=self.listbox_edit_selected(w)).pack(fill=tk.X)
            ttk.Button(frame_edit_remove, text="Copy", command=self.listbox_copy_selected(w)).pack(fill=tk.X)

            w.bind("<Control-c>", lambda e: self.listbox_copy_selected(w)())
            w.bind("<BackSpace>", lambda e: self.listbox_delete_selected(w)())
            w.bind("<Delete>", lambda e: self.listbox_delete_selected(w)())

            w.pack(side="left", fill=tk.BOTH, expand=True)
            frame_edit_remove.pack(side="right")
            args = get_args(class_)
            args = convert_types(args)
            if get_origin(args[0]) is Union:
                args = get_args(args[0])

            for arg in args:
                # ttk.Button(frame, text=f"Add {arg.__name__}", command=_(arg, w)).pack(fill=tk.X)
                menu.add_radiobutton(label=arg.__name__, command=self.new_object_window(arg, w))

            self._map[None] = (w, list)

        def init_frame_annotated_object():
            annotations.pop("return", None)

            for (k, v) in annotations.items():
                frame_annotated = ttk.Frame(frame_main)
                frame_annotated.pack(fill=tk.BOTH, expand=True)

                entry_types = v
                ttk.Label(frame_annotated, text=k, width=15).pack(side="left")

                entry_types = convert_types(entry_types)

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
                        combo.insert(tk.END, True)
                        combo.insert(tk.END, False)
                    elif issubclass_noexcept(entry_type, Enum):
                        combo["values"] = [en for en in entry_type]
                    elif entry_type is type(None):
                        if bool not in entry_types:
                            combo.insert(tk.END, None)
                    else:  # Type not supported, try other types
                        menu.add_radiobutton(label=f"New {entry_type.__name__}", command=self.new_object_window(entry_type, combo))
                        if get_origin(entry_type) in {list, Iterable, ABCIterable}:
                            editable_types.append(entry_type)

                menu.add_radiobutton(label="Edit selected", command=self.combo_edit_selected(w, editable_types))
                self._map[k] = (w, entry_types)

        if class_ is str:
            init_frame_str()
        elif class_ in {int, float}:
            init_frame_num()
        elif get_origin(class_) in {list, Iterable, ABCIterable}:
            init_frame_list()
        elif annotations or additional_annotations is not None:
            init_frame_annotated_object()
        else:
            tkdiag.Messagebox.show_error("This object cannot be edited.", "Load error", parent=self.origin_window)
            self.origin_window.after_idle(self._cleanup)  # Can not clean the object before it has been added to list
            return

        if old is not None:  # Edit
            self.load(old)

    @classmethod
    def set_origin_window(cls, window: ObjectEditWindow):
        cls.origin_window = window

    def update_window_title(self):
        self.origin_window.title(f"{'New' if self.old_object_info is None else 'Edit'} {self.class_.__name__} object")

    def close_frame(self):
        resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self)
        if resp is not None:
            if resp == "Yes":
                self.save()
            elif resp == "No":
                self._cleanup()

    def load(self, object_: ObjectInfo):
        object_ = object_.data if self._map.get(None) is None else object_
        for attr, (widget, types_) in self._map.items():
            if attr is not None:
                if attr not in object_:
                    continue

                val = object_[attr] 
            else:
                val = object_  # Single value type

            if isinstance(widget, ComboBoxObjects):
                if val not in widget["values"]:
                    widget.insert(tk.END, val)

                widget.current(widget["values"].index(val))

            elif isinstance(widget, ListBoxObjects):
                widget.insert(tk.END, *object_)

            elif isinstance(widget, tk.Text):
                widget.insert(tk.END, object_)

            elif isinstance(widget, ttk.Spinbox):
                widget.set(object_)

    def new_object_window(self, class_, widget):
        def __():
            return self.origin_window.open_object_edit_frame(class_, widget)

        return __

    def listbox_delete_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection):
                lb.delete(*selection)
            else:
                tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self.origin_window)

        return __

    def listbox_copy_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection):
                object_: ObjectInfo | Any = lb.get()[selection[0]]
                lb.insert(tk.END, object_)
            else:
                tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self.origin_window)

        return __

    def listbox_edit_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection) == 1:
                object_ = lb.get()[selection[0]]
                if isinstance(object_, ObjectInfo):
                    self.origin_window.open_object_edit_frame(object_.class_, lb, old=object_)
                else:
                    self.origin_window.open_object_edit_frame(type(object_), lb, old=object_)
            else:
                tkdiag.Messagebox.show_error("Select ONE item!", "Selection error", parent=self.origin_window)

        return __

    def combo_edit_selected(self, combo: ComboBoxObjects, types):
        def __():
            selection = combo.get()

            if isinstance(selection, list):
                return self.origin_window.open_object_edit_frame(Union[tuple(types)], combo, old=selection)
            elif isinstance(selection, ObjectInfo):
                return self.origin_window.open_object_edit_frame(selection.class_, combo, old=selection)
            else:
                if isinstance(selection, str) and not len(selection):
                    selection = None

                return self.origin_window.open_object_edit_frame(type(selection), combo, old=selection)

        return __

    def _cleanup(self):
        self.origin_window.clean_object_edit_frame()

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
                object_ = ObjectInfo(self.class_, map_)
                convert_to_objects(object_)  # Tries to create instances to check for errors

            # Edit was requested, delete old value
            if self.old_object_info is not None:
                ret_widget = self.return_widget
                if isinstance(ret_widget, ListBoxObjects):
                    ind = ret_widget.get().index(self.old_object_info)
                else:
                    ind = ret_widget["values"].index(self.old_object_info)

                ret_widget.delete(ind)

            self.return_widget.insert(tk.END, object_)
            if isinstance(self.return_widget, ComboBoxObjects):
                self.return_widget.current(self.return_widget["values"].index(object_))

            self._cleanup()
        except Exception as exc:
            tkdiag.Messagebox.show_error(f"Could not save the object.\n\n{exc}", "Saving error", parent=self.origin_window)
