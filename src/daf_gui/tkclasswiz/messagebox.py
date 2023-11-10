"""
Wrapper module, used to add support
for both tkinter and ttkbootstrap message boxes.

This module needs to be imported after ttkbootstrap!
"""
import sys
if sys.modules.get('ttkbootstrap') is not None:
    from ttkbootstrap.dialogs.dialogs import Messagebox as BootMb
    TTKBOOT_INSTALLED = True
else:
    import tkinter.messagebox as mb
    TTKBOOT_INSTALLED = False


__all__ = ("Messagebox",)


class Messagebox:
    """
    Wrapper for some of Messagebox methods, that offers compatibility between
    ttk and ttkbootstrap.
    """
    def _process_kwargs(kwargs):
        if "master" in kwargs:
            kwargs['parent'] = kwargs["master"]
            del kwargs["master"]

    if TTKBOOT_INSTALLED:
        @classmethod
        def yesnocancel(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            r = BootMb.yesnocancel(message, title, **kwargs)
            if r is not None and r != 'Cancel':
                return r == 'Yes'
        
        @classmethod
        def show_error(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            BootMb.show_error(message, title, **kwargs)

        @classmethod
        def show_info(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            BootMb.show_info(message, title, **kwargs)
    else:
        @classmethod
        def yesnocancel(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            return mb.askyesnocancel(title, message, **kwargs)

        @classmethod
        def show_error(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            mb.showerror(title, message, **kwargs)

        @classmethod
        def show_info(cls, title: str, message: str, **kwargs):
            cls._process_kwargs(kwargs)
            mb.showinfo(title, message, **kwargs)