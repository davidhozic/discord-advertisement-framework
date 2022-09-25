"""
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the daf.run function with the SqlCONTROLLER object.

    .. versionchanged:: v2.1
        Made SQL an optional functionality
"""
# TODO: Replace .query-s with select
from datetime import datetime
from typing import Callable, Dict, List, Literal, Any, Union, Optional
from contextlib import suppress
from typeguard import typechecked

from .tracing import *
from ..timing import *
from ..exceptions import *

from . import logging

import json
import copy
import re
import time
import asyncio

from .. import misc


class GLOBALS:
    """
    Stores global module variables.
    """
    lt_types = []
    sql_installed = False

# ------------------------------------ Configuration -------------------------------
SQL_MAX_SAVE_ATTEMPTS = 10
SQL_MAX_EHANDLE_ATTEMPTS = 3
SQL_RECOVERY_TIME = 0.5
SQL_RECONNECT_TIME = 5 * 60
SQL_RECONNECT_ATTEMPTS = 3
SQL_CONNECTOR_TIMEOUT = 6


# ------------------------------------ Optional ------------------------------------
try:
    from sqlalchemy import (
                            SmallInteger, Integer, BigInteger, NVARCHAR, DateTime,
                            Column, ForeignKey, Sequence, select
                        )            
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.engine import URL as SQLURL
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.declarative import declarative_base
    import sqlalchemy as sqa
    GLOBALS.sql_installed = True
except ImportError as exc:
    GLOBALS.sql_installed = False
# ----------------------------------------------------------------------------------


__all__ = (
    "LoggerSQL",
)


def register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]) -> Callable:
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


