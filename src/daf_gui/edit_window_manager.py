from tkclasswiz import ObjectEditWindow

import ttkbootstrap.dialogs as tkdiag


__all__ = (
   "EditWindowManager", 
)


class EditWindowManager:
    "Manager class for graphically editing objects"
    def __init__(self) -> None:
        self.window = None

    def open_object_edit_window(self, *args, **kwargs):
        if self.window is None or self.window.closed:
            self.window = ObjectEditWindow()
            self.window.open_object_edit_frame(*args, **kwargs)
        else:
            tkdiag.Messagebox.show_error("Object edit window is already open, close it first.", "Already open")
            self.window.focus()
