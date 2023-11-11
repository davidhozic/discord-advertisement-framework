from typing import get_origin, Iterable
from collections.abc import Iterable as ABCIterable

from .frame_number import *
from .frame_iterable import *
from .frame_string import *
from .frame_struct import *
from .frame_base import *


from ..dpi import dpi_scaled
from ..extensions import extendable
from ..utilities import gui_except

import tkinter as tk
import tkinter.ttk as ttk


__all__ = (
    "ObjectEditWindow",
)


@extendable
class ObjectEditWindow(tk.Toplevel):
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
        tuple: NewObjectFrameIterable,
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

        var = tk.BooleanVar(value=True)
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

    @gui_except()
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