@misc.doc_category("Logging", path="logging.sql")
class LoggerSQL(logging.LoggerBASE):
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
    dialect: str
        Dialect or database type (SQLite, mssql, )
    fallback: Optional[LoggerBASE]
        The fallback manager to use in case SQL logging fails.
    """
    Base = declarative_base() if GLOBALS.sql_installed else None

    @typechecked
    def __init__(self,
                username: Optional[str] = None,
                password: Optional[str] = None,
                server: Optional[str] = None,
                port: Optional[int] = None,
                database: Optional[str] = None,
                dialect: Optional[str] = None,
                fallback: Optional[logging.LoggerBASE] = logging.LoggerJSON("History")):

        if not GLOBALS.sql_installed:
            raise ModuleNotFoundError("You need to install extra requirements: pip install discord-advert-framework[sql]")

        # Save the connection parameters
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.database = database if database is not None else "messages"
        self.dialect = dialect
        if self.dialect is None:
            self.dialect = "sqlite"

        if self.dialect == "sqlite":
            self.database += ".db"

        self.fallback = fallback

        self.engine: sqa.engine.Engine = None
        self._sessionmaker: sessionmaker = None

        # Semaphore used to prevent multiple tasks from trying to access the `._save_log()` method at once.
        # Also used in the `.update()` method to prevent race conditions.
        self.safe_sem = asyncio.Semaphore(1)
        self.reconnecting = False # Flag that is True while reconnecting, used for emergency exit of other tasks

        # Caching (to avoid unnecessary queries)
        # TODO: Implement misc.CACHE object
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
        table: Base
            Name of the table to cache the row in.
        key: Any
            Row key.
        value: Any
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

    async def _reconnect_after(self, wait: int) -> None:
        """
        Reconnects the SQL manager to the database after <wait> if it was disconnected.

        Parameters
        -----------
        wait: int
            Time in seconds after which reconnect.
        """
        async def _reconnector():
            for tries in range(SQL_RECONNECT_ATTEMPTS):
                trace(f"[SQL]: Retrying to connect in {wait} seconds.")
                await asyncio.sleep(wait)
                trace(f"[SQL]: Reconnecting to database {self.database}.")
                with suppress(DAFSQLError):
                    self._begin_engine()
                    trace(f"[SQL]: Reconnected to the database {self.database}.")
                    self.reconnecting = False
                    logging.set_logger(self)
                    return

            trace(f"[SQL]: Failed to reconnect in {SQL_RECONNECT_ATTEMPTS} attempts, SQL logging is now disabled.")
           
        self.reconnecting = True
        await self._stop_engine()
        logging.set_logger(self.fallback)
        asyncio.create_task(_reconnector())

    async def _generate_lookup_values(self) -> None:
        """
        Generates the lookup values for all the different classes the @register_type decorator was used on.

        Raises
        -------------
        DAFSQLError(code=DAF_SQL_CR_LT_VALUES_ERROR)
            Raised when lookuptable values could not be inserted into the database.
        """
        session : Session
        try:
            trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
            async with self._sessionmaker() as session:
                async with session.begin():
                    for to_add in copy.deepcopy(GLOBALS.lt_types):  # Deep copied to prevent SQLAlchemy from deleting the data
                        existing = (await session.execute(select(type(to_add)).where(type(to_add).name == to_add.name))).fetchone()
                        if existing is not None:
                            existing = existing[0]
                        else:
                            session.add(to_add)
                            await session.flush()
                            existing = to_add

                        self._add_to_cache(type(to_add), to_add.name, existing.id)
        except Exception as ex:
            raise DAFSQLError(f"Unable to create lookuptables' rows.\nReason: {ex}", DAF_SQL_CR_LT_VALUES_ERROR)

    async def _create_tables(self) -> None:
        """
        Creates tables from the SQLAlchemy's descriptor classes

        Raises
        -----------
        DAFSQLError(code=DAF_SQL_CREATE_TABLES_ERROR)
            Raised when tables could not be created.
        """
        try:
            trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
            async with self.engine.begin() as tran:
                await tran.run_sync(self.Base.metadata.create_all)
            
        except Exception as ex:
            raise DAFSQLError(f"Unable to create all the tables.\nReason: {ex}", DAF_SQL_CREATE_TABLES_ERROR)

    def _begin_engine(self) -> None:
        """
        Creates the sqlalchemy engine.

        Raises
        ----------------
        DAFSQLError(code=DAF_SQL_BEGIN_ENGINE_ERROR)
            Raised when the engine could not connect to the specified database.
        """
        try:
            dialect = self.dialect
            if dialect == "sqlite":
                self.dialect += "+aiosqlite"

            sqlurl = SQLURL.create(
                self.dialect,
                self.username,
                self.password,
                self.server,
                self.port,
                self.database
            )

            self.engine = create_async_engine(sqlurl,
                                        echo=True, future=True, pool_pre_ping=True,
                                        connect_args={"timeout" : SQL_CONNECTOR_TIMEOUT})

            self._sessionmaker = sessionmaker(bind=self.engine, class_=AsyncSession)
        except Exception as ex:
            raise DAFSQLError(f"Unable to start engine.\nError: {ex}", DAF_SQL_BEGIN_ENGINE_ERROR)

    async def initialize(self) -> None:
        """
        This method initializes the connection to the database, creates the missing tables
        and fills the lookuptables with types defined by the register_type(lookup_table) function.

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
        """
        # Create engine for communicating with the SQL base
        self._begin_engine()
        # Create tables and the session class bound to the engine
        await self._create_tables()
        # Insert the lookuptable values
        await self._generate_lookup_values()
        await super().initialize()

    async def _get_insert_guild(self,
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
            async with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(GuildUSER.id).filter(GuildUSER.snowflake_id == snowflake).first()
                if result is not None:
                    result = result[0]
                    self._add_to_cache(GuildUSER, snowflake, result)
                else:
                    guild_type = self.GuildTYPE[_type]
                    result = GuildUSER(guild_type, snowflake, name)
                    session.add(result)
                    await session.flush()
                    result = result.id
                    self._add_to_cache(GuildUSER, snowflake, result)
        else:
            result = self.GuildUSER[snowflake]
        return result

    async def _get_insert_channels(self,
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

        # Put into cache if it is not already
        not_cached = [{"id": x["id"], "name": x["name"]} for x in channels if x["id"] not in self.CHANNEL] # Get snowflakes that are not cached
        not_cached_snow = [x["id"] for x in not_cached]
        if len(not_cached):
            async with self._sessionmaker.begin() as session:
                session: Session
                result = session.query(CHANNEL.id, CHANNEL.snowflake_id).where(CHANNEL.snowflake_id.in_(not_cached_snow)).all()
                for internal_id, snowflake_id in result:
                    self._add_to_cache(CHANNEL, snowflake_id, internal_id)
                to_add = [CHANNEL(x["id"], x["name"], guild_id) for x in not_cached if x["id"] not in self.CHANNEL]
                if len(to_add):
                    session.add_all(to_add)
                    await session.flush()
                    for channel in to_add:
                        self._add_to_cache(CHANNEL, channel.snowflake_id, channel.id)

        # Get from cache
        ret = [(self.CHANNEL.get(d["id"],None), d.get("reason", None)) for d in channels]
        return ret

    async def _stop_engine(self):
        """
        Closes the engine and the cursor.
        """
        await self.engine.dispose()

    async def _handle_error(self,
                            exception: SQLAlchemyError) -> bool:
        """
        Used to handle errors that happen in the _save_log method.

        Parameters
        ---------------
        exception: SQLAlchemyError
            SQLAlchemy exception

        Return
        --------
        bool
            Returns True on successful handling.
        """
        session: Session
        res = True
        message = str(exception)
        code = exception.code
        time.sleep(SQL_RECOVERY_TIME)
        try:
            # Handle the error
            if code == 208:  # Invalid object name (table deleted)
                self._create_tables()

            elif code in {547, 515}:   # Constraint conflict, NULL value
                r_table = re.search(r'(?<=table "dbo.).+(?=")', message) # Try to parse the table name with regex
                if r_table is not None:
                    self._clear_cache(r_table.group(0))  # Clears only the affected table cache
                else:
                    self._clear_cache()  # Clears all caching tables
                self._generate_lookup_values()

            elif code in {-1, 2, 53}:  # Disconnect error, reconnect after period
                await self._reconnect_after(SQL_RECONNECT_TIME)
                res = False # Don't try to save while reconnecting

            elif code == 2801: # Object was altered (via external source) after procedure was compiled
                pass # Just retry

            elif code == 1205: # Transaction deadlocked
                async with self._sessionmaker() as session:
                    await session.commit()

            else: # No handling instruction known
                res = False

        except Exception:
            # Error could not be handled, stop the engine
            res = False
            await self._stop_engine()

        return res  # Returns if the error was handled or not


    # _async_safe prevents multiple tasks from attempting to do operations on the database at the same time.
    # This is to avoid eg. procedures being called while they are being created,
    # handle error being called from different tasks, update method from causing a race condition,etc
    @misc._async_safe("safe_sem", 1)
    async def _save_log(self,
                        guild_context: dict,
                        message_context: dict):
        """
        This method saves the log generated by the xGUILD object into the database.

        Parameters
        -------------
        guild_context: dict
            Context generated by the xGUILD object, see guild.xGUILD._generate_log() for more info.
        message_context: dict
            Context generated by the xMESSAGE object, see guild.xMESSAGE.generate_log_context() for more info.
        """

        if self.reconnecting:
            # The SQL logger is in the middle of reconnection process
            # This means the logging is switched to something else but we still got here
            # since we entered before that happened and landed on a semaphore.
            await logging.save_log(guild_context, message_context)
            return

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

        _channels = []
        if channels is not None:
            channels = channels['successful'] + channels['failed']


        for tries in range(SQL_MAX_SAVE_ATTEMPTS):
            try:
                # Insert guild into the database and cache if it doesn't exist
                guild_id = await self._get_insert_guild(guild_snowflake, guild_name, guild_type)
                if channels is not None:
                    # Insert channels into the database and cache if it doesn't exist
                    _channels = await self._get_insert_channels(channels, guild_id)
                
                # TODO: Replace with python sqlalchemy code
                #     _channels = pytds.TableValuedParam("t_tmp_channel_log", rows=_channels)
                # # Execute the saved procedure that saves the log
                # self.cursor.callproc("sp_save_log", (json.dumps(sent_data),
                #                                     self.MessageTYPE.get(message_type, None),
                #                                     guild_id,
                #                                     self.MessageMODE.get(message_mode, None),
                #                                     dm_success_info_reason,
                #                                     _channels)) # Execute the stored procedure
                break
            except SQLAlchemyError as ex:
                #####################
                # TODO: Test for correctness
                code = ex.code
                message = str(ex)
                #####################
                trace(f"[SQL]: Saving log failed. Code: {code}, Message: {message}. Attempting recovery... (Tries left: {SQL_MAX_SAVE_ATTEMPTS - tries - 1})", TraceLEVELS.WARNING)
                # Run in executor to prevent blocking
                if not await self._handle_error(code, message):
                    raise DAFSQLError("Unable to handle SQL error", DAF_SQL_SAVE_LOG_ERROR) from ex

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
            await self._stop_engine()
            await misc._update(self, **kwargs)
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

        id = Column(Integer, primary_key=True)
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

        id = Column(Integer, primary_key=True)
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

        id = Column(Integer, primary_key=True)
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

        id = Column(Integer, primary_key=True)
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
        id = Column(Integer, primary_key=True)
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

        id = Column(Integer, primary_key= True)
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

        id = Column(Integer, primary_key=True)
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
