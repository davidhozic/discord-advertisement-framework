"""
Module contains definitions related to remote access from a graphical interface.
"""
from typing import Optional, Literal
from contextlib import suppress

from aiohttp import web as aiohttp_web

import asyncio


class GLOBALS:
    routes = aiohttp_web.RouteTableDef()
    http_task: asyncio.Task = None


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
    return getattr(GLOBALS.routes, type.lower())(path)


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

        self.web_app = aiohttp_web.Application()
        self.web_app.add_routes(GLOBALS.routes)
        self.runner = None
        self.sites = []

    async def initialize(self):
        GLOBALS.http_task = asyncio.create_task(
            aiohttp_web._run_app(self.web_app, host=self.host, port=self.port, print=False)
        )

    async def _close(self):
        await self.web_app.shutdown()
        await self.web_app.cleanup()
        task = GLOBALS.http_task
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
