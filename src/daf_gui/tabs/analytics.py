from ttkbootstrap.tableview import Tableview
from tkclasswiz.utilities import gui_confirm_action, gui_except
from tkclasswiz.dpi import dpi_scaled
from tkclasswiz.convert import *
from tkclasswiz.storage import *
from typing import List

from ..edit_window_manager import *
from ..connector import *

import ttkbootstrap.dialogs as tkdiag
import ttkbootstrap as ttk
import tkinter as tk

import daf.misc.instance_track as it
import tk_async_execute as tae
import daf

__all__ = (
    "AnalyticsTab",
    "AnalyticFrame",
)


class AnalyticsTab(ttk.Notebook):
    def __init__(self, edit_mgr: EditWindowManager, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        dpi_10 = dpi_scaled(10)

        self.add(
            AnalyticFrame(
                "analytic_get_message_log",
                "analytic_get_num_messages",
                [
                    {"text": "Date", "stretch": True},
                    {"text": "Number of successful", "stretch": True},
                    {"text": "Number of failed", "stretch": True},
                    {"text": "Guild snowflake", "stretch": True},
                    {"text": "Guild name", "stretch": True},
                    {"text": "Author snowflake", "stretch": True},
                    {"text": "Author name", "stretch": True},
                ],
                edit_mgr,
                master=self,
                padding=(dpi_10, dpi_10)
            ),
            text="Message tracking",
        )

        self.add(
            AnalyticFrame(
                "analytic_get_invite_log",
                "analytic_get_num_invites",
                [
                    {"text": "Date", "stretch": True},
                    {"text": "Count", "stretch": True},
                    {"text": "Guild snowflake", "stretch": True},
                    {"text": "Guild name", "stretch": True},
                    {"text": "Invite ID", "stretch": True},
                ],
                edit_mgr,
                master=self,
                padding=(dpi_10, dpi_10)
            ),
            text="Invite tracking",
        )


class AnalyticFrame(ttk.Frame):
    def __init__(
        self,
        getter_history: str,
        getter_counts: str,
        counts_coldata: dict,
        edit_mgr: EditWindowManager,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(10)

        self.edit_mgr = edit_mgr

        async def analytics_load_history():
            connection = get_connection()
            logger = await connection.get_logger()

            param_object = combo_history.combo.get()
            param_object_params = convert_to_objects(param_object.data)
            items = await connection.execute_method(
                it.ObjectReference.from_object(logger), getter_history, **param_object_params
            )
            items = convert_to_object_info(items)
            lst_history.clear()
            lst_history.insert(tk.END, *items)

        def show_log(listbox: ListBoxScrolled):
            selection = listbox.curselection()
            if len(selection) == 1:
                object_: ObjectInfo = listbox.get()[selection[0]]
                self.edit_mgr.open_object_edit_window(
                    object_.class_,
                    listbox,
                    old_data=object_,
                    check_parameters=False,
                    allow_save=False
                )
            else:
                tkdiag.Messagebox.show_error("Select ONE item!", "Empty list!")

        async def delete_logs_async(table, keys: List[int]):
            connection = get_connection()
            logger = await connection.get_logger()
            await connection.execute_method(
                it.ObjectReference.from_object(logger),
                "delete_logs",
                primary_keys=keys,
                table=table
            )

        @gui_confirm_action()
        @gui_except()
        def delete_logs(listbox: ListBoxScrolled):
            selection = listbox.curselection()
            if len(selection):
                all_ = listbox.get()
                if issubclass(all_[0].class_, dict):
                    raise ValueError("Only SQL logs can be deleted through the GUI at the moment.")

                tae.async_execute(
                    delete_logs_async(all_[0].class_, [all_[i].data["id"] for i in selection]),
                    wait=False,
                    pop_up=True,
                    master=self
                )
            else:
                tkdiag.Messagebox.show_error("Select atlest one item!", "Selection error.")

        frame_msg_history = ttk.Labelframe(self, padding=(dpi_10, dpi_10), text="Logs", bootstyle="primary")
        frame_msg_history.pack(fill=tk.BOTH, expand=True)

        combo_history = ComboEditFrame(
            self.edit_mgr.open_object_edit_window,
            [ObjectInfo(getattr(daf.logging.LoggerBASE, getter_history), {})],
            frame_msg_history,
        )
        combo_history.pack(fill=tk.X)

        frame_msg_history_bnts = ttk.Frame(frame_msg_history)
        frame_msg_history_bnts.pack(fill=tk.X, pady=dpi_10)
        ttk.Button(
            frame_msg_history_bnts,
            text="Get logs",
            command=lambda: tae.async_execute(analytics_load_history(), wait=False, pop_up=True, master=self)
        ).pack(side="left", fill=tk.X)
        ttk.Button(
            frame_msg_history_bnts,
            command=lambda: show_log(lst_history),
            text="View log"
        ).pack(side="left", fill=tk.X)
        ttk.Button(
            frame_msg_history_bnts,
            command=lambda: delete_logs(lst_history),
            text="Delete selected"
        ).pack(side="left", fill=tk.X)
        lst_history = ListBoxScrolled(frame_msg_history)
        lst_history.listbox.unbind_all("<Delete>")
        lst_history.listbox.unbind_all("<BackSpace>")
        lst_history.listbox.bind("<Delete>", lambda e: delete_logs(lst_history))
        lst_history.listbox.bind("<BackSpace>", lambda e: delete_logs(lst_history))
        lst_history.pack(expand=True, fill=tk.BOTH)

        # Number of messages
        async def analytics_load_num():
            connection = get_connection()
            logger = await connection.get_logger()
            param_object = combo_count.combo.get()
            parameters = convert_to_objects(param_object.data)
            count = await connection.execute_method(
                it.ObjectReference.from_object(logger),
                getter_counts,
                **parameters
            )

            tw_num.delete_rows()
            tw_num.insert_rows(0, count)
            tw_num.goto_first_page()

        frame_num = ttk.Labelframe(self, padding=(dpi_10, dpi_10), text="Counts", bootstyle="primary")
        combo_count = ComboEditFrame(
            self.edit_mgr.open_object_edit_window,
            [ObjectInfo(getattr(daf.logging.LoggerBASE, getter_counts), {})],
            frame_num,
        )
        combo_count.pack(fill=tk.X)
        tw_num = Tableview(
            frame_num,
            bootstyle="primary",
            coldata=counts_coldata,
            searchable=True,
            paginated=True,
            autofit=True)

        ttk.Button(
            frame_num,
            text="Calculate",
            command=lambda: tae.async_execute(analytics_load_num(), wait=False, pop_up=True, master=self)
        ).pack(anchor=tk.W, pady=dpi_10)

        frame_num.pack(fill=tk.BOTH, expand=True, pady=dpi_5)
        tw_num.pack(expand=True, fill=tk.BOTH)
