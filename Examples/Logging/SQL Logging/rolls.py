from datetime import timedelta
import daf

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

@daf.data_function
def get(st):
    item = st.pop(0)
    st.append(item)
    return item

accounts = [
    daf.ACCOUNT( token="SDASKDKLSADJKLSDJ",
                 is_user=False,
                 servers=[ 
                    daf.GUILD(12345, [daf.TextMESSAGE(None, timedelta(seconds=5), get(rolls.copy()), [12345], "edit")], True) 
                  ] )
]



daf.run(
    #logger=daf.LoggerSQL(dialect="mysql", username="user", password="pass", database="TestDB", server="127.0.0.1"),
    logger=daf.LoggerSQL(dialect="postgresql", username="postgres", password="pass", database="TestDB", server="127.0.0.1"),
    #logger=daf.LoggerSQL(dialect="mssql", username="sa", password="pass", database="TestDB", server="127.0.0.1"),
    #logger=daf.LoggerSQL(dialect="sqlite", database="testdb"),
    accounts=accounts
)
