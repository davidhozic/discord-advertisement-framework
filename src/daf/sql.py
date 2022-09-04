"""
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the daf.run function with the SqlCONTROLLER object.

    .. versionchanged:: v2.1
        Made SQL an optional functionality
"""
from datetime import datetime
from typing import Callable, Dict, List, Literal, Any, Union
from contextlib import suppress
from typeguard import typechecked

from .tracing import *
from .timing import *
from .common import *
from .exceptions import *

import json
import copy
import re
import time
import asyncio

from . import misc


__all__ = (
    "LoggerSQL",
    "_register_type",
    "get_sql_manager"
)


class GLOBALS:
    """
    Stores global module variables.
    """
    manager = None
    enabled = False
    lt_types = []
    sql_installed = False

# ------------------------------------ Optional ------------------------------------
try:
    from sqlalchemy import (
                            SmallInteger, Integer, BigInteger, NVARCHAR, DateTime,
                            Column, Identity, ForeignKey,
                            create_engine, text
                        )
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.declarative import declarative_base
    from pytds import ClosedConnectionError
    import pytds
    import sqlalchemy as sqa
    GLOBALS.sql_installed = True
except ImportError:
    GLOBALS.sql_installed = False
# ----------------------------------------------------------------------------------



def _register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]) -> Callable:
    """
    Returns a decorator which will create a row inside <lookuptable> table.
    The name of the inserted item is defined with the __logname__ variable
    which must be present in each framework class that is to be added to the lookuptable.
    The __logname__ also defines the object type name inside text logs (and sql).

    Parameters
    ------------
    lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]
        Name of the lookup table to insert the value into.

    Raises
    --------------
    DAFNotFoundError(code=DAF_SQL_LOOKUPTABLE_NOT_FOUND)
        Raised when the lookuptable descriptor class was not found.
    """
    def decorator_register_type(cls):
        # Iterate thru all module globals to find the lookup table
        # and insert a row into that lookup table (name of the type is defined with __logname__)
        if GLOBALS.sql_installed:
            for lt_name, lt_cls in globals().items():
                if lt_name == lookuptable:
                    GLOBALS.lt_types.append( lt_cls(cls.__logname__) )
                    return cls
            raise DAFNotFoundError(f"[SQL]: Unable to to find lookuptable: {lookuptable}", DAF_SQL_LOOKUPTABLE_NOT_FOUND)
        
        return cls

    return decorator_register_type

