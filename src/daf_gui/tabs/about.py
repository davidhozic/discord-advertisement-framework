import ttkbootstrap as ttk

from tkclasswiz.dpi import dpi_scaled
from PIL import Image, ImageTk

import webbrowser
import daf
import os


__all__ = (
    "AboutTab",
)


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


class AboutTab(ttk.Frame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)        
        dpi_10 = dpi_scaled(10)
        dpi_30 = dpi_scaled(30)
        logo_img = Image.open(f"{os.path.dirname(__file__)}/../img/logo.png")
        logo_img = logo_img.resize(
            (dpi_scaled(400), dpi_scaled(400)),
            resample=0
        )
        logo = ImageTk.PhotoImage(logo_img)
        info_bnts_frame = ttk.Frame(self)
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
        ttk.Label(self, text="Like the app? Give it a star :) on GitHub (^)").pack(pady=dpi_10)
        ttk.Label(self, text=CREDITS_TEXT).pack()
        label_logo = ttk.Label(self, image=logo)
        label_logo.image = logo
        label_logo.pack()
