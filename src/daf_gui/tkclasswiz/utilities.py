"""
Utility module.
"""
from typing import Any, Callable, Tuple
from functools import wraps

import importlib
from .messagebox import Messagebox

import tkinter as tk


__all__ = (
    "import_class",
    "gui_except",
    "gui_confirm_action",
    "issubclass_noexcept",
)


def import_class(path: str) -> type:
    """
    Imports the class provided by it's ``path``.
    """
    path = path.split(".")
    module_path, class_name = '.'.join(path[:-1]), path[-1]
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # Fall back for older versions, try to import from package instead of module
        module_path = module_path.split('.')[0]
        module = importlib.import_module(module_path)

    class_ = getattr(module, class_name)
    return class_


def gui_except(window = None):
    """
    Function that returns a decorator.
    The decorator returns a callable wrapper object.

    When the wrapper is called, it calls the original callee, and in case an exception is raised,
    the exception is displayed through a popup window.
    If no exception is raised, the callee's result is returned.


    Parameters
    --------------
    window: Optional[Any]
        Optional parent widget, if not provided, the owner of callee method will be used.
    """
    def decorator(fnc: Callable):
        @wraps(fnc, updated=[])
        class wrapper:
            def __init__(self, instance = None) -> None:
                self.inst = instance
            
            def __get__(self, instance, cls = None):
                return wrapper(instance)
            
            def __call__(self, *args: Any, **kwargs: Any) -> Any:
                parent = window or self.inst
                if not isinstance(parent, tk.BaseWidget):
                    parent = None

                try:
                    if self.inst is not None:
                        args = (self.inst, *args)

                    return fnc(*args, **kwargs)
                except Exception as exc:
                    Messagebox.show_error(f"Exception in {fnc.__name__}", str(exc), parent=parent)

        return wrapper()

    return decorator


def gui_confirm_action(parent = None):
    """
    Function that returns a decorator.
    The decorator returns a callable wrapper object.

    When the wrapper is called, the user is asked to confirm the action and if the user confirms,
    the original function is called and the wrapper returns the result.
    If action is cancelled, None is returned by the wrapper.

    Parameters
    --------------
    parent: Optional[Any]
        Optional parent widget, if not provided, the owner of callee method will be used.
    """
    def _gui_confirm_action(fnc: Callable):
        class wrapper:
            def __init__(self, bind = None) -> None:
                self.bind = bind

            def __call__(self, *args, **kwargs):
                result = Messagebox.yesnocancel("Confirm", "Are you sure?", parent=parent or self.bind)

                if self.bind is not None:
                    args = (self.bind, *args)  # self, *args

                if result:
                    return fnc(*args, **kwargs)
                
            def __get__(self, instance, cls = None):
                return wrapper(instance)

        return wrapper()

    return _gui_confirm_action


def issubclass_noexcept(cls: type, bases: Tuple[type]):
    """
    Same as :func:`inspect.issubclass`, but instead of raising an exception
    when the second argument is not a class, it returns False.
    """
    try:
        return issubclass(cls, bases)
    except Exception:
        return False
