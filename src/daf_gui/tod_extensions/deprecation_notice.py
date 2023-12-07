"""
Deprecation notices TOD extension.
"""
from tkclasswiz.object_frame.frame_struct import NewObjectFrameStruct

import ttkbootstrap.dialogs as tkdiag
import ttkbootstrap as ttk
import daf


DEPRECATION_NOTICES = {
    daf.AUDIO: [("daf.dtypes.AUDIO", "2.12", "Replaced with daf.dtypes.FILE")],
    daf.VoiceMESSAGE: [("daf.dtypes.AUDIO as type for data parameter", "2.12", "Replaced with daf.dtypes.FILE")],
}


def load_extension(frame: NewObjectFrameStruct, *args, **kwargs):
    if len(notices := DEPRECATION_NOTICES.get(frame.class_, [])):
        def show_deprecations():
            tkdiag.Messagebox.show_warning(
                f"\n{'-'*30}\n".join(f"'{title}' is scheduled for removal in v{version}.\nReason: '{reason}'" for title, version, reason in notices),
                "Deprecation notice",
                frame
            )

        ttk.Button(
            frame.frame_toolbar,
            text="Deprecation notices",
            bootstyle="dark",
            command=show_deprecations
        ).pack(side="right")
