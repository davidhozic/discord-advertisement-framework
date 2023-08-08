"""
Contains definitions for automatic object definition windows and frames.
"""
from typing import get_args, get_origin, Iterable, Union, Literal, Dict, Tuple, Any

from collections.abc import Iterable as ABCIterable
from contextlib import suppress
from enum import Enum


from .convert import *
from .dpi import *
from .utilities import *

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
import json


__all__ = (
    "Text",
    "ListBoxObjects",
    "ListBoxScrolled",
    "ComboBoxObjects",
    "ObjectEditWindow",
    "ComboBoxText",
    "ComboEditFrame",
)


HELP_URLS = {
    "daf": f"https://daf.davidhozic.com/en/v{'.'.join(daf.VERSION.split('.')[:2])}.x/?rtd_search={{}}",
    "_discord": f"https://docs.pycord.dev/en/v{discord._version.__version__}/search.html?q={{}}",
    "builtins": "https://docs.python.org/3/search.html?q={}"
}

# Mapping which tells the frame which methods can be executed on live objects
EXECUTABLE_METHODS = {
    daf.guild.GUILD: [daf.guild.GUILD.add_message, daf.guild.GUILD.remove_message],
    daf.guild.USER: [daf.guild.USER.add_message, daf.guild.USER.remove_message],
    daf.guild.AutoGUILD: [daf.guild.AutoGUILD.add_message, daf.guild.AutoGUILD.remove_message],
    daf.client.ACCOUNT: [daf.client.ACCOUNT.add_server, daf.client.ACCOUNT.remove_server]
}

ADDITIONAL_PARAMETER_VALUES = {
    daf.GUILD.remove_message: {
        # GUILD.messages
        "message": lambda old_info: old_info.data["messages"]
    },
    daf.USER.remove_message: {
        # GUILD.messages
        "message": lambda old_info: old_info.data["messages"]
    },
    daf.AutoGUILD.remove_message: {
        # GUILD.messages
        "message": lambda old_info: old_info.data["messages"]
    },
    daf.ACCOUNT.remove_server: {
        # ACCOUNT.servers
        "server": lambda old_info: old_info.data["servers"]
    }
}

DEPRECATION_NOTICES = {
    daf.AUDIO: [("daf.dtypes.AUDIO", "2.12", "Replaced with daf.dtypes.FILE")],
    daf.VoiceMESSAGE: [("daf.dtypes.AUDIO as type for data parameter", "2.12", "Replaced with daf.dtypes.FILE")],
}


TEXT_MAX_UNDO = 20
LAMBDA_TYPE = type(lambda x: None)


