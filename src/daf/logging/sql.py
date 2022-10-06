"""
    The sql module contains definitions related to the
    relational database logging that is available in this shiller.
    It is only used if the sql logging is enabled by passing
    the daf.run function with the SqlCONTROLLER object.

    .. versionchanged:: v2.1
        Made SQL an optional functionality
"""
# TODO: Error recovery
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
SQL_ENABLE_DEBUG = False
# Dictionary mapping the database dialect to it's connector
DIALECT_CONN_MAP = {
    "sqlite" : "aiosqlite",
    "mssql" : "pymssql",
    "postgresql" : "asyncpg",
    "mysql": "asyncmy"
}

# ------------------------------------ Optional ------------------------------------
try:
    from sqlalchemy import (
                            SmallInteger, Integer, BigInteger, DateTime,
                            Column, ForeignKey, Sequence, String, select
                        )            
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.engine import URL as SQLURL, create_engine
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.declarative import declarative_base
    import sqlalchemy as sqa
    GLOBALS.sql_installed = True
    ORMBase = declarative_base()
except ImportError as exc:
    SQLAlchemyError = Exception
    ORMBase = object
    GLOBALS.sql_installed = False
# ----------------------------------------------------------------------------------


__all__ = (
    "LoggerSQL",
)


def register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"], name_override: Optional[str] = None) -> Callable:
    """
    Returns a decorator which will create a row inside <lookuptable> table.

    Parameters
    ------------
    lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"]
        Name of the lookup table to insert the value into.
    name_override: Optional[str]
        Optional name override for the object to insert into the ``lookuptable``.
        If this is not passed, class name is used.

    Raises
    --------------
    ValueError
        Lookup table not found.
    """
    def decorator_register_type(cls):
        # Iterate thru all module globals to find the lookup table
        if GLOBALS.sql_installed:
            for table_cls in ORMBase.__subclasses__():
                if table_cls.__tablename__ == lookuptable:
                    GLOBALS.lt_types.append( table_cls(name_override if name_override is not None else cls.__name__) )
                    break
            else:
                raise ValueError(f"Lookup table {lookuptable} not found")
        
        return cls
    
    return decorator_register_type


