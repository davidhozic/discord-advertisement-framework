from typing import get_args, get_origin, Iterable, Union, Literal, Dict, Tuple

from collections.abc import Iterable as ABCIterable
from functools import partial
from enum import Enum


from ..convert import *
from ..dpi import *
from ..utilities import *
from ..storage import *
from ..messagebox import Messagebox
from ..extensions import extendable
from ..annotations import get_annotations

from .frame_base import *

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfile

import inspect
import copy
import json


__all__ = (
    "NewObjectFrameStruct",
    "NewObjectFrameStructView",
)


@extendable
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
    def __new__(cls, *args, **kwargs):
        if kwargs.get("allow_save", True):
            obj = super().__new__(NewObjectFrameStruct)
        else:
            obj = super().__new__(NewObjectFrameStructView)

        return obj

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
        super().__init__(class_, return_widget, parent, old_data, check_parameters,allow_save)
        self._map: Dict[str, Tuple[ComboBoxObjects, Iterable[type]]] = {}
        dpi_5 = dpi_scaled(5)

        if not (annotations := get_annotations(class_)):
            raise TypeError("This object cannot be edited.")

        # Template
        @gui_except(window=self)
        def save_template():
            filename = tkfile.asksaveasfilename(filetypes=[("JSON", "*.json")], parent=self)
            if filename == "":
                return

            json_data = convert_to_json(self.to_object(ignore_checks=True))

            if not filename.endswith(".json"):
                filename += ".json"

            with open(filename, "w", encoding="utf-8") as file:
                json.dump(json_data, file, indent=2)

            Messagebox.show_info("Finished", f"Saved to {filename}", parent=self)

        @gui_except(window=self)
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
        menu = tk.Menu(bnt_menu_template)
        menu.add_command(label="Load template", command=load_template)
        menu.add_command(label="Save template", command=save_template)
        bnt_menu_template.configure(menu=menu)
        bnt_menu_template.pack(side="left")

        def fill_values(k: str, entry_types: list, menu: tk.Menu, combo: ComboBoxObjects):
            "Fill ComboBox values based on types in ``entry_types`` and create New <object_type> buttons"
            any_filled = False
            for entry_type in entry_types:
                if get_origin(entry_type) is Literal:
                    values = get_args(entry_type)
                    combo["values"] = values
                    # tkvalid.add_option_validation(combo, values)
                elif entry_type is bool:
                    combo.insert(tk.END, True)
                    combo.insert(tk.END, False)
                    # tkvalid.add_option_validation(combo, ["True", "False", ''])
                elif issubclass_noexcept(entry_type, Enum):
                    combo["values"] = values = [en for en in entry_type]
                    # tkvalid.add_option_validation(combo, list(map(str, values)) + [''])
                elif entry_type is type(None):
                    if bool not in entry_types:
                        combo.insert(tk.END, None)
                else:  # Type not supported, try other types
                    any_filled = True
                    if self.allow_save:
                        menu.add_command(
                            label=f"New {self.get_cls_name(entry_type)}",
                            command=partial(self.new_object_frame, entry_type, combo)
                        )

            # Additional values to be inserted into ComboBox
            for value in additional_values.get(k, []):
                combo.insert(tk.END, value)

            # The class of last list like type. Needed when "Edit selected" is used
            # since we don't know what type it was
            return any_filled

        max_attr_name_len = max(*map(len, annotations), 15) - 2
        
        for (k, v) in annotations.items():
            # Init widgets
            entry_types = self.convert_types(v)
            frame_annotated = ttk.Frame(self.frame_main)
            frame_annotated.pack(fill=tk.BOTH, expand=True, pady=dpi_5)
            ttk.Label(frame_annotated, text=k, width=max_attr_name_len).pack(side="left")

            bnt_new_menu = ttk.Menubutton(frame_annotated, text="New")            
            menu_new = tk.Menu(bnt_new_menu)
            bnt_new_menu.configure(menu=menu_new)

            w = combo = ComboBoxObjects(frame_annotated)

            # Fill values
            any_filled = fill_values(k, entry_types, menu_new, combo)
            bnt_edit = ttk.Button(
                frame_annotated,
                text="🖋️",
                width=3,
                command=partial(self._edit_selected, k, w)
            )

            bnt_copy_paste = ttk.Menubutton(frame_annotated, text="C/P")
            copy_menu = tk.Menu(bnt_copy_paste)
            copy_menu.add_command(label="Copy", command=combo.save_to_clipboard)
            copy_menu.add_command(label="Paste", command=combo.paste_from_clipboard)
            bnt_copy_paste.configure(menu=copy_menu)

            if not (any_filled and self.allow_save):
                bnt_new_menu.configure(state="disabled")

            if not any_filled:
                bnt_edit.configure(state="disabled")

            dpi_5_h = dpi_5 // 2
            bnt_copy_paste.pack(side="right", padx=dpi_5_h)
            bnt_edit.pack(side="right", padx=dpi_5_h)
            bnt_new_menu.pack(side="right", padx=dpi_5_h)
            combo.pack(fill=tk.X, side="right", expand=True, padx=dpi_5_h)
            self._map[k] = (w, entry_types)

        if old_data is not None:  # Edit
            self.load(old_data)

        self.remember_gui_data()

    @extendable
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

    @extendable
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
                if not value:
                    continue

                value = self.cast_type(value, types_)

            map_[attr] = value

        object_ = ObjectInfo(self.class_, map_)  # Abstraction of the underlaying object
        if not ignore_checks and self.check_parameters and inspect.isclass(self.class_):  # Only check objects
            # Cache the object created for faster
            convert_to_objects(object_, cached=True)  # Tries to create instances to check for errors

        return object_

    def get_gui_data(self) -> dict:
        values = {}
        for attr, (widget, types_) in self._map.items():
            value = widget.get()
            if isinstance(value, str) and not value:  # Ignore empty values
                continue

            if isinstance(value, (list, tuple, set)):  # Copy lists else the values would change in the original state
                value = copy.copy(value)

            values[attr] = value

        return values

    @gui_except()
    def _edit_selected(self, key: str, combo: ComboBoxObjects):
        selection = combo.get()

        # Convert selection to any of the allowed types.
        # This is used for casting manually typed values (which are strings) into appropriate types
        # Eg. if a number is manually typed in and Edit button is clicked, this would result in a string type
        # edit request, which is not really the intend. The intend is to edit a number in this example.
        if isinstance(selection, str):
            selection = self.cast_type(selection, self._map[key][1])

        if isinstance(selection, list):
            types = self.convert_types(get_annotations(self.class_)[key])
            for type_ in types:
                if get_origin(type_) in {list, tuple, set, Iterable, ABCIterable}:
                    list_type = type_
                    break
            else:
                list_type = None

            return self.new_object_frame(list_type, combo, old_data=selection)
        if isinstance(selection, ObjectInfo):
            return self.new_object_frame(selection.class_, combo, old_data=selection)
        else:
            return self.new_object_frame(type(selection), combo, old_data=selection)


