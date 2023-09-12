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

    def dummy_listener(**kwargs):
        nonlocal handler_called
        handler_called = True

    handler_called = False
    daf.add_listener(event, dummy_listener)
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.001)
    assert handler_called, "Handler was not called"

    handler_called = False
    daf.remove_listener(event, dummy_listener)
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.001)
    assert not handler_called, "Handler was called"

    @daf.listen(event)
    def dummy_listener(**kwargs):
        nonlocal handler_called
        handler_called = True

    handler_called = False
    daf.emit(event, **expected_args)
    await asyncio.sleep(0.001)
    assert handler_called, "Handler was not called"
