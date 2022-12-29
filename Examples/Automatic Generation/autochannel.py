from datetime import timedelta
import daf


async def main():
    await daf.add_object(
        daf.ACCOUNT(
            token="SomeToken",
            is_user=False,
            servers=[
                daf.GUILD(snowflake=123456789,
                          messages=[
                                daf.TextMESSAGE(None, timedelta(seconds=5), "Hello World", channels=daf.message.AutoCHANNEL("shill", exclude_pattern="shill-[7-9]"))
                            ],
                          logging=True) 
            ]
        )
    )


daf.run(
    user_callback=main,
)