@misc.doc_category("Logging related", path="logging.sql")
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

    Raises
    ----------
    ValueError
        Unsupported dialect (db type).
    """

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

        if dialect not in DIALECT_CONN_MAP:
            raise ValueError(f"Unsupported dialect (db type): '{dialect}'. Supported types are: {tuple(DIALECT_CONN_MAP.keys())}.")

        # Save the connection parameters
        self.is_async = False # Set in _begin_engine
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

        # Set in ._begin_engine
        self.engine: sqa.engine.Engine = None
        self.session_maker: sessionmaker = None

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
        self.DataHISTORY = {}

        super().__init__(fallback)

    async def _run_async(self, method: Callable, *args, **kwargs):
        """
        Helper method that abstracts calls of
        non async functions so await can always be used

        Parameters
        -----------
        method: Callable
            The async/non-async method to call
        args
            Positional arguments for the method
        kwargs
            Keyword arguments for the method
        """
        result = method(*args, **kwargs)
        if self.is_async:
            result = await result

        return result

    def _add_to_cache(self, table: ORMBase, key: Any, value: Any) -> None:
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
            to_clear = [table.__name__ for table in ORMBase.__subclasses__() if table.__name__ in self.__slots__]
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
        session : Union[Session, AsyncSession]
        try:
            trace("[SQL]: Generating lookuptable values...", TraceLEVELS.NORMAL)
            async with self.session_maker() as session:
                for to_add in copy.deepcopy(GLOBALS.lt_types):  # Deep copied to prevent SQLAlchemy from deleting the data
                    existing = await self._run_async(session.execute, select(type(to_add)).where(type(to_add).name == to_add.name))
                    existing = existing.fetchone()
                    if existing is not None:
                        existing = existing[0]
                    else:
                        session.add(to_add)
                        await self._run_async(session.flush)
                        existing = to_add

                    self._add_to_cache(type(to_add), to_add.name, existing.id)
                
                await self._run_async(session.commit)
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
            session: AsyncSession
            trace("[SQL]: Creating tables...", TraceLEVELS.NORMAL)
            if self.is_async:
                async with self.engine.begin() as tran:
                    await tran.run_sync(ORMBase.metadata.create_all)
            else:
                with self.engine.connect() as tran:
                    tran.run_callable(ORMBase.metadata.create_all)
            
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
            if dialect == "mssql":
                # The only dialect that doesn't have async connectors
                self.is_async = False
                create_engine_ = create_engine
                session_class = Session
            else:
                self.is_async = True
                create_engine_ = create_async_engine
                session_class = AsyncSession
            
            sqlurl = SQLURL.create(
                f"{dialect}+{DIALECT_CONN_MAP[dialect]}",
                self.username,
                self.password,
                self.server,
                self.port,
                self.database
            )

            self.engine = create_engine_(sqlurl,
                                         echo=SQL_ENABLE_DEBUG)

            class SessionWrapper(session_class):
                """
                Wrapper class for the session that can always be used
                in async mode, even if the session it wraps is not async.
                """
                async def __aenter__(self_):
                    if self.is_async:
                        return await super().__aenter__()

                    return super().__enter__()
                
                async def __aexit__(self_, *args):
                    if self.is_async:
                        return await super().__aexit__(*args)

                    return super().__exit__(*args)

            self.session_maker = sessionmaker(bind=self.engine, class_=SessionWrapper)
        except Exception as ex:
            raise DAFSQLError(f"Unable to start engine.\nError: {ex}", DAF_SQL_BEGIN_ENGINE_ERROR)

    async def initialize(self) -> None:
        """
        This method initializes the connection to the database, creates the missing tables
        and fills the lookup tables with types defined by the register_type(lookup_table) function.

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
                        guild_type: int,
                        session: AsyncSession) -> int:
        """
        Inserts the guild into the db if it doesn't exist,
        adds it to cache and returns it's internal db id from cache.

        Parameters
        ------------
        snowflake: int
            The snowflake of the guild.
        name: name
            The name of the guild.
        guild_type: int
            ID of key pointing to guild_type.
        session: AsyncSession
            The session to use as transaction.
        """
        result = None
        if snowflake not in self.GuildUSER:
            result = await self._run_async(session.execute, select(GuildUSER.id).where(GuildUSER.snowflake_id == snowflake))

            result = result.first()
            if result is not None:
                result = result[0]
                self._add_to_cache(GuildUSER, snowflake, result)
            else:
                result = GuildUSER(guild_type, snowflake, name)
                savepoint = await self._run_async(session.begin_nested) # Savepoint
                session.add(result)
                await self._run_async(savepoint.commit)
                result = result.id
                self._add_to_cache(GuildUSER, snowflake, result)
        else:
            result = self.GuildUSER[snowflake]

        return result

    async def _get_insert_channels(self,
                                   channels: List[dict],
                                   guild_id: int,
                                   session: AsyncSession) -> List[Dict[int, Union[str, None]]]:
        """
        Adds missing channels to the database, then caches those added
        for performance.

        Parameters
        ------------
        channels: List[dict],
            List of dictionaries containing values for snowflake id ("id") and name of the channel ("name"). If sending to failed, it also contains text like description of the error ("reason").
        guild_id: int
            The internal DB id of the guild where the channels are in.
        session: AsyncSession:
            Session to use for transaction.

        Return
        -------------
        List[Dict[int, Union[str, None]]]
            List of dictionaries containing database ID of a channel and a reason why sending to channel failed.
        """

        # Put into cache if it is not already
        not_cached = [{"id": x["id"], "name": x["name"]} for x in channels if x["id"] not in self.CHANNEL] # Get snowflakes that are not cached
        not_cached_snow = [x["id"] for x in not_cached]
        if len(not_cached):
            # Search the database for non cached channels
            result = await self._run_async(session.execute, select(CHANNEL.id, CHANNEL.snowflake_id).where(CHANNEL.snowflake_id.in_(not_cached_snow)))
            result = result.all()
            for internal_id, snowflake_id in result:
                self._add_to_cache(CHANNEL, snowflake_id, internal_id)
            
            # Add the channels that are not in the database
            to_add = [CHANNEL(x["id"], x["name"], guild_id) for x in not_cached if x["id"] not in self.CHANNEL]
            if len(to_add):
                savepoint = await self._run_async(session.begin_nested) # Savepoint
                session.add_all(to_add)
                await self._run_async(savepoint.commit)
                for channel in to_add:
                    self._add_to_cache(CHANNEL, channel.snowflake_id, channel.id)

        # Get from cache
        ret = [{"id" : self.CHANNEL.get(d["id"], None), "reason" : d.get("reason", None)} for d in channels]
        return ret

    async def _get_insert_data(self, data: dict, session: AsyncSession) -> int:
        """
        Get's data's row ID from the cache/database, if it does not exists,
        it inserts into the database and then caches the value.

        Parameters
        -------------
        data: dict
            The data dictionary which represents sent data
        session: AsyncSession
            Session to use for transaction.

        Returns
        -------------
        int
            Primary key of a row inside DataHISTORY table.
        """
        json_data = json.dumps(data)
        result: tuple = None
        if json_data not in self.DataHISTORY:
            result = await self._run_async(session.execute, select(DataHISTORY.id).where(DataHISTORY.content == json_data))
            result = result.first()
            if result is None:
                # Add to the database
                to_add = DataHISTORY(json_data)
                savepoint = await self._run_async(session.begin_nested)
                session.add(to_add)
                await self._run_async(savepoint.commit)
                result = (to_add.id,)
            
            self._add_to_cache(DataHISTORY, json_data, result[0])

        return self.DataHISTORY.get(json_data)
            
    async def _stop_engine(self):
        """
        Closes the engine and the cursor.
        """
        await self._run_async(self.engine.dispose)

    async def _handle_error(self,
                            exc: SQLAlchemyError) -> bool:
        """
        Used to handle errors that happen in the _save_log method.

        Parameters
        ---------------
        exc: SQLAlchemyError
            The exception object.

        Return
        --------
        bool
            Returns True on successful handling.
        """
        session: AsyncSession
        message = exc.args[0]
        res = True
        await asyncio.sleep(SQL_RECOVERY_TIME)
        try:
            # TODO: Update to work on latest version
            # Handle the error
            if "no such table" in message:  # Invalid object name (table deleted)
                await self._create_tables()

            elif "" in message:   # Constraint conflict, NULL value
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
                async with self.session_maker() as session:
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
    @timeit(5)
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
        channels: List[dict] = message_context.get("channels", None)
        dm_success_info: dict = message_context.get("success_info", None)
        dm_success_info_reason: str = None

        # Lookup table values
        guild_type: int = self.GuildTYPE.get(guild_context["type"])
        message_type: int = self.MessageTYPE.get(message_context["type"])
        message_mode: Union[int, str, None] = message_context.get("mode", None)
        if message_mode is not None:
            message_mode = self.MessageMODE.get(message_mode)

        if dm_success_info is not None:
            if "reason" in dm_success_info:
                dm_success_info_reason = dm_success_info["reason"]

        _channels = []
        if channels is not None:
            channels = channels['successful'] + channels['failed']


        for tries in range(SQL_MAX_SAVE_ATTEMPTS):
            try:
                # Insert guild into the database and cache if it doesn't exist
                session: AsyncSession
                async with self.session_maker() as session:
                    guild_id = await self._get_insert_guild(guild_snowflake, guild_name, guild_type, session)
                    if channels is not None:
                    # Insert channels into the database and cache if it doesn't exist
                        _channels = await self._get_insert_channels(channels, guild_id, session)

                    data_id = await self._get_insert_data(sent_data, session)

                    # Save message log
                    message_log = MessageLOG(data_id, message_type, message_mode, dm_success_info_reason, guild_id)
                    session.add(message_log)
                    await self._run_async(session.flush)
                    if channels is not None:
                        to_add = [MessageChannelLOG(message_log.id, ch_id, reason) for ch_id, reason in (channel.values() for channel in _channels)]
                        session.add_all(to_add)

                    await self._run_async(session.commit)

                break
            except SQLAlchemyError as exc:
                # Run in executor to prevent blocking
                if not await self._handle_error(exc):
                    raise DAFSQLError("Unable to handle SQL error", DAF_SQL_SAVE_LOG_ERROR) from exc

        else:
            DAFSQLError(f"Unable to save log within {SQL_MAX_SAVE_ATTEMPTS} tries", DAF_SQL_SAVE_LOG_ERROR)

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
    class MessageTYPE(ORMBase):
        """
        Lookup table for storing xMESSAGE types

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """
        __tablename__ = "MessageTYPE"

        id = Column(SmallInteger().with_variant(Integer, "sqlite"), Sequence("msg_tp_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True), primary_key=True)
        name = Column(String(3072), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class MessageMODE(ORMBase):
        """
        Lookup table for storing message sending modes.

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """

        __tablename__ = "MessageMODE"

        id = Column(SmallInteger().with_variant(Integer, "sqlite"), Sequence("msg_mode_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True), primary_key=True)
        name = Column(String(3072), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class GuildTYPE(ORMBase):
        """
        Lookup table for storing xGUILD types

        Parameters
        -----------
        name: str
            Name of the xMESSAGE class.
        """

        __tablename__ = "GuildTYPE"

        id = Column(SmallInteger().with_variant(Integer, "sqlite"), Sequence("guild_tp_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True),  primary_key=True)
        name = Column(String(3072), unique=True)

        def __init__(self, name: str=None):
            self.name = name


    class GuildUSER(ORMBase):
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

        id = Column(Integer, Sequence("guild_user_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True), primary_key=True)
        snowflake_id = Column(BigInteger)
        name = Column(String(3072))
        guild_type = Column(SmallInteger, ForeignKey("GuildTYPE.id"), nullable=False)

        def __init__(self,
                    guild_type: int,
                    snowflake: int,
                    name: str):
            self.snowflake_id = snowflake
            self.name = name
            self.guild_type = guild_type


    class CHANNEL(ORMBase):
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
        id = Column(Integer, Sequence("channel_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True), primary_key=True)
        snowflake_id = Column(BigInteger)
        name = Column(String(3072))
        guild_id = Column(Integer, ForeignKey("GuildUSER.id"), nullable=False)

        def __init__(self,
                    snowflake: int,
                    name: str,
                    guild_id: int):
            self.snowflake_id = snowflake
            self.name = name
            self.guild_id = guild_id


    class DataHISTORY(ORMBase):
        """
        Table used for storing all the different data(JSON) that was ever sent (to reduce redundancy -> and file size in the MessageLOG).

        Parameters
        -----------
        content: str
            The JSON string representing sent data.
        """
        __tablename__ = "DataHISTORY"

        id = Column(Integer, Sequence("dhist_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True), primary_key= True)
        content = Column(String(3072))

        def __init__(self,
                    content: str):
            self.content = content

    class MessageLOG(ORMBase):
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

        id = Column(Integer, Sequence("ml_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True), primary_key=True)
        sent_data = Column(Integer, ForeignKey("DataHISTORY.id"))
        message_type = Column(SmallInteger, ForeignKey("MessageTYPE.id"), nullable=False)
        guild_id = Column(Integer, ForeignKey("GuildUSER.id"), nullable=False)
        message_mode = Column(SmallInteger, ForeignKey("MessageMODE.id")) # [TextMESSAGE, DirectMESSAGE]
        dm_reason = Column(String(3072))  # [DirectMESSAGE]
        timestamp = Column(DateTime)

        def __init__(self,
                    sent_data: int=None,
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


    class MessageChannelLOG(ORMBase):
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
        reason = Column(String(3072))
        def __init__(self,
                    message_log_id: int,
                    channel_id: int,
                    reason: str=None):
            self.log_id = message_log_id
            self.channel_id = channel_id
            self.reason = reason
