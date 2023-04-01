from typing import get_args, get_origin, Iterable, Union, Literal, Any
from collections.abc import Iterable as ABCIterable
from contextlib import suppress

from daf import VERSION as DAF_VERSION
from _discord._version import __version__ as PYCORD_VERSION

import ttkbootstrap as ttk
import tkinter as tk
import tkinter.messagebox as tkmsg

import webbrowser
import inspect
import types
import datetime as dt


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
    }
}


__all__ = (
    "Text",
    "ListBoxObjects",
    "ComboBoxObjects",
    "NewObjectWindow",
    "ObjectInfo",
    "convert_to_objects",
    "convert_to_json",
    "convert_from_json",
)


class Text(tk.Text):
    def get(self) -> str:
        return super().get("1.0", tk.END).removesuffix("\n")


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


class NewObjectWindow(ttk.Toplevel):
    open_widgets = {}

    def __init__(self, class_, return_widget: ComboBoxObjects | ListBoxObjects, parent = None, old: ObjectInfo = None, *args, **kwargs):
        def convert_types(types_in):
            if isinstance(types_in, str):
                _ = __builtins__.get(types_in)
                if _ is None:
                    try:
                        types_in = types_in(types, inspect.getmodule(class_).__dict__)
                    except Exception:
                        types_in = type(None)
                else:
                    types_in = _

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

        opened_widget = type(self).open_widgets.get(self.parent)
        if opened_widget is not None:
            opened_widget._cleanup()

        type(self).open_widgets[self.parent] = self
        super().__init__(
            master=parent,
            title=f"{'New' if old is None else 'Edit'} {class_.__name__} object",
            *args,
            **kwargs
        )

        frame_toolbar = ttk.Frame(self, padding=(5, 5))
        ttk.Button(frame_toolbar, text="Close", command=self.close_window).pack(side="left")

        bnt_save = ttk.Button(frame_toolbar, text="Save", command=self.save)
        bnt_save.pack(side="left")

        package = class_.__module__.split(".", 1)[0]
        help_url = HELP_URLS.get(package)
        if help_url is not None:
            def cmd():
                webbrowser.open(help_url.format(class_.__name__))

            ttk.Button(frame_toolbar, text="Help", command=cmd).pack(side="left")

        cb_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_toolbar, text="Keep on top", style='Roundtoggle.Toolbutton',
            onvalue=True, offvalue=False,
            command=lambda: self.attributes("-topmost", cb_var.get()), variable=cb_var,
        ).pack(side="right", padx=10)
        frame_toolbar.pack(fill=tk.X)
        self.attributes("-topmost", cb_var.get())

        frame_main = ttk.Frame(self, padding=(5, 5))
        frame_main.pack(expand=True, fill=tk.BOTH)

        # Additional annotations defined in daf to support more types
        annotations = getattr(class_.__init__, "__annotations__", None)
        additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_)

        if class_ is str:
            w = Text(frame_main)
            w.pack(fill=tk.BOTH, expand=True)
            self._map[None] = (w, class_)
        elif class_ in {int, float}:
            w = ttk.Spinbox(frame_main, from_=-9999, to=9999)
            w.pack(fill=tk.X)
            self._map[None] = (w, class_)
            self.resizable(True, False)
        elif get_origin(class_) in {list, Iterable, ABCIterable}:
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
        elif annotations is not None or additional_annotations is not None:
            if annotations is None:
                annotations = {}

            # Additional annotations
            if additional_annotations is not None:
                annotations = {**additional_annotations, **annotations}

            annotations.pop("return", None)
            for (k, v) in annotations.items():
                frame_annotated = ttk.Frame(frame_main, padding=(5, 5))
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
                    elif entry_type is type(None):
                        if bool not in entry_types:
                            combo.insert(tk.END, None)
                    else:  # Type not supported, try other types
                        menu.add_radiobutton(label=f"New {entry_type.__name__}", command=self.new_object_window(entry_type, combo))
                        if get_origin(entry_type) in {list, Iterable, ABCIterable}:
                            editable_types.append(entry_type)

                menu.add_radiobutton(label="Edit selected", command=self.combo_edit_selected(w, editable_types))
                self._map[k] = (w, entry_types)
        else:
            tkmsg.showerror("Load error", "This object cannot be edited.", parent=self)
            self._cleanup()
            return

        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())
        if old is not None:  # Edit
            self.load(old)

    def close_window(self):
        new_window = ttk.Toplevel(master=self, title="Save?", padx=10, pady=10)
        new_window.resizable(False, False)
        new_window.attributes("-topmost", True)
        new_window.bind("<Return>", lambda e: self.save())
        new_window.focus()
        ttk.Label(new_window, text="Do you want to save modifications?").pack(fill=tk.X, expand=True)
        yes_no_frame = ttk.Frame(new_window)
        ttk.Button(yes_no_frame, text="Yes", command=self.save).pack(side="left")
        ttk.Button(yes_no_frame, text="No", command=self._cleanup).pack(side="right")
        yes_no_frame.pack()

    def load(self, object_: ObjectInfo):
        object_ = object_.data if self._map.get(None) is None else object_
        for attr, (widget, types_) in self._map.items():
            try:
                val = object_[attr] if attr is not None else object_  # Single value type
            except Exception:
                continue

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

    def listbox_copy_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection):
                object_: ObjectInfo | Any = lb.get()[selection[0]]
                lb.insert(tk.END, object_)
            else:
                tkmsg.showerror("Empty list!", "Select atleast one item!", parent=self)

        return __

    def listbox_edit_selected(self, lb: ListBoxObjects):
        def __():
            selection = lb.curselection()
            if len(selection) == 1:
                object_ = lb.get()[selection[0]]
                if isinstance(object_, ObjectInfo):
                    NewObjectWindow(object_.class_, lb, self, object_)
                else:
                    NewObjectWindow(type(object_), lb, self, object_)
            else:
                tkmsg.showerror("Selection error", "Select ONE item!", parent=self)

        return __

    def combo_edit_selected(self, combo: ComboBoxObjects, types):
        def __():
            selection = combo.get()

            if isinstance(selection, list):
                return NewObjectWindow(Union[tuple(types)], combo, self, selection)
            elif isinstance(selection, ObjectInfo):
                return NewObjectWindow(selection.class_, combo, self, selection)
            else:
                if isinstance(selection, str) and not len(selection):
                    selection = None

                return NewObjectWindow(type(selection), combo, self, selection)

        return __

    def _cleanup(self):
        type(self).open_widgets[self.parent] = None
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
            tkmsg.showerror("Saving error", f"Could not save the object.\n\n{exc}", parent=self)
