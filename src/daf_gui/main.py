"""
Main file of the DAF GUI.
"""
from typing import Iterable, Awaitable
from PIL import Image, ImageTk

import tkinter as tk
import tkinter.filedialog as tkfile
import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap as ttk
import ttkbootstrap.tableview as tktw

import asyncio
import json
import sys
import os
import daf
import webbrowser

try:
    from .widgets import *
except ImportError:
    from widgets import *



WIN_UPDATE_DELAY = 0.005
CREDITS_TEXT = \
"""
Welcome to Discord Advertisement Framework - UI mode.
The UI runs on top of Discord Advertisement Framework and allows easier usage for those who
don't want to write Python code to use the software.

Authors: David Hozic - Student at UL FE.
"""

GITHUB_URL = "https://github.com/davidhozic/discord-advertisement-framework"
DOC_URL = f"https://daf.davidhozic.com/en/v{daf.VERSION}"


def gui_except(fnc: Callable):
    """
    Decorator that catches exceptions and displays them in GUI.
    """
    def wrapper(*args, **kwargs):
        try:
            return fnc(*args, **kwargs)
        except Exception as exc:
            tkdiag.Messagebox.show_error(f"{exc}\n(Exception in {fnc.__name__})")              

    return wrapper


def gui_confirm_action(fnc: Callable):
    """
    Decorator that asks the user to confirm the action before calling the
    targeted function (fnc).
    """
    def wrapper(*args, **kwargs):
        result = tkdiag.Messagebox.show_question("Are you sure?", "Confirm")
        if result == "Yes":
            return fnc(*args, **kwargs)

    return wrapper


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = ttk.Window(themename="cosmo")

        # DPI
        set_dpi(win_main.winfo_fpixels('1i'))
        dpi_5 = dpi_scaled(5)
        # path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        # photo = tk.PhotoImage(file=path)
        # win_main.iconphoto(True, photo)

        self.win_main = win_main
        screen_res = int(win_main.winfo_screenwidth() / 1.25), int(win_main.winfo_screenheight() / 1.5)
        win_main.wm_title(f"Discord Advert Framework {daf.VERSION}")
        win_main.wm_minsize(*screen_res)
        win_main.protocol("WM_DELETE_WINDOW", self.close_window)

        # Toolbar
        self.frame_toolbar = ttk.Frame(self.win_main)
        self.frame_toolbar.pack(fill=tk.X, side="top", padx=dpi_5, pady=dpi_5)
        self.bnt_toolbar_start_daf = ttk.Button(self.frame_toolbar, text="Start", command=self.start_daf)
        self.bnt_toolbar_start_daf.pack(side="left")
        self.bnt_toolbar_stop_daf = ttk.Button(self.frame_toolbar, text="Stop", state="disabled", command=self.stop_daf)
        self.bnt_toolbar_stop_daf.pack(side="left")

        # Main Frame
        self.frame_main = ttk.Frame(self.win_main)
        self.frame_main.pack(expand=True, fill=tk.BOTH, side="bottom")
        tabman_mf = ttk.Notebook(self.frame_main)
        tabman_mf.pack(fill=tk.BOTH, expand=True)
        self.tabman_mf = tabman_mf

        # Objects tab
        self.init_schema_tab()

        # Live inspect tab
        self.init_live_inspect_tab()

        # Output tab
        self.init_output_tab()

        # Analytics
        self.init_analytics_tab()

        # Credits tab
        self.init_credits_tab()

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # On close configuration
        self.win_main.protocol("WM_DELETE_WINDOW", self.close_window)

    def init_schema_tab(self):
        self.objects_edit_window = None
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)

        tab_schema = ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(tab_schema, text="Schema definition")

        # Object tab file menu
        bnt_file_menu = ttk.Menubutton(tab_schema, text="Schema")
        menubar_file = ttk.Menu(bnt_file_menu)
        menubar_file.add_command(label="Save schema", command=self.save_schema)
        menubar_file.add_command(label="Load schema", command=self.load_schema)
        menubar_file.add_command(label="Generate script", command=self.generate_daf_script)
        bnt_file_menu.configure(menu=menubar_file)
        bnt_file_menu.pack(anchor=tk.W)

        # Object tab account tab
        frame_tab_account = ttk.Labelframe(
            tab_schema,
            text="Accounts", padding=(dpi_10, dpi_10), bootstyle="primary")
        frame_tab_account.pack(side="left", fill=tk.BOTH, expand=True, pady=dpi_10, padx=dpi_5)

        @gui_except
        def import_accounts():
            "Imports account from live view"
            values = convert_to_object_info(daf.get_accounts(), save_original=False)
            if not len(values):
                raise ValueError("Live view has no elements.")

            self.lb_accounts.clear()
            self.lb_accounts.insert(tk.END, *values)

        menu_bnt = ttk.Menubutton(
            frame_tab_account,
            text="Object options"
        )
        menu = ttk.Menu(menu_bnt)
        menu.add_command(
            label="New ACCOUNT",
            command=lambda: self.open_object_edit_window(daf.ACCOUNT, self.lb_accounts)
        )
        menu.add_command(label="Edit", command=self.edit_accounts)
        menu.add_command(label="Remove", command=self.list_del_account)
        menu.add_command(
            label="Import from live view", command=import_accounts
        )

        menu_bnt.configure(menu=menu)
        menu_bnt.pack(anchor=tk.W, pady=dpi_5)

        frame_load_to_daf = ttk.Frame(frame_tab_account)
        frame_load_to_daf.pack(fill=tk.X, pady=dpi_5)
        ttk.Button(frame_load_to_daf, text="Load selected to DAF").pack(side="left")
        self.load_at_start_var = ttk.BooleanVar(value=True)

        ttk.Checkbutton(
            frame_load_to_daf, text="Load all at start", onvalue=True, offvalue=False, state="normal",
            variable=self.load_at_start_var
        ).pack(side="left", padx=dpi_5)

        self.lb_accounts = ListBoxScrolled(frame_tab_account)
        self.lb_accounts.pack(fill=tk.BOTH, expand=True, side="left")

        # Object tab account tab logging tab
        frame_logging = ttk.Labelframe(tab_schema, padding=(dpi_10, dpi_10), text="Logging", bootstyle="primary")
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
            ObjectInfo(daf.LoggerJSON, {"path": "History"}),
            ObjectInfo(daf.LoggerSQL, {}),
            ObjectInfo(daf.LoggerCSV, {"path": "History", "delimiter": ";"}),
        ]

        self.combo_tracing["values"] = [en for en in daf.TraceLEVELS]

    def init_live_inspect_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)

        def remove_account():
            selection = list_live_objects.curselection()
            if len(selection):
                @gui_confirm_action
                def _():
                    values = list_live_objects.get()
                    for i in selection:
                        async_execute(
                            daf.remove_object(values[i].real_object),
                            parent_window=self.win_main
                        )

                    async_execute(dummy_task(), lambda x: self.load_live_accounts(), self.win_main)

                _()
            else:
                tkdiag.Messagebox.show_error("Select atlest one item!", "Select errror")

        @gui_except
        def add_account():
            selection = combo_add_object_edit.combo.current()
            if selection >= 0:
                fnc: ObjectInfo = combo_add_object_edit.combo.get()
                mapping = {k: convert_to_objects(v) for k, v in fnc.data.items()}
                async_execute(fnc.class_(**mapping), parent_window=self.win_main)
            else:
                tkdiag.Messagebox.show_error("Combobox does not have valid selection.", "Combo invalid selection")

        def view_live_account():
            selection = list_live_objects.curselection()
            if len(selection) == 1:
                object_: ObjectInfo = list_live_objects.get()[selection[0]]
                self.open_object_edit_window(
                    daf.ACCOUNT,
                    list_live_objects,
                    old=object_
                )
            else:
                tkdiag.Messagebox.show_error("Select one item!", "Empty list!")

        tab_live = ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(tab_live, text="Live view")
        frame_add_account = ttk.Frame(tab_live)
        frame_add_account.pack(fill=tk.X, pady=dpi_10)

        combo_add_object_edit = ComboEditFrame(
            self,
            [ObjectInfo(daf.add_object, {})],
            master=frame_add_account,
            check_parameters=False
        )
        ttk.Button(frame_add_account, text="Execute", command=add_account).pack(side="left")
        combo_add_object_edit.pack(side="left", fill=tk.X, expand=True)

        frame_account_opts = ttk.Frame(tab_live)
        frame_account_opts.pack(fill=tk.X, pady=dpi_5)
        ttk.Button(frame_account_opts, text="Refresh", command=self.load_live_accounts).pack(side="left")
        ttk.Button(frame_account_opts, text="Edit", command=view_live_account).pack(side="left")
        ttk.Button(frame_account_opts, text="Remove", command=remove_account).pack(side="left")

        list_live_objects = ListBoxScrolled(tab_live)
        list_live_objects.pack(fill=tk.BOTH, expand=True)
        self.list_live_objects = list_live_objects

    def init_output_tab(self):
        self.tab_output = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_output, text="Output")
        text_output = ListBoxScrolled(self.tab_output)
        text_output.listbox.unbind("<Control-c>")
        text_output.listbox.unbind("<BackSpace>")
        text_output.listbox.unbind("<Delete>")
        text_output.pack(fill=tk.BOTH, expand=True)

        class STDIOOutput:
            def flush(self_):
                pass

            def write(self_, data: str):
                if data == '\n':
                    return

                for r in daf.tracing.TRACE_COLOR_MAP.values():
                    data = data.replace(r, "")

                text_output.insert(tk.END, data.replace("\033[0m", ""))
                if len(text_output.get()) > 1000:
                    text_output.delete(0, 500)

                text_output.see(tk.END)

        self._oldstdout = sys.stdout
        sys.stdout = STDIOOutput()

    def init_credits_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_30 = dpi_scaled(30)
        logo_img = Image.open(f"{os.path.dirname(__file__)}/img/logo.png")
        logo_img = logo_img.resize(
            (self.win_main.winfo_screenwidth() // 8, self.win_main.winfo_screenwidth() // 8),
            resample=0
        )
        logo = ImageTk.PhotoImage(logo_img)
        self.tab_info = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_info, text="About")
        info_bnts_frame = ttk.Frame(self.tab_info)
        info_bnts_frame.pack(pady=dpi_30)
        ttk.Button(info_bnts_frame, text="Github", command=lambda: webbrowser.open(GITHUB_URL)).grid(row=0, column=0)
        ttk.Button(
            info_bnts_frame,
            text="Documentation",
            command=lambda: webbrowser.open(DOC_URL)
        ).grid(row=0, column=1)
        ttk.Label(self.tab_info, text="Like the app? Give it a star :) on GitHub (^)").pack(pady=dpi_10)
        ttk.Label(self.tab_info, text=CREDITS_TEXT).pack()
        label_logo = ttk.Label(self.tab_info, image=logo)
        label_logo.image = logo
        label_logo.pack()

    def init_analytics_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)
        tab_analytics = ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(tab_analytics, text="Analytics")

        # Message log
        frame_msg_history = ttk.Labelframe(tab_analytics, padding=(dpi_10, dpi_10), text="Messages", bootstyle="primary")
        frame_msg_history.pack(fill=tk.BOTH, expand=True)

        frame_combo_messages = ComboEditFrame(
            self,
            [ObjectInfo(daf.logging.LoggerBASE.analytic_get_message_log, {})],
            frame_msg_history,
            check_parameters=False
        )
        frame_combo_messages.pack(fill=tk.X)
        self.frame_combo_messages = frame_combo_messages

        frame_msg_history_bnts = ttk.Frame(frame_msg_history)
        frame_msg_history_bnts.pack(fill=tk.X, pady=dpi_10)
        ttk.Button(
            frame_msg_history_bnts,
            text="Get logs",
            command=lambda: async_execute(self.analytics_load_msg(), parent_window=self.win_main)
        ).pack(side="left", fill=tk.X)
        ttk.Button(frame_msg_history_bnts, command=self.show_message_log, text="View log").pack(side="left", fill=tk.X)
        ttk.Button(
            frame_msg_history_bnts,
            command=self.export_message_log_json,
            text="Save selected as JSON"
        ).pack(side="left", fill=tk.X)

        lst_messages = ListBoxScrolled(frame_msg_history)
        lst_messages.pack(expand=True, fill=tk.BOTH)

        self.lst_message_log = lst_messages

        # Number of messages
        frame_num_msg = ttk.Labelframe(tab_analytics, padding=(dpi_10, dpi_10), text="Number of messages", bootstyle="primary")
        frame_combo_num_messages = ComboEditFrame(
            self,
            [ObjectInfo(daf.logging.LoggerBASE.analytic_get_num_messages, {})],
            frame_num_msg,
            check_parameters=False
        )

        coldata = [
            {"text": "Date", "stretch": True},
            {"text": "Number of successful", "stretch": True},
            {"text": "Number of failed", "stretch": True},
            {"text": "Guild snowflake", "stretch": True},
            {"text": "Guild name", "stretch": True},
            {"text": "Author snowflake", "stretch": True},
            {"text": "Author name", "stretch": True},
        ]
        tw_num_msg = tktw.Tableview(
            frame_num_msg,
            bootstyle="primary",
            coldata=coldata,
            searchable=True,
            paginated=True,
            autofit=True)
        frame_combo_num_messages.pack(fill=tk.X)

        ttk.Button(
            frame_num_msg,
            text="Calculate",
            command=lambda: async_execute(self.analytics_load_num_msg(), parent_window=self.win_main)
        ).pack(anchor=tk.W, pady=dpi_10)

        frame_num_msg.pack(fill=tk.BOTH, expand=True, pady=dpi_5)
        tw_num_msg.pack(expand=True, fill=tk.BOTH)

        self.tw_num_msg = tw_num_msg
        self.frame_combo_num_messages = frame_combo_num_messages

    @property
    def opened(self) -> bool:
        return self._window_opened

    def open_object_edit_window(self, *args, **kwargs):
        if self.objects_edit_window is None or self.objects_edit_window.closed:
            self.objects_edit_window = ObjectEditWindow()
            self.objects_edit_window.open_object_edit_frame(*args, **kwargs)

    def load_live_accounts(self):
        object_infos = convert_to_object_info(daf.get_accounts(), save_original=True)
        self.list_live_objects.clear()
        self.list_live_objects.insert(tk.END, *object_infos)

    async def analytics_load_msg(self):
        logger = daf.get_logger()
        if not isinstance(logger, daf.LoggerSQL):
            raise ValueError("Analytics only allowed when using LoggerSQL")

        param_object = self.frame_combo_messages.combo.get()
        data = param_object.data.copy()
        for k, v in data.items():
            if isinstance(v, ObjectInfo):
                data[k] = convert_to_objects(v)

        messages = await logger.analytic_get_message_log(
            **data
        )
        messages = convert_to_object_info(messages, cache=True)
        self.lst_message_log.clear()
        self.lst_message_log.insert(tk.END, *messages)

    async def analytics_load_num_msg(self):
        logger = daf.get_logger()
        if not isinstance(logger, daf.LoggerSQL):
            raise ValueError("Analytics only allowed when using LoggerSQL")

        param_object = self.frame_combo_num_messages.combo.get()
        data = param_object.data.copy()
        for k, v in data.items():
            if isinstance(v, ObjectInfo):
                data[k] = convert_to_objects(v)

        count = await logger.analytic_get_num_messages(
            **data
        )

        self.tw_num_msg.delete_rows()
        self.tw_num_msg.insert_rows(0, count)
        self.tw_num_msg.goto_first_page()

    def export_message_log_json(self):
        selection = self.lst_message_log.curselection()
        if len(selection):
            object_: list[ObjectInfo] = [convert_to_json(l) for i, l in enumerate(self.lst_message_log.get()) if i in selection]
            filename = tkfile.asksaveasfilename(filetypes=[("SQL data", "*.json")])
            if filename == "":
                return

            if not filename.endswith(".json"):
                filename += ".json"

            with open(filename, "w", encoding="utf-8") as writer:
                json.dump(object_, writer, indent=4)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def show_message_log(self):
        selection = self.lst_message_log.curselection()
        if len(selection) == 1:
            object_: ObjectInfo = self.lst_message_log.get()[selection[0]]
            self.open_object_edit_window(
                daf.sql.MessageLOG,
                self.lst_message_log,
                old=object_,
                check_parameters=False,
                allow_save=False
            )
        else:
            tkdiag.Messagebox.show_error("Select ONE item!", "Empty list!")

    def edit_logger(self):
        selection = self.combo_logging_mgr.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo_logging_mgr.get()
            self.open_object_edit_window(object_.class_, self.combo_logging_mgr, old=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def edit_accounts(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            object_: ObjectInfo = self.lb_accounts.get()[selection[0]]
            self.open_object_edit_window(daf.ACCOUNT, self.lb_accounts, old=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def list_del_account(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            @gui_confirm_action
            def _():
                self.lb_accounts.delete(*selection)
            _()
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def generate_daf_script(self):
        """
        Converts the schema into DAF script
        """
        filename = tkfile.asksaveasfilename(filetypes=[("DAF Python script", "*.py")], )
        if filename == "":
            return

        logger = self.combo_logging_mgr.get()
        tracing = self.combo_tracing.get()
        logger_is_present = str(logger) != ""
        tracing_is_present = str(tracing) != ""
        run_logger_str = "\n    logger=logger," if logger_is_present else ""
        run_tracing_str = f"\n    debug={tracing}" if tracing_is_present else ""

        accounts: list[ObjectInfo] = self.lb_accounts.get()

        accounts_str, imports, other_str = convert_objects_to_script(accounts)
        imports = "\n".join(set(imports))
        if other_str != "":
            other_str = "\n" + other_str

        if logger_is_present:
            logger_str, logger_imports, _ = convert_objects_to_script(logger)
            logger_imports = "\n".join(set(logger_imports))
        else:
            logger_imports = ""

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
{imports}
{f"from {tracing.__module__} import {tracing.__class__.__name__}" if tracing_is_present else ""}
import daf{other_str}

# Define the logger
{f"logger = {logger_str}" if logger_is_present else ""}

# Defined accounts
accounts = {accounts_str}

# Run the framework (blocking)
daf.run(
    accounts=accounts,{run_logger_str}{run_tracing_str}
)
'''
        with open(filename, "w", encoding="utf-8") as file:
            file.write(_ret)

        if not file.name.endswith(".py"):
            os.rename(file.name, file.name + ".py")

    @gui_except
    def save_schema(self) -> bool:
        filename = tkfile.asksaveasfilename(filetypes=[("JSON", "*.json")])
        if filename == "":
            return False

        json_data = {
            "loggers": {
                "all": convert_to_json(self.combo_logging_mgr["values"]),
                "selected_index": self.combo_logging_mgr.current(),
            },
            "tracing": self.combo_tracing.current(),
            "accounts": convert_to_json(self.lb_accounts.get()),
        }

        if not filename.endswith(".json"):
            filename += ".json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)

        tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self.win_main)

        return True

    @gui_except
    def load_schema(self):
        filename = tkfile.askopenfilename(filetypes=[("JSON", "*.json")])
        if filename == "":
            return

        with open(filename, "r", encoding="utf-8") as file:
            json_data = json.load(file)

            # Load accounts
            accounts = convert_from_json(json_data["accounts"])
            self.lb_accounts.clear()
            self.lb_accounts.listbox.insert(tk.END, *accounts)

            # Load loggers
            loggers = [convert_from_json(x) for x in json_data["loggers"]["all"]]
            self.combo_logging_mgr["values"] = loggers
            selected_index = json_data["loggers"]["selected_index"]
            if selected_index >= 0:
                self.combo_logging_mgr.current(selected_index)

            # Tracing
            tracing_index = json_data["tracing"]
            if tracing_index >= 0:
                self.combo_tracing.current(json_data["tracing"])

    @gui_except
    def start_daf(self):
        logger = self.combo_logging_mgr.get()
        if isinstance(logger, str) and logger == "":
            logger = None
        elif logger is not None:
            logger = convert_to_objects(logger)

        tracing = self.combo_tracing.get()
        if isinstance(tracing, str) and tracing == "":
            tracing = None

        async_execute(daf.initialize(logger=logger, debug=tracing), parent_window=self.win_main)
        if self.load_at_start_var.get():
            self.add_accounts_daf()

        self.bnt_toolbar_start_daf.configure(state="disabled")
        self.bnt_toolbar_stop_daf.configure(state="enabled")
        self._daf_running = True

    def stop_daf(self):
        async_execute(daf.shutdown(), parent_window=self.win_main)
        self._daf_running = False
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")

    @gui_except
    def add_accounts_daf(self):
        accounts = self.lb_accounts.get()
        for account in accounts:
            async_execute(daf.add_object(convert_to_objects(account)), parent_window=self.win_main)

    def close_window(self):
        resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self.win_main)
        if resp is None or resp == "Cancel" or resp == "Yes" and not self.save_schema():
            return

        self._window_opened = False
        if self._daf_running:
            self.stop_daf()

        async def _tmp():
            sys.stdout = self._oldstdout
            self.win_main.destroy()
            self.win_main.quit()

        async_execute(_tmp())

    async def _process(self):
        self.win_main.update()


def run():
    win_main = Application()

    async def update_task():
        while win_main.opened:
            await win_main._process()
            await asyncio.sleep(WIN_UPDATE_DELAY)

    loop = asyncio.new_event_loop()
    async_start(loop)
    loop.run_until_complete(update_task())
    loop.run_until_complete(async_stop())


if __name__ == "__main__":
    run()
