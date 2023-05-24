"""
Module contains definitions related to remote access from a graphical interface.
"""
from typing import Optional, Literal, Coroutine
from contextlib import suppress

from aiohttp.web import (
    Response, Request, RouteTableDef, Application, _run_app, json_response,
    HTTPException, HTTPInternalServerError
)

from . import convert

import asyncio

import daf

__all__ = ("RemoteAccessCLIENT",)


class GLOBALS:
    routes = RouteTableDef()
    http_task: asyncio.Task = None


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
                json_data = await request.json()
                return await fnc(**json_data["parameters"])
            except HTTPException:
                raise  # Don't wrap already HTTP exceptions

            except Exception as exc:
                raise HTTPInternalServerError(reason=str(exc))

        return getattr(GLOBALS.routes, type.lower())(path)(request_wrapper)

    return decorator


class RemoteAccessCLIENT:
    """
    Client used for processing remote requests from a GUI located on a different network.

    Parameters
    ---------------
    host: Optional[str]
        The host address. Defaults to ``0.0.0.0``.
    port: Optional[int]
        The http port. Defaults to ``80``.
    username: Optional[str]
        The basic authorization username. Defaults to ``None``.
    password: Optional[str]
        The basic authorization password. Defaults to ``None``.
    """
    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = 80,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.web_app = Application()
        self.web_app.add_routes(GLOBALS.routes)

    async def initialize(self):
        GLOBALS.http_task = asyncio.create_task(
            _run_app(self.web_app, host=self.host, port=self.port, print=False)
        )

    async def _close(self):
        await self.web_app.shutdown()
        await self.web_app.cleanup()
        task = GLOBALS.http_task
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@register("/ping", "GET")
async def http_ping():
    return create_json_response(message="pong")


@register("/logging", "GET")
async def http_get_logger():
    return create_json_response(logger=convert.convert_object_to_semi_dict(daf.get_logger()))


@register("/object", "GET")
async def http_get_object(object_id: int):
    object = daf.misc.get_by_id(object_id)
    if object is None:
        raise HTTPInternalServerError(reason="Object not present in DAF.")

    return create_json_response(object=convert.convert_object_to_semi_dict(object))


@register("/method", "POST")
async def http_execute_method(object_id: int, method_name: str, **kwargs):
    object = daf.misc.get_by_id(object_id)
    if object is None:
        raise HTTPInternalServerError(reason="Object not present in DAF.")

    try:
        result = getattr(object, method_name)(**convert.convert_from_semi_dict(kwargs, True))
        if isinstance(result, Coroutine):
            result = await result

    except Exception as exc:
        raise HTTPInternalServerError(reason=f"Error executing method {method_name}. ({exc})")

    return create_json_response(f"Executed method {method_name}.", result=convert.convert_object_to_semi_dict(result))
