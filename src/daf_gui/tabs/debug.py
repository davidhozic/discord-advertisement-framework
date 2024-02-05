import ttkbootstrap as ttk
import tkinter as tk

from tkclasswiz.storage import ListBoxScrolled

import daf
import sys


__all__ = (
    "DebugTab",
)


class DebugTab(ttk.Frame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)        
        text_output = ListBoxScrolled(self)
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
