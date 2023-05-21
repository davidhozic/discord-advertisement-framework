"""
Module contains definitions related to different connection
clients.
"""
from typing import List, Any

from daf_gui.widgets.convert import ObjectInfo

try:
    from .widgets.convert import *
except ImportError:
    from widgets.convert import *


import daf

__all__ = (
    "AbstractConnectionCLIENT",
    "LocalConnectionCLIENT",
)


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
    
    async def refresh(self, object_info: ObjectInfo[Any]):
        """
        Re-retrieves the object inside ObjectInfo and returns a new ObjectInfo,
        which represents update state of an actual object.

        Parameters
        ------------
        object_info: ObjectInfo[Any]
            The ObjectInfo that represent the Python object we want to refresh.
        """
        raise NotImplementedError
    
    async def update(self, object_info: ObjectInfo[Any]):
        """
        Update the existing Python object inside DAF with
        new parameters defined in ``object_info``.
        """
        raise NotImplementedError



class LocalConnectionCLIENT(AbstractConnectionCLIENT):
    """
    Client used for starting and running DAF locally, on the same
    device as the graphical interface.
    """
    def initialize(self, *args, **kwargs):
        return daf.initialize(*args, **kwargs)
    
    def shutdown(self):
        return daf.shutdown()

    async def get_accounts(self) -> List[daf.client.ACCOUNT]:
        return daf.get_accounts()
    
    def add_account(self, account: daf.client.ACCOUNT):
        return daf.add_object(account)

    def remove_account(self, account: daf.client.ACCOUNT):
        return daf.remove_object(account)
