from datetime import timedelta
import daf
import asyncio


async def main():
    await daf.add_object(
        daf.GUILD(
            snowflake=123456789,
            messages=[
                daf.TextMESSAGE(
                    None, timedelta(seconds=5), "Hello World",
                    channels=daf.message.AutoCHANNEL("shill", exclude_pattern="shill-[7-9]")
                )
            ],
            logging=True
        )
    )


daf.run(
    token="SomeServerTokenHere",
    user_callback=main,
)