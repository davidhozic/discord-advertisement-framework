"""
Description:
This is an example of an additional application layer you can build with this framework.
The application sends a message saying 'Good morning' every day at 10 AM and then sends a picture of a coffe cup from a randomized list.
"""
import  framework as fw
import app.app





servers = [
    fw.GUILD(
        guild_id=123456789,
        messages_to_send=[

            fw.MESSAGE(start_period=None, end_period=10, data=app.app.get_data(), channel_ids=[123456789], clear_previous=False, start_now=True)
        ],
        generate_log=True
    )
]


############################################################################################
fw.run(  token="YOUR TOKEN", server_list=servers)
                    
    