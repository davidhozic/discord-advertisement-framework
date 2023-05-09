"""
Contains definitions for automatic object definition windows and frames.
"""
from typing import get_args, get_origin, Iterable, Union, Literal

from collections.abc import Iterable as ABCIterable
from contextlib import suppress
from enum import Enum

from .convert import *
from .dpi import *
from .async_util import *

from .storage import *
from .extra import *

import _discord as discord
import daf

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag

import webbrowser
import inspect
import copy


__all__ = (
    "Text",
    "ListBoxObjects",
    "ListBoxScrolled",
    "ComboBoxObjects",
    "ObjectEditWindow",
    "NewObjectFrame",
    "ComboBoxText",
    "ComboEditFrame",
)


HELP_URLS = {
    "daf": f"https://daf.davidhozic.com/en/v{daf.VERSION}/?rtd_search={{}}",
    "_discord": f"https://docs.pycord.dev/en/v{discord._version.__version__}/search.html?q={{}}",
    "builtins": "https://docs.python.org/3/search.html?q={}"
}

TEXT_MAX_UNDO = 20


class ObjectEditWindow(ttk.Toplevel):
    """
    Top level window for creating and editing new objects.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closed = False

        dpi_5 = dpi_scaled(5)

        # Elements
        self.opened_frames = []
        self.frame_main = ttk.Frame(self, padding=(dpi_5, dpi_5))
        self.frame_toolbar = ttk.Frame(self, padding=(dpi_5, dpi_5))
        ttk.Button(self.frame_toolbar, text="Close", command=self.close_object_edit_frame).pack(side="left")
        ttk.Button(self.frame_toolbar, text="Save", command=self.save_object_edit_frame).pack(side="left")

        self.frame_toolbar.pack(expand=False, fill=tk.X)
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
        """
        Opens new frame for defining an object.
        """
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

    """
    Frame for inside the :class:`ObjectEditWindow` that allows object definition.

    Parameters
    -------------
    class_: Any
        The class we are defining for.
    return_widget: ComboBoxObjects | ListBoxScrolled
        The widget to insert the ObjectInfo into after saving.
    parent: TopLevel
        The parent window.
    old: ObjectInfo
        The old ObjectInfo object to edit.
    check_parameters: bool
        Check parameters (by creating the real object) upon saving.
    allow_save: bool
        If False, will open in read-only mode.
    """
    origin_window: ObjectEditWindow = None

    def __init__(
        self,
        class_,
        return_widget: Union[ComboBoxObjects, ListBoxScrolled],
        parent = None,
        old: ObjectInfo = None,
        check_parameters: bool = True,
        allow_save = True,
    ):
        self.class_ = class_
        self.return_widget = return_widget
        self._map = {}
        self._original_gui_data = {}
        self.parent = parent
        self.old_object_info = old  # Edit requested
        self.check_parameters = check_parameters  # At save time
        self.allow_save = allow_save  # Allow save or not allow (eg. viewing SQL data)

        super().__init__(master=parent)

        self.init_toolbar_frame(class_)
        if not self.init_main_frame(class_):
            return

        if old is not None:  # Edit
            self.load()

        self.save_gui_values()

    def init_main_frame(self, class_) -> bool:
        frame_main = ttk.Frame(self)
        frame_main.pack(expand=True, fill=tk.BOTH)
        self.frame_main = frame_main

        annotations = {}
        with suppress(AttributeError):
            if inspect.isclass(class_):
                annotations = class_.__init__.__annotations__
            else:
                annotations = class_.__annotations__

        additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_)
        if additional_annotations is not None:
            annotations = {**annotations, **additional_annotations}

        if class_ is str:
            self.init_str()
        elif class_ in {int, float}:
            self.init_int_float(class_)
        elif get_origin(class_) in {list, Iterable, ABCIterable, tuple}:
            self.init_iterable(class_)
        elif annotations:
            self.init_structured(annotations)
        else:
            tkdiag.Messagebox.show_error("This object cannot be edited.", "Load error", parent=self.origin_window)
            self.origin_window.after_idle(self._cleanup)  # Can not clean the object before it has been added to list
            return False

        return True

    def init_toolbar_frame(self, class_):
        frame_toolbar = ttk.Frame(self)
        self.frame_toolbar = frame_toolbar

        package = class_.__module__.split(".", 1)[0]
        help_url = HELP_URLS.get(package)
        if help_url is not None:
            def cmd():
                webbrowser.open(help_url.format(self.get_cls_name(class_)))

            ttk.Button(frame_toolbar, text="Help", command=cmd).pack(side="left")

        add_widgets = ADDITIONAL_WIDGETS.get(class_)
        if add_widgets is not None:
            for add_widg in add_widgets:
                setup_cmd = add_widg.setup_cmd
                add_widg = add_widg.widget_class(frame_toolbar, *add_widg.args, **add_widg.kwargs)
                setup_cmd(add_widg, self)

        frame_toolbar.pack(fill=tk.X)

    def init_structured(self, annotations: dict):
        dpi_5 = dpi_scaled(5)
        annotations.pop("return", None)

        for (k, v) in annotations.items():
            frame_annotated = ttk.Frame(self.frame_main)
            frame_annotated.pack(fill=tk.BOTH, expand=True)

            entry_types = v
            ttk.Label(frame_annotated, text=k, width=15).pack(side="left")

            entry_types = self.convert_types(entry_types)

            bnt_menu = ttk.Menubutton(frame_annotated)
            menu = tk.Menu(bnt_menu)
            bnt_menu.configure(menu=menu)

            w = combo = ComboBoxObjects(frame_annotated)
            bnt_menu.pack(side="right")
            combo.pack(fill=tk.X, side="right", expand=True, padx=dpi_5, pady=dpi_5)

            last_list_type = None
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
                    if get_origin(entry_type) in {list, tuple, set, Iterable, ABCIterable}:
                        last_list_type = entry_type

                    if self.allow_save:
                        menu.add_command(
                            label=f"New {self.get_cls_name(entry_type)}",
                            command=self._lambda(self.new_object_frame, entry_type, combo)
                        )

            menu.add_command(
                label=f"{'Edit' if self.allow_save else 'View'} selected", 
                command=self.combo_edit_selected(w, last_list_type)
            )
            self._map[k] = (w, entry_types)

    def init_iterable(self, class_):
        w = ListBoxScrolled(self.frame_main, height=20)
        self._map[None] = (w, [list])
        frame_edit_remove = ttk.Frame(self.frame_main)
        frame_edit_remove.pack(side="right")
        if self.allow_save:
            menubtn = ttk.Menubutton(frame_edit_remove, text="Add object")
            menu = tk.Menu(menubtn)
            menubtn.configure(menu=menu)
            menubtn.pack()
            ttk.Button(frame_edit_remove, text="Remove", command=w.listbox_delete_selected).pack(fill=tk.X)
            ttk.Button(frame_edit_remove, text="Edit", command=self.listbox_edit_selected(w)).pack(fill=tk.X)
            ttk.Button(frame_edit_remove, text="Copy", command=w.listbox_copy_selected).pack(fill=tk.X)
            args = get_args(class_)
            args = self.convert_types(args)
            if get_origin(args[0]) is Union:
                args = get_args(args[0])

            for arg in args:
                menu.add_command(label=self.get_cls_name(arg), command=self._lambda(self.new_object_frame, arg, w))
        else:
            ttk.Button(frame_edit_remove, text="View", command=self.listbox_edit_selected(w)).pack(fill=tk.X)

        w.pack(side="left", fill=tk.BOTH, expand=True)

    def init_int_float(self, class_):
        w = ttk.Spinbox(self.frame_main, from_=-9999, to=9999)
        w.pack(fill=tk.X)
        self._map[None] = (w, [class_])

    def init_str(self):
        w = Text(self.frame_main, undo=True, maxundo=TEXT_MAX_UNDO)
        w.pack(fill=tk.BOTH, expand=True)
        self._map[None] = (w, [str])

    def _read_gui_values(self) -> dict:
        """
        Returns dictionary who's keys are the class parameters and keys
        are the actual values.
        """
        values = {}
        for attr, (widget, types_) in self._map.items():
            value = widget.get()
            if isinstance(value, (list, tuple, set)):  # Copy lists else the values would change in the original state
                value = copy.copy(value)

            values[attr] = value

        return values

    def save_gui_values(self):
        """
        Saves the original GUI values for change check at save.
        """
        self._original_gui_data = self._read_gui_values()
    
    @property
    def modified(self) -> bool:
        """
        Returns True if the GUI values have been modified.
        """
        current_values = self._read_gui_values()
        return current_values != self._original_gui_data

    @staticmethod
    def get_cls_name(cls):
        if hasattr(cls, "_name"):
            return cls._name
        if hasattr(cls, "__name__"):
            return cls.__name__
        else:
            return cls

    @classmethod
    def set_origin_window(cls, window: ObjectEditWindow):
        cls.origin_window = window

    @classmethod
    def convert_types(cls, types_in):
        while get_origin(types_in) is Union:
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
                    subtypes.extend(cls.convert_types(st))

        return types_in + subtypes

    def update_window_title(self):
        self.origin_window.title(f"{'New' if self.old_object_info is None else 'Edit'} {self.get_cls_name(self.class_)} object")

    def close_frame(self):
        if self.allow_save and self.modified:
            resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self)
            if resp is not None:
                if resp == "Yes":
                    self.save()
                elif resp == "No":
                    self._cleanup()
        else:
            self._cleanup()

    def load(self):
        """
        Loads the old object info data into the GUI.
        """
        object_ = self.old_object_info.data if self._map.get(None) is None else self.old_object_info
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

            elif isinstance(widget, ListBoxScrolled):
                widget.insert(tk.END, *object_)

            elif isinstance(widget, tk.Text):
                widget.insert(tk.END, object_)

            elif isinstance(widget, ttk.Spinbox):
                widget.set(object_)

    @staticmethod
    def _lambda(method, *args, **kwargs):
        def _():
            return method(*args, **kwargs)

        return _

    def new_object_frame(
        self,
        class_,
        widget,
        *args,
        **kwargs
    ):
        """
        Opens up a new object frame on top of the current one.
        Parameters are the same as in :class:`NewObjectFrame` (current class) with the exception
        of ``check_parameters`` and ``allow_save`` - These are inherited from current frame.
        """
        return self.origin_window.open_object_edit_frame(
            class_, widget, check_parameters=self.check_parameters, allow_save=self.allow_save, *args, **kwargs
        )

    def listbox_edit_selected(self, lb: ListBoxScrolled):
        def __():
            selection = lb.curselection()
            if len(selection) == 1:
                object_ = lb.get()[selection[0]]
                if isinstance(object_, ObjectInfo):
                    self.new_object_frame(object_.class_, lb, old=object_)
                else:
                    self.new_object_frame(type(object_), lb, old=object_)
            else:
                tkdiag.Messagebox.show_error("Select ONE item!", "Selection error", parent=self.origin_window)

        return __

    def combo_edit_selected(self, combo: ComboBoxObjects, original_type = None):
        def __():
            selection = combo.get()

            if isinstance(selection, list):
                return self.new_object_frame(original_type, combo, old=selection)
            if isinstance(selection, ObjectInfo):
                return self.new_object_frame(selection.class_, combo, old=selection)
            else:
                if isinstance(selection, str) and not len(selection):
                    selection = None

                return self.new_object_frame(type(selection), combo, old=selection)

        return __

    def _cleanup(self):
        self.origin_window.clean_object_edit_frame()

    def _gui_to_object(self):
        map_ = {}
        for attr, (widget, types_) in self._map.items():
            value = widget.get()

            if isinstance(value, str):  # Ignore empty values
                if not len(value):
                    continue

                # Iterate all valid types until conversion is successful                        
                for type_ in types_:
                    with suppress(Exception):
                        value = type_(value)
                        break

            map_[attr] = value

        single_value = map_.get(None)
        if single_value is not None:
            object_ = single_value
        else:
            object_ = ObjectInfo(self.class_, map_)
            if self.check_parameters:
                convert_to_objects(object_)  # Tries to create instances to check for errors

        return object_

    def _update_old_object(self, new: Union[ObjectInfo, Any]):
        if self.old_object_info is not None:
            old = self.old_object_info
            if isinstance(old, ObjectInfo):
                new.real_object = old.real_object

            ret_widget = self.return_widget
            if isinstance(ret_widget, ListBoxScrolled):
                ind = ret_widget.get().index(self.old_object_info)
            else:
                ind = ret_widget["values"].index(self.old_object_info)

            ret_widget.delete(ind)

        self.return_widget.insert(tk.END, new)
        if isinstance(self.return_widget, ComboBoxObjects):
            self.return_widget.current(self.return_widget["values"].index(new))

        self.old_object_info = new

    def save(self):
        """
        Saves the GUI data into ObjectInfo and place it in the return widget.
        If the real object is linked to ObjectInfo, also execute update metho of the
        real object if it has one.
        """
        try:
            if not self.allow_save:
                raise TypeError("Saving is not allowed in this context!")

            object_ = self._gui_to_object()
            self._update_old_object(object_)
            self._cleanup()
        except Exception as exc:
            tkdiag.Messagebox.show_error(
                f"Could not save the object.\n\n{exc}",
                "Saving error",
                parent=self.origin_window
            )
