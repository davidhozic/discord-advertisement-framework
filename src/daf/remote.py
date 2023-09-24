"""
Module contains definitions related to remote access from a graphical interface.
"""
from typing import Optional, Literal, Awaitable
from contextlib import suppress
from functools import update_wrapper

from aiohttp import BasicAuth
from aiohttp.web import (
    Request, RouteTableDef, Application, _run_app, json_response,
    HTTPException, HTTPInternalServerError, HTTPUnauthorized, WebSocketResponse, WSMsgType
)

from .events import *
from .logging.tracing import *
from .misc import doc, instance_track as it
from . import convert
from . import logging
from . import client

import asyncio
import ssl


__all__ = ("RemoteAccessCLIENT",)


# Constants
# ------------
MAX_PACKET_SIZE_BYTE = 10**9


class GLOBALS:
    routes = RouteTableDef()
    http_task: asyncio.Task = None
    remote_client: "RemoteAccessCLIENT" = None


def create_json_response(message: str = None, dict_: dict = {}, **kwargs):
    """
    Creates a JSON response representing JSON response.

    Parameters
    -----------
    message: str
        Status message to return to the server.
    kwargs:
        Other keys
    """
    return json_response({
        "message": message,
        "result": {**kwargs, **dict_}
    })


def register(path: str, type: Literal["GET", "POST", "DELETE", "PATCH"]):
    """
    Used to register a route handler.

    Parameters
    --------------
    path: str
        The http URL path.
    type: Literal["GET", "POST", "DELETE", "PATCH"]
        Request type.
    """
    def decorator(fnc):
        async def request_wrapper(request: Request):
            try:
                authorization = request.headers.get("Authorization")
                if (
                    authorization is None and GLOBALS.remote_client.auth is not None or
                    authorization != GLOBALS.remote_client.auth
                ):
                    raise HTTPUnauthorized(reason="Wrong username / password")

                if request.content_type == "application/json":
                    json_data = await request.json()
                    return await fnc(**json_data["parameters"])
                
                # In case the data is not JSON, just pass the original request object
                return await fnc(request)
            except HTTPException:
                raise  # Don't wrap already HTTP exceptions

            except Exception as exc:
                raise HTTPInternalServerError(reason=str(exc)) from exc

        # For documentation purposes
        fnc.__doc__ = (fnc.__doc__ or "") + f'\n\n    :Route:\n        {path}\n\n    :Method:\n        {type}'
        update_wrapper(request_wrapper, fnc)

        # Use the original aiohttp decorator
        return getattr(GLOBALS.routes, type.lower())(path)(request_wrapper)

    return decorator


@doc.doc_category("Clients")
class RemoteAccessCLIENT:
    """
    Client used for processing remote requests from a GUI located on a different network.

    Parameters
    ---------------
    host: Optional[str]
        The host address. Defaults to ``0.0.0.0`` (Listens on all network interfaces).
    port: Optional[int]
        The http port. Defaults to ``80``.
    username: Optional[str]
        The basic authorization username. Defaults to ``None``.
    password: Optional[str]
        The basic authorization password. Defaults to ``None``.
    certificate: Optional[str]
        Path to a certificate file. Used when HTTPS is desired instead of HTTP. (Recommended if username & password)
    private_key: Optional[str]
        Path to a private key file that belongs to ``certificate``.
    private_key_pwd: Optional[str]
        The password of ``private_key`` if it has any.

    Raises
    -----------
    ValueError
        Private key is required with certificate.
    """
    def __init__(
        self,
        host: Optional[str] = "0.0.0.0",
        port: Optional[int] = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
        certificate: Optional[str] = None,
        private_key: Optional[str] = None,
        private_key_pwd: Optional[str] = None
    ) -> None:
        self.host = host
        self.port = port
        self.auth = BasicAuth(username, password).encode() if username is not None else None

        if certificate is not None:
            if private_key is None:
                raise ValueError("'private_key' parameter is needed when certificate is provided.")

            # HTTPS ssl context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certificate, private_key, private_key_pwd)
        else:
            context = None

        self.ssl_ctx = context
        self.web_app = Application(client_max_size=MAX_PACKET_SIZE_BYTE)
        self.web_app.add_routes(GLOBALS.routes)

    async def initialize(self):
        GLOBALS.http_task = asyncio.create_task(
            _run_app(self.web_app, host=self.host, port=self.port, print=False, ssl_context=self.ssl_ctx)
        )

    async def _close(self):
        await self.web_app.shutdown()
        await self.web_app.cleanup()
        task = GLOBALS.http_task
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@register("/ping", "GET")
@doc.doc_category("Connection", api_type="HTTP")
async def http_ping():
    """
    Pinging route for testing connection.
    """
    return create_json_response(message="pong")


