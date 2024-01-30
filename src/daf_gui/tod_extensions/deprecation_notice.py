"""
Deprecation notices TOD extension.
"""
from tkclasswiz.object_frame.frame_struct import NewObjectFrameStruct

import ttkbootstrap.dialogs as tkdiag
import ttkbootstrap as ttk
import daf


DEPRECATION_NOTICES = {
    daf.AutoGUILD: [
        ("Using text (str) on 'include_pattern'", "4.2.0", "AutoGUILD's include_pattern now accepts a BaseLogic object."),
        ("'exclude_pattern' parameter", "4.2.0", "Exclusion can now be done with 'include_pattern'")
    ],
    daf.AutoCHANNEL: [
        ("Using text (str) on 'include_pattern'", "4.2.0", "AutoCHANNEL's include_pattern now accepts a BaseLogic object."),
        ("'exclude_pattern' parameter", "4.2.0", "Exclusion can now be done with 'include_pattern'")
    ],
    daf.TextMESSAGE: [("'start_period' & 'end_period' & 'start_in'", "4.2.0", "Replaced with 'period' parameter")],
    daf.VoiceMESSAGE: [("'start_period' & 'end_period' & 'start_in'", "4.2.0", "Replaced with 'period' parameter")],
    daf.DirectMESSAGE: [("'start_period' & 'end_period' & 'start_in'", "4.2.0", "Replaced with 'period' parameter")],
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
