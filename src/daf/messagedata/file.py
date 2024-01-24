
from typing import Union, Optional
from typeguard import typechecked
from os.path import basename

from ..misc.doc import doc_category
from ..logging.tracing import *

import io

__all__ = ("FILE",)

@typechecked
@doc_category("Message data")
class FILE:
    """
    FILE object used as a data parameter to the xMESSAGE objects.
    This is needed opposed to a normal file object because this way,
    you can edit the file after the framework has already been started.

    .. caution::
        This is used for sending an actual file and **NOT it's contents as text**.

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
