import ttkbootstrap as ttk

from tkclasswiz.utilities import gui_except, gui_confirm_action
from tkclasswiz.dpi import dpi_scaled
from tkclasswiz.convert import *
from tkclasswiz.storage import *

from ..edit_window_manager import *
from ..connector import *

import ttkbootstrap.dialogs as tkdiag
import tk_async_execute as tae
import tkinter as tk
import daf


__all__ = (
    "LiveTab",
)


class LiveTab(ttk.Frame):
    def __init__(self, edit_mgr: EditWindowManager, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)
        
        self.edit_mgr = edit_mgr
        frame_add_account = ttk.Frame(self)
        frame_add_account.pack(fill=tk.X, pady=dpi_10)

        self.combo_add_object_edit = ComboEditFrame(
            self.edit_mgr.open_object_edit_window,
            [ObjectInfo(daf.add_object, {})],
            master=frame_add_account,
        )
        ttk.Button(frame_add_account, text="Execute", command=self.add_account).pack(side="left")
        self.combo_add_object_edit.pack(side="left", fill=tk.X, expand=True)

        frame_account_opts = ttk.Frame(self)
        frame_account_opts.pack(fill=tk.X, pady=dpi_5)
        ttk.Button(frame_account_opts, text="Refresh", command=self.load_accounts).pack(side="left")  # TODO
        ttk.Button(frame_account_opts, text="Edit", command=self.view_live_account).pack(side="left")
        ttk.Button(frame_account_opts, text="Remove", command=self.remove_account).pack(side="left")

        list_live_objects = ListBoxScrolled(self)
        list_live_objects.pack(fill=tk.BOTH, expand=True)
        self.list_live_objects = list_live_objects
        # The default bind is removal from list and not from actual daf.
        list_live_objects.listbox.unbind_all("<BackSpace>")
        list_live_objects.listbox.unbind_all("<Delete>")
        list_live_objects.listbox.bind("<BackSpace>", lambda e: self.remove_account())
        list_live_objects.listbox.bind("<Delete>", lambda e: self.remove_account())

    @gui_except()
    def add_account(self):
        connection = get_connection()
        selection = self.combo_add_object_edit.combo.current()
        if selection >= 0:
            fnc: ObjectInfo = self.combo_add_object_edit.combo.get()
            fnc_data = convert_to_objects(fnc.data)
            tae.async_execute(connection.add_account(**fnc_data), wait=False, pop_up=True, master=self)
        else:
            tkdiag.Messagebox.show_error("Combobox does not have valid selection.", "Combo invalid selection")

    @gui_confirm_action()
    @gui_except()
    def remove_account(self):
        connection = get_connection()
        selection = self.list_live_objects.curselection()
        if len(selection):
            values = self.list_live_objects.get()
            for i in selection:
                tae.async_execute(
                    connection.remove_account(values[i].real_object),
                    wait=False,
                    pop_up=True,
                    callback=self.load_accounts,
                    master=self
                )
        else:
            tkdiag.Messagebox.show_error("Select atlest one item!", "Select errror")
    
    @gui_except()
    def view_live_account(self):
        selection = self.list_live_objects.curselection()
        if len(selection) == 1:
            object_: ObjectInfo = self.list_live_objects.get()[selection[0]]
            self.edit_mgr.open_object_edit_window(
                daf.ACCOUNT,
                self.list_live_objects,
                old_data=object_
            )
        else:
            tkdiag.Messagebox.show_error("Select one item!", "Empty list!")

    @gui_except()
    def load_accounts(self):
        connection = get_connection()
        async def _load_accounts():
            object_infos = convert_to_object_info(await connection.get_accounts(), save_original=True)
            self.list_live_objects.clear()
            self.list_live_objects.insert(tk.END, *object_infos)

        tae.async_execute(_load_accounts(), wait=False, pop_up=True, master=self)