@register("/logging", "GET")
@doc.doc_category("Logging", api_type="HTTP")
async def http_get_logger():
    """
    Returns active message / invite logger.

    Returns
    ----------
    LoggerBASE
        Active logger.
    """
    return create_json_response(logger=convert.convert_object_to_semi_dict(logging.get_logger()))


@register("/object", "GET")
@doc.doc_category("Object", api_type="HTTP")
async def http_get_object(object_id: int):
    """
    Returns a tracked object, tracked with @track_id decorator.

    Parameters
    -------------
    object_id: int
        The ID of the object to obtain.

    Returns
    ---------
    object
        The object linked to ``object_id``.
    """
    object = it.get_by_id(object_id)
    return create_json_response(object=convert.convert_object_to_semi_dict(object))


@register("/method", "POST")
@doc.doc_category("Object", api_type="HTTP")
async def http_execute_method(object_id: int, method_name: str, **kwargs):
    """
    Executes a method on a object. The method is an actual Python method.

    Parameters
    ----------
    object_id: int
        The ID of the object to execute on.
    method_name: str
        The name of the method to execute.
    kwargs
        Variadic keyword arguments to pass to the executed method.

    Returns
    -------
    Any
        The returned value from method.
    """
    object = it.get_by_id(object_id)
    try:
        result = getattr(object, method_name)(**convert.convert_from_semi_dict(kwargs))
        if isinstance(result, Awaitable):
            result = await result

    except Exception as exc:
        raise HTTPInternalServerError(reason=f"Error executing method {method_name}. ({exc})")

    return create_json_response(f"Executed method {method_name}.", result=convert.convert_object_to_semi_dict(result))


@register("/subscribe", "GET")
async def http_ws_live_connect(request: Request):
    """
    Route for subscribing to remote published events.
    This is a WebSocket upgrade route.

    The WebSocket connection will send events in the following JSON format:
    
    .. code-block:: JSON
    
        {
            "type": str, # Event type (eg. "trace")
            "data": dict # (Optional) Dictionary of data related to event, this differs on different event types.
        }
    """
    # Event listeners
    async def trace_event_publisher(level: TraceLEVELS, message: str):
        await ws.send_json(
            convert.convert_object_to_semi_dict(
                {"type": "trace", "data": {"level": level, "message": message}}     
            )
        )

    async def shutdown_event_publisher():
        await ws.send_json(
            convert.convert_object_to_semi_dict(
                {"type": "shutdown"}
            )
        )
        await ws.close()

    async def account_expire_event_publisher(account: client.ACCOUNT):
        await ws._stored_content_type(
            convert.convert_object_to_semi_dict(
                {"type": "account_expired", "data": {"account": account}}
            )
        )

    ws = WebSocketResponse()
    await ws.prepare(request)

    evt = get_global_event_ctrl()
    evt.add_listener(EventID.g_trace, trace_event_publisher)
    evt.add_listener(EventID.g_account_expired, account_expire_event_publisher)
    evt.add_listener(EventID.g_daf_shutdown, shutdown_event_publisher)
    evt.add_listener(EventID.g_daf_shutdown, ws.close)

    async for message in ws:
        if message.type == WSMsgType.CLOSE:
            await ws.close()

    evt.remove_listener(EventID.g_trace, trace_event_publisher)
    evt.remove_listener(EventID.g_account_expired, account_expire_event_publisher)
    evt.remove_listener(EventID.g_daf_shutdown, shutdown_event_publisher)
    evt.remove_listener(EventID.g_daf_shutdown, ws.close)
    return ws
