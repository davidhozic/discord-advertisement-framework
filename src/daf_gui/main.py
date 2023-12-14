"""
Main file of the DAF GUI.
"""
from importlib.util import find_spec
from pathlib import Path
from typing import List

from daf.misc import instance_track as it

import subprocess
import sys

import tk_async_execute as tae


installed = find_spec("ttkbootstrap") is not None


# Automatically install GUI requirements if GUI is requested to avoid making it an optional dependency
# One other way would be to create a completely different package on pypi for the core daf, but that is a lot of
# work to be done. It is better to auto install.
TTKBOOSTRAP_VERSION = "1.10.1"

if not installed:
    print("Auto installing requirements: ttkbootstrap")
    subprocess.check_call([sys.executable.replace("pythonw", "python"), "-m", "pip", "install", f"ttkbootstrap=={TTKBOOSTRAP_VERSION}"])

import ttkbootstrap as ttk

from tkclasswiz.convert import *
from tkclasswiz.dpi import *
from tkclasswiz.object_frame.window import ObjectEditWindow
from tkclasswiz.storage import *
from tkclasswiz.utilities import *
from .connector import *

from PIL import Image, ImageTk
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.toast import ToastNotification
import tkinter as tk
import tkinter.filedialog as tkfile
import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap.tableview as tktw

import json
import sys
import os
import daf
import webbrowser
import warnings


WIN_UPDATE_DELAY = 0.005
CREDITS_TEXT = \
"""
Welcome to Discord Advertisement Framework - UI mode.
The UI runs on top of Discord Advertisement Framework and allows easier usage for those who
don't want to write Python code to use the software.

This is written as part of my bachelor thesis as a degree finishing project
"Framework for advertising NFT on social network Discord".
"""

GITHUB_URL = "https://github.com/davidhozic/discord-advertisement-framework"
DOC_URL = f"https://daf.davidhozic.com/en/v{'.'.join(daf.VERSION.split('.')[:2])}.x/"
DISCORD_URL = "https://discord.gg/DEnvahb2Sw"

OPTIONAL_MODULES = [
    # Label, optional name, installed var
    ("SQL logging", "sql", daf.logging.sql.SQL_INSTALLED),
    ("Voice messages", "voice", daf.dtypes.GLOBALS.voice_installed),
    ("Web features (Chrome)", "web", daf.web.GLOBALS.selenium_installed),
]


class GLOBAL:
    app: "Application" = None


