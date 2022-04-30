"""
    ~    sql    ~
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
from  datetime   import datetime
import enum
from  typing     import Literal
from  sqlalchemy import (
                         JSON, SmallInteger, Integer, BigInteger, String, DateTime, Boolean,
                         Column, Identity, ForeignKey,
                         create_engine, text
                        )
from  sqlalchemy.orm import sessionmaker
from  sqlalchemy.ext.declarative import declarative_base
from  sqlalchemy_utils import create_database, database_exists
from  .tracing import *
import time

__all__ = (
    "LoggerSQL",
    "register_type",
    "get_sql_manager"
)


def timeit(fn):
    def _runner(*arg, **kwarg):
        startms = time.time()
        ret = fn(*arg, **kwarg)
        endmsg = time.time()
        print(f"Ran for {(endmsg - startms)*1000}")
        return ret
    return _runner


class GLOBALS:
    """~ class ~
    @Name: GLOBALS
    @Info: Stores global module variables """
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
        for lt_name, lt_cls in globals().items():
            if lt_name == lookuptable:
                GLOBALS.lt_types.append( lt_cls(cls.__logname__) )
                return cls
        raise Exception(f"[SQL]: Unable to to find lookuptable: {lookuptable}")
    return _register_type


class LoggerSQL:
    """
    ~ class ~
    @Name: LoggerSQL
    @Info: This class is used for controlling
           the SQL database used for messagge logs
    @Param:
        username: str :: Username to login to the database with
        password: str :: Password to use when logging into the database
        server  : str :: Address of the SQL server
        database: str :: Name of the database used for logs"""

    Base = declarative_base()
    __slots__ = (
        "engine",
        "Session",
        "commit_buffer",
        "username",
        "__password",
        "server",
        "database",

        "MessageMODE",
        "MessageTYPE",
        "GuildTYPE"
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
        self.engine = None
        self.Session  = None
        self.MessageMODE = {}
        self.MessageTYPE = {}
        self.GuildTYPE   = {}

    def create_analytic_objects(self):
        """
        ~ Method ~
        @Name: create_analytic_objects
        @Info: Creates Stored Procedures, Views and Functions via SQL code.
               The method iterates thru a list, first checking if the object exists
                -> if it does exist, it uses ALTER + "stm", if it doesn't exist,
                   it uses CREATE + "stm" command to create the object inside the SQL database.
        @Param: void"""
        stms = [
            {   "name" :   "vMessageLogFullDETAIL",
                "stm"    : """
                            VIEW {} AS
                                SELECT ml.id id, ml.sent_data SentData, mt.name MessageTYPE, gt.name GuildTYPE , gu.snowflake_id GuildID, gu.name GuildName, mm.name MessageMode, ml.dm_success DMSuccess, ml.dm_reason DMReason, ml.[timestamp] [Timestamp]
                                FROM MessageLOG ml JOIN MessageTYPE mt ON ml.message_type  = mt.id
                                LEFT JOIN MessageMODE mm ON mm.id = ml.message_mode
                                JOIN GuildUSER gu ON gu.id = ml.guild_id
                               	JOIN GuildTYPE gt ON gu.guild_type = gt.id ;"""
            },
            {
                "name": "fnRelativeSuccess",
                "stm": """FUNCTION {}(@log_id smallInt) RETURNS real AS
                          -- Returns relative number of successful channels vs all channels
                                BEGIN
                                    DECLARE @ret real;
                                    SELECT @ret = 100*CAST(successful as REAL) / all_ch
                                    FROM
                                    (
                                        SELECT SUM(CASE WHEN reason IS NULL THEN 1 ELSE 0 END) successful, COUNT(channel_id) all_ch
                                        FROM MessageChannelLOG mlc
                                        WHERE log_id = @log_id 
                                        GROUP BY log_id
                                    ) a;
                                    RETURN @ret;
                                END"""
            },
            {
                "name" : "spFilterBySuccessRate",
                "stm" : """PROCEDURE {}(@min tinyint, @max tinyint)
                           --  Returns TextCHANNEL and VoiceCHANNEL logs where 100*succeeded_channels/all_channels is [@min, @max]
                            AS
                            BEGIN 
                                SELECT *
                                FROM MessageChannelLOG mcl FULL JOIN MessageLOG ml ON mcl.log_id = ml.id 
                                WHERE dbo.fnRelativeSuccess(log_id) IN (@min, @max);	
                            END"""
            }
        ]
        with self.Session() as session:
            for statement in stms:
                # Union the 2 system tables containing views and procedures/functions, then select only the element that matches the item we want to create, it it returns None, it doesnt exist
                if session.execute(text(f"SELECT * FROM (SELECT SPECIFIC_NAME AS Name  FROM INFORMATION_SCHEMA.ROUTINES UNION SELECT TABLE_NAME AS Name  FROM INFORMATION_SCHEMA.VIEWS) a WHERE Name= '{statement['name']}'")).first() is None:
                    session.execute(text("CREATE " + statement["stm"].format(statement["name"]) ))
                else:
                    session.execute(text("ALTER " + statement["stm"].format(statement["name"]) ))

            session.commit()

    def initialize(self):
        """
        ~ Method ~
        @Name: initialize
        @Info: This method initializes the connection to the database, creates the missing tables
               and fills the lookuptables with types defined by the register_type(lookup_table) function.
        @Param: void"""
        # Create engine for communicating with the SQL base
        try:
            self.engine = create_engine(f"mssql+pymssql://{self.username}:{self.__password}@{self.server}/{self.database}", echo=False)
            self.Session = sessionmaker(bind=self.engine)
            if not database_exists(self.engine.url):
                trace("[SQL]: Creating database...", TraceLEVELS.NORMAL)
                create_database(self.engine.url)
        except Exception as ex:
            trace(f"[SQL]: Unable to start engine. Reason:\n{ex}", TraceLEVELS.ERROR)
            return False
        # Create tables and the session class bound to the engine
        try:
            trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
            self.Base.metadata.create_all(bind=self.engine)
        except Exception as ex:
            trace(f"[SQL]: Unable to create all the tables. Reason:\n{ex}", TraceLEVELS.ERROR)
            return False
        # Insert the lookuptable values
        try:
            trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
            with self.Session() as session:
                for to_add in GLOBALS.lt_types:
                    existing = session.query(type(to_add)).filter_by(name=to_add.name).first()
                    if existing is None:
                        session.add(to_add)
                        existing = session.query(type(to_add)).filter_by(name=to_add.name).first()
                    
                    getattr(self, type(to_add).__name__)[to_add.name] = existing.id # Set the internal lookup values to later prevent time consuming queries
                
                session.commit()
        except Exception as ex:
            trace(f"[SQL]: Unable to create lookuptables' rows. Reason: {ex}", TraceLEVELS.ERROR)
            return False
        # Initialize views, procedures and functions
        try:
            trace("[SQL]: Creating Views, Procedures & Functions", TraceLEVELS.NORMAL)
            self.create_analytic_objects()
        except Exception as ex:
            trace(f"[SQL]: Unable to create views, procedures and functions. Reason: {ex}", TraceLEVELS.ERROR)

        return True
    @timeit
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

        sent_data = message_context.pop("sent_data")
        guild_snowflake = guild_context.pop("id")
        guild_name = guild_context.pop("name")
        guild_type: str = guild_context.pop("type")
        message_type: str = message_context.pop("type")
        message_mode = message_context.pop("mode", None)
        channels = message_context.pop("channels", None)
        dm_success_info = message_context.pop("success_info", None)

        log_object = MessageLOG(sent_data=sent_data)
        # Add DirectMESSAGE success information
        if dm_success_info is not None:
            log_object.dm_success = dm_success_info["success"]
            if not log_object.dm_success:
                log_object.dm_reason = dm_success_info["reason"]

        with self.Session() as session:
            # Map MessageTYPE to an identificator
            log_object.message_type = self.MessageTYPE[message_type]
 
            if message_mode is not None:
                # If message_mode exists [DirectMESSAGE and TextMESSAGE] then map the message_mode to an identificator
                log_object.message_mode = self.MessageMODE[message_mode]
            else:
                log_object.message_mode = None

            # Update GUILD/USER table
            result = session.query(GuildUSER).filter(GuildUSER.snowflake_id == guild_snowflake).first()
            if result is None:
                guild_type = self.GuildTYPE[guild_type]
                result = GuildUSER(guild_type, guild_snowflake, guild_name)
                session.add(result)
                session.flush()

            # Reference the guild_id with id from GuildUSER lookup table
            guild_lookup = result.id
            log_object.guild_id = guild_lookup

            # Save the message log
            session.add(log_object)
            if channels is not None:
                # If channels exist [TextMESSAGE and VoiceMESSAGE], update the CHANNELS table with the correct name
                # and only insert the channel Snowflake identificators into the message log
                channels = channels["successful"] + channels["failed"]
                channels_snow = [x["id"] for x in channels]

                result = session.query(CHANNEL).filter(CHANNEL.snowflake_id.in_(channels_snow)).all()
                result_snow = {x.snowflake_id for x in result}  # Snowflakes returned by querry
                for channel in channels:
                    if channel["id"] not in result_snow:
                        item = CHANNEL(channel["id"], channel["name"], guild_lookup) 
                        session.add(item)
                        result.append(item)

                session.flush()
                to_add = []
                for channel in result:
                    index = channels_snow.index(channel.snowflake_id)
                    to_add.append(MessageChannelLOG(log_object.id, channel.id, channels[index].pop("reason", None) ) )

                session.add_all(to_add)

            session.commit()


class MessageTYPE(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageTYPE
    @Info: Lookup table for storing xMESSAGE types
    @Param:
        name: Name of the xMESSAGE class"""
    __tablename__ = "MessageTYPE"
    
    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildTYPE(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: GuildTYPE
    @Info: Lookup table for storing xGUILD types
    @Param:
        name: Name of the xGUILD class"""

    __tablename__ = "GuildTYPE"
    
    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildUSER(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: GUILD
    @Info: Guild
    @Param: Table that represents GUILD and USER object inside the database
        snowflake: int :: Snowflake identificator of the guild/user
        name: str      :: Name of the guild/user"""

    __tablename__ = "GuildUSER"
    
    id = Column(SmallInteger, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(String)
    guild_type = Column(SmallInteger, ForeignKey("GuildTYPE.id"))

    def __init__(self,
                 guild_type: int,
                 snowflake: int,
                 name: str):
        self.snowflake_id = snowflake
        self.name = name
        self.guild_type = guild_type


class CHANNEL(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: CHANNEL
    @Info: Maps the snowflake id to a name and GUILD id
    @Param:
        snowflake: int :: Snowflake identificator
        name: str      :: Name of the channel
        guild_id: int  :: Snowflake identificator pointing to a GUILD/USER"""

    __tablename__ = "CHANNEL"
    id = Column(SmallInteger, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(String)
    guild_id = Column(SmallInteger, ForeignKey("GuildUSER.id", ondelete="CASCADE"))

    def __init__(self,
                 snowflake: int,
                 name: str,
                 guild_id: int):
        self.snowflake_id = snowflake
        self.name = name
        self.guild_id = guild_id


class MessageMODE(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageMODE
    @Info: Lookup table for storing different message send modes [TextMESSAGE, DirectMESSAGE]
    @Param:
        name: Name of the mode"""

    __tablename__ = "MessageMODE"
    
    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(String(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class MessageLOG(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageLOG
    @Info: The logging table containing information for each message send attempt.
           NOTE: This table is missing successful and failed channels (or DM success status)
                  that is because those are a seperate table
    @Param:
        sent_data: str          :: JSONized data that was sent by the xMESSAGE object
        message_type: int       :: id pointing to a row inside the MessageTYPE lookup table
        message_mode: int       :: id pointing to a row inside the MessageMODE lookup table
        guild_snowflake: int    :: Discord's snowflake identificator descripting the guild object (or user)
        guild_type: int         :: id pointing to a row inside the GuildTYPE lookup table"""

    __tablename__ = "MessageLOG"
    
    id = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    sent_data = Column(JSON)
    message_type = Column(SmallInteger, ForeignKey("MessageTYPE.id", ))
    guild_id =     Column(SmallInteger, ForeignKey("GuildUSER.id", ondelete="CASCADE"))
    message_mode = Column(SmallInteger, ForeignKey("MessageMODE.id" )) # [TextMESSAGE, DirectMESSAGE]
    dm_success  = Column(Boolean) # [DirectMESSAGE]
    dm_reason   = Column(String)  # [DirectMESSAGE]
    timestamp = Column(DateTime)

    def __init__(self,
                 sent_data: str=None,
                 message_type: int=None,
                 message_mode: int=None,
                 dm_success: tuple=(None, None),
                 guild_id: int=None):
        self.sent_data = sent_data
        self.message_type = message_type
        self.message_mode = message_mode
        self.guild_id = guild_id
        self.dm_success, self.dm_reason = dm_success
        self.timestamp = datetime.now().replace(microsecond=0)


class MessageChannelLOG(LoggerSQL.Base):
    """
    ~ SQL Table Descriptor Class ~
    @Name: MessageChannelLOG
    @Info: This is a table that contains a log of channels that are
           linked to a certain message log.
    @Param:
        name: Name of the mode"""

    __tablename__ = "MessageChannelLOG"
    
    log_id = Column(Integer, ForeignKey("MessageLOG.id", ondelete="CASCADE"), primary_key=True)
    channel_id = Column(SmallInteger, ForeignKey("CHANNEL.id"), primary_key=True)
    reason = Column(String)
    def __init__(self,
                 message_log_id: int,
                 channel_id: int,
                 reason: str=None):
        self.log_id = message_log_id
        self.channel_id = channel_id
        self.reason = reason


def initialize(mgr_object: LoggerSQL) -> bool:
    """~ function ~
    @Name: initialize
    @Info: This function initializes the sql manager and also the selected database
           NOTE: If initialization fails, file logs will be used
    @Param:
        mgr_object: LoggerSQL :: SQL database manager object responsible for saving the logs
                                 into the SQL database"""
    trace("[SQL]: Initializing logging...", TraceLEVELS.NORMAL)
    GLOBALS.manager = mgr_object
    if GLOBALS.manager.initialize():
        GLOBALS.enabled = True
        trace("[SQL]: Initialization was successful!", TraceLEVELS.NORMAL)
        return True

    trace("Unable to setup SQL logging, file logs will be used instead.", TraceLEVELS.WARNING)
    return False


def get_sql_manager() -> LoggerSQL:
    """~ function ~
    @Name: get_sql_manager
    @Info: Returns the LoggerSQL object that was originally
           passed to the framework.run(...) function"""
    return GLOBALS.manager
