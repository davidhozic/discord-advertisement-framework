"""
Module used to add extensions to add extensions
to TOD.
"""
from typing import Callable, TypeVar


T = TypeVar('T')


class Extension:
    def __init__(self, name: str, version: str, loader: Callable[[T], None]) -> None:
        self._name = name
        self._version = version
        self._loader = loader

    def __call__(self, *args: T, **kwargs: T) -> None:
        self._loader(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def loader(self):
        return self._loader


def extendable(cls: T):
    """
    Decorator that makes the class extendable.
    """
    class ExtendableClass(cls):
        __registered_tod_ext__ = []

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            extension: Extension
            for extension in self.__registered_tod_ext__:
                extension(self)

        @classmethod
        def register_extension(cls, extension: Extension):
            cls.__registered_tod_ext__.append(extension)

        @classmethod
        def get_extensions(cls):
            return cls.__registered_tod_ext__[:]

    ExtendableClass.__name__ = cls.__name__
    return ExtendableClass
