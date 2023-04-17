"""
Module contains additional widgets and their setup handlers.
"""
import _discord as discord
import daf

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag
import tkinter.filedialog as tkfile

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
    w.pack(side="right")


def setup_additional_widget_color_picker(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        widget, types = window._map.get("value")
        _ = tkdiag.Querybox.get_color(window, "Choose color")
        if _ is None:
            return

        rgb, hsl, hex_ = _
        color = int(hex_.lstrip("#"), base=16)
        if color not in widget["values"]:
            widget.insert(tk.END, color)

        widget.set(color)

    w.configure(command=_callback)
    w.pack(side="right")


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
    w.pack(side="right")


def setup_additional_widget_file_chooser_logger(w: ttk.Button, window: "NewObjectFrame"):
    def _callback(*args):
        path = tkfile.askdirectory(parent=window)
        if path == "":
            return

        filename_combo = window._map.get("path")[0]
        filename_combo.insert(tk.END, path)
        filename_combo.set(path)

    w.configure(command=_callback)
    w.pack(side="right")

# Map that maps the instance we are defining class to a list of additional objects.
ADDITIONAL_WIDGETS = {
    dt.datetime: [AdditionalWidget(ttk.Button, setup_additional_widget_datetime, text="Select date")],
    discord.Colour: [AdditionalWidget(ttk.Button, setup_additional_widget_color_picker, text="Color picker")],
    daf.FILE: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
    daf.LoggerJSON: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.LoggerCSV: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser_logger, text="Select folder")],
    daf.AUDIO: [AdditionalWidget(ttk.Button, setup_additional_widget_file_chooser, text="File browse")],
}


__all__ = list(globals().keys())
__all__.append("ADDITIONAL_WIDGETS")
