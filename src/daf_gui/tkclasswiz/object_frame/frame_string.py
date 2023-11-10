
from typing import Any

from ..storage import *
from .frame_base import *
from ..extensions import extendable

import tkinter as tk


TEXT_MAX_UNDO = 20


__all__ = (
    "NewObjectFrameString",
)


@extendable
class NewObjectFrameString(NewObjectFrameBase):
    def __init__(
        self,
        class_: Any,
        return_widget: Any,
        parent=None,
        old_data: str = None,
        check_parameters: bool = True,
        allow_save=True
    ):
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