class NewObjectFrameBase(ttk.Frame):
    """
    Base Frame for inside the :class:`ObjectEditWindow` that allows object definition.

    Parameters
    -------------
    class_: Any
        The class we are defining for.
    return_widget: Any
        The widget to insert the ObjectInfo into after saving.
    parent: TopLevel
        The parent window.
    old_data: Any
        The old_data gui data.
    check_parameters: bool
        Check parameters (by creating the real object) upon saving.
        This is ignored if editing a function instead of a class.
    allow_save: bool
        If False, will open in read-only mode.
    """
    origin_window: "ObjectEditWindow" = None

    def __init__(
        self,
        class_: Any,
        return_widget: Union[ComboBoxObjects, ListBoxObjects, None],
        parent = None,
        old_data: Any = None,
        check_parameters: bool = True,
        allow_save = True,
    ):
        self.class_ = class_
        self.return_widget = return_widget
        self._original_gui_data = None
        self.parent = parent
        self.check_parameters = check_parameters  # At save time
        self.allow_save = allow_save  # Allow save or not allow (eg. viewing SQL data)
        self.old_gui_data = old_data  # Set in .load

        # If return_widget is None, it's a floating display with no return value
        editing_index = return_widget.current() if return_widget is not None else -1
        if editing_index == -1:
            editing_index = None

        self.editing_index = editing_index  # The index of old_gui_data inside the return widget

        super().__init__(master=parent)
        self.init_toolbar_frame(class_)
        self.init_main_frame()

    @staticmethod
    def get_cls_name(cls):
        if hasattr(cls, "_name"):
            return cls._name
        if hasattr(cls, "__name__"):
            return cls.__name__
        else:
            return cls

    @staticmethod
    def _lambda(method, *args, **kwargs):
        def _():
            return method(*args, **kwargs)

        return _

    @classmethod
    def set_origin_window(cls, window: "ObjectEditWindow"):
        cls.origin_window = window

    @classmethod
    def cast_type(cls, value: Any, types: Iterable):
        """
        Tries to convert *value* into one of the types inside *types* (first successful).

        Raises
        ----------
        TypeError
            Could not convert into any type.
        """

        CAST_FUNTIONS = {
            dict: lambda v: convert_dict_to_object_info(json.loads(v))
        }

        for type_ in filter(lambda t: cls.get_cls_name(t) in __builtins__, types):
            with suppress(Exception):
                cast_funct = CAST_FUNTIONS.get(type_)
                if cast_funct is None:
                    value = type_(value)
                else:
                    value = cast_funct(value)
                break
        else:
            raise TypeError(f"Could not convert '{value}' to any of accepted types.\nAccepted types: '{types}'")

        return value

    @classmethod
    def convert_types(cls, types_in):
        def remove_wrapped(types: list):
            r = types.copy()
            for type_ in types:
                # It's a wrapper of some class -> remove the wrapped class
                if hasattr(type_, "__wrapped__"):
                    if type_.__wrapped__ in r:
                        r.remove(type_.__wrapped__)

            return r

        while get_origin(types_in) is Union:
            types_in = get_args(types_in)

        if not isinstance(types_in, list):
            if isinstance(types_in, tuple):
                types_in = list(types_in)
            else:
                types_in = [types_in, ]

        # Also include inherited objects
        subtypes = []
        for t in types_in:
            if hasattr(t, "__subclasses__") and t.__module__.split('.', 1)[0] in {"_discord", "daf"}:
                for st in t.__subclasses__():
                    subtypes.extend(cls.convert_types(st))

        # Remove wrapped classes (eg. wrapped by decorator)
        return remove_wrapped(types_in + subtypes)

    def init_main_frame(self):
        frame_main = ttk.Frame(self)
        frame_main.pack(expand=True, fill=tk.BOTH)
        self.frame_main = frame_main

    def init_toolbar_frame(self, class_):
        frame_toolbar = ttk.Frame(self)
        frame_toolbar.pack(fill=tk.X)
        self.frame_toolbar = frame_toolbar

        # Help button
        package = class_.__module__.split(".", 1)[0]
        help_url = HELP_URLS.get(package)
        if help_url is not None:
            def cmd():
                webbrowser.open(help_url.format(self.get_cls_name(class_)))

            ttk.Button(frame_toolbar, text="Help", command=cmd).pack(side="left")

        # Deprecation notices
        if len(notices := DEPRECATION_NOTICES.get(class_, [])):
            dep_frame = ttk.Frame(self)
            dep_frame.pack(fill=tk.X, pady=dpi_scaled(5))

            def show_deprecations():
                tkdiag.Messagebox.show_warning(
                    f"\n{'-'*30}\n".join(f"'{title}' is scheduled for removal in v{version}.\nReason: '{reason}'" for title, version, reason in notices),
                    "Deprecation notice",
                    self
                )
            ttk.Button(dep_frame, text="Deprecation notices", bootstyle="dark", command=show_deprecations).pack(side="left")

        # Additional widgets
        add_widgets = ADDITIONAL_WIDGETS.get(class_)
        if add_widgets is not None:
            for add_widg in add_widgets:
                setup_cmd = add_widg.setup_cmd
                add_widg = add_widg.widget_class(frame_toolbar, *add_widg.args, **add_widg.kwargs)
                setup_cmd(add_widg, self)

    @property
    def modified(self) -> bool:
        """
        Returns True if the GUI values have been modified.
        """
        current_values = self.get_gui_data()
        return current_values != self._original_gui_data

    def update_window_title(self):
        "Set's the window title according to edit context."
        self.origin_window.title(f"{'New' if self.old_gui_data is None else 'Edit'} {self.get_cls_name(self.class_)} object")

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

    def new_object_frame(
        self,
        class_,
        widget,
        *args,
        **kwargs
    ):
        """
        Opens up a new object frame on top of the current one.
        Parameters are the same as in :class:`NewObjectFrame` (current class).
        """
        allow_save = kwargs.pop("allow_save", self.allow_save)
        return self.origin_window.open_object_edit_frame(
            class_, widget, allow_save=allow_save, *args, **kwargs
        )

    def to_object(self):
        """
        Creates an object from the GUI data.
        """
        raise NotImplementedError

    def load(self, old_data: Any):
        """
        Loads the old object info data into the GUI.

        Parameters
        -------------
        old_data: Any
            The old gui data to load.
        """
        raise NotImplementedError

    def save(self):
        """
        Save the current object into the return widget and then close this frame.
        """
        try:
            if not self.allow_save or self.return_widget is None:
                raise TypeError("Saving is not allowed in this context!")

            object_ = self.to_object()
            self._update_ret_widget(object_)
            self._cleanup()
        except Exception as exc:
            tkdiag.Messagebox.show_error(
                f"Could not save the object.\n{exc}",
                "Saving error",
                parent=self.origin_window
            )

    def remember_gui_data(self):
        """
        Remembers GUI data for change checking.
        """
        self._original_gui_data = self.get_gui_data()

    def get_gui_data(self) -> Any:
        """
        Returns all GUI values.
        """
        raise NotImplementedError

    def _cleanup(self):
        self.origin_window.clean_object_edit_frame()

    def _update_ret_widget(self, new: Any):
        ind = self.return_widget.count()
        if self.old_gui_data is not None:
            ret_widget = self.return_widget
            if self.editing_index is not None:  # The index of edited item inside return widget
                ind = self.editing_index
                ret_widget.delete(ind)

        self.return_widget.insert(ind, new)
        if isinstance(self.return_widget, ComboBoxObjects):
            self.return_widget.current(ind)
        else:
            self.return_widget.selection_set(ind)


