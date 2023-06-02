"""
Module contains additional widgets and their setup handlers.
"""
from contextlib import suppress

from .utilities import *
from .convert import *
from .dpi import *
from .connector import get_connection

import _discord as discord
import daf

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
        date = tkdiag.Querybox.get_date(frame, title="Select the date")
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
        _ = tkdiag.Querybox.get_color(frame, "Choose color")
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
        (oi := frame.old_object_info) is None or
        oi.real_object is None
    ):
        return

    def _callback(*args):
        async def update():
            old = frame.old_object_info
            values = {
                k: convert_to_objects(v)
                for k, v in frame._read_gui_values().items()
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
        (oi := frame.old_object_info) is None or
        oi.real_object is None
    ):
        return

    def _callback(*args):
        async def refresh():
            opened_frames = frame.origin_window.opened_frames
            connection = get_connection()
            # Need to do this on all previous frames, otherwise we would have wrong data
            for frame_ in reversed(opened_frames):
                old_object_info = frame_.old_object_info
                if not isinstance(old_object_info, list) and hasattr(old_object_info.real_object, "_daf_id"):
                    real = await connection.refresh(old_object_info.real_object)  # Get refresh object from DAF
                    frame_._update_old_object(convert_to_object_info(real, True))
                    frame_.load()

                frame_.save_gui_values()

        async_execute(refresh(), parent_window=frame.origin_window)

    w.configure(command=_callback)
    ToolTip(w, "Load updated values from the object into the window", topmost=True)
    w.pack(side="right", padx=dpi_scaled(2))


# Map that maps the instance we are defining class to a list of additional objects.
ADDITIONAL_WIDGETS = {
    dt.datetime: [AdditionalWidget(ttk.Button, setup_additional_widget_datetime, text="Select date")],
    discord.Colour: [AdditionalWidget(ttk.Button, setup_additional_widget_color_picker, text="Color picker")],
    daf.FILE: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
    daf.LoggerJSON: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.LoggerCSV: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.AUDIO: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
}

for name in dir(daf):
    item = getattr(daf, name)
    with suppress(TypeError):
        if hasattr(item, "update"):
            if item not in ADDITIONAL_WIDGETS:
                ADDITIONAL_WIDGETS[item] = []

            ADDITIONAL_WIDGETS[item].extend([
                AdditionalWidget(ttk.Button, setup_additional_live_update, text="Live update"),
                AdditionalWidget(ttk.Button, setup_additional_live_refresh, text="Refresh")
            ])


__all__ = list(globals().keys())
