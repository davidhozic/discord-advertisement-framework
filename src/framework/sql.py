"""
    ~    sql    ~
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
from    datetime import datetime
from    sqlalchemy import JSON, BigInteger, Column, Identity, Integer, String, DateTime,ForeignKey, null
from    sqlalchemy.ext.declarative import declarative_base
from    sqlalchemy import create_engine
from    sqlalchemy.orm import sessionmaker
from    .tracing import *

class LOGGERSQL:
    Base = declarative_base()
    __slots__ = (
        "__engine",
        "Session"
    )

    def __init__(self,
                 username: str,
                 password: str,
                 server: str,
                 database: str):
        self.__engine = create_engine(f"mssql+pymssql://{username}:{password}@{server}/{database}", echo=True)
        self.Base.metadata.create_all(bind=self.__engine)
        self.Session = sessionmaker(bind=self.__engine)

    def save_log(self,
                 guild_context: dict,
                 message_context: dict):

        log_object = MessageLOG(sent_data=message_context.pop("sent_data"),
                                guild_snowflake=guild_context.pop("id"))

        guild_type: str = guild_context.pop("type")
        message_type: str = message_context.pop("type")
        message_mode = message_context.pop("mode", None)

        channels = message_context.pop("channels", None)
        successful_ch = None
        failed_ch     = None
        if channels is not None:
            successful_ch = []
            failed_ch = []
            for channel in channels["successful"]:
                successful_ch.append(MsgLogSuccCHANNEL(channel["id"], NotImplemented))
            for channel in channels["failed"]:
                failed_ch.append(MsgLogFailCHANNEL(channel["id"], NotImplemented, channel["reason"]))

        with self.Session() as session:
            guild_type = session.query(GuildTYPE).filter(GuildTYPE.name == guild_type).first()
            log_object.guild_type = guild_type.ID

            message_type = session.query(MessageTYPE).filter(MessageTYPE.name == message_type).first()
            log_object.message_type = message_type.ID

            if message_mode is not None:
                message_mode = session.query(MessageSendMODE).filter(MessageSendMODE.name == message_mode).first()
                log_object.message_mode = message_mode.ID
            else:
                log_object.message_mode = null

            session.add(log_object)

            if channels is not None:
                log_object = session.query(MessageLOG).order_by(MessageLOG.ID.desc()).first()
                for channel in successful_ch + failed_ch:
                    channel.MessageLogID = log_object.ID

                session.add_all(successful_ch+failed_ch)

            session.commit()



class MessageTYPE(LOGGERSQL.Base):
    __tablename__ = "MessageTYPE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildTYPE(LOGGERSQL.Base):
    __tablename__ = "GuildTYPE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class MessageSendMODE(LOGGERSQL.Base):
    __tablename__ = "MessageSendMODE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class MsgLogSuccCHANNEL(LOGGERSQL.Base):
    __tablename__ = "MsgLogSuccCHANNEL"
    SnowflakeID = Column(BigInteger, primary_key=True)
    MessageLogID = Column(Integer, ForeignKey("MessageLOG.ID", ondelete="CASCADE"), primary_key=True)

    def __init__(self, snowflake: int=None, message_log_id: int=None):
        self.SnowflakeID = snowflake
        self.MessageLogID = message_log_id


class MsgLogFailCHANNEL(LOGGERSQL.Base):
    __tablename__ = "MsgLogFailCHANNEL"
    SnowflakeID = Column(BigInteger, primary_key=True)
    MessageLogID = Column(Integer, ForeignKey("MessageLOG.ID", ondelete="CASCADE"), primary_key=True)
    reason = Column(String())

    def __init__(self, snowflake: int=None, message_log_id: int=None, reason: str=None):
        self.SnowflakeID = snowflake
        self.MessageLogID = message_log_id
        self.reason = reason


class MessageLOG(LOGGERSQL.Base):
    __tablename__ = "MessageLOG"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    sent_data = Column(JSON)
    message_type = Column(Integer, ForeignKey("MessageTYPE.ID", ))
    message_mode = Column(Integer, ForeignKey("MessageSendMODE.ID", ))
    guild_snowflakeID = Column(BigInteger)
    guild_type = Column(Integer, ForeignKey("GuildTYPE.ID"))
    timestamp = Column(DateTime)

    def __init__(self,
                 sent_data: str=None,
                 message_type: int=None,
                 message_mode: int=None,
                 guild_snowflake: int=None,
                 guild_type: int=None):
        self.sent_data = sent_data
        self.message_type = message_type
        self.message_mode = message_mode,
        self.guild_snowflakeID = guild_snowflake
        self.guild_type = guild_type
        self.timestamp = datetime.now()

#############################
# TESTING
############################
# async def main():
#     control = LOGGERSQL("sa","Security1","212.235.190.203", "ProjektDH")
#     with control.Session() as session:
#         with open("test.json", 'r', encoding='utf-8') as file:
#             data = json.load(file)
#         new = MessageTYPE(type="TextMESSAGE")
#         session.add(new)
#         session.commit()
#         new = MessageSendMODE(mode="edit")
#         session.add(new)
#         session.commit()

#         new = MessageLOG(sent_data=data, message_type=0, message_mode=0, guild_snowflake=863071397207212052)
#         session.add(new)
#         session.commit()

#         test = session.query(MessageLOG).filter(MessageLOG.ID.between(0, 5))
#         pass
#     pass

# if __name__ == "__main__":
#     asyncio.run(main())