@typechecked
class LoggerSQL:
    """
    Used for controlling the SQL database used for message logs.

    Parameters
    ------------
    username: str
        Username to login to the database with.
    password: str
        Password to use when logging into the database.
    server:   str
        Address of the SQL server.
    database: str
        Name of the database used for logs.
    """

    Base = declarative_base() if GLOBALS.sql_installed else None # Optional package group needs to be installed
    __slots__ = (
        "engine",
        "cursor",
        "_sessionmaker",
        "username",
        "password",
        "server",
        "database",
        "safe_sem",
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

        if not GLOBALS.sql_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[sql]")

        # Save the connection parameters
        self.username = username
        self.password = password
        self.server = server
        self.database = database
        self.engine: sqa.engine.Engine = None
        self.cursor: pytds.Cursor = None
        self._sessionmaker: sessionmaker = None

        # Semaphore used to prevent multiple tasks from trying to access the `._save_log()` method at once.
        # Also used in the `.update()` method to prevent race conditions.
        self.safe_sem = asyncio.Semaphore(1)

        # Caching (to avoid unnecessary queries)
        ## Lookup table caching
        self.MessageMODE = {}
        self.MessageTYPE = {}
        self.GuildTYPE = {}

        ## Other object caching
        self.GuildUSER = {}
        self.CHANNEL = {}

    def _add_to_cache(self, table: Base, key: Any, value: Any) -> None:
        """
        Adds a value to the internal cache of a certain table.

        Parameters
        ------------
        - table: Base
            Name of the table to cache the row in.
        - key: Any
            Row key.
        - value: Any
            Row value.
        """
        getattr(self, table.__name__)[key] = value

    def _clear_cache(self, *to_clear: str) -> None:
        """
        Clears the caching dictionaries inside the object that match any of the tables.

        Parameters
        -----------
        *to_clear: str
            Custom number of positional arguments of caching dictionaries to clear.
        """
        if len(to_clear) == 0:  # Clear all cached tables if nothing was passed
            to_clear = [table.__name__ for table in self.Base.__subclasses__() if table.__name__ in self.__slots__]
        else:
            to_clear = [table for table in to_clear if table in self.__slots__]

        for k in to_clear:
            getattr(self, k).clear()

    def _reconnect_after(self, wait: int, loop: asyncio.AbstractEventLoop) -> None:
        """
        Reconnects the SQL manager to the database after <wait> if it was disconnected.

        Parameters
        -----------
        wait: int
            Time in seconds after which reconnect.
        loop: AbstractEventLoop
            Asyncio event loop (for thread executor).
        """
        def _reconnect():
            """
            Tries to reconnect after <wait>, if it failed,
            it retries after <wait>
            """
            for tries in range(SQL_RECONNECT_ATTEMPTS):
                trace(f"[SQL]: Reconnecting to database {self.database}.")
                with suppress(DAFSQLError):
                    self._begin_engine()
                    trace(f"[SQL]: Reconnected to the database {self.database}.")
                    GLOBALS.enabled = True
                    return

                if tries != SQL_RECONNECT_ATTEMPTS - 1: # Don't wait if it's the last attempt
                    trace(f"[SQL]: Retrying to connect in {wait} seconds.")
                    time.sleep(wait)

            trace(f"[SQL]: Failed to reconnect in {SQL_RECONNECT_ATTEMPTS} attempts, SQL logging is now disabled.")

        GLOBALS.enabled = False
        self._stop_engine()
        loop.run_in_executor(None, _reconnect)

    def _create_data_types(self) -> None:
        """
        Creates data types that are used by the framework to log messages.

        Raises
        --------------
        DAFSQLError(code=DAF_SQL_CREATE_DT_ERROR)
            Raised when the method is unable to create the SQL custom data types.
        """
        session: Session

        stms = [
            {
                "name": "t_tmp_channel_log",
                "stm": "TYPE {} AS TABLE(id int, reason nvarchar(max))"
            }
        ]
        try:
            trace("[SQL]: Creating data types...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for statement in stms:
                    if session.execute(text(f"SELECT name FROM sys.types WHERE name=:name"), {"name":statement["name"]}).first() is None:
                        session.execute(text("CREATE " + statement["stm"].format(statement["name"]) ))
        except Exception as ex:
            raise DAFSQLError(f"Unable to create SQL data types\nReason: {ex}", DAF_SQL_CREATE_DT_ERROR)


    def _create_analytic_objects(self) -> None:
        """
        Creates Stored Procedures, Views and Functions via SQL code.

        Raises
        ------------
        DAFSQLError(code=DAF_SQL_CREATE_VPF_ERROR)
            Raised whenever the method is unable to create all the views, procedures, functions.
        """
        session: Session
        stms = [
            {
                "name" : "vMessageLogFullDETAIL",
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
	                   
	                   DECLARE @existence tinyint;
                	   SELECT @existence = (CASE WHEN EXISTS(SELECT TOP(1) 1 FROM @channels) THEN 1 ELSE 0 END)
                	   
	                   IF @existence = 1
	                   BEGIN        
	                    	INSERT INTO MessageChannelLOG (log_id, channel_id, reason)
	                   		SELECT @last_log_id, ch.id, ch.reason FROM @channels ch;
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
        try:
            trace("[SQL]: Creating Views, Procedures & Functions...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for statement in stms:
                    session.execute(text("CREATE OR ALTER " + statement["stm"].format(statement["name"]) ))
        except Exception as ex:
            raise DAFSQLError(f" Unable to create views, procedures and functions.\nReason: {ex}", DAF_SQL_CREATE_VPF_ERROR)


    def _generate_lookup_values(self) -> None:
        """
        Generates the lookup values for all the different classes the @_register_type decorator was used on.

        Raises
        -------------
        DAFSQLError(code=DAF_SQL_CR_LT_VALUES_ERROR)
            Raised when lookuptable values could not be inserted into the database.
        """
        session : Session
        try:
            trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
            with self._sessionmaker.begin() as session:
                for to_add in copy.deepcopy(GLOBALS.lt_types):  # Deep copied to prevent SQLAlchemy from deleting the data
                    existing = session.query(type(to_add)).where(type(to_add).name == to_add.name).first()
                    if existing is None:
                        session.add(to_add)
                        session.flush()
                        existing = to_add
                    self._add_to_cache(type(to_add), to_add.name, existing.id)
        except Exception as ex:
            raise DAFSQLError(f"Unable to create lookuptables' rows.\nReason: {ex}", DAF_SQL_CR_LT_VALUES_ERROR)

    def _create_tables(self) -> None:
        """
        Creates tables from the SQLAlchemy's descriptor classes

        Raises
        -----------
        DAFSQLError(code=DAF_SQL_CREATE_TABLES_ERROR)
            Raised when tables could not be created.
        """
        try:
            trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
            self.Base.metadata.create_all(bind=self.engine)
        except Exception as ex:
            raise DAFSQLError(f"Unable to create all the tables.\nReason: {ex}", DAF_SQL_CREATE_TABLES_ERROR)

    def _connect_cursor(self) -> None:
        """
        Creates a cursor for the database (for faster communication)

        Raises
        ------------
        DAFSQLError(code=DAF_SQL_CURSOR_CONN_ERROR)
            Raised when the cursor connection could not be established.
        """
        try:
            trace("[SQL]: Connecting the cursor...", TraceLEVELS.NORMAL)
            self.cursor = self.engine.raw_connection().cursor()
        except Exception as ex:
            raise DAFSQLError(f"Unable to connect the cursor. Reason: {ex}", DAF_SQL_CURSOR_CONN_ERROR)

    def _begin_engine(self) -> None:
        """
        Creates the sqlalchemy engine.

        Raises
        ----------------
        DAFSQLError(code=DAF_SQL_BEGIN_ENGINE_ERROR)
            Raised when the engine could not connect to the specified database.
        """
        try:
            self.engine = create_engine(f"mssql+pytds://{self.username}:{self.password}@{self.server}/{self.database}",
                                        echo=False,future=True, pool_pre_ping=True,
                                        connect_args={"login_timeout" : SQL_CONNECTOR_TIMEOUT, "timeout" : SQL_CONNECTOR_TIMEOUT})
            self._sessionmaker = sessionmaker(bind=self.engine)
        except Exception as ex:
            raise DAFSQLError(f"Unable to start engine.\nError: {ex}", DAF_SQL_BEGIN_ENGINE_ERROR)

    async def initialize(self) -> None:
        """
        This method initializes the connection to the database, creates the missing tables
        and fills the lookuptables with types defined by the _register_type(lookup_table) function.

        .. note::
            This is automatically called when running the daf.

        Raises
        -----------
        Inherited from DAFSQLError
            from ``._begin_engine()``
        Inherited from DAFSQLError
            from ``._create_tables()``
        Inherited from DAFSQLError
            from ``._generate_lookup_values()``
        Inherited from DAFSQLError
            from ``._create_data_types()``
        Inherited from DAFSQLError
            from ``._create_analytic_objects()``
        Inherited from DAFSQLError
            from ``._connect_cursor()``
        """
        # Create engine for communicating with the SQL base
        self._begin_engine()
        # Create tables and the session class bound to the engine
        self._create_tables()
        # Insert the lookuptable values
        self._generate_lookup_values()
        # Create datatypes
        self._create_data_types()
        # Initialize views, procedures and functions
        self._create_analytic_objects()
        # Connect the cursor for faster procedure calls
        self._connect_cursor()
        GLOBALS.enabled = True

    def _get_insert_guild(self,
                          snowflake: int,
                          name: str,
                          _type: str) -> int:
        """
        Inserts the guild into the db if it doesn't exist,
        adds it to cache and returns it's internal db id from cache.

        Parameters
        ------------
        snowflake: int
            The snowflake of the guild.
        name: name
            The name of the guild.
        _type: str
            The type of the guild.
        """
        result = None
        if snowflake not in self.GuildUSER:
            with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(GuildUSER.id).filter(GuildUSER.snowflake_id == snowflake).first()
                if result is not None:
                    result = result[0]
                    self._add_to_cache(GuildUSER, snowflake, result)
                else:
                    guild_type = self.GuildTYPE[_type]
                    result = GuildUSER(guild_type, snowflake, name)
                    session.add(result)
                    session.flush()
                    result = result.id
                    self._add_to_cache(GuildUSER, snowflake, result)
        else:
            result = self.GuildUSER[snowflake]
        return result

    def _get_insert_channels(self,
                        channels: List[dict],
                        guild_id: int) -> List[Dict[int, Union[str, None]]]:
        """
        Adds missing channels to the database, then caches those added
        for performance.

        Parameters
        ------------
        channels: List[dict],
            List of dictionaries containing values for snowflake id ("id") and name of the channel ("name"). If sending to failed, it also contains text like description of the error ("reason").
        guild_id: int
            The internal DB id of the guild where the channels are in.

        Return
        -------------
        List[Dict[int, Union[str, None]]]
            List of dictionaries containing database ID of a channel and a reason why sending to channel failed.
        """

        not_cached = [{"id": x["id"], "name": x["name"]} for x in channels if x["id"] not in self.CHANNEL] # Get snowflakes that are not cached
        not_cached_snow = [x["id"] for x in not_cached]
        if len(not_cached):
            with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(CHANNEL.id, CHANNEL.snowflake_id).where(CHANNEL.snowflake_id.in_(not_cached_snow)).all()
                for internal_id, snowflake_id in result:
                    self._add_to_cache(CHANNEL, snowflake_id, internal_id)
                to_add = [CHANNEL(x["id"], x["name"], guild_id) for x in not_cached if x["id"] not in self.CHANNEL]
                if len(to_add):
                    session.add_all(to_add)
                    session.flush()
                    for channel in to_add:
                        self._add_to_cache(CHANNEL, channel.snowflake_id, channel.id)

        ret = [(self.CHANNEL.get(d["id"],None), d.get("reason", None)) for d in channels]
        #For some reason pytds doesn't like when a row with a NULL column value is followed by a row with a non NULL column value
        for channel in ret.copy():
            if channel[1] is None:
                ret.append(ret.pop(0))
            else:
                break
        return ret

    def _stop_engine(self):
        """
        Closes the engine and the cursor.
        """
        self.cursor.close()
        self.engine.dispose()
        GLOBALS.enabled = False

    def _handle_error(self,
                     exception: int, message: str,
                     loop: asyncio.AbstractEventLoop) -> bool:
        """
        Used to handle errors that happen in the _save_log method.

        Return
        --------
        Returns bool on successful handling.
        """
        session: Session
        res = True
        time.sleep(SQL_RECOVERY_TIME)
        try:
            # Handle the error
            if exception == 208:  # Invalid object name (table deleted)
                self._create_tables()
                self._create_data_types()
                self._create_analytic_objects()

            elif exception in {547, 515}:   # Constraint conflict, NULL value
                r_table = re.search(r'(?<=table "dbo.).+(?=")', message) # Try to parse the table name with regex
                if r_table is not None:
                    self._clear_cache(r_table.group(0))  # Clears only the affected table cache
                else:
                    self._clear_cache()  # Clears all caching tables
                self._generate_lookup_values()

            elif exception in {-1, 2, 53}:  # Disconnect error, reconnect after period
                self._reconnect_after(SQL_RECONNECT_TIME, loop)
                res = False # Don't try to save while reconnecting

            elif exception == 2812:
                self._create_data_types()
                self._create_analytic_objects()

            elif exception == 2801: # Object was altered (via external source) after procedure was compiled
                pass # Just retry

            elif exception == 1205: # Transaction deadlocked
                with self._sessionmaker() as session:
                    session.commit()

            else: # No handling instruction known
                res = False

        except Exception:
            # Error could not be handled, stop the engine
            res = False
            self._stop_engine()

        return res  # Returns if the error was handled or not


    # _async_safe prevents multiple tasks from attempting to do operations on the database at the same time.
    # This is to avoid eg. procedures being called while they are being created,
    # handle error being called from different tasks, update method from causing a race condition,etc.
    @misc._async_safe("safe_sem", 1)
    async def _save_log(self,
                 guild_context: dict,
                 message_context: dict) -> bool:
        """
        This method saves the log generated by the xGUILD object into the database.

        Parameters
        -------------
        guild_context: dict
            Context generated by the xGUILD object, see guild.xGUILD._generate_log() for more info.
        message_context: dict
            Context generated by the xMESSAGE object, see guild.xMESSAGE._generate_log_context() for more info.

        Return
        -------
        Returns bool value indicating success (True) or failure (False).
        """

        if not GLOBALS.enabled:
            # While current task was waiting for safe_sem to be released,
            # some other task disabled the logging due to an recoverable error.
            # Proceeding would result in failure anyway, so just return False.
            return False

        # Parse the data
        sent_data: dict = message_context.get("sent_data")
        guild_snowflake: int = guild_context.get("id")
        guild_name: str = guild_context.get("name")
        guild_type: str = guild_context.get("type")
        message_type: str = message_context.get("type")
        message_mode: str = message_context.get("mode", None)
        channels: List[dict] = message_context.get("channels", None)
        dm_success_info: dict = message_context.get("success_info", None)
        dm_success_info_reason: str = None

        if dm_success_info is not None:
            if "reason" in dm_success_info:
                dm_success_info_reason = dm_success_info["reason"]

        _channels = pytds.default
        if channels is not None:
            channels = channels['successful'] + channels['failed']


        for tries in range(SQL_MAX_SAVE_ATTEMPTS):
            try:
                # Insert guild into the database and cache if it doesn't exist
                guild_id = self._get_insert_guild(guild_snowflake, guild_name, guild_type)
                if channels is not None:
                    # Insert channels into the database and cache if it doesn't exist
                    _channels = self._get_insert_channels(channels, guild_id)
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

                code = ex.number if hasattr(ex, "number") else -1     # The exception does't have a number attribute
                message = ex.text if hasattr(ex, "text") else str(ex) # The exception does't have a text attribute
                trace(f"[SQL]: Saving log failed. {code} - {message}. Attempting recovery... (Tries left: {SQL_MAX_SAVE_ATTEMPTS - tries - 1})")
                loop = asyncio.get_event_loop()
                # Run in executor to prevent blocking
                if not await loop.run_in_executor(None, self._handle_error, code, message, asyncio.get_event_loop()):
                    break

        trace("[SQL]: Saving log failed. Switching to file logging.")
        return False

    @misc._async_safe("safe_sem", 1)
    async def update(self, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset, meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update, these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed.
        Other
            Raised from .initialize() method.
        """
        try:
            self._stop_engine()
            await misc._update(self, **kwargs)
            GLOBALS.enabled = True
        except Exception:
            # Reinitialize since engine was disconnected
            await self.initialize()
            raise


if GLOBALS.sql_installed:
    # Do not create ORM classes if the optional group is not installed
    class MessageTYPE(LoggerSQL.Base):
        """
        Lookup table for storing xMESSAGE types

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """
        __tablename__ = "MessageTYPE"

        id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
        name = Column(NVARCHAR(20), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class MessageMODE(LoggerSQL.Base):
        """
        Lookup table for storing message sending modes.

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """

        __tablename__ = "MessageMODE"

        id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
        name = Column(NVARCHAR(20), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class GuildTYPE(LoggerSQL.Base):
        """
        Lookup table for storing xGUILD types

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """

        __tablename__ = "GuildTYPE"

        id = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
        name = Column(NVARCHAR(20), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class GuildUSER(LoggerSQL.Base):
        """
        Table for storing different guilds and users.

        Parameters
        -----------
        guild_type: int
            Foreign key pointing to GuildTYPE.id.
        snowflake: int
            Discord's snowflake ID of the guild.
        name: str
            The name of the guild.
        """
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
        """
        Table for storing different channels.

        Parameters
        -----------
        snowflake: int
            Discord's snowflake ID of the channel.
        name: str
            The name of the channel.
        guild_id: int
            Foreign key pointing to GuildUSER.id.
        """


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


    class DataHISTORY(LoggerSQL.Base):
        """
        Table used for storing all the different data(JSON) that was ever sent (to reduce redundancy -> and file size in the MessageLOG).

        Parameters
        -----------
        content: str
            The JSON string representing sent data.
        """
        __tablename__ = "DataHISTORY"

        id = Column(Integer, Identity(start=0, increment=1), primary_key= True)
        content = Column(NVARCHAR)

        def __init__(self,
                    content: str):
            self.content = content

    class MessageLOG(LoggerSQL.Base):
        """
        Table containing information for each message send attempt.

        NOTE: This table is missing successful and failed channels (or DM success status).That is because those are a separate table.

        Parameters
        ------------
        sent_data: str
            JSONized data that was sent by the xMESSAGE object.
        message_type: int
            Foreign key  pointing to a row inside the MessageTYPE lookup table.
        message_mode: int
            Foreign key pointing to a row inside the MessageMODE lookup table.
        dm_reason: str
            If DM sent succeeded, it is null, if it failed it contains a string description of the error.
        guild_id: int
            Foreign key pointing the guild this message was advertised to.
        """

        __tablename__ = "MessageLOG"

        id = Column(Integer, Identity(start=0, increment=1), primary_key=True)
        sent_data = Column(Integer, ForeignKey("DataHISTORY.id"))
        message_type = Column(SmallInteger, ForeignKey("MessageTYPE.id"), nullable=False)
        guild_id = Column(Integer, ForeignKey("GuildUSER.id"), nullable=False)
        message_mode = Column(SmallInteger, ForeignKey("MessageMODE.id")) # [TextMESSAGE, DirectMESSAGE]
        dm_reason = Column(NVARCHAR)  # [DirectMESSAGE]
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
        """
        This is a table that contains a log of channels that are linked to a certain message log.

        Parameters
        ------------
        message_log_id: int
            Foreign key pointing to MessageLOG.id.
        channel_id: int
            Foreign key pointing to CHANNEL.id.
        reason: str
            Stringified description of Exception that caused the send attempt to be successful for a certain channel.
        """

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


async def initialize(mgr_object: LoggerSQL) -> bool:
    """
    This function initializes the sql manager and also the selected database.

    Parameters
    -----------
    mgr_object: LoggerSQL
        SQL database manager object responsible for saving the logs into the SQL database.

    Returns
    ----------
    True
        Logging will be SQL.
    False
        Logging will be file based.

    Raises
    ------------
    Any
        Any exceptions raised in mgr_object.initialize() method
    """
    _ret = False
    if mgr_object is not None:    
        trace("[SQL]: Initializing logging...", TraceLEVELS.NORMAL)
        try:
            await mgr_object.initialize()
            _ret = True
            trace("[SQL]: Initialization was successful!", TraceLEVELS.NORMAL)
        except DAFSQLError as exc:
            trace(f"[SQL:] Unable to initialize manager, reason\n: {exc}", TraceLEVELS.ERROR)

    GLOBALS.manager = mgr_object
    return _ret


def get_sql_manager() -> LoggerSQL:
    """
    Returns the LoggerSQL object that was originally passed to the
    daf.run(...) function or None if the SQL logging is disabled
    """
    return GLOBALS.manager
