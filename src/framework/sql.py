"""
    ~    sql    ~
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
from  datetime   import datetime
from  typing     import Literal
from requests import Session
from  sqlalchemy import JSON, BigInteger, Column, Identity, Integer, String, DateTime,ForeignKey, create_engine, text
from  sqlalchemy.orm import sessionmaker
from  sqlalchemy.ext.declarative import declarative_base
from  sqlalchemy_utils import create_database, database_exists
from  .tracing import *

__all__ = (
    "LOGGERSQL",
    "register_type",
    "get_sql_manager"
)


class GLOBALS:
    manager  = None
    enabled  = False
    lt_types = []

def register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]):
    """
    ~ Decorator ~
    @Name: register_type
    @Info:
        This is a function that returns a decorator which will create a row inside
        <lookuptable> table. The name of the inserted item is defined with the __logname__ variable
        which must be present in each framework class that is to be added to the lookuptable.
        The __logname__ also defines the object type name inside text logs (and sql).
    @Params:
        lookuptable: str :: Name of the lookup table to insert the value into
    """
    def _register_type(cls):
        # Iterate thru all module globals to find the lookup table
        # and insert a row into that lookup table (name of the type is defined with __logname__)
        for item, value in globals().items():
            if item == lookuptable:
                GLOBALS.lt_types.append( value(cls.__logname__) )
                return cls
        trace(f"Unable to to find lookuptable: {lookuptable}", TraceLEVELS.ERROR)
        return cls
    return _register_type


class LOGGERSQL:
    """
    ~ class ~
    @Name: LOGGERSQL
    @Info: This class is used for controlling
           the SQL database used for messagge logs
    @Param:
        username: str :: Username to login to the database with
        password: str :: Password to use when logging into the database
        server  : str :: Address of the SQL server
        database: str :: Name of the database used for logs"""

    Base = declarative_base()
    __slots__ = (
        "__engine",
        "Session",
        "commit_buffer",
        "username",
        "__password",
        "server",
        "database"
    )

    def __init__(self,
                 username: str,
                 password: str,
                 server: str,
                 database: str):
        # Save the connection parameters
        self.username = username
        self.__password = password
        self.server = server
        self.database = database
        self.commit_buffer = []
        self.__engine = None
        self.Session  = None

    def initialize(self):
        """
        ~ Method ~
        @Name: initialize
        @Info: This method initializes the connection to the database, creates the missing tables
               and fills the lookuptables with types defined by the register_type(lookup_table) function.
        @Param: void"""
        # Create engine for communicating with the SQL base
        try:
            self.__engine = create_engine(f"mssql+pymssql://{self.username}:{self.__password}@{self.server}/{self.database}", echo=False)
            if not database_exists(self.__engine.url):
                create_database(self.__engine.url)
        except Exception as ex:
            trace(f"Unable to start SQL engine. Reason:\n{ex}", TraceLEVELS.ERROR)
            return False
        # Create tables and the session class bound to the engine
        try:
            self.Base.metadata.create_all(bind=self.__engine)
            self.Session = sessionmaker(bind=self.__engine)
        except Exception as ex:
            trace(f"Unable to create all the SQL Tables. Reason:\n{ex}", TraceLEVELS.ERROR)
            return False
        # Insert the lookuptable values
        try:
            with self.Session() as session:
                for to_add in GLOBALS.lt_types:
                    existing = session.query(type(to_add)).filter(type(to_add).name == to_add.name).first()
                    if existing is None:
                        session.add(to_add)
                session.commit()
        except Exception as ex:
            trace(f"Unable to create lookuptables' rows. Reason: {ex}", TraceLEVELS.ERROR)
        # Initialize views, procedures and functions
        try:
            stms = [ # list of dictionaries containing "select" which is the statement to return the item with the view, procedure name we are adding,
                     # and "stm" which is the statement used to create view, procedure, which is concatenated to CREATE or ALTER 
                {
                "select" : r"SELECT * FROM ProjektDH.sys.procedures WHERE name = 'spFilterChannelSuccess'",
                "stm"    : "PROCEDURE spFilterChannelSuccess(@min INT, @max INT) AS BEGIN SELECT * FROM (SELECT *, 	(100*CAST((SELECT COUNT(*) FROM OPENJSON(SuccessInfo, '$.successful')) AS real)/ 	((SELECT COUNT(*) FROM OPENJSON(SuccessInfo, '$.failed')  WHERE MessageTYPE != 'DirectMESSAGE')+(SELECT COUNT(*) FROM OPENJSON(SuccessInfo, '$.successful') WHERE MessageTYPE != 'DirectMESSAGE'))) relativeSuccess 	FROM vMessageLogFullDETAIL 	WHERE MessageTYPE != 'DirectMESSAGE') a 	WHERE relativeSuccess >= @min   AND relativeSuccess <= @max; END"
                },
                {
                "select" : r"SELECT * FROM ProjektDH.INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'vMessageLogFullDETAIL'",
                "stm"    : "VIEW vMessageLogFullDETAIL AS SELECT ml.ID, ml.sent_data SentData, mt.name MessageTYPE, ml.guild_snowflakeID GuildSnowflake, mm.name MessageMode, ml.success_info SuccessInfo, ml.[timestamp] [Timestamp] FROM MessageLOG ml JOIN MessageTYPE mt ON ml.message_type  = mt.ID JOIN GuildTYPE gt ON gt.ID = ml.guild_type JOIN MessageMODE mm ON mm.ID = ml.message_mode;"
                }
            ]
            with self.Session() as session:
                for s in stms:
                    if session.execute(text(s["select"])).first() is None:
                        session.execute(text("CREATE " + s["stm"] ))
                    else:
                        session.execute(text("ALTER " + s["stm"] ))
                session.commit()
        except Exception as ex:
            trace(f"Unable to create views, procedures and functions. Reason: {ex}", TraceLEVELS.ERROR)

        return True

    def save_log(self,
                 guild_context: dict,
                 message_context: dict):
        """
        ~ Method ~
        @Name: save_log
        @Info: This method saves the log generated by
               the xGUILD object into the database
        @Param:
            guild_context: dict     ::  Context generated by the xGUILD object,
                                        see guild.xGUILD.generate_log() for more info
            message_context: dict   ::  Context generated by the xMESSAGE object,
                                        see guild.xMESSAGE.generate_log_context() for more info"""

        log_object = MessageLOG(sent_data=message_context.pop("sent_data"),
                                guild_snowflake=guild_context.pop("id"))

        guild_type: str = guild_context.pop("type")
        message_type: str = message_context.pop("type")
        message_mode = message_context.pop("mode", None)
        channels = message_context.pop("channels", None)
        dm_success_info = message_context.pop("success_info", None)

        with self.Session() as session:
            guild_type = session.query(GuildTYPE).filter(GuildTYPE.name == guild_type).first()
            log_object.guild_type = guild_type.ID

            message_type = session.query(MessageTYPE).filter(MessageTYPE.name == message_type).first()
            log_object.message_type = message_type.ID

            if message_mode is not None:
                message_mode = session.query(MessageMODE).filter(MessageMODE.name == message_mode).first()
                log_object.message_mode = message_mode.ID
            else:
                log_object.message_mode = None

            if channels is not None:
                log_object.success_info = channels
            else:
                log_object.success_info = dm_success_info

            session.add(log_object)
            session.commit()


class MessageTYPE(LOGGERSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageTYPE
    @Info: Lookup table for storing xMESSAGE types
    @Param:
        name: Name of the xMESSAGE class"""
    __tablename__ = "MessageTYPE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildTYPE(LOGGERSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: GuildTYPE
    @Info: Lookup table for storing xGUILD types
    @Param:
        name: Name of the xGUILD class"""

    __tablename__ = "GuildTYPE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class MessageMODE(LOGGERSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageMODE
    @Info: Lookup table for storing different message send modes [TextMESSAGE, DirectMESSAGE]
    @Param:
        name: Name of the mode"""

    __tablename__ = "MessageMODE"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class MessageLOG(LOGGERSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageLOG
    @Info: The logging table containing information for each message send attempt.
           NOTE: This table is missing successful and failed channels (or DM success status)
                  that is because those are a seperate table
    @Param:
        sent_data: str          :: JSONized data that was sent by the xMESSAGE object
        message_type: int       :: ID pointing to a row inside the MessageTYPE lookup table
        message_mode: int       :: ID pointing to a row inside the MessageMODE lookup table
        guild_snowflake: int    :: Discord's snowflake identificator descripting the guild object (or user)
        guild_type: int         :: ID pointing to a row inside the GuildTYPE lookup table"""

    __tablename__ = "MessageLOG"
    ID = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    sent_data = Column(JSON)
    message_type = Column(Integer, ForeignKey("MessageTYPE.ID", ))
    guild_snowflakeID = Column(BigInteger)
    message_mode = Column(Integer(), ForeignKey("MessageMODE.ID", )) # Only for TextMESSAGE and DirectMESSAGE
    success_info  = Column(JSON)
    guild_type = Column(Integer(), ForeignKey("GuildTYPE.ID"))
    timestamp = Column(DateTime())

    def __init__(self,
                 sent_data: str=None,
                 message_type: int=None,
                 message_mode: int=None,
                 success_info: str=None,
                 guild_snowflake: int=None,
                 guild_type: int=None):
        self.sent_data = sent_data
        self.message_type = message_type
        self.message_mode = message_mode
        self.guild_snowflakeID = guild_snowflake
        self.success_info = success_info
        self.guild_type = guild_type
        self.timestamp = datetime.now().replace(microsecond=0)

def initialize(mgr_object: LOGGERSQL) -> bool:
    """
    ~ function ~
    @Name: initialize
    @Info: This function initializes the sql manager and also the selected database
           NOTE: If initialization fails, file logs will be used
    @Param:
        mgr_object: LOGGERSQL :: SQL database manager object responsible for saving the logs
                                 into the SQL database"""

    GLOBALS.manager = mgr_object
    if type(GLOBALS.manager) is LOGGERSQL and GLOBALS.manager.initialize():
        GLOBALS.enabled = True
        return True

    trace("Unable to setup SQL logging, file logs will be used instead.", TraceLEVELS.WARNING)
    return False


def get_sql_manager() -> LOGGERSQL:
    return GLOBALS.manager