"""
Main file of the DAF GUI.
"""
from importlib.util import find_spec
from pathlib import Path

from .edit_window_manager import *
from .tabs import *

import tk_async_execute as tae
import subprocess
import json
import sys


# Automatically install GUI requirements if GUI is requested to avoid making it an optional dependency
# One other way would be to create a completely different package on pypi for the core daf, but that is a lot of
# work to be done. It is better to auto install.
to_install = [
    ("ttkbootstrap", "==1.10.1"),
]

version_path = Path.home().joinpath("./gui_versions.json")
if not version_path.exists():
    version_path.touch()

with open(version_path, "r") as file:
    try:
        version_data = json.load(file)
    except json.JSONDecodeError as exc:
        version_data = {}

for package, version in to_install:
    installed_version = version_data.get(package, "0")
    if find_spec(package) is None or installed_version != version:
        print(f"Auto installing {package}{version}")
        subprocess.check_call(
            [
                sys.executable.replace("pythonw", "python"),
                "-m", "pip", "install", "-U",
                package + version
            ]
        )
        version_data[package] = version

with open(version_path, "w") as file:
    json.dump(version_data, file)


import ttkbootstrap as ttk

from tkclasswiz.convert import *
from tkclasswiz.dpi import *
from tkclasswiz.storage import *
from tkclasswiz.utilities import *
from .connector import *

from PIL import Image, ImageTk
from ttkbootstrap.toast import ToastNotification
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap.style as tkstyle

import webbrowser
import sys
import os
import daf


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


class GLOBAL:
    app: "Application" = None


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = ttk.Window(themename="cosmo")
        self.win_main = win_main
        
        # Object edit
        self.edit_mgr = EditWindowManager()

        # DPI
        set_dpi(win_main.winfo_fpixels('1i'))
        dpi_5 = dpi_scaled(5)
        dpi_10 = dpi_scaled(10)

        path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        photo = ImageTk.PhotoImage(file=path)
        win_main.iconphoto(0, photo)

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

        # Main Frame
        self.frame_main = ttk.Frame(self.win_main)
        self.frame_main.pack(expand=True, fill=tk.BOTH, side="bottom")
        tabman_mf = ttk.Notebook(self.frame_main)
        tabman_mf.pack(fill=tk.BOTH, expand=True)
        self.tabman_mf = tabman_mf

        # Connection
        self.combo_connection_edit = ComboEditFrame(
            self.edit_mgr.open_object_edit_window,
            [
                ObjectInfo(LocalConnectionCLIENT, {}),
                ObjectInfo(RemoteConnectionCLIENT, {"host": "http://"}),
            ],
            self.frame_toolbar,
        )
        self.combo_connection_edit.pack(side="left", fill=ttk.X, expand=True)

        # Toast notifications
        self.init_event_listeners()

        # Optional dependencies tab
        self.tabman_mf.add(OptionalTab(padding=(dpi_10, dpi_10)), text="Optional modules")

        # Objects tab
        self.tab_schema = SchemaTab(self.edit_mgr, self.combo_connection_edit, master=tabman_mf, padding=(dpi_10, dpi_10))
        tabman_mf.add(self.tab_schema, text="Schema definition")

        # Live inspect tab
        self.tabman_mf.add(LiveTab(self.edit_mgr, padding=(dpi_10, dpi_10)), text="Live view")

        # Output tab
        self.init_output_tab()

        # Analytics
        self.tabman_mf.add(AnalyticsTab(self.edit_mgr, padding=(dpi_10, dpi_10)), text="Analytics")

        # Credits tab
        self.init_credits_tab()

        # GUI menu
        self.init_menu()

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

    def init_menu(self):
        "Initializes GUI toolbar menu"
        menu = ttk.Menu(self.win_main)
        theme_menu = ttk.Menu(menu)
        menu.add_cascade(label="Theme", menu=theme_menu)

        style = tkstyle.Style()
        def use_theme(theme: str):
            return lambda: style.theme_use(theme)

        for theme in style.theme_names():
            theme_menu.add_radiobutton(label=theme, command=use_theme(theme))

        self.win_main.config(menu=menu)

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

    @gui_except()
    def load_live_accounts(self):
        async def load_accounts():
            object_infos = convert_to_object_info(await self.connection.get_accounts(), save_original=True)
            self.list_live_objects.clear()
            self.list_live_objects.insert(tk.END, *object_infos)

        tae.async_execute(load_accounts(), wait=False, pop_up=True, master=self.win_main)

    def start_daf(self):
        # Initialize connection
        connection: AbstractConnectionCLIENT = convert_to_objects(self.combo_connection_edit.combo.get())
        self.connection = connection
        kwargs = {}

        kwargs["logger"] = self.tab_schema.get_logger()
        kwargs["debug"] = self.tab_schema.get_tracing()

        window = tae.async_execute(
            connection.initialize(**kwargs, save_to_file=self.tab_schema.save_to_file),
            wait=True,
            pop_up=True,
            show_exceptions=False,
            master=self.win_main
        )
        exc = window.future.exception()
        if exc is not None:
            raise exc

        self._daf_running = True
        if self.tab_schema.auto_load_accounts:
            self.tab_schema.load_accounts()

        self.bnt_toolbar_start_daf.configure(state="disabled")
        self.bnt_toolbar_stop_daf.configure(state="enabled")

    def stop_daf(self):
        self._daf_running = False
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")
        tae.async_execute(self.connection.shutdown(), wait=False, pop_up=True, master=self.win_main)

    def close_window(self):
        resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self.win_main)
        if resp is None or resp == "Cancel" or resp == "Yes" and not self.tab_schema.save_schema():
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