def gui_daf_assert_running():
    if not GLOBAL.app._daf_running:
        raise ConnectionError("Start the framework first (START button)")


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = ttk.Window(themename="cosmo")

        # DPI
        set_dpi(win_main.winfo_fpixels('1i'))
        dpi_5 = dpi_scaled(5)
        path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        photo = ImageTk.PhotoImage(file=path)
        win_main.iconphoto(0, photo)

        self.win_main = win_main
        screen_res = int(win_main.winfo_screenwidth() / 1.25), int(win_main.winfo_screenheight() / 1.375)
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

        # Connection
        self.combo_connection_edit = ComboEditFrame(
            self.open_object_edit_window,
            [
                ObjectInfo(LocalConnectionCLIENT, {}),
                ObjectInfo(RemoteConnectionCLIENT, {"host": "http://"}),
            ],
            self.frame_toolbar,
        )
        self.combo_connection_edit.pack(side="left", fill=ttk.X, expand=True)

        # Main Frame
        self.frame_main = ttk.Frame(self.win_main)
        self.frame_main.pack(expand=True, fill=tk.BOTH, side="bottom")
        tabman_mf = ttk.Notebook(self.frame_main)
        tabman_mf.pack(fill=tk.BOTH, expand=True)
        self.tabman_mf = tabman_mf


        # Toast notifications
        self.init_event_listeners()

        # Optional dependencies tab
        self.init_optional_dep_tab()

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

        # Window config
        self.win_main.protocol("WM_DELETE_WINDOW", self.close_window)
        self.tabman_mf.select(1)

        # Connection
        self.connection: AbstractConnectionCLIENT = None


        if sys.version_info.minor == 12 and sys.version_info.major == 3:
            tkdiag.Messagebox.show_warning(
                "DAF's support on Python 3.12 is limited. Web browser features and"
                " SQL logging are not supported in Python 3.12. Please install Python 3.11 instead.\n"
                "Additional GUI can be unstable on Python 3.12",
                "Compatibility warning!"
            )

    def init_event_listeners(self):
        "Initializes event listeners."
        bootstyle_map = {
            daf.TraceLEVELS.DEBUG: ttk.LIGHT,
            daf.TraceLEVELS.NORMAL: ttk.PRIMARY,
            daf.TraceLEVELS.WARNING: ttk.WARNING,
            daf.TraceLEVELS.ERROR: ttk.DANGER,
            daf.TraceLEVELS.DEPRECATED: ttk.DARK
        }
        dpi_78, dpi_600 = dpi_scaled(78), dpi_scaled(600)

        def trace_listener(level: daf.TraceLEVELS, message: str):
            last_toast: ToastNotification = ToastNotification.last_toast
            if last_toast is not None and last_toast.toplevel.winfo_exists():
                next_position = max((last_toast.position[1] + dpi_78) % dpi_600, dpi_78)
            else:
                next_position = dpi_78

            toast = ToastNotification(
                level.name,
                message,
                bootstyle=bootstyle_map[level],
                icon="",
                duration=5000,
                position=(10, next_position, "se"),
                topmost=True
            )
            ToastNotification.last_toast = toast
            toast.show_toast()

        ToastNotification.last_toast = None
        evt = daf.get_global_event_ctrl()
        evt.add_listener(
            daf.EventID.g_trace, lambda level, message: self.win_main.after_idle(trace_listener, level, message)
        )
        evt.add_listener(
            daf.EventID._ws_disconnect, lambda: self.win_main.after_idle(self.stop_daf)
        )

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

        # Accounts list. Defined here since it's needed below
        self.lb_accounts = ListBoxScrolled(frame_tab_account)

        @gui_except()
        @gui_confirm_action()
        def import_accounts():
            "Imports account from live view"
            async def import_accounts_async():
                accs = await self.connection.get_accounts()
                # for acc in accs:
                #     acc.intents = None  # Intents cannot be loaded properly

                values = convert_to_object_info(accs)
                if not len(values):
                    raise ValueError("Live view has no elements.")

                self.lb_accounts.clear()
                self.lb_accounts.insert(tk.END, *values)

            gui_daf_assert_running()
            tae.async_execute(import_accounts_async(), wait=False, pop_up=True, master=self.win_main)

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
        menu.add_command(label="Remove", command=self.lb_accounts.delete_selected)
        menu_bnt.configure(menu=menu)
        menu_bnt.pack(anchor=tk.W)

        frame_account_bnts = ttk.Frame(frame_tab_account)
        frame_account_bnts.pack(fill=tk.X, pady=dpi_5)
        ttk.Button(
            frame_account_bnts, text="Import from DAF (live)", command=import_accounts
        ).pack(side="left")
        t = ttk.Button(
            frame_account_bnts, text="Load selection to DAF (live)", command=lambda: self.add_accounts_daf(True)
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
            ObjectInfo(daf.LoggerJSON, {"path": str(Path.home().joinpath("daf/History"))}),
            ObjectInfo(daf.LoggerSQL, {"database": str(Path.home().joinpath("daf/messages")), "dialect": "sqlite"}),
            ObjectInfo(daf.LoggerCSV, {"path": str(Path.home().joinpath("daf/History")), "delimiter": ";"}),
        ]
        self.combo_logging_mgr.current(0)

        tracing_values = [en for en in daf.TraceLEVELS]
        self.combo_tracing["values"] = tracing_values
        self.combo_tracing.current(tracing_values.index(daf.TraceLEVELS.NORMAL))

    def init_live_inspect_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)

        @gui_confirm_action()
        def remove_account():
            selection = list_live_objects.curselection()
            if len(selection):
                values = list_live_objects.get()
                for i in selection:
                    tae.async_execute(
                        self.connection.remove_account(values[i].real_object),
                        wait=False,
                        pop_up=True,
                        callback=self.load_live_accounts,
                        master=self.win_main
                    )
            else:
                tkdiag.Messagebox.show_error("Select atlest one item!", "Select errror")

        @gui_except()
        def add_account():
            gui_daf_assert_running()
            selection = combo_add_object_edit.combo.current()
            if selection >= 0:
                fnc: ObjectInfo = combo_add_object_edit.combo.get()
                fnc_data = convert_to_objects(fnc.data)
                tae.async_execute(self.connection.add_account(**fnc_data), wait=False, pop_up=True, master=self.win_main)
            else:
                tkdiag.Messagebox.show_error("Combobox does not have valid selection.", "Combo invalid selection")

        def view_live_account():
            selection = list_live_objects.curselection()
            if len(selection) == 1:
                object_: ObjectInfo = list_live_objects.get()[selection[0]]
                self.open_object_edit_window(
                    daf.ACCOUNT,
                    list_live_objects,
                    old_data=object_
                )
            else:
                tkdiag.Messagebox.show_error("Select one item!", "Empty list!")

        tab_live = ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(tab_live, text="Live view")
        frame_add_account = ttk.Frame(tab_live)
        frame_add_account.pack(fill=tk.X, pady=dpi_10)

        combo_add_object_edit = ComboEditFrame(
            self.open_object_edit_window,
            [ObjectInfo(daf.add_object, {})],
            master=frame_add_account,
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
        # The default bind is removal from list and not from actual daf.
        list_live_objects.listbox.unbind_all("<BackSpace>")
        list_live_objects.listbox.unbind_all("<Delete>")
        list_live_objects.listbox.bind("<BackSpace>", lambda e: remove_account())
        list_live_objects.listbox.bind("<Delete>", lambda e: remove_account())

    def init_output_tab(self):
        self.tab_output = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_output, text="Output")
        text_output = ListBoxScrolled(self.tab_output)
        text_output.unbind("<Control-c>")
        text_output.unbind("<BackSpace>")
        text_output.unbind("<Delete>")
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
            (dpi_scaled(400), dpi_scaled(400)),
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
        ttk.Button(
            info_bnts_frame,
            text="My Discord server",
            command=lambda: webbrowser.open(DISCORD_URL)
        ).grid(row=0, column=2)
        ttk.Label(self.tab_info, text="Like the app? Give it a star :) on GitHub (^)").pack(pady=dpi_10)
        ttk.Label(self.tab_info, text=CREDITS_TEXT).pack()
        label_logo = ttk.Label(self.tab_info, image=logo)
        label_logo.image = logo
        label_logo.pack()

    def init_analytics_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)
        tab_analytics = ttk.Notebook(self.tabman_mf, padding=(dpi_5, dpi_5))  # ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(tab_analytics, text="Analytics")

        def create_analytic_frame(
            getter_history: str,
            getter_counts: str,
            counts_coldata: dict,
            tab_name: str
        ):
            """
            Creates a logging tab.

            Parameters
            -------------
            getter_history: str
                The name of the LoggerBASE method that is used to retrieve actual logs.
            getter_counts: str
                The name of the LoggerBASE method that is used to retrieve counts.
            counts_coldata: dict
                Column data for TableView used for counts.
            tab_name: str
                The title to write inside the tab button.
            """
            async def analytics_load_history():
                gui_daf_assert_running()
                logger = await self.connection.get_logger()

                param_object = combo_history.combo.get()
                param_object_params = convert_to_objects(param_object.data)
                items = await self.connection.execute_method(
                    it.ObjectReference(it.get_object_id(logger)), getter_history, **param_object_params
                )
                items = convert_to_object_info(items)
                lst_history.clear()
                lst_history.insert(tk.END, *items)

            def show_log(listbox: ListBoxScrolled):
                selection = listbox.curselection()
                if len(selection) == 1:
                    object_: ObjectInfo = listbox.get()[selection[0]]
                    self.open_object_edit_window(
                        object_.class_,
                        listbox,
                        old_data=object_,
                        check_parameters=False,
                        allow_save=False
                    )
                else:
                    tkdiag.Messagebox.show_error("Select ONE item!", "Empty list!")

            async def delete_logs_async(primary_keys: List[int]):
                logger = await self.connection.get_logger()
                await self.connection.execute_method(
                    it.ObjectReference(it.get_object_id(logger)),
                    "delete_logs",
                    primary_keys=primary_keys  # TODO: update on server
                )

            @gui_confirm_action()
            def delete_logs(listbox: ListBoxScrolled):
                selection = listbox.curselection()
                if len(selection):
                    all_ = listbox.get()
                    tae.async_execute(
                        delete_logs_async([all_[i].data["id"] for i in selection]),
                        wait=False,
                        pop_up=True,
                        master=self.win_main
                    )
                else:
                    tkdiag.Messagebox.show_error("Select atlest one item!", "Selection error.")

            frame_message = ttk.Frame(tab_analytics, padding=(dpi_5, dpi_5))
            tab_analytics.add(frame_message, text=tab_name)
            frame_msg_history = ttk.Labelframe(frame_message, padding=(dpi_10, dpi_10), text="Logs", bootstyle="primary")
            frame_msg_history.pack(fill=tk.BOTH, expand=True)

            combo_history = ComboEditFrame(
                self.open_object_edit_window,
                [ObjectInfo(getattr(daf.logging.LoggerBASE, getter_history), {})],
                frame_msg_history,
            )
            combo_history.pack(fill=tk.X)

            frame_msg_history_bnts = ttk.Frame(frame_msg_history)
            frame_msg_history_bnts.pack(fill=tk.X, pady=dpi_10)
            ttk.Button(
                frame_msg_history_bnts,
                text="Get logs",
                command=lambda: tae.async_execute(analytics_load_history(), wait=False, pop_up=True, master=self.win_main)
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
                gui_daf_assert_running()
                logger = await self.connection.get_logger()
                param_object = combo_count.combo.get()
                parameters = convert_to_objects(param_object.data)
                count = await self.connection.execute_method(it.ObjectReference(it.get_object_id(logger)), getter_counts, **parameters)

                tw_num.delete_rows()
                tw_num.insert_rows(0, count)
                tw_num.goto_first_page()

            frame_num = ttk.Labelframe(frame_message, padding=(dpi_10, dpi_10), text="Counts", bootstyle="primary")
            combo_count = ComboEditFrame(
                self.open_object_edit_window,
                [ObjectInfo(getattr(daf.logging.LoggerBASE, getter_counts), {})],
                frame_num,
            )
            combo_count.pack(fill=tk.X)
            tw_num = tktw.Tableview(
                frame_num,
                bootstyle="primary",
                coldata=counts_coldata,
                searchable=True,
                paginated=True,
                autofit=True)

            ttk.Button(
                frame_num,
                text="Calculate",
                command=lambda: tae.async_execute(analytics_load_num(), wait=False, pop_up=True, master=self.win_main)
            ).pack(anchor=tk.W, pady=dpi_10)

            frame_num.pack(fill=tk.BOTH, expand=True, pady=dpi_5)
            tw_num.pack(expand=True, fill=tk.BOTH)

        # Message tab
        create_analytic_frame(
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
            "Message tracking"
        )

        # Invite tab
        create_analytic_frame(
            "analytic_get_invite_log",
            "analytic_get_num_invites",
            [
                {"text": "Date", "stretch": True},
                {"text": "Count", "stretch": True},
                {"text": "Guild snowflake", "stretch": True},
                {"text": "Guild name", "stretch": True},
                {"text": "Invite ID", "stretch": True},
            ],
            "Invite tracking"
        )

    def init_optional_dep_tab(self):
        dpi_10 = dpi_scaled(10)
        dpi_5 = dpi_scaled(5)
        frame_optionals = ttk.Frame(self.tabman_mf, padding=(dpi_10, dpi_10))
        self.tabman_mf.add(frame_optionals, text="Optional modules")
        ttk.Label(
            frame_optionals,
            text=
            "This section allows you to install optional packages available inside DAF\n"
            "Be aware that loading may be slower when installing these."
        ).pack(anchor=tk.NW)
        frame_optionals_packages = ttk.Frame(frame_optionals)
        frame_optionals_packages.pack(fill=tk.BOTH, expand=True)

        def install_deps(optional: str, gauge: ttk.Floodgauge, bnt: ttk.Button):
            @gui_except()
            def _installer():
                subprocess.check_call([
                    sys.executable.replace("pythonw", "python"), "-m", "pip", "install",
                    f"discord-advert-framework[{optional}]=={daf.VERSION}"
                ])
                tkdiag.Messagebox.show_info("To apply the changes, restart the program!")

            return _installer

        for row, (title, optional_name, installed_flag) in enumerate(OPTIONAL_MODULES):
            ttk.Label(frame_optionals_packages, text=title).grid(row=row, column=0)
            gauge = ttk.Floodgauge(
                frame_optionals_packages, bootstyle=ttk.SUCCESS if installed_flag else ttk.DANGER, value=0
            )
            gauge.grid(pady=dpi_5, row=row, column=1)
            if not installed_flag:
                gauge.start()
                bnt_install = ttk.Button(frame_optionals_packages, text="Install")
                bnt_install.configure(command=install_deps(optional_name, gauge, bnt_install))
                bnt_install.grid(row=row, column=1)

    def open_object_edit_window(self, *args, **kwargs):
        if self.objects_edit_window is None or self.objects_edit_window.closed:
            self.objects_edit_window = ObjectEditWindow()
            self.objects_edit_window.open_object_edit_frame(*args, **kwargs)
        else:
            tkdiag.Messagebox.show_error("Object edit window is already open, close it first.", "Already open")
            self.objects_edit_window.focus()

    @gui_except()
    def load_live_accounts(self):
        async def load_accounts():
            gui_daf_assert_running()
            object_infos = convert_to_object_info(await self.connection.get_accounts(), save_original=True)
            self.list_live_objects.clear()
            self.list_live_objects.insert(tk.END, *object_infos)

        tae.async_execute(load_accounts(), wait=False, pop_up=True, master=self.win_main)

    def edit_logger(self):
        selection = self.combo_logging_mgr.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo_logging_mgr.get()
            self.open_object_edit_window(object_.class_, self.combo_logging_mgr, old_data=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def edit_accounts(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            object_: ObjectInfo = self.lb_accounts.get()[selection[0]]
            self.open_object_edit_window(daf.ACCOUNT, self.lb_accounts, old_data=object_)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")

    def generate_daf_script(self):
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
        connection_mgr = self.combo_connection_edit.combo.get()
        logger_is_present = str(logger) != ""
        tracing_is_present = str(tracing) != ""
        remote_is_present = isinstance(connection_mgr, ObjectInfo) and connection_mgr.class_ is RemoteConnectionCLIENT
        run_logger_str = "\n    logger=logger," if logger_is_present else ""
        run_tracing_str = f"\n    debug={tracing}," if tracing_is_present else ""
        run_remote_str = "\n    remote_client=remote_client," if remote_is_present else ""

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

        if remote_is_present:
            connection_mgr: RemoteConnectionCLIENT = convert_to_objects(connection_mgr)
            kwargs = {"host": "0.0.0.0", "port": connection_mgr.port}
            if connection_mgr.auth is not None:
                kwargs["username"] = connection_mgr.auth.login
                kwargs["password"] = connection_mgr.auth.password

            remote_str, remote_imports, _ = convert_objects_to_script(ObjectInfo(daf.RemoteAccessCLIENT, kwargs))
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
import daf{other_str}

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

        tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self.win_main)

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
                "all": convert_to_dict(self.combo_connection_edit.combo["values"]),
                "selected_index": self.combo_connection_edit.combo.current()
            }
        }

        if not filename.endswith(".json"):
            filename += ".json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)

        tkdiag.Messagebox.show_info(f"Saved to {filename}", "Finished", self.win_main)

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

                self.combo_connection_edit.combo["values"] = clients
                selected_index = connection_data["selected_index"]
                if selected_index >= 0:
                    self.combo_connection_edit.combo.current(selected_index)

    # @gui_except()
    def start_daf(self):
        # Initialize connection
        connection = convert_to_objects(self.combo_connection_edit.combo.get())
        self.connection = connection
        kwargs = {}

        logger = self.combo_logging_mgr.get()
        if logger is not None and not isinstance(logger, str):
            kwargs["logger"] = convert_to_objects(logger)

        tracing = self.combo_tracing.get()
        if not isinstance(tracing, str):
            kwargs["debug"] = tracing

        window = tae.async_execute(
            connection.initialize(**kwargs, save_to_file=self.save_objects_to_file_var.get()),
            wait=True,
            pop_up=True,
            show_exceptions=False,
            master=self.win_main
        )
        exc = window.future.exception()
        if exc is not None:
            raise exc

        self._daf_running = True
        if self.load_at_start_var.get():
            self.add_accounts_daf()

        self.bnt_toolbar_start_daf.configure(state="disabled")
        self.bnt_toolbar_stop_daf.configure(state="enabled")

    def stop_daf(self):
        self._daf_running = False
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")
        tae.async_execute(self.connection.shutdown(), wait=False, pop_up=True, master=self.win_main)

    @gui_except()
    def add_accounts_daf(self, selection: bool = False):
        gui_daf_assert_running()
        accounts = self.lb_accounts.get()
        if selection:
            indexes = self.lb_accounts.curselection()
            if not len(indexes):
                raise ValueError("Select at least one item.")

            indexes = set(indexes)
            accounts = [a for i, a in enumerate(accounts) if i in indexes]

        for account in accounts:
            tae.async_execute(
                self.connection.add_account(convert_to_objects(account)),
                wait=False,
                pop_up=True,
                master=self.win_main
            )

    def close_window(self):
        resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self.win_main)
        if resp is None or resp == "Cancel" or resp == "Yes" and not self.save_schema():
            return

        if self._daf_running:
            tae.async_execute(self.connection.shutdown(), pop_up=True)

        sys.stdout = self._oldstdout
        self.win_main.quit()

    def until_closed(self):
        "Runs until closed"
        self.win_main.mainloop()


def run():
    app = Application()
    GLOBAL.app = app
    tae.start()
    app.until_closed()
    tae.stop()
