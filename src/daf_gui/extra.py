"""
Module contains additional widgets and their setup handlers.
"""
from contextlib import suppress

from .utilities import *
from .convert import *
from .dpi import *
from .connector import get_connection

import _discord as discord
from daf.misc import instance_track as it

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag
import tkinter.filedialog as tkfile
from ttkbootstrap.tooltip import ToolTip

import datetime as dt


class AdditionalWidget:
    """
    Configuration class for additional widgets inside the object definition frame.
    """
    def __init__(self, widget_class, setup_cmd, *args, **kwargs) -> None:
        self.widget_class = widget_class
        self.args = args
        self.kwargs = kwargs
        self.setup_cmd = setup_cmd


def setup_additional_widget_datetime(w: ttk.Button, frame):
    def _callback(*args):
        date = tkdiag.Querybox.get_date(w, title="Select the date")
        for attr in {"year", "month", "day"}:
            widget, types_ = frame._map.get(attr)
            value = getattr(date, attr)
            if value not in widget["values"]:
                widget.insert(tk.END, value)

            widget.set(value)

    w.configure(command=_callback)
    w.pack(side="right")


def setup_additional_widget_color_picker(w: ttk.Button, frame):
    def _callback(*args):
        widget, types = frame._map.get("value")
        _ = tkdiag.Querybox.get_color(w, "Choose color")
        if _ is None:
            return

        rgb, hsl, hex_ = _
        color = int(hex_.lstrip("#"), base=16)
        if color not in widget["values"]:
            widget.insert(tk.END, color)

        widget.set(color)

    w.configure(command=_callback)
    w.pack(side="right")


def setup_additional_widget_file_chooser(w: ttk.Button, frame):
    def _callback(*args):
        file = tkfile.askopenfile(parent=frame)
        if file is None:  # File not opened
            return

        filename = None
        with file:
            filename = file.name

        filename_combo = frame._map.get("filename")[0]
        filename_combo.insert(tk.END, filename)
        filename_combo.set(filename)

    w.configure(command=_callback)
    w.pack(side="right")


def setup_additional_widget_file_chooser_logger(w: ttk.Button, frame):
    def _callback(*args):
        path = tkfile.askdirectory(parent=frame)
        if path == "":
            return

        filename_combo = frame._map.get("path")[0]
        filename_combo.insert(tk.END, path)
        filename_combo.set(path)

    w.configure(command=_callback)
    w.pack(side="right")


def setup_additional_live_update(w: ttk.Button, frame):
    # Don't have a bound object instance
    if (
        not frame.allow_save or
        (oi := frame.old_gui_data) is None or
        oi.real_object is None or
        oi.real_object.ref == -1
    ):
        return

    def _callback(*args):
        async def update():
            old = frame.old_gui_data
            values = {
                k: convert_to_objects(v)
                for k, v in frame.get_gui_data().items()
                if not isinstance(v, str) or v != ''
            }
            connector = get_connection()
            await connector.execute_method(old.real_object, "update", **values)

        async_execute(update(), parent_window=frame.origin_window)

    w.configure(command=_callback)
    ToolTip(w, "Update the actual object with new parameters (taken from this window)", topmost=True)
    w.pack(side="right")


def setup_additional_live_refresh(w: ttk.Button, frame):
    # Don't have a bound object instance
    if (
        (oi := frame.old_gui_data) is None or
        oi.real_object is None or
        oi.real_object.ref == -1
    ):
        return

    def _callback(*args):
        async def refresh():
            opened_frames = frame.origin_window.opened_frames
            connection = get_connection()
            # Need to do this on all previous frames, otherwise we would have wrong data
            for frame_ in reversed(opened_frames):
                old_gui_data = frame_.old_gui_data
                if not isinstance(old_gui_data, list) and isinstance(old_gui_data.real_object, it.ObjectReference):
                    real = await connection.refresh(old_gui_data.real_object)  # Get refresh object from DAF
                    frame_.load(convert_to_object_info(real, True))

                frame_.remember_gui_data()

        async_execute(refresh(), parent_window=frame.origin_window)

    w.configure(command=_callback)
    ToolTip(w, "Load updated values from the object into the window", topmost=True)
    w.pack(side="right", padx=dpi_scaled(2))


def setup_additional_live_properties(w: ttk.Menubutton, frame):
    # Don't have a bound object instance
    oi: ObjectInfo
    if (
        (oi := frame.old_gui_data) is None or
        oi.real_object is None or
        oi.real_object.ref == -1 or
        not oi.property_map # Empty dict
    ):
        return

    def _callback(property_name: str):
        property_value, property_type = frame.old_gui_data.property_map[property_name]

        class PropertyView:
            """
            Fake class used to generate a view-only object edit frame.
            """
            def __init__(self, value: property_type) -> None:
                pass

        frame.new_object_frame(
            PropertyView, None,
            allow_save=False, old_data=ObjectInfo(PropertyView, {"value": property_value})
        )

    menu = ttk.Menu(w, title="Property menu")
    for k in oi.property_map:
        menu.add_command(command=frame._lambda(_callback, k), label=k)

    w.configure(menu=menu)
    ToolTip(w, "Inspect additional properties of the object.", topmost=True)
    w.pack(side="right", padx=dpi_scaled(2))


def setup_additional_widget_default_intents(w: ttk.Button, frame):
    def _callback(*args):
        default = discord.Intents.default()
        map_: dict = frame._map.copy()
        del map_["kwargs"]

        # v = (widget, annotated_types)
        # k = parameter name
        for k, v in map_.items():
            widget, _ = v
            widget.set(str(getattr(default, k)))

    w.configure(command=_callback)
    ToolTip(w, text="Enable everything except privileged intents.", topmost=True)
    w.pack(side="right")


# Map that maps the instance we are defining class to a list of additional objects.
ADDITIONAL_WIDGETS = {
    dt.datetime: [AdditionalWidget(ttk.Button, setup_additional_widget_datetime, text="Select date")],
    discord.Colour: [AdditionalWidget(ttk.Button, setup_additional_widget_color_picker, text="Color picker")],
    daf.FILE: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
    daf.LoggerJSON: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.LoggerCSV: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.AUDIO: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
    discord.Intents: [AdditionalWidget(ttk.Button, setup_additional_widget_default_intents, text="Load default")]
}

for name in dir(daf):
    item = getattr(daf, name)
    with suppress(TypeError):
        if hasattr(item, "update"):
            if item not in ADDITIONAL_WIDGETS:
                ADDITIONAL_WIDGETS[item] = []

            ADDITIONAL_WIDGETS[item].extend([
                AdditionalWidget(ttk.Button, setup_additional_live_update, text="Live update"),
                AdditionalWidget(ttk.Button, setup_additional_live_refresh, text="Refresh"),
            ])

        if hasattr(item, "_daf_id"):
            if item not in ADDITIONAL_WIDGETS:
                ADDITIONAL_WIDGETS[item] = []

            ADDITIONAL_WIDGETS[item].append(
                AdditionalWidget(ttk.Menubutton, setup_additional_live_properties, text="View property"),
            )
