"""
Method execution TOD extension.
"""
from ..tk_object_define.object_frame.frame_struct import NewObjectFrameStruct
from ..tk_object_define.convert import convert_to_objects, ObjectInfo
from ..tk_object_define.storage import ComboEditFrame
from ..connector import get_connection
from ..tk_object_define.dpi import *

import ttkbootstrap.dialogs as tkdiag
import tk_async_execute as tae
import ttkbootstrap as ttk
import tkinter as tk
import daf

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


def load_extension(frame: NewObjectFrameStruct):
    if (
            frame.old_gui_data is None or
            # getattr since class_ can also be non ObjectInfo
            getattr(frame.old_gui_data, "real_object", None) is None or
            (available_methods := EXECUTABLE_METHODS.get(frame.class_)) is None or
            not frame.allow_save
        ):
            return

    def execute_method():
        async def runner():
            method = frame_execute_method.combo.get()
            if not isinstance(method, ObjectInfo):  # String typed in that doesn't match any names
                tkdiag.Messagebox.show_error("No method selected!", "Selection error", frame.origin_window)
                return

            method_param = convert_to_objects(method.data, skip_real_conversion=True)
            connection = get_connection()
            # Call the method though the connection manager
            await connection.execute_method(
                frame.old_gui_data.real_object,
                method.class_.__name__,
                **method_param,
            )

        tae.async_execute(runner(), wait=False, pop_up=True, master=frame.origin_window)

    dpi_5, dpi_10 = dpi_scaled(5), dpi_scaled(10)
    frame_method = ttk.LabelFrame(
        frame,
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
            extra_values[k] = v(frame.old_gui_data)

        return frame.new_object_frame(class_, widget, *args, **kwargs, additional_values=extra_values)

    frame_execute_method = ComboEditFrame(new_object_frame_with_values, combo_values, master=frame_method)
    frame_execute_method.pack(side="right", fill=tk.X, expand=True)
    frame_method.pack(fill=tk.X)
