"""
Help button TOD extension.
"""
from tkclasswiz.object_frame.frame_struct import NewObjectFrameStruct

import ttkbootstrap as ttk
import webbrowser
import _discord
import daf


HELP_URLS = {
    "daf": f"https://daf.davidhozic.com/en/v{'.'.join(daf.VERSION.split('.')[:2])}.x/?rtd_search={{}}",
    "_discord": f"https://docs.pycord.dev/en/v{_discord._version.__version__}/search.html?q={{}}",
}


def load_extension(frame: NewObjectFrameStruct, *args, **kwargs):
    package = frame.class_.__module__.split(".", 1)[0]
    help_url = HELP_URLS.get(package)
    if help_url is not None:
        def cmd():
            webbrowser.open(help_url.format(frame.get_cls_name(frame.class_)))

        ttk.Button(frame.frame_toolbar, text="Help", command=cmd).pack(side="left")
