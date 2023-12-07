"""
Module contains definitions related to different connection
clients.
"""
from typing import List, Optional, Literal, Awaitable

from daf.logging.tracing import TraceLEVELS, trace
from daf.misc import instance_track as it

from tkclasswiz.convert import *
from tkclasswiz.utilities import *

from aiohttp import ClientSession, BasicAuth, WSMsgType
from aiohttp import web

import daf
import asyncio


__all__ = (
    "AbstractConnectionCLIENT",
    "LocalConnectionCLIENT",
    "RemoteConnectionCLIENT",
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

    async def add_account(self, obj: daf.client.ACCOUNT):
        """
        Adds and initializes a new account into DAF.

        Parameters
        --------------
        account: obj: ObjectInfo[daf.client.ACCOUNT]
            The account to add.
        """
        raise NotImplementedError

    async def remove_account(self, account_ref: it.ObjectReference):
        """
        Logs out and removes account from DAF.

        Parameters
        ----------------
        account_ref: it.ObjectReference
            The reference to account to remove.
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

    async def refresh(self, object_ref: it.ObjectReference) -> object:
        """
        Returns updated state of the object.

        Parameters
        ------------
        object_ref
            Reference to an object to refresh.
        """
        raise NotImplementedError

    async def execute_method(self, object_ref: it.ObjectReference, method_name: str, **kwargs):
        """
        Executes a method inside object and returns the result.

        Parameter
        -----------
        object_ref
            Reference to an object to execute method on.
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

    def _convert_ids(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_ids(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert_ids(x) for x in obj]

        if isinstance(obj, it.ObjectReference):
            return it.get_by_id(obj.ref)

        return obj

    async def shutdown(self):
        await daf.shutdown()
        self.connected = False

    def add_account(self, obj: daf.client.ACCOUNT):
        return daf.add_object(obj)

    def remove_account(self, account_ref: it.ObjectReference):
        return daf.remove_object(it.get_by_id(account_ref.ref))

    async def get_accounts(self) -> List[daf.client.ACCOUNT]:
        return daf.get_accounts()

    async def get_logger(self) -> daf.logging.LoggerBASE:
        return daf.get_logger()

    async def refresh(self, object_ref: it.ObjectReference):
        return it.get_by_id(object_ref.ref)  # Local connection can just use the local object

    async def execute_method(self, object_ref: it.ObjectReference, method_name: str, **kwargs):
        result = getattr(it.get_by_id(object_ref.ref), method_name)(**self._convert_ids(kwargs))
        if isinstance(result, Awaitable):
            result = await result

        return result


class RemoteConnectionCLIENT(AbstractConnectionCLIENT):
    """
    Client used for connecting to DAF running on a remote server though
    the HTTP protocol. The connection is based fully on request from the GUI (this client).

    Parameters
    ------------
    host: str
        The URL / IP of the host.
    port: Optional[int]
        The HTTP port of the host.
        Defaults to 80.
    username: Optional[str]
        The username to login with.
    password: Optional[str].
        The password to login with.
    verify_ssl: Optional[bool]
        Defaults to True. If True, connection will be refused when the certificate does not match the host name.
    """
    TIMEOUT = 10 * 60  # * seconds / minute

    __passwords__ = ("password", )

    def __init__(
        self,
        host: str,
        port: int = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: Optional[bool] = True
    ) -> None:
        self.session = None
        self._ws_task: asyncio.Task = None
        self.connected = False

        self.host = host.rstrip('/')  # Remove any slashes in the back to prevent errors with port
        self.port = port
        self.auth = None
        if username is not None:
            self.auth = BasicAuth(username, password)

        if verify_ssl is None:
            verify_ssl = False

        self.verify_ssl = verify_ssl

    async def _request(self, method: Literal["GET", "POST", "DELETE", "PATCH"], route: str, **kwargs):
        method = method.lower()
        additional_kwargs = {}
        if not self.verify_ssl:
            additional_kwargs["ssl"] = False

        trace(f"Requesting {route} with {method}.", TraceLEVELS.DEBUG)
        async with getattr(self.session, method)(route, json={"parameters": kwargs}, timeout=self.TIMEOUT, **additional_kwargs) as response:
            if response.status != 200:
                raise web.HTTPException(reason=response.reason)

            return await response.json()

    async def initialize(self, *args, **kwargs):
        try:
            self.session = ClientSession(f"{self.host}:{self.port}", auth=self.auth)
            daf.tracing.initialize(kwargs.get("debug", TraceLEVELS.NORMAL))
            daf.events.initialize()
            trace("Pinging server.")
            await self._ping()
            self.connected = True
            GLOBALS.connection = self  # Set self as global connection
            self._ws_task = asyncio.create_task(self._connect_ws())
        except Exception:
            await self.session.close()
            raise

    async def _connect_ws(self):
        evt = daf.events.get_global_event_ctrl()
        try:
            trace("Connecting to live WebSocket connection.")
            additional_kwargs = {}
            if not self.verify_ssl:
                additional_kwargs["ssl"] = False

            async with self.session.ws_connect("/subscribe", auth=self.auth, **additional_kwargs) as ws:
                trace("Connected to WebSocket.")
                async for message in ws:
                    trace(f"WebSocket received {message.type}", TraceLEVELS.DEBUG)
                    if message.type == WSMsgType.TEXT:
                        resp = daf.convert_from_semi_dict(message.json())
                        type = resp["type"]
                        data = resp.get("data")
                        if type == "trace":
                            trace(data["message"], data["level"])

                        elif type == "shutdown":
                            await ws.close()
                    elif message.type == WSMsgType.ERROR:
                        raise ws.exception()

                    elif message.type in {WSMsgType.CLOSE, WSMsgType.CLOSING}:
                        trace(message.type, TraceLEVELS.DEBUG)

        except Exception as exc:
            trace("WebSocket error, closing connection!", TraceLEVELS.ERROR, exc)

        if self.connected:  # Only call this if the task has not ended due to manual disconnect
            await evt.emit(daf.EventID._ws_disconnect)

        trace("Websocket connection closed", TraceLEVELS.DEBUG)

    async def shutdown(self):
        trace("Closing connection.")
        self.connected = False
        await self.session.close()
        await self._ws_task
        await daf.events.get_global_event_ctrl().stop()

    async def add_account(self, obj: daf.client.ACCOUNT):
        response = await self._request(
            "POST", "/accounts",
            account=daf.convert.convert_object_to_semi_dict(obj)
        )

    async def remove_account(self, account_ref: it.ObjectReference):
        response = await self._request("DELETE", "/accounts", account_id=account_ref.ref)

    async def get_accounts(self) -> List[daf.client.ACCOUNT]:
        response = await self._request("GET", "/accounts")
        return daf.convert.convert_from_semi_dict(response["result"]["accounts"])

    async def get_logger(self):
        response = await self._request("GET", "/logging")
        return daf.convert.convert_from_semi_dict(response["result"]["logger"])

    async def refresh(self, object_ref: it.ObjectReference):
        response = await self._request("GET", "/object", object_id=object_ref.ref)
        return daf.convert.convert_from_semi_dict(response["result"]["object"])

    async def execute_method(self, object_ref: it.ObjectReference, method_name: str, **kwargs):
        kwargs = daf.convert.convert_object_to_semi_dict(kwargs)
        response = await self._request("POST", "/method", object_id=object_ref.ref, method_name=method_name, **kwargs)
        return daf.convert.convert_from_semi_dict(response["result"]["result"])

    def _ping(self):
        return self._request("GET", "/ping")


def get_connection() -> AbstractConnectionCLIENT:
    return GLOBALS.connection
