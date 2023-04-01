"""
Main file of the DAF GUI.
"""
from typing import Iterable, Awaitable
import ttkbootstrap as ttk
from PIL import Image, ImageTk

import tkinter as tk
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfile

import asyncio
import json
import sys
import os


import daf

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


class Application():
    def __init__(self) -> None:
        # Window initialization
        win_main = ttk.Window(themename="minty")
        # path = os.path.join(os.path.dirname(__file__), "img/logo.png")
        # photo = tk.PhotoImage(file=path)
        # win_main.iconphoto(True, photo)

        self.win_main = win_main
        screen_res = win_main.winfo_screenwidth() // 2, win_main.winfo_screenheight() // 2
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
        self.tabman_mf = ttk.Notebook(self.frame_main)
        self.tabman_mf.pack(fill=tk.BOTH, expand=True)

        # Objects tab
        self.tab_objects = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_objects, text="Objects definition")
        self.lb_accounts = ListBoxObjects(self.tab_objects)
        self.bnt_add_object = ttk.Button(self.tab_objects, text="Add ACCOUNT", command=lambda: NewObjectWindow(daf.ACCOUNT, self.lb_accounts, self.win_main))
        self.bnt_edit_object = ttk.Button(self.tab_objects, text="Edit", command=self.edit_accounts)
        self.bnt_remove_object = ttk.Button(self.tab_objects, text="Remove", command=self.list_del_account)
        self.bnt_add_object.pack(anchor=tk.NW, fill=tk.X)
        self.bnt_edit_object.pack(anchor=tk.NW, fill=tk.X)
        self.bnt_remove_object.pack(anchor=tk.NW, fill=tk.X)
        self.lb_accounts.pack(fill=tk.BOTH, expand=True)

        # Logging tab
        self.tab_logging = ttk.Frame(self.tabman_mf, padding=(5, 5))
        self.tabman_mf.add(self.tab_logging, text="Logging")
        self.label_logging_mgr = ttk.Label(self.tab_logging, text="Selected logger:")
        self.label_logging_mgr.pack(anchor=tk.N)

        frame_logger_select = ttk.Frame(self.tab_logging)
        frame_logger_select.pack(fill=tk.X)
        self.combo_logging_mgr = ComboBoxObjects(frame_logger_select)
        self.bnt_edit_logger = ttk.Button(frame_logger_select, text="Edit", command=self.edit_logger)
        self.combo_logging_mgr.pack(fill=tk.X, side="left", expand=True)
        self.bnt_edit_logger.pack(anchor=tk.N, side="right")

        self.combo_logging_mgr["values"] = [
            ObjectInfo(daf.LoggerJSON, {}),
            ObjectInfo(daf.LoggerSQL, {}),
            ObjectInfo(daf.LoggerCSV, {}),
        ]

        # Output tab
        self.tab_output = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_output, text="Output")
        text_output = ttk.ScrolledText(self.tab_output, state="disabled")
        text_output.pack(fill=tk.BOTH, expand=True)

        class STDIOOutput:
            def flush(self_):
                pass

            def write(self_, data: str):
                text_output.configure(state="normal")
                for r in daf.tracing.TRACE_COLOR_MAP.values():
                    data = data.replace(r, "")

                text_output.insert(tk.END, data.replace("\033[0m", ""))
                if text_output.count("1.0", tk.END, "lines")[0] > 1000:
                    text_output.delete("1.0", "500.0")

                text_output.see(tk.END)
                text_output.configure(state="disabled")

        self._oldstdout = sys.stdout
        sys.stdout = STDIOOutput()

        # Credits tab
        logo_img = Image.open(f"{os.path.dirname(__file__)}/img/logo.png")
        logo_img = logo_img.resize((self.win_main.winfo_screenwidth() // 8, self.win_main.winfo_screenwidth() // 8), resample=0)
        logo = ImageTk.PhotoImage(logo_img)
        self.tab_info = ttk.Frame(self.tabman_mf)
        self.tabman_mf.add(self.tab_info, text="Credits")
        ttk.Label(self.tab_info, text=CREDITS_TEXT).pack()
        label_logo = ttk.Label(self.tab_info, image=logo)
        label_logo.image = logo
        label_logo.pack()

        # File menu
        self.bnt_file_menu = ttk.Menubutton(self.frame_main, text="Load/Save/Generate")
        self.menubar_file = ttk.Menu(self.bnt_file_menu)
        self.menubar_file.add_command(label="Save schema", command=self.save_schema)
        self.menubar_file.add_command(label="Load schema", command=self.load_schema)
        self.menubar_file.add_command(label="Generate script", command=self.generate_daf_script)
        self.bnt_file_menu.configure(menu=self.menubar_file)
        self.bnt_file_menu.pack()

        # Status variables
        self._daf_running = False
        self._window_opened = True

        # Tasks
        self._async_queue = asyncio.Queue()

        # On close configuration
        self.win_main.protocol("WM_DELETE_WINDOW", self.close_window)

    @property
    def opened(self) -> bool:
        return self._window_opened

    def edit_logger(self):
        selection = self.combo_logging_mgr.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo_logging_mgr.get()
            NewObjectWindow(object_.class_, self.combo_logging_mgr, self.win_main, object_)
        else:
            tkmsg.showerror("Empty list!", "Select atleast one item!")

    def edit_accounts(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            object_: ObjectInfo = self.lb_accounts.get()[selection[0]]
            NewObjectWindow(object_.class_, self.lb_accounts, self.win_main, object_)
        else:
            tkmsg.showerror("Empty list!", "Select atleast one item!")

    def list_del_account(self):
        selection = self.lb_accounts.curselection()
        if len(selection):
            self.lb_accounts.delete(*selection)
        else:
            tkmsg.showerror("Empty list!", "Select atleast one item!")

    def generate_daf_script(self):
        """
        Converts the schema into DAF script
        """
        file = tkfile.asksaveasfile(filetypes=[("DAF Python script", "*.py")])
        if file is None:
            return

        logger = self.combo_logging_mgr.get()
        logger_is_present = str(logger) != ""
        run_logger_str = "\n    logger=logger" if logger_is_present else ""

        accounts: list[ObjectInfo] = self.lb_accounts.get()

        def convert_objects_to_script(object: ObjectInfo | list | tuple | set):
            object_data = []
            import_data = []

            if isinstance(object, ObjectInfo):
                object_str = f"{object.class_.__name__}(\n    "
                attr_str = ""
                for attr, value in object.data.items():
                    if isinstance(value, ObjectInfo | list | tuple | set):
                        value, import_data_ = convert_objects_to_script(value)
                        import_data.extend(import_data_)

                    elif isinstance(value, str):
                        value = f'"{value}"'

                    attr_str += f"{attr}={value},\n"

                object_str += "    ".join(attr_str.splitlines(True)) + ")"
                object_data.append(object_str)
                import_data.append(f"from {object.class_.__module__} import {object.class_.__name__}")

            elif isinstance(object, list | tuple | set):
                _list_data = "[\n"
                for element in object:
                    object_str, import_data_ = convert_objects_to_script(element)
                    _list_data += object_str + ",\n"
                    import_data.extend(import_data_)

                _list_data = "    ".join(_list_data.splitlines(keepends=True))
                _list_data += "]"
                object_data.append(_list_data)

            else:
                object_data.append(str(object))

            return ",".join(object_data), import_data

        accounts_str, imports = convert_objects_to_script(accounts)
        imports = "\n".join(set(imports))

        _ret = f'''
"""
Automatically generated file for Discord Advertisement Framework {daf.VERSION}.
This can be run eg. 24/7 on a server without graphical interface.

The file has the required classes and functions imported, then the logger is defined and the
accounts list is defined.

At the bottom of the file the framework is then started with the run function.
"""

# Import the necessary items
{f"from {logger.class_.__module__} import {logger.class_.__name__}" if logger_is_present else ""}
{imports}

import daf

# Define the logger
{f"logger = {logger}" if logger_is_present else ""}

# Defined accounts
accounts = {accounts_str}


# Run the framework (blocking)

daf.run(
    accounts=accounts,{run_logger_str}
)
'''
        with file:
            file.write(_ret)

        if not file.name.endswith(".py"):
            os.rename(file.name, file.name + ".py")

    def save_schema(self):
        file = tkfile.asksaveasfile(filetypes=[("JSON", "*.json")])
        if file is None:
            return

        json_data = {
            "loggers": {
                "all": [convert_to_json(x) for x in self.combo_logging_mgr["values"]],
                "selected_index": self.combo_logging_mgr.current(),
            },
            "accounts": [convert_to_json(x) for x in self.lb_accounts.get()],
        }

        with file:
            json.dump(json_data, file, indent=2)

        if not file.name.endswith(".json"):
            os.rename(file.name, file.name + ".json")

    def load_schema(self):
        try:
            file = tkfile.askopenfile(filetypes=[("JSON", "*.json")])
            if file is None:
                return

            with file:
                json_data = json.load(file)

                # Load accounts
                accounts = convert_from_json(json_data["accounts"])
                self.lb_accounts.delete(0, tk.END)
                self.lb_accounts.insert(tk.END, *accounts)

                # Load loggers
                loggers = [convert_from_json(x) for x in json_data["loggers"]["all"]]
                self.combo_logging_mgr["values"] = loggers
                selected_index = json_data["loggers"]["selected_index"]
                if selected_index >= 0:
                    self.combo_logging_mgr.current(selected_index)

        except Exception as exc:
            tkmsg.showerror("Schema load error!", f"Could not load schema!\n\n{exc}")

    def start_daf(self):
        try:
            logger = self.combo_logging_mgr.get()
            if isinstance(logger, str) and logger == "":
                logger = None
            elif logger is not None:
                logger = convert_to_objects(logger)

            self._async_queue.put_nowait(daf.initialize(logger=logger))
            self._async_queue.put_nowait([daf.add_object(convert_to_objects(account)) for account in self.lb_accounts.get()])
            self.bnt_toolbar_start_daf.configure(state="disabled")
            self.bnt_toolbar_stop_daf.configure(state="enabled")
            self._daf_running = True
        except Exception as exc:
            print(exc)
            tkmsg.showerror("Start error!", f"Could not start daf due to exception!\n\n{exc}")

    def stop_daf(self):
        self._async_queue.put_nowait(daf.shutdown())
        self._daf_running = False
        self.bnt_toolbar_start_daf.configure(state="enabled")
        self.bnt_toolbar_stop_daf.configure(state="disabled")

    def close_window(self):
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
            tkmsg.showerror("Coroutine error", str(exc))

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
