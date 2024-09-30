"""
Main file of the DAF GUI.
"""
import tk_async_execute as tae
import ttkbootstrap as ttk

from ttkbootstrap.toast import ToastNotification
from tkclasswiz.utilities import *
from tkclasswiz.storage import *
from tkclasswiz.convert import *
from tkclasswiz.dpi import *
from PIL import ImageTk

from .edit_window_manager import *
from .connector import *
from .tabs import *

import ttkbootstrap.dialogs.dialogs as tkdiag
import ttkbootstrap.style as tkstyle
import tkinter as tk

import os
import daf


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
        self.tabman_mf.add(DebugTab(), text="Output")

        # Analytics
        self.tabman_mf.add(AnalyticsTab(self.edit_mgr, padding=(dpi_10, dpi_10)), text="Analytics")

        # About tab
        self.tabman_mf.add(AboutTab(), text="About")

        # GUI menu
        self.init_menu()

        # Status variables
        self._daf_running = False

        # Window config
        self.win_main.protocol("WM_DELETE_WINDOW", self.close_window)
        self.tabman_mf.select(1)

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

        last_toast: ToastNotification = None
        def trace_listener(level: daf.TraceLEVELS, message: str):
            nonlocal last_toast
       
            if last_toast is None:
                next_position = dpi_78
            elif last_toast.toplevel is None or last_toast.toplevel.winfo_exists():
                # If toplevel is None, that means that tkinter re-entered the its event loop in the
                # toast.show_toast() call before that same function was able to set the toplevel attribute.
                # This happens due to ttkbootstrap library providing the 'alpha' parameter to Tkinter's TopLevel class,
                # which causes Tkinter to re-enter its event loop and process another after_idle(trace_listener, ...) command.
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
            last_toast = toast
            toast.show_toast()

        evt = daf.get_global_event_ctrl()
        evt.add_listener(
            daf.EventID.g_trace, lambda level, message: self.win_main.after_idle(trace_listener, level, message)
        )
        evt.add_listener(
            daf.EventID._ws_disconnect, lambda: self.win_main.after_idle(self.stop_daf)
        )

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
        tae.async_execute(get_connection().shutdown(), pop_up=True)

    def close_window(self):
        resp = tkdiag.Messagebox.yesnocancel("Do you wish to save?", "Save?", alert=True, parent=self.win_main)
        if resp is None or resp == "Cancel" or resp == "Yes" and not self.tab_schema.save_schema():
            return

        if self._daf_running:
            self.stop_daf()

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
