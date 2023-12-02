
from typing import Union, Any
from .frame_base import *
from ..extensions import extendable
import tkinter as tk
import tkinter.ttk as ttk

__all__ = (
    "NewObjectFrameNumber",
)

@extendable
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
