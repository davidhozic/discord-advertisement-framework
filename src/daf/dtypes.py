"""
    The module contains definitions regarding the data types
    you can send using the xxxMESSAGE objects.
"""
from typing import Any, Callable, Coroutine, Union, Optional
from os.path import basename
from typeguard import typechecked
import importlib.util as iu
import io

from .logging.tracing import *
from .misc import doc


__all__ = (
    "data_function",
    "_FunctionBaseCLASS",
    "FILE",
    "AUDIO"
)


class GLOBALS:
    "Storage class used for storing global variables"
    voice_installed: bool = iu.find_spec("nacl") is not None


#######################################################################
# Decorators
#######################################################################
class _FunctionBaseCLASS:
    """
    Used as a base class to FunctionCLASS which gets created in :ref:`data_function` decorator.
    Because the FunctionCLASS is inaccessible outside the :ref:`data_function` decorator,
    this class is used to detect if the MESSAGE.data parameter is of function type,
    because the function isinstance also returns True when comparing
    the object to it's class or to the base class from which the object class is inherited from.
    """


@doc.doc_category("Types")
def data_function(fnc: Callable):
    """
    Decorator used for wrapping a function that will return data to send when the message is ready.

    The ``fnc`` function must return data that is of type that the **x**\\ MESSAGE object supports.
    **If the type returned is not valid, the send attempt will simply be ignored and nothing will be logged at at**,
    this is useful if you want to use the ``fnc`` function to control whenever the message is ready to be sent.
    For example: if we have a function defined like this:

    .. code-block::
        :emphasize-lines: 3

        @daf.data_function
        def get_data():
            return None

        ...
        daf.TextMESSAGE(..., data=get_data())
        ...

    then no messages will ever be sent,
    nor will any logs be made since invalid values are simply ignored by the framework.



    Parameters
    ------------
    fnc: Callable
        The function to wrap.

    Returns
    -----------
    FunctionCLASS
        A class for creating wrapper objects is returned. These wrapper objects can be used as
        a ``data`` parameter to the :ref:`Messages` objects.


    .. literalinclude:: ../../DEP/main_data_function.py
        :language: python
        :emphasize-lines: 12, 24
    """

    class FunctionCLASS(_FunctionBaseCLASS):
        """
        Used for creating special classes that are then used to create objects in the daf.MESSAGE
        data parameter, allows for sending dynamic content received thru an user defined function.

        Parameters
        -----------
        - Custom number of positional and keyword arguments.

        .. literalinclude:: ../../Examples/Message Types/TextMESSAGE/main_data_function.py
            :language: python
        """
        __slots__ = (
            "args",
            "kwargs",
            "func_name",
        )

        def __init__(self, *args: Any, **kwargs: Any):
            self.args = args
            self.kwargs = kwargs
            self.func_name = fnc.__name__

        async def retrieve(self):
            """
            Retrieves the data from the user function.
            """
            _ = fnc(*self.args, **self.kwargs)
            if isinstance(_, Coroutine):
                return await _
            return _

        def __str__(self) -> str:
            return self.func_name

    return FunctionCLASS


#######################################################################
# Other
#######################################################################
@typechecked
@doc.doc_category("Types")
class FILE:
    """
    FILE object used as a data parameter to the xMESSAGE objects.
    This is needed opposed to a normal file object because this way,
    you can edit the file after the framework has already been started.

    .. caution::
        This is used for sending an actual file and **NOT it's contents as text**.

    .. versionchanged:: 2.10

        The file's data is loaded at file creation to support
        transfers over a remote connection.
        Additionaly this class replaces :class:`daf.dtypes.AUDIO` for
        audio streaming.

        New properties: stream, filename, data, hex.


    Parameters
    -------------
    filename: str
        The filename of file you want to send.
    data: Optional[Union[bytes, str]]
        Optional raw data or hex string represending raw data.

        If this parameter is not given (set as None), the data will be automatically obtained from ``filename`` file.
        Defaults to ``None``.

        .. versionadded:: 2.10

    Raises
    -----------
    FileNotFoundError
        The ``filename`` does not exist.
    OSError
        Could not read file ``filename``.
    ValueError
        The ``data`` parameter is of incorrect format.
    """
    __slots__ = ("_filename", "_basename", "_data")

    def __init__(self, filename: str, data: Optional[Union[bytes, str]] = None):
        if data is None:
            with open(filename, "rb") as file:
                data = file.read()

        elif isinstance(data, str):
            data = bytes.fromhex(data)

        self._filename = filename
        self._basename = basename(filename)
        self._data = data

    def __repr__(self) -> str:
        return f"FILE(filename={self._filename})"

    @property
    def stream(self) -> io.BytesIO:
        "Returns a stream to data provided at creation."
        return io.BytesIO(self._data)

    @property
    def filename(self) -> str:
        "The name of the file"
        return self._basename
    
    @property
    def fullpath(self) -> str:
        "The full path to the file"
        return self._filename

    @property
    def data(self) -> bytes:
        "Returns the raw binary data"
        return self._data

    @property
    def hex(self) -> str:
        "Returns HEX representation of the data."
        return self._data.hex()

    def to_dict(self):
        """
        Returns dictionary representation of this data type.

        .. versionadded:: 2.10
        """
        return {
            "type:": "File",
            "filename": self.fullpath
        }


@typechecked
@doc.doc_category("Types")
class AUDIO(FILE):
    """
    Used for streaming audio from file.

    .. deprecated:: 2.10

        Use :class:`daf.dtypes.FILE` instead.

    Parameters
    -----------------
    filename: str
        Path to the file you want streamed.

    Raises
    ----------
    FileNotFoundError
        Raised when the file not found.
    OSError
        Could not load audio file.
    """

    def __init__(self, filename: str) -> None:
        trace("AUDIO is deprecated, use FILE instead.", TraceLEVELS.DEPRECATED)
        return super().__init__(filename)

    @property
    def url(self):
        return self.filename
