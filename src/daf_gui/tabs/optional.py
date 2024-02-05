import ttkbootstrap as ttk

from tkclasswiz.utilities import gui_except
from tkclasswiz.dpi import dpi_scaled
from tkclasswiz.convert import *
from tkclasswiz.storage import *

from ..connector import *

import ttkbootstrap.dialogs as tkdiag
import tkinter as tk
import subprocess
import sys

import daf


__all__ = (
    "OptionalTab",
)


OPTIONAL_MODULES = [
    # Label, optional name, installed var
    ("SQL logging", "sql", daf.logging.sql.SQL_INSTALLED),
    ("Voice messages", "voice", daf.message.voice_based.GLOBAL.voice_installed),
    ("Web features (Chrome)", "web", daf.web.GLOBALS.selenium_installed),
]


class OptionalTab(ttk.Frame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        dpi_5 = dpi_scaled(5)

        ttk.Label(
            self,
            text=
            "This section allows you to install optional packages available inside DAF\n"
            "Be aware that loading may be slower when installing these."
        ).pack(anchor=tk.NW)

        frame_optionals_packages = ttk.Frame(self)
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
