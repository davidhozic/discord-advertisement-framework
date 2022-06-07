"""~    sql    ~
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the framework.run function with the SqlCONTROLLER object.
"""
from  datetime   import datetime
from  typing     import List, Literal, Any
from  contextlib import suppress
from  sqlalchemy import (
                         SmallInteger, Integer, BigInteger, NVARCHAR, DateTime,
                         Column, Identity, ForeignKey,
                         create_engine, text
                        )
from  sqlalchemy.exc  import SQLAlchemyError
from  sqlalchemy.orm import sessionmaker, Session
from  sqlalchemy.ext.declarative import declarative_base
from  pytds import (
                    ClosedConnectionError,
                    TimeoutError,
                    Error as PyTDSError
                   )
from  .tracing import *
from  .timing import *
from  .const import *
import json
import copy
import re
import time
import asyncio
import pytds

__all__ = (
    "LoggerSQL",
    "register_type",
    "get_sql_manager"
)


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
        "cursor",
        "_sessionmaker",
        "commit_buffer",
        "username",
        "__password",
        "server",
        "database",
        "lock",
        # Caching dictionaries
        "MessageMODE",
        "MessageTYPE",
        "GuildTYPE",
        "GuildUSER",
        "CHANNEL"
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
        self.cursor = None
        self._sessionmaker  = None
        self.lock = asyncio.Lock() # Lock used to prevent multiple tasks from accessing the database at the same time
        # Caching (to avoid unneccessary queries)
        ## Lookup table caching
        self.MessageMODE = {}
        self.MessageTYPE = {}
        self.GuildTYPE   = {}

        ## Other object caching
        self.GuildUSER = {}
        self.CHANNEL = {}

    def add_to_cache(self, table: Base, key: Any, value: Any) -> None:
        """~ Method ~
        @Info: Adds a value to the internal cache of a certain table"""
        getattr(self, table.__name__)[key] = value

    def clear_cache(self, *to_clear) -> None:
        """~ Method ~
        @Info: Clears the caching dicitonaries inside the object that match any of the tables"""
        if len(to_clear) == 0:  # Clear all cached tables if nothing was passead
            to_clear = self.__slots__
        tables = [k for k in globals() if k in to_clear]  # Serch for classes in the module's namespace
        for k in tables:
            getattr(self, k).clear()

    def reconnect_after(self, wait: int, loop: asyncio.AbstractEventLoop) -> None:
        """ ~ Method ~
        @Info: reconnects the SQL manager to the database after <time>.
        @Params:
            - time: int ~ Time in seconds after which reconnect"""
        def _reconnect():
            """
            ~ Coroutine ~
            @Info: Tries to reconnect after <wait>, if it failed,
                   it retries after <wait>"""
            for tries in range(SQL_RECONNECT_ATTEMPTS):
                trace(f"[SQL]: Reconnecting to database {self.database}.")
                if self.connect_cursor():
                    trace(f"[SQL]: Reconnected to the database {self.database}.")
                    GLOBALS.enabled = True
                    return
                if tries != SQL_RECONNECT_ATTEMPTS - 1: # Don't wait if it's the last attempt
                    trace(f"[SQL]: Retrying to connect in {wait} seconds.")
                    time.sleep(wait) 

            trace(f"[SQL]: Failed to reconnect in {SQL_RECONNECT_ATTEMPTS} attempts, SQL logging is now disabled.")

        GLOBALS.enabled = False
        self.cursor.close()
        loop.run_in_executor(None, _reconnect)

    def create_data_types(self) -> bool:
        """~ Method ~
        @Info: Creates datatypes that are used by the framework to log messages"""
        session: Session
        
        stms = [
            {
                "name": "t_tmp_channel_log",
                "stm": "TYPE {} AS TABLE(id int, reason nvarchar(max))"
            }
        ]
        with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
            trace("[SQL]: Creating data types...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for statement in stms:
                    if session.execute(text(f"SELECT name FROM sys.types WHERE name=:name"), {"name":statement["name"]}).first() is None:
                        session.execute(text("CREATE " + statement["stm"].format(statement["name"]) ))

            return True
        
        return False

    def create_analytic_objects(self) -> bool:
        """~ Method ~
        @Info: Creates Stored Procedures, Views and Functions via SQL code.
               The method iterates thru a list, first checking if the object exists
                -> if it does exist, it uses ALTER + "stm", if it doesn't exist,
                   it uses CREATE + "stm" command to create the object inside the SQL database.
        @Param: void"""
        stms = [
            {   
                "name" :   "vMessageLogFullDETAIL",
                "stm"    : """
                VIEW {} AS
                SELECT ml.id id, dh.content sent_data, mt.name message_type, gt.name guild_type , gu.snowflake_id guild_id, gu.name guild_name, mm.name message_mode, ml.dm_reason dm_reason, ml.[timestamp] [timestamp]
                FROM MessageLOG ml JOIN MessageTYPE mt ON ml.message_type  = mt.id
                LEFT JOIN MessageMODE mm ON mm.id = ml.message_mode
                JOIN GuildUSER gu ON gu.id = ml.guild_id
                JOIN GuildTYPE gt ON gu.guild_type = gt.id
                JOIN DataHistory dh ON dh.id = ml.sent_data"""
            },
            {
                "name" : "tr_delete_msg_log",
                "stm"  : """
                TRIGGER {} ON MessageChannelLOG FOR DELETE
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
                "name" : "fn_log_success_rate",
                "stm"  : """
                FUNCTION {}(@log_id int) 
                RETURNS decimal(8,5) AS
                BEGIN
                    /*
                    * ~ function ~
                    * @Info: Returns relative number of successful channels for specific log_id. 
                    * 		  If the log_id does not appear in the table, it returns 1/
                    */
                    DECLARE @rate decimal(8,5);

                    IF (SELECT CAST(COUNT(*) AS decimal(8,5)) FROM MessageChannelLOG WHERE log_id = @log_id) = 0
                        RETURN 1;
                    
                    SELECT @rate = (SELECT CAST(COUNT(*) AS decimal(8,5)) FROM MessageChannelLOG WHERE log_id = @log_id AND reason IS NULL) /
                                (SELECT COUNT(*) FROM MessageChannelLOG WHERE log_id = @log_id)

                    RETURN @rate;
                END"""
            },
            {
                "name" : "fn_guilduser_success_rate",
                "stm"  : """
                FUNCTION {}(@snowflake_id bigint,
                            @limit int = 1000) 
                RETURNS decimal(8,5) AS
                BEGIN 
                    /* ~ function ~
                    * @Info: Returns relative number of fully successful attempts for specific guild/user.
                    * 	      If guild/user is not found or there are no logs for the guild/user, returns 1.
                    */
                    DECLARE @internal_id int, @guild_type nvarchar(20), @rate decimal(8,5);

                    SELECT  @internal_id = gu.id, 
                            @guild_type = gt.name 
                    FROM GuildUSER gu JOIN GuildTYPE gt ON gu.guild_type = gt.id
                    WHERE snowflake_id = @snowflake_id;
                    
                    IF @internal_id IS NULL OR (SELECT COUNT(*) FROM MessageLOG WHERE guild_id = @internal_id) = 0 OR @limit = 0
                        RETURN 1;
                        
                    IF @guild_type = 'GUILD'
                    BEGIN
                        WITH tmp_table AS (SELECT TOP (@limit) id FROM MessageLOG WHERE guild_id = @internal_id ORDER BY id DESC)	 -- Get all the rows that match the internal guild/user id
                            SELECT @rate = 
                                (SELECT CAST(COUNT(*) AS decimal(8,5)) FROM tmp_table WHERE dbo.fn_log_success_rate(id) = 1) / 
                                (SELECT COUNT(*) FROM tmp_table); -- fully successful vs all
                    END
                    
                    ELSE IF @guild_type = 'USER' 
                    BEGIN
                        WITH tmp_table AS (SELECT TOP (@limit) dm_reason FROM MessageLOG WHERE guild_id = @internal_id ORDER BY id DESC)	 -- Get all the rows that match the internal guild/user id
                            SELECT @rate = 
                                (SELECT CAST(COUNT(*) AS decimal(8,5)) FROM tmp_table WHERE dm_reason IS  NULL) /  -- If dm_reason is NULL, then the send attempt was successful
                                (SELECT COUNT(*) FROM tmp_table); -- successful vs all
                    END
                    
                    RETURN @rate;
                END"""
            },
            {
                "name" : "sp_save_log",
                "stm" : """
                PROCEDURE {}(@sent_data nvarchar(max),
                             @message_type smallint,
                             @guild_id int,
                             @message_mode smallint,
                             @dm_reason nvarchar(max),
                             @channels t_tmp_channel_log READONLY) AS
                /* Procedure that saves the log							 
                * This is done within sql instead of python for speed optimization
                */
                BEGIN
	                BEGIN TRY
                        DECLARE @existing_data_id int = NULL;
                   	    DECLARE @last_log_id      int = NULL;

                	    SELECT @existing_data_id = id FROM DataHISTORY dh WHERE dh.content = @sent_data;	
                  
                        IF @existing_data_id IS NULL
                        BEGIN
                            INSERT INTO DataHISTORY(content) VALUES(@sent_data);
                            SELECT @existing_data_id = id FROM DataHISTORY dh WHERE dh.content = @sent_data;
                        END
                    
                    
	                    INSERT INTO MessageLOG(sent_data, message_type, guild_id, message_mode, dm_reason, [timestamp]) VALUES(
	                        @existing_data_id, @message_type, @guild_id, @message_mode, @dm_reason, GETDATE()
	                    );
	                                      		
	                   SET @last_log_id = SCOPE_IDENTITY();
	                   
	                   DECLARE @existance tinyint;
                	   SELECT @existance = (CASE WHEN EXISTS(SELECT TOP(1) 1 FROM @channels) THEN 1 ELSE 0 END)
                	   
	                   IF @existance = 1
	                   BEGIN        
	                    	INSERT INTO MessageChannelLOG (log_id, channel_id, reason)
	                   		SELECT @last_log_id, ch.id, ch.reason FROM @channels ch --OPENJSON(@channels) WITH(id int, reason nvarchar(max)) ch;
	                   END
	                   COMMIT;
	                   BEGIN TRAN;

	                END TRY
                    BEGIN CATCH
                   		ROLLBACK;
                   		BEGIN TRAN;
                        THROW;                   		
                    END CATCH
                END"""
            }
        ]
        with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
            trace("[SQL]: Creating Views, Procedures & Functions...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for statement in stms:
                    session.execute(text("CREATE OR ALTER " + statement["stm"].format(statement["name"]) ))
            return True

        return False

    def generate_lookup_values(self) -> bool:
        """~ Method ~
        @Info: Generates the lookup values for all the different classes the @register_type decorator was used on.
        """
        session : Session
        
        with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
            trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for to_add in copy.deepcopy(GLOBALS.lt_types):  # Deepcopied to prevent SQLAlchemy from deleting the data
                    existing = session.query(type(to_add)).where(type(to_add).name == to_add.name).first()
                    if existing is None:
                        session.add(to_add)
                        session.flush()
                        existing = to_add
                    self.add_to_cache(type(to_add), to_add.name, existing.id)
            return True

        return False

    def create_tables(self) -> bool:
        """~ Method ~
        @Info: Creates tables from the SQLAlchemy's descriptor classes"""
        with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
            trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
            self.Base.metadata.create_all(bind=self.engine)
            return True
        
        return False

    def connect_cursor(self) -> bool:
        """ ~ Method ~
        @Info: Creates a cursor for the database (for faster communication)"""
        with suppress(Exception):
            trace("[SQL]: Connecting the cursor...", TraceLEVELS.NORMAL)
            self.cursor = self.engine.raw_connection().cursor()
            return True
        return False

    def begin_engine(self) -> bool:
        """~ Method ~
        @Info: Creates engine"""
        with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
            self.engine = create_engine(f"mssql+pytds://{self.username}:{self.__password}@{self.server}/{self.database}",
                                        echo=False,future=True, pool_pre_ping=True,
                                        connect_args={"login_timeout" : SQL_CONNECTOR_TIMEOUT, "timeout" : SQL_CONNECTOR_TIMEOUT})
            self._sessionmaker = sessionmaker(bind=self.engine)
            return True

        return False

    # def create_database(self) -> bool:
    #     """ ~ Method ~
    #     @Info: Creates database if it doesn't exist"""
    #     with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
    #         trace("[SQL]: Creating database...", TraceLEVELS.NORMAL)
    #         if not database_exists(self.engine.url):
    #             create_database(self.engine.url)
    #         return True
    #     return False

    def initialize(self) -> bool:
        """~ Method ~
        @Info: This method initializes the connection to the database, creates the missing tables
               and fills the lookuptables with types defined by the register_type(lookup_table) function.
        @Param: void"""

        # Create engine for communicating with the SQL base
        if not self.begin_engine():
            trace("[SQL]: Unable to start engine.", TraceLEVELS.ERROR)
            return False
        
        # if not self.create_database():
        #     trace("[SQL]: Unable to create database")
        #     return False
        
        # Create tables and the session class bound to the engine
        if not self.create_tables():
            trace("[SQL]: Unable to create all the tables.", TraceLEVELS.ERROR)
            return False

        # Insert the lookuptable values        
        if not self.generate_lookup_values():
            trace("[SQL]: Unable to create lookuptables' rows.", TraceLEVELS.ERROR)
            return False

        # Create datatypes
        if not self.create_data_types():
            trace("[SQL]: Unable to data types", TraceLEVELS.ERROR)
            return False

        # Initialize views, procedures and functions
        if not self.create_analytic_objects():
            trace("[SQL]: Unable to create views, procedures and functions.", TraceLEVELS.ERROR)
            return False
        
        # Connect the cursor for faster procedure calls
        if not self.connect_cursor():
            trace("[SQL]: Unable to connect the cursor", TraceLEVELS.ERROR)
            return False

        return True
    
    def get_insert_guild(self,
                    snowflake: int,
                    name: str,
                    _type: str) -> int:
        """~ Method ~
        @Info:
        Inserts the guild into the db if it doesn't exist,
        adds it to cache and returns it's internal db id from cache."""
        result = None          
        if snowflake not in self.GuildUSER:
            with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(GuildUSER.id).filter(GuildUSER.snowflake_id == snowflake).first()
                if result is not None:
                    result = result[0]
                    self.add_to_cache(GuildUSER, snowflake, result)
                else:
                    guild_type = self.GuildTYPE[_type]
                    result = GuildUSER(guild_type, snowflake, name)
                    session.add(result)
                    session.flush()
                    result = result.id
                    self.add_to_cache(GuildUSER, snowflake, result)
        else:
            result = self.GuildUSER[snowflake]
        return result

    def get_insert_channels(self,
                        channels: List[dict],
                        guild_id: int) -> List[dict]:
        """~ Method ~
        @Info: 
            - Adds missing channels to the database, where it then caches those added,
              to avoid unnecessary quaries if all channels exist and then returns
              a list of dicitonaries containing internal DB id and reason why sending failed.

        @Param:
        - channels: List[dict[id, name]] ~ List of dictionaries containing snowflake_id and name of the channel"""

        not_cached = [{"id": x["id"], "name": x["name"]} for x in channels  if x["id"] not in self.CHANNEL] # Get snowflakes that are not cached
        not_cached_snow = [x["id"] for x in not_cached]
        if len(not_cached):
            with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(CHANNEL.id, CHANNEL.snowflake_id).where(CHANNEL.snowflake_id.in_(not_cached_snow)).all()
                for internal_id, snowflake_id in result:
                    self.add_to_cache(CHANNEL, snowflake_id, internal_id)
                to_add = [CHANNEL(x["id"], x["name"], guild_id) for x in not_cached if x["id"] not in self.CHANNEL]
                if len(to_add):
                    session.add_all(to_add)
                    session.flush()
                    for channel in to_add:
                        self.add_to_cache(CHANNEL, channel.snowflake_id, channel.id)
        
        ret = [(self.CHANNEL.get(d["id"],None), d.get("reason", None))  for d in channels]
        #For some reason pytds doesn't like when a row with a NULL column value is followed by a row with a non NULL column value
        for channel in ret.copy():
            if channel[1] is None:
                ret.append(ret.pop(0))
            else:
                break
        return ret
    
    def stop_engine(self):
        """~ Method ~
        @Info: Closes the engine and the cursor"""
        self.cursor.close()
        self.engine.dispose()
        GLOBALS.enabled = False

    def handle_error(self,
                     exception: int, message: str,
                     loop: asyncio.AbstractEventLoop) -> bool:
        """~ function ~
        @Info: Used to handle errors that happen in the save_log method.
        @Return: Returns BOOL indicating if logging to the base should be attempted again."""
        res = False
        time.sleep(SQL_RECOVERY_TIME)
        # Handle the error
        if exception == 208:  # Invalid object name (table deleted)
            if self.create_tables() and self.create_data_types() and self.create_analytic_objects():
                res = True
        elif exception in {547, 515}:   # Constraint conflict, NULL value 
            r_table = re.search(r'(?<=table "dbo.).+(?=")', message)
            if r_table is not None:
                self.clear_cache(r_table.group(0))  # Clears only the affected table cache 
            else:
                self.clear_cache()  # Clears all caching tables
            res = self.generate_lookup_values()
        elif exception in {-1, 2, 53}:  # Diconnect error, reconnect after period
                self.reconnect_after(SQL_RECONNECT_TIME, loop)
        elif exception == 2812:
            if self.create_data_types() and self.create_analytic_objects():
                res = True
        elif exception == 2801: # Object was altered (via external source) after procedure was compiled
            res = True # Just retry
        elif exception == 1205: # Transaction deadlocked
            with suppress(SQLAlchemyError, TimeoutError, PyTDSError):
                with self._sessionmaker() as session:
                    session.commit() # Just commit
                res = True

        # Could not handle the error, switch to file logging permanently
        if not res and exception not in {-1, 2, 53}:
            self.stop_engine()

        return res  # Returns if the error was handled or not

    async def save_log(self,
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
                
        if dm_success_info is not None:
            if "reason" in dm_success_info:
                dm_success_info_reason = dm_success_info["reason"]

        _channels = pytds.default
        if channels is not None:
            channels = channels['successful'] + channels['failed']

        # Prevent multiple tasks from attempting to do operations on the database at the same time
        # This is to avoid eg. procedures being called while they are being created,
        # handle error being called from different tasks, etc.
        async with self.lock: 
            if not GLOBALS.enabled:
                # While current task was waiting for lock to be released, 
                # some other task disabled the logging due to an unhandable error
                return False

            for tries in range(SQL_MAX_SAVE_ATTEMPTS):
                try:
                    # Insert guild into the database and cache if it doesn't exist
                    guild_id = self.get_insert_guild(guild_snowflake, guild_name, guild_type)
                    if channels is not None:
                        # Insert channels into the database and cache if it doesn't exist
                        _channels = self.get_insert_channels(channels, guild_id)
                        _channels = pytds.TableValuedParam("t_tmp_channel_log", rows=_channels)
                    # Execute the saved procedure that saves the log
                    self.cursor.callproc("sp_save_log", (json.dumps(sent_data), 
                                                        self.MessageTYPE.get(message_type, None),
                                                        guild_id,
                                                        self.MessageMODE.get(message_mode, None),
                                                        dm_success_info_reason,
                                                        _channels)) # Execute the stored procedure

                    return True
                
                except Exception as ex:
                    if isinstance(ex, SQLAlchemyError):
                        ex = ex.orig  # Get the original exception

                    if isinstance(ex, ClosedConnectionError):
                        ex.text = ex.args[0]
                        ex.number = 53  # Because only text is returned

                    code = ex.number  if hasattr(ex, "number") else -1      # The exception does't have a number attribute
                    message = ex.text if hasattr(ex, "text")   else str(ex) # The exception does't have a text attribute
                    trace(f"[SQL]: Saving log failed. {code} - {message}. Attempting recovery... (Tries left: {SQL_MAX_SAVE_ATTEMPTS - tries - 1})")
                    loop = asyncio.get_event_loop()
                    # Run in executor to prevent blocking
                    if not await loop.run_in_executor(None, self.handle_error, code, message, asyncio.get_event_loop()):
                        break
        
        trace(f"[SQL]: Saving log failed. Switching to file logging.")
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

    id = Column(Integer, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(NVARCHAR)
    guild_type = Column(SmallInteger, ForeignKey("GuildTYPE.id"), nullable=False)

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
    id = Column(Integer, Identity(start=0,increment=1),primary_key=True)
    snowflake_id = Column(BigInteger)
    name = Column(NVARCHAR)
    guild_id = Column(Integer, ForeignKey("GuildUSER.id"), nullable=False)

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
    message_type = Column(SmallInteger, ForeignKey("MessageTYPE.id"), nullable=False)
    guild_id =     Column(Integer, ForeignKey("GuildUSER.id"), nullable=False)
    message_mode = Column(SmallInteger, ForeignKey("MessageMODE.id")) # [TextMESSAGE, DirectMESSAGE]
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
    channel_id = Column(Integer, ForeignKey("CHANNEL.id"), primary_key=True)
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
    return False


def get_sql_manager() -> LoggerSQL:
    """~ function ~
    @Info: Returns the LoggerSQL object that was originally
           passed to the framework.run(...) function 
           or None if the SQL logging is disabled"""
    return GLOBALS.manager if GLOBALS.enabled else None
