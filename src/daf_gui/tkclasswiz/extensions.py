"""
Module used to add extensions to add extensions
to TOD.
"""
from typing import Callable, TypeVar, Union
from inspect import isclass
from functools import wraps

T = TypeVar('T')


class Extension:
    def __init__(self, name: str, version: str, loader: Callable[[T], None]) -> None:
        self._name = name
        self._version = version
        self._loader = loader

    def __repr__(self) -> str:
        return f"Extension(name={self._name}, version={self._version}, loader={self._loader.__name__})"

    def __call__(self, *args: T, **kwargs: T) -> None:
        return self._loader(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def loader(self):
        return self._loader


def extendable(obj: Union[T, list]):
    """
    Decorator that makes the class extendable.
    
    Parameters
    ---------------
    obj: T
        Function or a class that can be extended.
        If class, then the extension functions  will be called after the __init__ function.
        The extension functions receive the actual class instance.

        If function, the extension functions will be called after function call.
        The extension functions receive the same parameters as original function and the result of the
        original function, so the signature must be: def name(<original parameters>, <original return value>).
        or if it's a method: def name(self, <original parameters>, <original return value>).
        In the case of MULTIPLE extensions added to the function, the <original return value> will be recursively
        passed to all the extensions as the result of previous extension.
    """
    if isclass(obj):
        @wraps(obj, updated=[])
        class ExtendableClass(obj):
            __reg_post_ext__ = []
            __reg_pre_ext__ = []

            def __init__(self, *args, **kwargs):
                for extension in ExtendableClass.__reg_pre_ext__:
                    extension(self, *args, **kwargs)

                super().__init__(*args, **kwargs)

                extension: Extension
                for extension in ExtendableClass.__reg_post_ext__:
                    extension(self, *args, **kwargs)

            @classmethod
            def register_pre_extension(cls, extension: Extension):
                cls.__reg_pre_ext__.append(extension)

            @classmethod
            def register_post_extension(obj, extension: Extension):
                obj.__reg_post_ext__.append(extension)

            @classmethod
            def get_extensions(obj):
                return obj.__reg_pre_ext__, obj.__reg_post_ext__[:]

        return ExtendableClass
    else:
        @wraps(obj, updated=[])
        class ExtendableFunction:
            __reg_post_ext__ = []
            __reg_pre_ext__ = []

            def __init__(self, bind: object = None) -> None:
                self.bind = bind

            def __call__(self, *args, **kwargs):
                if self.bind is not None:
                    extra_args = (self.bind,)  # self reference
                else:
                    extra_args = ()

                for ext in ExtendableFunction.__reg_pre_ext__:
                    ext(*extra_args, *args, **kwargs)

                r = obj(*extra_args, *args, **kwargs)
                
                for ext in ExtendableFunction.__reg_post_ext__:
                    r = ext(*extra_args, *args, r, **kwargs)

                return r

            def __get__(self, instance, cls):
                # Bind the wrapper callable object into a callable object "instance"
                return ExtendableFunction(instance)

            @classmethod
            def register_pre_extension(cls, extension: Extension):
                cls.__reg_pre_ext__.append(extension)

            @classmethod
            def register_post_extension(cls, extension: Extension):
                cls.__reg_post_ext__.append(extension)

            @classmethod
            def get_extensions(obj):
                return obj.__reg_pre_ext__, obj.__reg_post_ext__[:]


        return ExtendableFunction()
