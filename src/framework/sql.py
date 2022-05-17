"""~    sql    ~
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
from  datetime   import datetime
from  typing     import Literal
from  contextlib import suppress
from  sqlalchemy import (
                         SmallInteger, Integer, BigInteger, NVARCHAR, DateTime,
                         Column, Identity, ForeignKey,
                         create_engine, text
                        )
from sqlalchemy.exc  import SQLAlchemyError                        
from  sqlalchemy.orm import sessionmaker
from  sqlalchemy.ext.declarative import declarative_base
from  sqlalchemy_utils import create_database, database_exists
from  .tracing import *
import time
import json

__all__ = (
    "LoggerSQL",
    "register_type",
    "get_sql_manager"
)

def timeit(fnc):
    def _timeit(*args, **kwargs):
        start = time.time()
        ret = fnc(*args, **kwargs)
        end = time.time()
        print(f"Took {(end-start)*1000} ms")
        return ret
    return _timeit

class GLOBALS:
    """~ class ~
    @Info: Stores global module variables """
    manager  = None
    enabled = False
    lt_types = []


def register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]):
    """~ Decorator ~
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
    """~ class ~
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
        "SESSION",
        "commit_buffer",
        "username",
        "__password",
        "server",
        "database",

        # Caching dictionaries
        "MessageMODE",
        "MessageTYPE",
        "GuildTYPE",
        "GuildUSER"
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
        self.SESSION  = None
        # Caching (to avoid unneccessary queries)
        ## Lookup table caching
        self.MessageMODE = {}
        self.MessageTYPE = {}
        self.GuildTYPE   = {}
        ## Other object caching
        self.GuildUSER = {}

    def create_analytic_objects(self) -> bool:
        """~ Method ~
        @Info: Creates Stored Procedures, Views and Functions via SQL code.
               The method iterates thru a list, first checking if the object exists
                -> if it does exist, it uses ALTER + "stm", if it doesn't exist,
                   it uses CREATE + "stm" command to create the object inside the SQL database.
        @Param: void"""
        stms = [
            {   "name" :   "vMessageLogFullDETAIL",
                "stm"    : """VIEW {} AS
                                SELECT ml.id id, (SELECT content FROM DataHistory dh WHERE dh.id = ml.sent_data) sent_data, mt.name message_type, gt.name guild_type , gu.snowflake_id guild_id, gu.name guild_name, mm.name message_mode, ml.dm_reason dm_reason, ml.[timestamp] [timestamp]
                                FROM MessageLOG ml JOIN MessageTYPE mt ON ml.message_type  = mt.id
                                LEFT JOIN MessageMODE mm ON mm.id = ml.message_mode
                                JOIN GuildUSER gu ON gu.id = ml.guild_id
                                JOIN GuildTYPE gt ON gu.guild_type = gt.id"""
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
            },
            {
                "name" : "tr_delete_msg_log",
                "stm"  : """TRIGGER {} ON MessageChannelLOG FOR DELETE
                            AS
                            /* Trigger deletes a MessageLOG row matching the deleted channel log in case all the rows of MessageChannelLOG
                            * referencing that specific MessageLOG row were deleted
                            */
                            BEGIN
                                DECLARE @MessageLogID int;
                                SELECT @MessageLogID = del.log_id FROM DELETED del;
                                IF (SELECT COUNT(*) FROM MessageChannelLOG mlc WHERE mlc.log_id = @MessageLogID) = 0
                                BEGIN 
                                    PRINT 'Deleting message log (ID: '+ CAST(@MessageLogID as nvarchar(max)) +') because all of the channel logs referencing it were deleted';
                                    DELETE FROM MessageLOG WHERE id = @MessageLogID;
                                END
                            END"""
            },
            {
                "name" : "sp_save_log",
                "stm" : """PROCEDURE {}(@sent_data nvarchar(max),
                                        @message_type nvarchar(max),
                                        @guild_snowflake bigint,
                                        @message_mode nvarchar(max),
                                        @dm_reason nvarchar(max),
                                        @channels ntext) AS
            /* Procedure that saves the log							 
            * This is done within sql instead of python for speed optimization
            */
            BEGIN
                DECLARE @existing_data_id int;
                DECLARE @message_type_id  smallint = (SELECT id FROM MessageTYPE mt WHERE mt.name = @message_type);
                DECLARE @guild_id         smallint = (SELECT id FROM GuildUSER gu WHERE gu.snowflake_id = @guild_snowflake);
                DECLARE @message_mode_id  smallint = (SELECT id FROM MessageMODE mm WHERE mm.name = @message_mode);
                DECLARE @last_log_id      int;

                SELECT @existing_data_id = id FROM DataHISTORY dh WHERE dh.content = @sent_data;	
                
                IF @existing_data_id IS NULL
                BEGIN
                    INSERT INTO DataHISTORY(content) VALUES(@sent_data);
                    SELECT @existing_data_id = id FROM DataHISTORY dh WHERE dh.content = @sent_data;
                END
                
                INSERT INTO MessageLOG(sent_data, message_type, guild_id, message_mode, dm_reason, [timestamp]) VALUES(
                    @existing_data_id, @message_type_id, @guild_id, @message_mode_id, @dm_reason, GETDATE()
                );
                SET @last_log_id = SCOPE_IDENTITY();
                
                INSERT INTO MessageChannelLOG (log_id, channel_id, reason)
                SELECT @last_log_id, (SELECT CHANNEL.id FROM CHANNEL WHERE CHANNEL.snowflake_id = dc.id), reason FROM OPENJSON(@channels) WITH(name nvarchar(max), id bigint, reason nvarchar(max)) dc
            END"""
            },
            {
                "name": "sp_insert_channels",
                "stm":"""PROCEDURE {}(@channels ntext, @guild_id bigint) AS
                        -- Procedure adds missing channels to the CHANNEL table
                        BEGIN
	                        DECLARE @channels_t TABLE(id bigint, name nvarchar(max));
	                        
	                       INSERT INTO @channels_t(id, name)
	                       SELECT a.id, a.name FROM OPENJSON(@channels) WITH(id bigint, name nvarchar(max)) a;
	                       
                            INSERT INTO CHANNEL(snowflake_id, name, guild_id)
                            SELECT id, name, @guild_id FROM @channels_t chjson
                            WHERE NOT EXISTS(SELECT snowflake_id FROM CHANNEL WHERE snowflake_id = chjson.id);

                            UPDATE CHANNEL
                            SET name = chjson.name
                            FROM CHANNEL JOIN @channels_t chjson ON chjson.id = CHANNEL.snowflake_id
                        END"""
            }
        ]
        with suppress():
            with self.SESSION() as session:
                for statement in stms:
                    # Union the 2 system tables containing views and procedures/functions, then select only the element that matches the item we want to create, it it returns None, it doesnt exist
                    if session.execute(text(f"SELECT * FROM sys.all_objects WHERE name= '{statement['name']}'")).first() is None:
                        session.execute(text("CREATE " + statement["stm"].format(statement["name"]) ))
                    else:
                        session.execute(text("ALTER " + statement["stm"].format(statement["name"]) ))
            return True
        
        return False

    def generate_lookup_values(self) -> bool:
        """~ Method ~
        @Info: Generates the lookup values for all the different classes the @register_type decorator was used on.
        """
        with suppress():
            with self.SESSION() as session:
                for to_add in GLOBALS.lt_types:
                    existing = session.query(type(to_add)).filter_by(name=to_add.name).first()
                    if existing is None:
                        session.add(to_add)
                        session.flush()
                        existing = to_add

                    getattr(self, type(to_add).__name__)[to_add.name] = existing.id # Set the internal lookup values to later prevent time consuming queries
            return True

        return False

    def create_tables(self) -> bool:
        """~ Method ~
        @Info: Creates tables from the SQLAlchemy's descriptor classes"""
        with suppress():
            self.Base.metadata.create_all(bind=self.engine)
            return True
        
        return False
    
    def begin_engine(self) -> bool:
        """~ Method ~
        @Info: Creates engine and the databatabase"""
        with suppress():
            self.engine = create_engine(f"mssql+pymssql://{self.username}:{self.__password}@{self.server}/{self.database}", echo=False)
            self.SESSION = sessionmaker(bind=self.engine, autoflush=True, autocommit=True)
            if not database_exists(self.engine.url):
                trace("[SQL]: Creating database...", TraceLEVELS.NORMAL)
                create_database(self.engine.url)
            return True
        
        return False

    def initialize(self) -> bool:
        """~ Method ~
        @Info: This method initializes the connection to the database, creates the missing tables
               and fills the lookuptables with types defined by the register_type(lookup_table) function.
        @Param: void"""
        # Create engine for communicating with the SQL base
        if not self.begin_engine():
            trace("[SQL]: Unable to start engine.", TraceLEVELS.ERROR)
            return False
        
        # Create tables and the session class bound to the engine
        trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
        if not self.create_tables():
            trace("[SQL]: Unable to create all the tables.", TraceLEVELS.ERROR)
            return False

        # Insert the lookuptable values        
        trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
        if not self.generate_lookup_values():
            trace("[SQL]: Unable to create lookuptables' rows.", TraceLEVELS.ERROR)
            return False

        # Initialize views, procedures and functions
        trace("[SQL]: Creating Views, Procedures & Functions", TraceLEVELS.NORMAL)
        if not self.create_analytic_objects():
            trace("[SQL]: Unable to create views, procedures and functions.", TraceLEVELS.ERROR)

        return True

    @timeit
    def save_log(self,
                 guild_context: dict,
                 message_context: dict) -> bool:
        """~ Method ~
        @Info: This method saves the log generated by
               the xGUILD object into the database
        @Param:
            guild_context: dict     ::  Context generated by the xGUILD object,
                                        see guild.xGUILD.generate_log() for more info.
            message_context: dict   ::  Context generated by the xMESSAGE object,
                                        see guild.xMESSAGE.generate_log_context() for more info.
        @Return: Returns bool value indicating success (True) or failure (False)."""

        def handle_error(exception: str) -> bool:
            """~ async function ~
            @Info: Used to handle errors that happen in the save_log method.
            @Return: Returns BOOL indicating if logging to the base should be attempted again."""
            res = False
            if "Invalid object name" in exception:  # SQLAlchemy's error codes are too broad, so string comparison is used.
                res = self.create_tables()
            
            return res

        # Parse the data
        sent_data = message_context.get("sent_data")
        guild_snowflake = guild_context.get("id")
        guild_name = guild_context.get("name")
        guild_type: str = guild_context.get("type")
        message_type: str = message_context.get("type")
        message_mode = message_context.get("mode", None)
        channels = message_context.get("channels", None)
        dm_success_info = message_context.get("success_info", None)
        dm_success_info_reason = None

        # Maximum 3 tries to succeed, turn off base logging if it doesn't work
        for tries in range(3):
            try:
                # Add DirectMESSAGE success information
                if dm_success_info is not None:
                    if "reason" in dm_success_info:
                        dm_success_info_reason = dm_success_info["reason"]
                
                with self.SESSION() as session:
                    # Map MessageTYPE to an identificator
                    # Update GUILD/USER table
                    result = None
                    if guild_snowflake not in self.GuildUSER:
                        result = session.query(GuildUSER.id).filter(GuildUSER.snowflake_id == guild_snowflake).first()
                        if result is not None:
                            result = result[0]
                            self.GuildUSER[guild_snowflake] = result
                    else:
                        result = self.GuildUSER[guild_snowflake]
                    
                    if result is None:
                        guild_type = self.GuildTYPE[guild_type]
                        result = GuildUSER(guild_type, guild_snowflake, guild_name)
                        session.add(result)
                        session.flush()
                        
                        result = result.id
                        self.GuildUSER[guild_snowflake] = result

                    # Reference the guild_id with id from GuildUSER lookup table
                    guild_lookup = result

                    stms = ""
                    channels_str = None
                    if channels is not None:
                        # If channels exist [TextMESSAGE and VoiceMESSAGE], update the CHANNELS table with the correct name
                        # and only insert the channel Snowflake identificators into the message log
                        channels_str = f"{json.dumps(channels['successful'] + channels['failed'])}"
                        # Query the channels and add missing ones
                        stms += f"EXEC sp_insert_channels :channels, :guild_id;"
                    
                    # Execute raw sql call for faster saving of the log
                    stms += f"EXEC sp_save_log :data, :message_type, :guild_snowflake, :message_mode, :dm_reason, :channels;COMMIT;"
                    self.engine.execute(text(stms), channels=channels_str,
                                                    data=json.dumps(sent_data),
                                                    message_type=message_type,
                                                    guild_id=guild_lookup,
                                                    guild_snowflake=guild_snowflake,
                                                    message_mode=message_mode,
                                                    dm_reason=dm_success_info_reason)
                    return True

            except SQLAlchemyError as ex:
                ex = ex.orig.args[1].decode()
                trace(f"Attempt to save into the database failed , retrying. Tries left: {2 - tries}", TraceLEVELS.WARNING)
                if not handle_error(ex):
                    break
            except:
                break

        trace(f"Unable to save to databse {self.database}. Switching to file logging", TraceLEVELS.WARNING)
        GLOBALS.enabled = False
        return False


