from ttkbootstrap.tooltip import ToolTip

from tkclasswiz.utilities import gui_except, gui_confirm_action
from tkclasswiz.dpi import dpi_scaled
from tkclasswiz.convert import *
from tkclasswiz.storage import *

from operator import getitem
from pathlib import Path

from ..edit_window_manager import *
from ..connector import *


import ttkbootstrap.dialogs as tkdiag
import tkinter.filedialog as tkfile
import ttkbootstrap as ttk
import tkinter as tk

import tk_async_execute as tae
import json
import daf


__all__ = (
    "SchemaTab",
)


class SchemaTab(ttk.Frame):
    """
    The schema tab of DAF GUI application.
    """
    def __init__(
        self,
        edit_window_manager: EditWindowManager,
        combo_conn: ComboEditFrame,
        *args,
        **kwargs,
    ):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)

        super().__init__(*args, **kwargs)

        self.edit_mgr = edit_window_manager
        self.combo_conn = combo_conn

        # Object tab file menu
        bnt_file_menu = ttk.Menubutton(self, text="Schema")
        menubar_file = tk.Menu(bnt_file_menu)
        menubar_file.add_command(label="Save schema", command=self.save_schema)
        menubar_file.add_command(label="Load schema", command=self.load_schema)
        menubar_file.add_command(label="Generate script", command=self.save_schema_as_script)
        bnt_file_menu.configure(menu=menubar_file)
        bnt_file_menu.pack(anchor=tk.W)

        # Object tab account tab
        frame_tab_account = ttk.Labelframe(
            self,
            text="Accounts", padding=(dpi_10, dpi_10), bootstyle="primary")
        frame_tab_account.pack(side="left", fill=tk.BOTH, expand=True, pady=dpi_10, padx=dpi_5)

        # Accounts list. Defined here since it's needed below
        self.lb_accounts = ListBoxScrolled(frame_tab_account)

        menu_bnt = ttk.Menubutton(
            frame_tab_account,
            text="Object options"
        )
        menu = ttk.Menu(menu_bnt)
        menu.add_command(
            label="New ACCOUNT",
            command=lambda: self.edit_mgr.open_object_edit_window(daf.ACCOUNT, self.lb_accounts)
        )

        menu.add_command(label="Edit", command=self.edit_accounts)
        menu.add_command(label="Remove", command=self.lb_accounts.delete_selected)
        menu_bnt.configure(menu=menu)
        menu_bnt.pack(anchor=tk.W)

        frame_account_bnts = ttk.Frame(frame_tab_account)
        frame_account_bnts.pack(fill=tk.X, pady=dpi_5)
        ttk.Button(
            frame_account_bnts, text="Import from DAF (live)", command=self.import_accounts
        ).pack(side="left")
        t = ttk.Button(
            frame_account_bnts, text="Load selection to DAF (live)", command=lambda: self.load_accounts(True)
        ).pack(side="left")
        self.load_at_start_var = ttk.BooleanVar(value=True)
        t = ttk.Checkbutton(
            frame_account_bnts, text="Load all at start", onvalue=True, offvalue=False,
            variable=self.load_at_start_var
        )
        ToolTip(t, "When starting DAF, load all accounts from the list automatically.")
        t.pack(side="left", padx=dpi_5)
        self.save_objects_to_file_var = ttk.BooleanVar(value=False)
        t = ttk.Checkbutton(
            frame_account_bnts, text="Preserve state on shutdown", onvalue=True, offvalue=False,
            variable=self.save_objects_to_file_var,
        )
        ToolTip(
            t,
            "When stopping DAF, save all account state (and guild, message, ...) to a file.\n"
            "When starting DAF, load everything from that file."
        )
        t.pack(side="left", padx=dpi_5)

        self.lb_accounts.pack(fill=tk.BOTH, expand=True, side="left")

        # Object tab account tab logging tab
        frame_logging = ttk.Labelframe(self, padding=(dpi_10, dpi_10), text="Logging", bootstyle="primary")
        label_logging_mgr = ttk.Label(frame_logging, text="Selected logger:")
        label_logging_mgr.pack(anchor=tk.N)
        frame_logging.pack(side="left", fill=tk.BOTH, expand=True, pady=dpi_10, padx=dpi_5)

        frame_logger_select = ttk.Frame(frame_logging)
        frame_logger_select.pack(fill=tk.X)
        self.combo_logging_mgr = ComboBoxObjects(frame_logger_select)
        self.bnt_edit_logger = ttk.Button(frame_logger_select, text="Edit", command=self.edit_logger)
        self.combo_logging_mgr.pack(fill=tk.X, side="left", expand=True)
        self.bnt_edit_logger.pack(anchor=tk.N, side="right")

        self.label_tracing = ttk.Label(frame_logging, text="Selected trace level:")
        self.label_tracing.pack(anchor=tk.N)
        frame_tracer_select = ttk.Frame(frame_logging)
        frame_tracer_select.pack(fill=tk.X)
        self.combo_tracing = ComboBoxObjects(frame_tracer_select)
        self.combo_tracing.pack(fill=tk.X, side="left", expand=True)

        self.combo_logging_mgr["values"] = [
            ObjectInfo(daf.LoggerJSON, {"path": str(Path.home().joinpath("daf/History"))}),
            ObjectInfo(daf.LoggerSQL, {"database": str(Path.home().joinpath("daf/messages")), "dialect": "sqlite"}),
            ObjectInfo(daf.LoggerCSV, {"path": str(Path.home().joinpath("daf/History")), "delimiter": ";"}),
        ]
        self.combo_logging_mgr.current(0)

        tracing_values = [en for en in daf.TraceLEVELS]
        self.combo_tracing["values"] = tracing_values
        self.combo_tracing.current(tracing_values.index(daf.TraceLEVELS.NORMAL))

    @property
    def save_to_file(self):
        return self.save_objects_to_file_var.get()
    
    @property
    def auto_load_accounts(self):
        return self.load_at_start_var.get()

    def get_tracing(self) -> daf.TraceLEVELS:
        return self._get_converted(self.combo_tracing, daf.TraceLEVELS)

    def get_logger(self) -> daf.LoggerBASE:
        return self._get_converted(self.combo_logging_mgr, daf.LoggerBASE)

    @gui_except()
    def _get_converted(self, combo: ComboBoxObjects, cls: type):
        value = combo.get()
        conv = convert_to_objects(value)
        if not isinstance(conv, cls):
            raise ValueError(f"Invalid tracing value {value}.")

        return conv

    @gui_except()
    @gui_confirm_action()
    def import_accounts(self):
        "Imports account from live view"
        async def import_accounts_async():
            accs = await get_connection().get_accounts()
            # for acc in accs:
            #     acc.intents = None  # Intents cannot be loaded properly

            values = convert_to_object_info(accs)
            if not len(values):
                raise ValueError("Live view has no elements.")

            self.lb_accounts.clear()
            self.lb_accounts.insert(tk.END, *values)

        tae.async_execute(import_accounts_async(), wait=False, pop_up=True, master=self)

    @gui_except()
    def load_accounts(self, selection: bool = False):
        connection = get_connection()
        accounts = self.lb_accounts.get()
        if selection:
            accounts = [accounts[i] for i in self.lb_accounts.curselection()]

        accounts = convert_to_objects(list(accounts))

        for account in accounts:
            tae.async_execute(
                connection.add_account(account),
                wait=False,
                pop_up=True,
                master=self
            )

    @gui_except()
    def save_schema(self) -> bool:
        filename = tkfile.asksaveasfilename(filetypes=[("JSON", "*.json")])
        if filename == "":
            return False

        json_data = {
            "loggers": {
                "all": convert_to_dict(self.combo_logging_mgr["values"]),
                "selected_index": self.combo_logging_mgr.current(),
            },
            "tracing": self.combo_tracing.current(),
            "accounts": convert_to_dict(self.lb_accounts.get()),
            "connection": {
                "all": convert_to_dict(self.combo_conn.combo["values"]),
                "selected_index": self.combo_conn.combo.current()
            }
        }

        if not filename.endswith(".json"):
            filename += ".json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)

        tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self)
        return True

    @gui_except()
    def load_schema(self):
        filename = tkfile.askopenfilename(filetypes=[("JSON", "*.json")])
        if filename == "":
            return

        with open(filename, "r", encoding="utf-8") as file:
            json_data = json.load(file)

            # Load accounts
            accounts = json_data.get("accounts")
            if accounts is not None:
                accounts = convert_from_dict(accounts)
                self.lb_accounts.clear()
                self.lb_accounts.insert(tk.END, *accounts)

            # Load loggers
            logging_data = json_data.get("loggers")
            if logging_data is not None:
                loggers = [convert_from_dict(x) for x in logging_data["all"]]

                self.combo_logging_mgr["values"] = loggers
                selected_index = logging_data["selected_index"]
                if selected_index >= 0:
                    self.combo_logging_mgr.current(selected_index)

            # Tracing
            tracing_index = json_data.get("tracing")
            if tracing_index is not None and tracing_index >= 0:
                self.combo_tracing.current(json_data["tracing"])

            # Remote client
            connection_data = json_data.get("connection")
            if connection_data is not None:
                clients = [convert_from_dict(x) for x in connection_data["all"]]

                self.combo_conn.combo["values"] = clients
                selected_index = connection_data["selected_index"]
                if selected_index >= 0:
                    self.combo_conn.combo.current(selected_index)

    def save_schema_as_script(self):
        """
        Converts the schema into DAF script
        """
        filename = tkfile.asksaveasfilename(filetypes=[("DAF Python script", "*.py")], )
        if filename == "":
            return

        if not filename.endswith(".py"):
            filename += ".py"

        logger = self.combo_logging_mgr.get()
        tracing = self.combo_tracing.get()
        connection_mgr = self.combo_conn.combo.get()
        logger_is_present = str(logger) != ""
        tracing_is_present = str(tracing) != ""
        remote_is_present = isinstance(connection_mgr, ObjectInfo) and connection_mgr.class_ is RemoteConnectionCLIENT
        run_logger_str = "\n    logger=logger," if logger_is_present else ""
        run_tracing_str = f"\n    debug={tracing}," if tracing_is_present else ""
        run_remote_str = "\n    remote_client=remote_client," if remote_is_present else ""

        accounts: list[ObjectInfo] = self.lb_accounts.get()

        accounts_str, imports = convert_objects_to_script(accounts)
        imports = "\n".join(set(imports))

        if logger_is_present:
            logger_str, logger_imports = convert_objects_to_script(logger)
            logger_imports = "\n".join(set(logger_imports))
        else:
            logger_imports = ""

        if remote_is_present:
            connection_mgr: RemoteConnectionCLIENT = convert_to_objects(connection_mgr)
            kwargs = {"host": "0.0.0.0", "port": connection_mgr.port}
            if connection_mgr.auth is not None:
                kwargs["username"] = connection_mgr.auth.login
                kwargs["password"] = connection_mgr.auth.password

            remote_str, remote_imports = convert_objects_to_script(ObjectInfo(daf.RemoteAccessCLIENT, kwargs))
            remote_imports = "\n".join(set(remote_imports))
        else:
            remote_str, remote_imports = "", ""

        _ret = f'''
"""
Automatically generated file for Discord Advertisement Framework {daf.VERSION}.
This can be run eg. 24/7 on a server without graphical interface.

The file has the required classes and functions imported, then the logger is defined and the
accounts list is defined.

At the bottom of the file the framework is then started with the run function.
"""

# Import the necessary items
{logger_imports}
{remote_imports}
{imports}
{f"from {tracing.__module__} import {tracing.__class__.__name__}" if tracing_is_present else ""}
import daf

# Define the logger
{f"logger = {logger_str}" if logger_is_present else ""}

# Define remote control context
{f"remote_client = {remote_str}" if remote_is_present else ""}

# Defined accounts
accounts = {accounts_str}

# Run the framework (blocking)
daf.run(
    accounts=accounts,{run_logger_str}{run_tracing_str}{run_remote_str}
    save_to_file={self.save_objects_to_file_var.get()}
)
'''
        with open(filename, "w", encoding="utf-8") as file:
            file.write(_ret)

        tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self)

    def edit_logger(self):
        selection = self.combo_logging_mgr.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo_logging_mgr.get()
            self.edit_mgr.open_object_edit_window(object_.class_, self.combo_logging_mgr, old_data=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def edit_accounts(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            object_: ObjectInfo = self.lb_accounts.get()[selection[0]]
            self.edit_mgr.open_object_edit_window(daf.ACCOUNT, self.lb_accounts, old_data=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")