class NewObjectFrameStructView(NewObjectFrameStruct):
    """
    Same as :class:`NewObjectFrameStruct`, but creates a wrapper Viewer class, which's attributes automatically
    get mapped as annotations, which the :class:`NewObjectFrameStruct` knows how to handle.
    """
    def __init__(self, class_, *args, **kwargs):
        class Viewer:
            def __init__(self) -> None:
                pass

        Viewer.__name__ = class_.__name__

        old_data: ObjectInfo = kwargs["old_data"]
        Viewer.__init__.__annotations__ = {k: v.class_ if isinstance(v, ObjectInfo) else type(v) for k, v in old_data.data.items()}
        super().__init__(Viewer, *args, **kwargs)

    @gui_except()
    def _edit_selected(self, key: str, combo: ComboBoxObjects):
        selection = combo.get()

        # Convert selection to any of the allowed types.
        # This is used for casting manually typed values (which are strings) into appropriate types
        # Eg. if a number is manually typed in and Edit button is clicked, this would result in a string type
        # edit request, which is not really the intend. The intend is to edit a number in this example.
        if isinstance(selection, str):
            selection = self.cast_type(selection, self._map[key][1])

        if isinstance(selection, ObjectInfo):
            return self.new_object_frame(selection.class_, combo, old_data=selection)
        else:
            return self.new_object_frame(type(selection), combo, old_data=selection)