class MessageTYPE(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: Lookup table for storing xMESSAGE types
    @Param:
        name: Name of the xMESSAGE class"""
    __tablename__ = "MessageTYPE"

    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(NVARCHAR(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildTYPE(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: Lookup table for storing xGUILD types
    @Param:
        name: Name of the xGUILD class"""

    __tablename__ = "GuildTYPE"

    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(NVARCHAR(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name


class GuildUSER(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: Guild
    @Param: Table that represents GUILD and USER object inside the database
        snowflake: int :: Snowflake identificator of the guild/user
        name: str      :: Name of the guild/user"""

    __tablename__ = "GuildUSER"

    id = Column(SmallInteger, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(NVARCHAR)
    guild_type = Column(SmallInteger, ForeignKey("GuildTYPE.id"))

    def __init__(self,
                 guild_type: int,
                 snowflake: int,
                 name: str):
        self.snowflake_id = snowflake
        self.name = name
        self.guild_type = guild_type


class CHANNEL(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: Maps the snowflake id to a name and GUILD id
    @Param:
        snowflake: int :: Snowflake identificator
        name: str      :: Name of the channel
        guild_id: int  :: Snowflake identificator pointing to a GUILD/USER"""

    __tablename__ = "CHANNEL"
    id = Column(SmallInteger, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(NVARCHAR)
    guild_id = Column(SmallInteger, ForeignKey("GuildUSER.id", ondelete="CASCADE"))

    def __init__(self,
                 snowflake: int,
                 name: str,
                 guild_id: int):
        self.snowflake_id = snowflake
        self.name = name
        self.guild_id = guild_id


class MessageMODE(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: Lookup table for storing different message send modes [TextMESSAGE, DirectMESSAGE]
    @Param:
        name: Name of the mode"""

    __tablename__ = "MessageMODE"

    id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    name = Column(NVARCHAR(20), unique=True)

    def __init__(self, name: str=None):
        self.name = name

class DataHISTORY(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info:
        This table is used for storing all the different data(JSON) that was ever sent (to reduce redundancy -> and file size in the MessageLOG)."""
    __tablename__ = "DataHISTORY"
    
    id = Column(Integer, Identity(start=0, increment=1), primary_key= True)
    content = Column(NVARCHAR)
    
    def __init__(self,
                 content: str):
        self.content = content

class MessageLOG(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: The logging table containing information for each message send attempt.
           NOTE: This table is missing successful and failed channels (or DM success status)
                  that is because those are a seperate table
    @Param:
        sent_data: str          :: JSONized data that was sent by the xMESSAGE object
        message_type: int       :: id pointing to a row inside the MessageTYPE lookup table
        message_mode: int       :: id pointing to a row inside the MessageMODE lookup table
        dm_reason: str          :: If DM sent succeeded, it is null, if it failed it contains a string description of the error
        guild_id: int           :: Internal database id of the guild this message was advertised to"""

    __tablename__ = "MessageLOG"

    id = Column(Integer, Identity(start=0, increment=1), primary_key=True)
    sent_data = Column(Integer, ForeignKey("DataHISTORY.id"))
    message_type = Column(SmallInteger, ForeignKey("MessageTYPE.id", ))
    guild_id =     Column(SmallInteger, ForeignKey("GuildUSER.id", ondelete="CASCADE"))
    message_mode = Column(SmallInteger, ForeignKey("MessageMODE.id" )) # [TextMESSAGE, DirectMESSAGE]
    dm_reason   = Column(NVARCHAR)  # [DirectMESSAGE]
    timestamp = Column(DateTime)

    def __init__(self,
                 sent_data: str=None,
                 message_type: int=None,
                 message_mode: int=None,
                 dm_reason: str=None,
                 guild_id: int=None):
        self.sent_data = sent_data
        self.message_type = message_type
        self.message_mode = message_mode
        self.dm_reason = dm_reason
        self.guild_id = guild_id
        self.timestamp = datetime.now().replace(microsecond=0)


class MessageChannelLOG(LoggerSQL.Base):
    """~ SQL Table Descriptor Class ~
    @Info: This is a table that contains a log of channels that are
           linked to a certain message log.
    @Param:
        name: Name of the mode"""

    __tablename__ = "MessageChannelLOG"

    log_id = Column(Integer, ForeignKey("MessageLOG.id", ondelete="CASCADE"), primary_key=True)
    channel_id = Column(SmallInteger, ForeignKey("CHANNEL.id"), primary_key=True)
    reason = Column(NVARCHAR)
    def __init__(self,
                 message_log_id: int,
                 channel_id: int,
                 reason: str=None):
        self.log_id = message_log_id
        self.channel_id = channel_id
        self.reason = reason


def initialize(mgr_object: LoggerSQL) -> bool:
    """~ function ~
    @Info: This function initializes the sql manager and also the selected database
           NOTE: If initialization fails, file logs will be used
    @Param:
        mgr_object: LoggerSQL :: SQL database manager object responsible for saving the logs
                                 into the SQL database"""
    trace("[SQL]: Initializing logging...", TraceLEVELS.NORMAL)
    if mgr_object is not None and mgr_object.initialize():
        trace("[SQL]: Initialization was successful!", TraceLEVELS.NORMAL)
        GLOBALS.enabled = True
        GLOBALS.manager = mgr_object
        return True

    trace("Unable to setup SQL logging, file logs will be used instead.", TraceLEVELS.WARNING)
    return False


def get_sql_manager() -> LoggerSQL:
    """~ function ~
    @Info: Returns the LoggerSQL object that was originally
           passed to the framework.run(...) function 
           or None if the SQL logging is disabled"""
    return GLOBALS.manager if GLOBALS.enabled else None
