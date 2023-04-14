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
    from .convert import *
except ImportError:
    from widgets import *
    from convert import *


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


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = ttk.Window(themename="cosmo")
        # path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        # photo = tk.PhotoImage(file=path)
        # win_main.iconphoto(True, photo)

        self.win_main = win_main
        screen_res = int(win_main.winfo_screenwidth() / 1.25), int(win_main.winfo_screenheight() / 1.5)
        win_main.wm_title(f"Discord Advert Framework {daf.VERSION}")
        win_main.wm_minsize(*screen_res)
        win_main.protocol("WM_DELETE_WINDOW", self.close_window)

        # Console initialization
        self.win_debug = None

        # Toolbar
        self.frame_toolbar = ttk.Frame(self.win_main)
        self.frame_toolbar.pack(fill=tk.X, side="top", padx=5, pady=5)
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

        # Output tab
        self.init_output_tab()

        # Analytics
        self.init_analytics_tab()

        # Credits tab
        self.init_credits_tab()

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # Tasks
        self._async_queue = asyncio.Queue()

        # On close configuration
        self.win_main.protocol("WM_DELETE_WINDOW", self.close_window)

    def init_schema_tab(self):
        self.objects_edit_window = None

        tab_schema = ttk.Frame(self.tabman_mf, padding=(10, 10))
        self.tabman_mf.add(tab_schema, text="Schema definition")

        # Object tab file menu
        bnt_file_menu = ttk.Menubutton(tab_schema, text="Load/Save/Generate")
        menubar_file = ttk.Menu(bnt_file_menu)
        menubar_file.add_command(label="Save schema", command=self.save_schema)
        menubar_file.add_command(label="Load schema", command=self.load_schema)
        menubar_file.add_command(label="Generate script", command=self.generate_daf_script)
        bnt_file_menu.configure(menu=menubar_file)
        bnt_file_menu.pack(anchor=tk.W)

        # Object tab account tab
        frame_tab_account = ttk.Labelframe(tab_schema, text="Accounts", padding=(10, 10), bootstyle="primary")
        frame_tab_account.pack(side="left", fill=tk.BOTH, expand=True, pady=10, padx=5)

        frame_account_bnts = ttk.Frame(frame_tab_account, padding=(0, 10))
        frame_account_bnts.pack(fill=tk.X)
        self.bnt_add_object = ttk.Button(
            frame_account_bnts,
            text="Add ACCOUNT",
            command=lambda: self.open_object_edit_window(daf.ACCOUNT, self.lb_accounts)
        )
        self.bnt_edit_object = ttk.Button(frame_account_bnts, text="Edit", command=self.edit_accounts)
        self.bnt_remove_object = ttk.Button(frame_account_bnts, text="Remove", command=self.list_del_account)
        self.bnt_add_object.pack(side="left")
        self.bnt_edit_object.pack(side="left")
        self.bnt_remove_object.pack(side="left")

        self.lb_accounts = ListBoxScrolled(frame_tab_account, background="#000")
        self.lb_accounts.pack(fill=tk.BOTH, expand=True)

        # Object tab account tab logging tab
        frame_logging = ttk.Labelframe(tab_schema, padding=(10, 10), text="Logging", bootstyle="primary")
        label_logging_mgr = ttk.Label(frame_logging, text="Selected logger:")
        label_logging_mgr.pack(anchor=tk.N)
        frame_logging.pack(side="left", fill=tk.BOTH, expand=True, pady=10, padx=5)

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
        logo_img = Image.open(f"{os.path.dirname(__file__)}/img/logo.png")
        logo_img = logo_img.resize(
            (self.win_main.winfo_screenwidth() // 8, self.win_main.winfo_screenwidth() // 8),
            resample=0
        )
        logo = ImageTk.PhotoImage(logo_img)
        self.tab_info = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_info, text="About")
        info_bnts_frame = ttk.Frame(self.tab_info)
        info_bnts_frame.pack(pady=30)
        ttk.Button(info_bnts_frame, text="Github", command=lambda: webbrowser.open(GITHUB_URL)).grid(row=0, column=0)
        ttk.Button(
            info_bnts_frame,
            text="Documentation",
            command=lambda: webbrowser.open(DOC_URL)
        ).grid(row=0, column=1)
        ttk.Label(self.tab_info, text="Like the app? Give it a star :) on GitHub (^)").pack(pady=10)
        ttk.Label(self.tab_info, text=CREDITS_TEXT).pack()
        label_logo = ttk.Label(self.tab_info, image=logo)
        label_logo.image = logo
        label_logo.pack()

    def init_analytics_tab(self):
        tab_analytics = ttk.Frame(self.tabman_mf, padding=(10, 10))
        self.tabman_mf.add(tab_analytics, text="Analytics")

        # Message log
        frame_msg_history = ttk.Labelframe(tab_analytics, padding=(10, 10), text="Messages", bootstyle="primary")
        frame_msg_history.pack(fill=tk.BOTH, expand=True)

        frame_combo_messages = ComboEditFrame(
            self.edit_analytics_messages,
            ObjectInfo(daf.logging.LoggerBASE.analytic_get_message_log, {}),
            frame_msg_history
        )
        frame_combo_messages.pack(fill=tk.X)
        self.frame_combo_messages = frame_combo_messages

        frame_msg_history_bnts = ttk.Frame(frame_msg_history)
        frame_msg_history_bnts.pack(fill=tk.X, pady=10)
        ttk.Button(
            frame_msg_history_bnts,
            text="Get logs",
            command=lambda: self._async_queue.put_nowait(self.analytics_load_msg())
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
        frame_num_msg = ttk.Labelframe(tab_analytics, padding=(10, 10), text="Number of messages", bootstyle="primary")
        frame_combo_num_messages = ComboEditFrame(
            self.edit_analytics_num_msg,
            ObjectInfo(daf.logging.LoggerBASE.analytic_get_num_messages, {}),
            frame_num_msg
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
            command=lambda: self._async_queue.put_nowait(self.analytics_load_num_msg())
        ).pack(anchor=tk.W, pady=10)

        frame_num_msg.pack(fill=tk.BOTH, expand=True, pady=5)
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
        messages = convert_to_object_info(messages)
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

    def edit_analytics_messages(self):
        selection = self.frame_combo_messages.combo.current()
        if selection >= 0:
            object_: ObjectInfo = self.frame_combo_messages.combo.get()
            self.open_object_edit_window(
                daf.logging.LoggerBASE.analytic_get_message_log,
                self.frame_combo_messages.combo,
                old=object_,
                check_parameters=False
            )
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def edit_analytics_num_msg(self):
        selection = self.frame_combo_num_messages.combo.current()
        if selection >= 0:
            object_: ObjectInfo = self.frame_combo_num_messages.combo.get()
            self.open_object_edit_window(
                daf.logging.LoggerBASE.analytic_get_num_messages,
                self.frame_combo_num_messages.combo,
                old=object_,
                check_parameters=False
            )
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

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
            self.lb_accounts.delete(*selection)
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

    def save_schema(self) -> bool:
        filename = tkfile.asksaveasfilename(filetypes=[("JSON", "*.json")])
        if filename == "":
            return False

        json_data = {
            "loggers": {
                "all": [convert_to_json(x) for x in self.combo_logging_mgr["values"]],
                "selected_index": self.combo_logging_mgr.current(),
            },
            "tracing": self.combo_tracing.current(),
            "accounts": [convert_to_json(x) for x in self.lb_accounts.get()],
        }

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)

        if not filename.endswith(".json"):
            os.rename(filename, filename + ".json")

        return True

    def load_schema(self):
        try:
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

        except Exception as exc:
            tkdiag.Messagebox.show_error(f"Could not load schema!\n\n{exc}", "Schema load error!")

    def start_daf(self):
        try:
            logger = self.combo_logging_mgr.get()
            if isinstance(logger, str) and logger == "":
                logger = None
            elif logger is not None:
                logger = convert_to_objects(logger)

            tracing = self.combo_tracing.get()
            if isinstance(tracing, str) and tracing == "":
                tracing = None

            self._async_queue.put_nowait(daf.initialize(logger=logger, debug=tracing))
            self._async_queue.put_nowait(
                [daf.add_object(convert_to_objects(account)) for account in self.lb_accounts.get()]
            )
            self.bnt_toolbar_start_daf.configure(state="disabled")
            self.bnt_toolbar_stop_daf.configure(state="enabled")
            self._daf_running = True
        except Exception as exc:
            print(exc)
            tkdiag.Messagebox.show_error(f"Could not start daf due to exception!\n\n{exc}", "Start error!")

    def stop_daf(self):
        self._async_queue.put_nowait(daf.shutdown())
        self._daf_running = False
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")

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

        self._async_queue.put_nowait(_tmp())

    async def _run_coro_gui_errors(self, coro: Awaitable):
        try:
            await coro
        except asyncio.QueueEmpty:
            raise
        except Exception as exc:
            tkdiag.Messagebox.show_error(str(exc), "Coroutine error")

    async def _process(self):
        self.win_main.update()
        try:
            t = self._async_queue.get_nowait()
            if isinstance(t, Iterable):
                for c in t:
                    asyncio.create_task(self._run_coro_gui_errors(c))
            else:
                await self._run_coro_gui_errors(t)
        except asyncio.QueueEmpty:
            pass


def run():
    win_main = Application()

    async def update_task():
        while win_main.opened:
            await win_main._process()
            await asyncio.sleep(WIN_UPDATE_DELAY)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(update_task())


if __name__ == "__main__":
    run()
