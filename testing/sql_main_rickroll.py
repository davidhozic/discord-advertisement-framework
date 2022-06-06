import framework as fw
import secret

rolls = [
    "https://i.pinimg.com/originals/b7/fb/80/b7fb80122cf46d0e584f3a0768aef282.gif",
    "https://bit.ly/3sHrjQZ",
    "https://static.wikia.nocookie.net/a1dea591-8a10-4c02-a573-5321c601c129",
    "https://www.gifcen.com/wp-content/uploads/2022/03/rickroll-gif-4.gif",
    "https://bit.ly/3u5D8Dt",
    "http://static1.squarespace.com/static/60503ac20951e15087fbe7b8/60504609ee9c445722c9dd4e/60e3f9b541eb1b01e8e46854/1627103366283/RalphRoll.gif?format=1500w",
    "https://i.imgflip.com/56bhvt.gif",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
]

@fw.data_function
def get(st):
    item = st.pop(0)
    st.append(item)
    return item

servers = [
    fw.GUILD(
        guild_id=12345,
        messages_to_send=[
            fw.TextMESSAGE(None, 5, get(rolls.copy()), [12345], "edit", True)
        ],
        generate_log=True
    )
]


fw.run(
    token=secret.C_TOKEN,
    is_user=False, 
    server_list=servers,
    sql_manager=fw.LoggerSQL("username", "password", "server address", "database name") # *Note: The database must be created manually,
                                                                                        #  everything else in the database is then created automatically
)