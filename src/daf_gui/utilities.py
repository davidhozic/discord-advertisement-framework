"""
Contains common utilities
"""
from typing import Awaitable


import ttkbootstrap.dialogs.dialogs as tkdiag

import asyncio


async def run_coro_gui_errors(coro: Awaitable, origin=None):
    try:
        await coro
    except asyncio.QueueEmpty:
        raise
    except Exception as exc:
        tkdiag.Messagebox.show_error(str(exc), "Coroutine error", origin)