class NewObjectFrameStruct(NewObjectFrameBase):
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
    old_data: ObjectInfo
        The old_data ObjectInfo object to edit.
    check_parameters: bool
        Check parameters (by creating the real object) upon saving.
        This is ignored if editing a function instead of a class.
    allow_save: bool
        If False, will open in read-only mode.
    additional_values: Dict[str, Any]
        A mapping of additional values to be inserted into corresponding field.
    """
    def __init__(
        self,
        class_,
        return_widget: Union[ComboBoxObjects, ListBoxScrolled],
        parent = None,
        old_data: ObjectInfo = None,
        check_parameters: bool = True,
        allow_save = True,
        additional_values: dict = {},
    ):
        def get_annotations(class_) -> dict:
            """
            Returns class / function annotations including overrides.
            """
            annotations = {}
            with suppress(AttributeError):
                if inspect.isclass(class_):
                    annotations = class_.__init__.__annotations__
                else:
                    annotations = class_.__annotations__

            additional_annotations = ADDITIONAL_ANNOTATIONS.get(class_, {})
            annotations = {**annotations, **additional_annotations}

            if "return" in annotations:
                del annotations["return"]

            return annotations

        super().__init__(class_, return_widget, parent, old_data, check_parameters, allow_save)
        self._map: Dict[str, Tuple[ComboBoxObjects, Iterable[type]]] = {}
        dpi_5 = dpi_scaled(5)

        if not (annotations := get_annotations(class_)):
            tkdiag.Messagebox.show_error("This object cannot be edited.", "Load error", parent=self)
            self.origin_window.after_idle(self._cleanup)  # Can not clean the object before it has been added to list
            return

        # Template
        @gui_except(parent=self)
        def save_template():
            filename = tkfile.asksaveasfilename(filetypes=[("JSON", "*.json")], parent=self)
            if filename == "":
                return

            json_data = convert_to_json(self.to_object(ignore_checks=True))

            if not filename.endswith(".json"):
                filename += ".json"

            with open(filename, "w", encoding="utf-8") as file:
                json.dump(json_data, file, indent=2)

            tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self)

        @gui_except(parent=self)
        def load_template():
            filename = tkfile.askopenfilename(filetypes=[("JSON", "*.json")], parent=self)
            if filename == "":
                return

            with open(filename, "r", encoding="utf-8") as file:
                json_data: dict = json.loads(file.read())
                object_info = convert_from_json(json_data)
                # Get class_ attribute if we have the ObjectInfo type, if not just compare the actual type
                if object_info.class_ is not self.class_:
                    raise TypeError(
                        f"The selected template is not a {self.class_.__name__} template.\n"
                        f"The requested template is for type: {object_info.class_.__name__}!"
                    )

                self.load(object_info)

        bnt_menu_template = ttk.Menubutton(self.frame_toolbar, text="Template")
        menu = ttk.Menu(bnt_menu_template)
        menu.add_command(label="Load template", command=load_template)
        menu.add_command(label="Save template", command=save_template)
        bnt_menu_template.configure(menu=menu)
        bnt_menu_template.pack(side="left")

        def fill_values(k: str, entry_types: list, menu: ttk.Menu, combo: ComboBoxObjects):
            "Fill ComboBox values based on types in ``entry_types`` and create New <object_type> buttons"
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

            # Additional values to be inserted into ComboBox
            for value in additional_values.get(k, []):
                combo.insert(tk.END, value)

            # The class of last list like type. Needed when "Edit selected" is used
            # since we don't know what type it was
            return last_list_type

        @gui_except(self)
        def edit_selected(key: str, combo: ComboBoxObjects, original_type = None):
            selection = combo.get()

            # Convert selection to any of the allowed types.
            # This is used for casting manually typed values (which are strings) into appropriate types
            # Eg. if a number is manually typed in and Edit button is clicked, this would result in a string type
            # edit request, which is not really the intend. The intend is to edit a number in this example.
            if isinstance(selection, str):
                selection = self.cast_type(selection, self._map[key][1])

            if isinstance(selection, list):
                return self.new_object_frame(original_type, combo, old_data=selection)
            if isinstance(selection, ObjectInfo):
                return self.new_object_frame(selection.class_, combo, old_data=selection)
            else:
                return self.new_object_frame(type(selection), combo, old_data=selection)

        for (k, v) in annotations.items():
            # Init widgets
            entry_types = self.convert_types(v)
            frame_annotated = ttk.Frame(self.frame_main)
            frame_annotated.pack(fill=tk.BOTH, expand=True)
            ttk.Label(frame_annotated, text=k, width=15).pack(side="left")

            bnt_menu = ttk.Menubutton(frame_annotated)
            menu = tk.Menu(bnt_menu)
            bnt_menu.configure(menu=menu)
            bnt_menu.pack(side="right")

            w = combo = ComboBoxObjects(frame_annotated)
            combo.pack(fill=tk.X, side="right", expand=True, padx=dpi_5, pady=dpi_5)

            # Fill values
            last_list_type = fill_values(k, entry_types, menu, combo)

            # Edit / view command button
            menu.add_command(
                label=f"{'Edit' if self.allow_save else 'View'} selected",
                command=self._lambda(edit_selected, k, w, last_list_type)
            )
            self._map[k] = (w, entry_types)

        self.init_method_frame()
        if old_data is not None:  # Edit
            self.load(old_data)

        self.remember_gui_data()

    def init_method_frame(self):
        "Inits the frame that supports method executino on live objects."
        if (
            self.old_gui_data is None or
            # getattr since class_ can also be non ObjectInfo
            getattr(self.old_gui_data, "real_object", None) is None or
            (available_methods := EXECUTABLE_METHODS.get(self.class_)) is None or
            not self.allow_save
        ):
            return

        def execute_method():
            async def runner():
                method = frame_execute_method.combo.get()
                if not isinstance(method, ObjectInfo):  # String typed in that doesn't match any names
                    tkdiag.Messagebox.show_error("No method selected!", "Selection error", self.origin_window)
                    return

                method_param = convert_to_objects(method.data, skip_real_conversion=True)
                connection = get_connection()
                # Call the method though the connection manager
                await connection.execute_method(
                    self.old_gui_data.real_object,
                    method.class_.__name__,
                    **method_param,
                )

            async_execute(runner(), parent_window=self.origin_window)

        dpi_5, dpi_10 = dpi_scaled(5), dpi_scaled(10)
        frame_method = ttk.LabelFrame(
            self,
            text="Method execution (WARNING! Method data is NOT preserved when closing / saving the frame!)",
            padding=(dpi_5, dpi_10),
            bootstyle=ttk.INFO
        )
        ttk.Button(frame_method, text="Execute", command=execute_method).pack(side="left")
        combo_values = []
        for unbound_meth in available_methods:
            combo_values.append(ObjectInfo(unbound_meth, {}))

        def new_object_frame_with_values(class_, widget, *args, **kwargs):
            """
            Middleware method for opening a new object frame, that fills in additional
            values for the specific method (class_) we are editing.
            """
            extra_values = ADDITIONAL_PARAMETER_VALUES.get(class_, {}).copy()
            for k, v in extra_values.items():
                extra_values[k] = v(self.old_gui_data)

            return self.new_object_frame(class_, widget, *args, **kwargs, additional_values=extra_values)

        frame_execute_method = ComboEditFrame(new_object_frame_with_values, combo_values, master=frame_method)
        frame_execute_method.pack(side="right", fill=tk.X, expand=True)
        frame_method.pack(fill=tk.X)

    def load(self, old_data: ObjectInfo):
        data = old_data.data
        for attr, (widget, types_) in self._map.items():
            if attr not in data:
                continue

            val = data[attr]

            if val not in widget["values"]:
                widget.insert(tk.END, val)

            widget.current(widget["values"].index(val))

        self.old_gui_data = old_data

    def to_object(self, *, ignore_checks = False) -> ObjectInfo:
        """
        Converts GUI data into an ObjectInfo abstraction object.

        Parameters
        ------------
        ignore_checks: bool
            Don't check the correctness of given parameters.
        """
        map_ = {}
        widget: ComboBoxObjects
        for attr, (widget, types_) in self._map.items():
            value = widget.get()
            # Either it's a string needing conversion or a Literal constant not to be converted
            if isinstance(value, str):
                if not len(value):  # Ignore empty values
                    continue

                if Literal is not get_origin(types_[0]):
                    value = self.cast_type(value, types_)

            map_[attr] = value

        extra_args = {}
        if (old_gui_data := self.old_gui_data) is not None:
            # Don't erase the bind to the real object in case this is an edit of an existing ObjectInfo
            extra_args["real_object"] = old_gui_data.real_object
            # Also don't erase any saved properties if received from a live object.
            extra_args["property_map"] = old_gui_data.property_map

        object_ = ObjectInfo(self.class_, map_, **extra_args)  # Abstraction of the underlaying object
        if not ignore_checks and self.check_parameters and inspect.isclass(self.class_):  # Only check objects
            # Cache the object created for faster
            convert_to_objects(object_, cached=True)  # Tries to create instances to check for errors

        return object_

    def get_gui_data(self) -> dict:
        values = {}
        for attr, (widget, types_) in self._map.items():
            value = widget.get()
            if isinstance(value, (list, tuple, set)):  # Copy lists else the values would change in the original state
                value = copy.copy(value)

            values[attr] = value

        return values


class NewObjectFrameNumber(NewObjectFrameBase):
    def __init__(self, class_: Any, return_widget: Any, parent=None, old_data: Any = None, check_parameters: bool = True, allow_save=True):
        super().__init__(class_, return_widget, parent, old_data, check_parameters, allow_save)
        self.storage_widget = ttk.Spinbox(self.frame_main, from_=-9999, to=9999)
        self.storage_widget.pack(fill=tk.X)

        if old_data is not None:  # Edit
            self.load(old_data)

        self.remember_gui_data()

    def load(self, old_data: Union[int, float]):
        self.storage_widget.set(old_data)
        self.old_gui_data = old_data

    def get_gui_data(self) -> Union[int, float]:
        return self.return_widget.get()

    def to_object(self):
        return self.cast_type(self.storage_widget.get(), [self.class_])


class NewObjectFrameIterable(NewObjectFrameBase):
    def __init__(self, class_: Any, return_widget: Any, parent=None, old_data: list = None, check_parameters: bool = True, allow_save=True):
        def edit_selected(lb: ListBoxScrolled):
            selection = lb.curselection()
            if len(selection) == 1:
                object_ = lb.get()[selection[0]]
                if isinstance(object_, ObjectInfo):
                    self.new_object_frame(object_.class_, lb, old_data=object_)
                else:
                    self.new_object_frame(type(object_), lb, old_data=object_)
            else:
                tkdiag.Messagebox.show_error("Select ONE item!", "Selection error", parent=self)

        dpi_5 = dpi_scaled(5)
        super().__init__(class_, return_widget, parent, old_data, check_parameters, allow_save)
        self.storage_widget = w = ListBoxScrolled(self.frame_main, height=20)

        frame_edit_remove = ttk.Frame(self.frame_main, padding=(dpi_5, 0))
        frame_edit_remove.pack(side="right")
        if self.allow_save:
            menubtn = ttk.Menubutton(frame_edit_remove, text="Add object")
            menu = tk.Menu(menubtn)
            menubtn.configure(menu=menu)
            menubtn.pack()
            ttk.Button(frame_edit_remove, text="Remove", command=w.delete_selected).pack(fill=tk.X)
            ttk.Button(frame_edit_remove, text="Edit", command=lambda: edit_selected(w)).pack(fill=tk.X)

            frame_up_down = ttk.Frame(frame_edit_remove)
            frame_up_down.pack(fill=tk.X, expand=True, pady=dpi_5)
            ttk.Button(frame_up_down, text="Up", command=lambda: w.move_selection(-1)).pack(side="left", fill=tk.X, expand=True)
            ttk.Button(frame_up_down, text="Down", command=lambda: w.move_selection(1)).pack(side="left", fill=tk.X, expand=True)

            frame_cp = ttk.Frame(frame_edit_remove)
            frame_cp.pack(fill=tk.X, expand=True)
            ttk.Button(frame_cp, text="Copy", command=w.save_to_clipboard).pack(side="left", fill=tk.X, expand=True)
            ttk.Button(frame_cp, text="Paste", command=w.paste_from_clipboard).pack(side="left", fill=tk.X, expand=True)

            args = get_args(self.class_)
            args = self.convert_types(args)
            if get_origin(args[0]) is Union:
                args = get_args(args[0])

            for arg in args:
                menu.add_command(label=self.get_cls_name(arg), command=self._lambda(self.new_object_frame, arg, w))
        else:
            ttk.Button(frame_edit_remove, text="View", command=lambda: edit_selected(w)).pack(fill=tk.X)

        w.pack(side="left", fill=tk.BOTH, expand=True)

        if old_data is not None:
            self.load(old_data)

        self.remember_gui_data()

    def load(self, old_data: List[Any]):
        self.storage_widget.insert(tk.END, *old_data)
        self.old_gui_data = old_data

    def get_gui_data(self) -> Any:
        return self.storage_widget.get()

    def to_object(self):
        return self.get_gui_data()  # List items are not to be converted


class NewObjectFrameString(NewObjectFrameBase):
    def __init__(self, class_: Any, return_widget: Any, parent=None, old_data: str = None, check_parameters: bool = True, allow_save=True):
        super().__init__(class_, return_widget, parent, old_data, check_parameters, allow_save)
        self.storage_widget = Text(self.frame_main, undo=True, maxundo=TEXT_MAX_UNDO)
        self.storage_widget.pack(fill=tk.BOTH, expand=True)

        if old_data is not None:
            self.load(old_data)

        self.remember_gui_data()

    def load(self, old_data: Any):
        self.storage_widget.insert(tk.END, old_data)
        self.old_gui_data = old_data

    def get_gui_data(self) -> Any:
        return self.storage_widget.get()

    def to_object(self):
        return self.get_gui_data()


class ObjectEditWindow(ttk.Toplevel):
    """
    Top level window for creating and editing new objects.
    """

    # Map used to map types to specific class.
    # If type is not in this map, structured object will be assumed.
    TYPE_INIT_MAP = {
        str: NewObjectFrameString,
        float: NewObjectFrameNumber,
        int: NewObjectFrameNumber,
        list: NewObjectFrameIterable,
        Iterable: NewObjectFrameIterable,
        ABCIterable: NewObjectFrameIterable,
        tuple: NewObjectFrameIterable
    }

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
        NewObjectFrameBase.set_origin_window(self)
        self.protocol("WM_DELETE_WINDOW", self.close_object_edit_frame)

    @property
    def closed(self) -> bool:
        return self._closed

    def open_object_edit_frame(self, class_, *args, **kwargs):
        """
        Opens new frame for defining an object.
        Parameters are the same as for NewObjectFrameBase.
        """
        prev_frame = None
        if len(self.opened_frames):
            prev_frame = self.opened_frames[-1]

        class_origin = get_origin(class_)
        if class_origin is None:
            class_origin = class_

        frame_class = self.TYPE_INIT_MAP.get(class_origin, NewObjectFrameStruct)
        self.opened_frames.append(frame := frame_class(class_, *args, **kwargs, parent=self.frame_main))
        frame.pack(fill=tk.BOTH, expand=True)
        frame.update_window_title()
        if prev_frame is not None:
            prev_frame.pack_forget()

        self.set_default_size_y()

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
            self.set_default_size_y()
        else:
            self._closed = True
            self.destroy()

    def set_default_size_y(self):
        "Sets window Y size to default"
        self.update()
        self.geometry(f"{self.winfo_width()}x{self.winfo_reqheight()}")
