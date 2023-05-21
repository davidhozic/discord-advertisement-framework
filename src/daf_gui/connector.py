"""
Module contains definitions related to different connection
clients.
"""
from typing import List

from .convert import *
from .utilities import *

import daf


__all__ = (
    "AbstractConnectionCLIENT",
    "LocalConnectionCLIENT",
    "get_connection",
)


class GLOBALS:
    connection: "AbstractConnectionCLIENT" = None


class AbstractConnectionCLIENT:
    """
    Interface for connection clients.
    """
    async def initialize(self, *args, **kwargs):
        """
        Method for initializing DAF.

        Parameters
        ------------
        args
            Custom number of positional arguments.
        kwargs:
            Custom number of keyword arguments.
        """
        raise NotImplementedError

    async def shutdown(self):
        """
        Method calls DAF's shutdown core function.
        """
        raise NotImplementedError

    async def add_account(self, account: daf.client.ACCOUNT):
        """
        Adds and initializes a new account into DAF.

        Parameters
        --------------
        account: daf.client.ACCOUNT
            The account to add.
        """
        raise NotImplementedError

    async def remove_account(self, account: daf.client.ACCOUNT):
        """
        Logs out and removes account from DAF.

        Paramterers
        ----------------
        account: daf.client.ACCOUNT
            The account to remove from DAF.
        """
        raise NotImplementedError

    async def get_accounts(self) -> List[daf.client.ACCOUNT]:
        """
        Retrieves a list of all accounts in DAF.
        """
        raise NotImplementedError

    async def get_logger(self) -> daf.logging.LoggerBASE:
        """
        Returns the logger object used in DAF.
        """
        raise NotImplementedError

    async def refresh(self, object_: object) -> object:
        """
        Returns updated state of the object.

        Parameters
        ------------
        object_: object
            The object that we want to refresh.
        """
        raise NotImplementedError

    async def execute_method(self, object_: object, method_name: str, *args, **kwargs):
        """
        Executes a method inside object and returns the result.

        Parameter
        -----------
        object_: object
            The object to execute the method on.
        method_name: str
            The name of the method to execute.
        args: Any
            Custom number of positional arguments to pass to the method.
        kwargs: Any
            Custom number of keyword arguments to pass to the method.
        """
        raise NotImplementedError


class LocalConnectionCLIENT(AbstractConnectionCLIENT):
    """
    Client used for starting and running DAF locally, on the same
    device as the graphical interface.
    """
    def __init__(self) -> None:
        self.connected = False

    async def initialize(self, *args, **kwargs):
        await daf.initialize(*args, **kwargs)
        GLOBALS.connection = self  # Set self as global connection
        self.connected = True

    async def shutdown(self):
        await daf.shutdown()
        self.connected = False

    def add_account(self, account: daf.client.ACCOUNT):
        return daf.add_object(account)

    def remove_account(self, account: daf.client.ACCOUNT):
        return daf.remove_object(account)

    async def get_accounts(self) -> List[daf.client.ACCOUNT]:
        return daf.get_accounts()

    async def get_logger(self) -> daf.logging.LoggerBASE:
        return daf.get_logger()

    async def refresh(self, object_: object) -> object:
        return object_  # Local connection can just use the local object

    async def execute_method(self, object_: object, method_name: str, *args, **kwargs):
        result = getattr(object_, method_name)(*args, **kwargs)
        if isinstance(result, Coroutine):
            result = await result

        return result


def get_connection() -> AbstractConnectionCLIENT:
    return GLOBALS.connection
