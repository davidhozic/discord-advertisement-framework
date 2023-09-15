from datetime import timedelta

import daf
import pytest
import asyncio


@pytest.mark.parametrize(
        "event, expected_args",
        [
            (daf.EventID.daf_startup, {}),
            (daf.EventID.daf_shutdown, {}),
            (
                daf.EventID.message_ready,
                {"message": daf.TextMESSAGE(None, timedelta(seconds=5), "Hello World", daf.AutoCHANNEL("test"))}
            ),
        ]
)
async def test_events(event: daf.EventID, expected_args: dict):
    handler_called = True
    handler_called2 = True

    def dummy_listener(*args, **kwargs):
        nonlocal handler_called
        handler_called = True

    def dummy_listener2(*args, **kwargs):
        nonlocal handler_called2
        handler_called2 = True

    handler_called = False
    daf.add_listener(event, dummy_listener)
    daf.add_listener(event, dummy_listener2)
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.01)
    assert handler_called and handler_called2, "Handler was not called"

    handler_called = False
    handler_called2 = False
    daf.remove_listener(event, dummy_listener)
    daf.remove_listener(event, dummy_listener2)
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.01)
    assert not (handler_called or handler_called2), "Handler was called"

    @daf.listen(event)
    def dummy_listener(*args, **kwargs):
        nonlocal handler_called
        handler_called = True

    @daf.listen(event)
    def dummy_listener2(*args, **kwargs):
        nonlocal handler_called2
        handler_called2 = True

    handler_called = False
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.01)
    daf.remove_listener(event, dummy_listener)
    daf.remove_listener(event, dummy_listener2)
    assert handler_called and handler_called2, "Handler was not called"

