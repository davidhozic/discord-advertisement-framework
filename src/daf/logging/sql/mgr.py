"""
    The sql module contains definitions related to the relational database logging.

    .. versionchanged:: v2.7
        Added Discord invite link tracking.
"""
from datetime import datetime, date
from typing import Callable, Dict, List, Literal, Any, Union, Optional, Tuple, get_args
from contextlib import suppress
from pathlib import Path
from typeguard import typechecked

from ..tracing import TraceLEVELS, trace
from .. import _logging as logging
from ...misc import doc, instance_track, async_util

import json
import copy
import asyncio


class GLOBALS:
    """
    Stores global module variables.
    """
    lt_types = []


# ------------------------------------ Configuration -------------------------------
SQL_MAX_SAVE_ATTEMPTS = 5
SQL_RECOVERY_TIME = 1
SQL_RECONNECT_TIME = 5 * 60
SQL_ENABLE_DEBUG = False
SQL_TABLE_CACHE_SIZE = 1000
# Dictionary mapping the database dialect to it's connector
DIALECT_CONN_MAP = {
    "sqlite": "aiosqlite",
    "mssql": "pymssql",
    "postgresql": "asyncpg",
    "mysql": "asyncmy"
}
# ------------------------------------ Optional ------------------------------------
try:
    from .tables import *

    from sqlalchemy import (
        select, text, case, delete, func,
        Integer, String, event,
    )
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.engine import URL as SQLURL, create_engine
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import (
        sessionmaker,
        Session,
    )
    import sqlalchemy as sqa
    import aiosqlite

    SQL_INSTALLED = True
except ImportError:
    AsyncSession = object
    Session = object
    SQLAlchemyError = Exception
    ORMBase = object
    SQL_INSTALLED = False
# ----------------------------------------------------------------------------------


__all__ = (
    "LoggerSQL",
    "register_type",
    "SQL_INSTALLED",
)


def register_type(lookuptable: Literal["GuildTYPE", "MessageTYPE", "MessageMODE"],
                  name_override: Optional[str] = None) -> Callable:
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
        if SQL_INSTALLED:
            for table_cls in ORMBase.__subclasses__():
                if table_cls.__tablename__ == lookuptable:
                    GLOBALS.lt_types.append(table_cls(name_override if name_override is not None else cls.__name__))
                    break
            else:
                raise ValueError(f"Lookup table {lookuptable} not found")

        return cls

    if name_override is not None:
        return decorator_register_type(object)

    return decorator_register_type


class TableCache:
    """
    Used for caching table values to IDs for faster access.
    When maximum cache is exceeded, 1/4 of the first added elements is purged
    from cache.

    Parameters
    -------------
    table: ORMBase
        The table this cache is for.
    limit: int
        Max elements to hold.
    """
    def __init__(self, table: ORMBase, limit: int):
        self.table = table
        self.limit = limit
        self.data = {}

    def insert(self, key: Any, value: Any) -> None:
        """
        Inserts value to a specific key

        Parameters
        ------------
        key: Any
            Where to insert.
        value: Any
            What to insert.
        """
        if len(self.data) == self.limit:
            # Remove 1/4 of the cache
            for i in range(int(len(self.data) / 4)):
                self.remove()

        if key in self.data:
            # Remove the value if it already exists
            del self.data[key]

        # Add item to cache
        self.data[key] = value

    def get(self, key: Any) -> Any:
        """
        Returns the cached value.

        Parameters
        key: Any
            The key at which cached value is located.
        """
        return self.data.get(key)

    def remove(self, key: Optional[Any] = None) -> None:
        """
        Removes the cache item at key.

        Parameters
        ------------
        key: Optional[Any]
            The key at which to remove the cached object.
            If not passed, removes first element in cache.

        Raises
        ---------
        ValueError
            The item is not present in the cache.
        ValueError
            No elements are present in cache.
        """
        if key is None:
            if not len(self.data):
                raise ValueError("No elements are present in cache.")

            key = next(iter(self.data))

        del self.data[key]

    def clear(self) -> None:
        "Clears the cache of all values"
        self.data.clear()

    def get_table(self) -> ORMBase:
        "Returns the table this cache is for"
        return self.table

    def exists(self, key: Any) -> bool:
        """
        Returns True if the key is cached.

        Parameters
        -----------
        key: Any
            Cache key to check.
        """
        return key in self.data


@instance_track.track_id
@doc.doc_category("Logging reference", path="logging.sql")
class LoggerSQL(logging.LoggerBASE):
    """
    .. versionchanged:: v2.7

        - Invite link tracking.
        - Default database file output set to /<user-home-dir>/daf/messages

    Used for controlling the SQL database used for message logs.

    Parameters
    ------------
    username: Optional[str]
        Username to login to the database with.
    password: Optional[str]
        Password to use when logging into the database.
    server: Optional[str]
        Address of the server.
    port: Optional[int]
        The port of the database server.
    database: Optional[str]
        Name of the database used for logs.
    dialect: Optional[str]
        Dialect or database type (SQLite, mssql, )
    fallback: Optional[LoggerBASE]
        The fallback manager to use in case SQL logging fails.
        (Default: :class:`~daf.logging.LoggerJSON` ("History"))

    Raises
    ----------
    ValueError
        Unsupported dialect (db type).
    ModuleNotFoundError
        Extra requirements are required.
    """

    @typechecked
    def __init__(self,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 server: Optional[str] = None,
                 port: Optional[int] = None,
                 database: Optional[str] = None,
                 dialect: Literal["sqlite", "mssql", "postgresql", "mysql"] = None,
                 fallback: Optional[logging.LoggerBASE] = ...):

        if not SQL_INSTALLED:
            raise ModuleNotFoundError("Need to install extra requirements: pip install discord-advert-framework[sql]")

        if fallback is Ellipsis:
            # Cannot use None as this can be a legit user value
            # and cannot pass directly due to Sphinx issues
            fallback = logging.LoggerJSON()

        if dialect is None:
            dialect = "sqlite"

        dialect = dialect.lower()
        if dialect not in DIALECT_CONN_MAP:
            raise ValueError(f"Unsupported 'dialect': '{dialect}'. Supported: {tuple(DIALECT_CONN_MAP.keys())}.")

        # Save the connection parameters
        self.is_async = False  # Set in _begin_engine
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.database = database if database is not None else str(Path.home().joinpath("daf/messages"))
        self.dialect = dialect

        if self.dialect == "sqlite":
            self.database += ".db"
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)

        # Set in ._begin_engine
        self.engine: sqa.engine.Engine = None
        self.session_maker: sessionmaker = None
        self.reconnecting = False  # Flag that is True while reconnecting, used for emergency exit of other tasks

        # Caching (to avoid unnecessary queries)
        # Lookup table caching
        self.message_mode_cache = TableCache(MessageMODE, SQL_TABLE_CACHE_SIZE)
        self.message_type_cache = TableCache(MessageTYPE, SQL_TABLE_CACHE_SIZE)
        self.guild_type_cache = TableCache(GuildTYPE, SQL_TABLE_CACHE_SIZE)

        # Other object caching
        self.guild_user_cache = TableCache(GuildUSER, SQL_TABLE_CACHE_SIZE)
        self.channel_cache = TableCache(CHANNEL, SQL_TABLE_CACHE_SIZE)
        self.data_history_cache = TableCache(DataHISTORY, SQL_TABLE_CACHE_SIZE)
        self.invites_cache = TableCache(Invite, SQL_TABLE_CACHE_SIZE)

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
        raise NotImplementedError  # This function is defined in .begin_engine

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
        for var in vars(self).values():
            if isinstance(var, TableCache) and table is var.get_table():
                var.insert(key, value)

    def _clear_caches(self, *to_clear: str) -> None:
        """
        Clears the caching dictionaries inside the object that match any of the tables.

        Parameters
        -----------
        *to_clear: str
            Custom number of positional arguments of caching dictionaries to clear.
        """
        if len(to_clear) == 0:  # Clear all cached tables if nothing was passed
            to_clear = [cache for cache in vars(self).values() if isinstance(cache, TableCache)]
        else:
            to_clear = [getattr(self, table) for table in to_clear if hasattr(self, table)]

        for k in to_clear:
            k.clear()

    async def _reconnect_after(self, wait: int) -> None:
        """
        Reconnects the SQL manager to the database after <wait> if it was disconnected.

        Parameters
        -----------
        wait: int
            Time in seconds after which reconnect.
        """
        async def _reconnector():
            session: Union[Session, AsyncSession]
            # Always try to reconnect
            while True:
                trace(f"Retrying to connect in {wait} seconds.")
                await asyncio.sleep(wait)
                trace(f"Reconnecting to database {self.database}.")
                with suppress(SQLAlchemyError, ConnectionError):
                    async with self.session_maker() as session:
                        await self._run_async(session.execute, select(text("1")))  # Test with SELECT 1;

                    trace(f"Reconnected to the database {self.database}.")
                    self.reconnecting = False
                    logging._set_logger(self)
                    return

        self.reconnecting = True
        logging._set_logger(self.fallback)
        asyncio.create_task(_reconnector())

    async def _generate_lookup_values(self) -> None:
        """
        Generates the lookup values for all the different classes the @register_type decorator was used on.

        Raises
        -------------
        RuntimeError
            Raised when lookuptable values could not be inserted into the database.
        """
        try:
            trace("Generating lookuptable values...", TraceLEVELS.NORMAL)
            async with self.session_maker() as session:
                # Deep copied to prevent SQLAlchemy from deleting the data
                for to_add in copy.deepcopy(GLOBALS.lt_types):
                    existing = await self._run_async(
                        session.execute,
                        select(type(to_add)).where(type(to_add).name == to_add.name)
                    )
                    existing = existing.fetchone()
                    if existing is not None:
                        existing = existing[0]
                    else:
                        session.add(to_add)
                        await self._run_async(session.commit)
                        existing = to_add

                    self._add_to_cache(type(to_add), to_add.name, existing)
        except Exception as ex:
            raise RuntimeError("Unable to create lookuptables' rows.") from ex

    async def _create_tables(self) -> None:
        """
        Creates tables from the SQLAlchemy's descriptor classes

        Raises
        -----------
        RuntimeError
            Raised when tables could not be created.
        """
        try:
            trace("Creating tables...", TraceLEVELS.NORMAL)
            if self.is_async:
                async with self.engine.begin() as tran:
                    await tran.run_sync(ORMBase.metadata.create_all)
            else:
                with self.engine.connect() as tran:
                    tran.run_callable(ORMBase.metadata.create_all)

        except Exception as ex:
            raise RuntimeError("Unable to create all the tables.") from ex

    def _begin_engine(self) -> None:
        """
        Creates the sqlalchemy engine.

        Raises
        ----------------
        RuntimeError
            Raised when the engine could not connect to the specified database.
        """
        try:
            dialect = self.dialect
            if dialect == "mssql":
                # The only dialect that doesn't have async connectors
                async def _run_async(method: Callable, *args, **kwargs):
                    return method(*args, **kwargs)

                self.is_async = False
                create_engine_ = create_engine
                session_class = Session
            else:
                async def _run_async(method: Callable, *args, **kwargs):
                    return await method(*args, **kwargs)

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

            self.engine = create_engine_(sqlurl, echo=SQL_ENABLE_DEBUG)

            if dialect == "sqlite":  # Enable foreign keys for SQLite to allow cascades
                def on_connect(dbapi_conn, conn_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")

                event.listen(self.engine.sync_engine if self.is_async else self.engine, "connect", on_connect)

            self._run_async = _run_async

            class SessionWrapper(session_class):
                """
                Wrapper class for the session that can always be used
                in async mode, even if the session it wraps is not async.
                """
                if self.is_async:
                    async def __aenter__(self_):
                        return await super().__aenter__()

                    async def __aexit__(self_, *args):
                        return await super().__aexit__(*args)
                else:
                    async def __aenter__(self_):
                        return self_.__enter__()

                    async def __aexit__(self_, *args):
                        return self_.__exit__(*args)

            self.session_maker = sessionmaker(bind=self.engine, class_=SessionWrapper, expire_on_commit=False)
        except Exception as ex:
            raise RuntimeError(f"Unable to start engine.\nError: {ex}")

    async def initialize(self) -> None:
        """
        This method initializes the connection to the database, creates the missing tables
        and fills the lookup tables with types defined by the register_type(lookup_table) function.

        .. note::
            This is automatically called when running the daf.

        Raises
        -----------
        Any
            from ``._begin_engine()``
            from ``._create_tables()``
            from ``._generate_lookup_values()``
        """
        trace(f"{type(self).__name__} logs will be saved to {self.database}")
        # Create engine for communicating with the SQL base
        self._begin_engine()
        # Create tables and the session class bound to the engine
        await self._create_tables()
        # Insert the lookuptable values
        await self._generate_lookup_values()
        await super().initialize()

    async def __get_insert_base(
        self,
        key: Any,
        cache_object: TableCache,
        compare_key,
        type_: type,
        session: Union[AsyncSession, Session],
        *args,
        **kwargs
    ):
        result = None
        if not cache_object.exists(key):
            result = await self._run_async(
                session.execute,
                select(type_).where(compare_key)
            )
            result = result.first()
            if result is not None:
                result = result[0]
            else:
                result = type_(*args, **kwargs)
                session.add(result)
                await self._run_async(session.commit)
                await self._run_async(session.begin)
                result = result

            cache_object.insert(key, result)
        else:
            result = cache_object.get(key)

        return result

    def _get_insert_invite(
        self,
        id_: str,
        guild: "GuildUSER",
        session: Union[AsyncSession, Session]
    ) -> int:
        """
        Inserts the invite link into the db if it doesn't exist,
        adds it to cache and returns it's internal db id from cache.

        Parameters
        ------------
        id_: str
            The invite link ID (final part of URL).
        guild: GuildUSER,
            The guild that
        session: Union[AsyncSession, Session]
            The session to use as transaction.
        """
        return self.__get_insert_base(id_, self.invites_cache, Invite.discord_id == id_, Invite, session, id_, guild)

    def _get_insert_guild(self,
                          snowflake: int,
                          name: str,
                          guild_type: int,
                          session: Union[AsyncSession, Session]) -> int:
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
        session: Union[AsyncSession, Session]
            The session to use as transaction.
        """
        return self.__get_insert_base(
            snowflake,
            self.guild_user_cache,
            GuildUSER.snowflake_id == snowflake,
            GuildUSER,
            session,
            guild_type,
            snowflake,
            name
        )

    async def _get_insert_channels(self,
                                   channels: List[dict],
                                   guild: "GuildUSER",
                                   session: Union[AsyncSession, Session]) -> List[Dict[int, Union[str, None]]]:
        """
        Adds missing channels to the database, then caches those added
        for performance.

        Parameters
        ------------
        channels: List[dict]
            List of dictionaries containing values for snowflake id ("id") and name of the channel ("name").
            If sending to failed, it also contains text like description of the error ("reason").
        guild: GuildUSER
            The internal DB id of the guild where the channels are in.
        session: Union[AsyncSession, Session]
            Session to use for transaction.

        Return
        -------------
        List[Dict[int, Union[str, None]]]
            List of dictionaries containing database ID of a channel and a reason why sending to channel failed.
        """

        # Put into cache if it is not already
        # Get snowflakes that are not cached
        not_cached = [{"id": x["id"], "name": x["name"]} for x in channels if not self.channel_cache.exists(x["id"])]
        not_cached_snow = [x["id"] for x in not_cached]
        if len(not_cached):
            # Search the database for non cached channels
            result = await self._run_async(
                session.execute,
                select(CHANNEL).where(CHANNEL.snowflake_id.in_(not_cached_snow))
            )
            result = result.all()
            for (channel,) in result:
                self.channel_cache.insert(channel.snowflake_id, channel)

            # Add the channels that are not in the database
            to_add = [
                CHANNEL(x["id"], x["name"], guild)
                for x in not_cached if not self.channel_cache.exists(x["id"])
            ]
            if len(to_add):
                session.add_all(to_add)
                await self._run_async(session.commit)
                await self._run_async(session.begin)
                for channel in to_add:
                    self.channel_cache.insert(channel.snowflake_id, channel)

        # Get from cache
        ret = [(self.channel_cache.get(d["id"]), d.get("reason", None)) for d in channels]
        return ret

    def _get_insert_data(self, data: dict, session: Union[AsyncSession, Session]) -> int:
        """
        Get's data's row ID from the cache/database, if it does not exists,
        it inserts into the database and then caches the value.

        Parameters
        -------------
        data: dict
            The data dictionary which represents sent data
        session: Union[AsyncSession, Session]
            Session to use for transaction.

        Returns
        -------------
        int
            Primary key of a row inside DataHISTORY table.
        """
        const_data = json.dumps(data)
        return self.__get_insert_base(
            const_data,
            self.data_history_cache,
            DataHISTORY.content.cast(String) == const_data,
            DataHISTORY,
            session,
            const_data
        )

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
        res = True
        await asyncio.sleep(SQL_RECOVERY_TIME)
        try:
            if getattr(exc, "connection_invalidated", False):
                res = False
                await self._reconnect_after(SQL_RECONNECT_TIME)
            else:
                if self.dialect == "sqlite":
                    Path(self.database).parent.mkdir(parents=True, exist_ok=True)

                await self._create_tables()
                self._clear_caches()
                await self._generate_lookup_values()

        except Exception:
            # Error could not be handled, stop the engine
            res = False
            await self._stop_engine()

        return res  # Returns if the error was handled or not

    async def _save_log_invite(
        self,
        session: Union[AsyncSession, Session],
        guild_context: dict,
        invite_context: dict
    ):
        # Parse the data
        guild_snowflake: int = guild_context.get("id")
        guild_name: str = guild_context.get("name")
        invite_id: str = invite_context.get("id")
        invite_member_id = invite_context["member"].get("id")
        invite_member_name = invite_context["member"].get("name")

        # Lookup table values
        guild_type_obj = self.guild_type_cache.get(guild_context["type"])
        # Insert guild into the database and cache if it doesn't exist
        guild_obj = await self._get_insert_guild(guild_snowflake, guild_name, guild_type_obj, session)
        member_obj = await self._get_insert_guild(
            invite_member_id,
            invite_member_name,
            self.guild_type_cache.get("USER"),
            session
        )
        invite_obj = await self._get_insert_invite(invite_id, guild_obj, session)
        invite_log_obj = InviteLOG(
            invite_obj,
            member_obj
        )
        session.add(invite_log_obj)

    async def _save_log_message(
        self,
        session: Union[AsyncSession, Session],
        guild_context: dict,
        message_context: Optional[dict] = None,
        author_context: Optional[dict] = None,
    ):
        # Parse the data
        author_name: str = author_context.get("name")
        author_snowflake: str = author_context.get("id")
        sent_data: dict = message_context.get("sent_data")
        guild_snowflake: int = guild_context.get("id")
        guild_name: str = guild_context.get("name")
        channels: List[dict] = message_context.get("channels", None)
        dm_success_info: dict = message_context.get("success_info", None)
        dm_success_info_reason: str = None
        message_mode: Union[int, str, None] = message_context.get("mode", None)

        if dm_success_info is not None and "reason" in dm_success_info:
            dm_success_info_reason = dm_success_info["reason"]

        _channels = []
        if channels is not None:
            channels = channels['successful'] + channels['failed']

        # Lookup table values
        guild_type_obj = self.guild_type_cache.get(guild_context["type"])
        message_type_obj = self.message_type_cache.get(message_context["type"])
        message_mode_obj = self.message_mode_cache.get(message_mode)
        # Insert guild into the database and cache if it doesn't exist
        guild_obj = await self._get_insert_guild(guild_snowflake, guild_name, guild_type_obj, session)
        if channels is not None:
            # Insert channels into the database and cache if it doesn't exist
            _channels = await self._get_insert_channels(channels, guild_obj, session)

        data_obj = await self._get_insert_data(sent_data, session)
        author_obj = await self._get_insert_guild(
            author_snowflake,
            author_name,
            self.guild_type_cache.get("USER"),
            session
        )

        # Save message log
        message_log_obj = MessageLOG(
            data_obj,
            message_type_obj,
            message_mode_obj,
            dm_success_info_reason,
            guild_obj,
            author_obj,
            [
                MessageChannelLOG(channel, reason)
                for channel, reason in _channels
            ],
        )
        session.add(message_log_obj)

    # with_semaphore prevents multiple tasks from attempting to do operations on the database at the same time.
    @async_util.with_semaphore("_mutex")
    async def _save_log(
        self,
        guild_context: dict,
        message_context: Optional[dict] = None,
        author_context: Optional[dict] = None,
        invite_context: Optional[dict] = None
    ):
        """
        This method saves the log generated by the xGUILD object into the database.

        Parameters
        -------------
        guild_context: dict
            Context generated by the xGUILD object, see guild.xGUILD.generate_log_context() for more info.
        message_context: dict
            Context generated by the xMESSAGE object, see guild.xMESSAGE.generate_log_context() for more info.
        author_context: dict
            Context generated by the ACCOUNT object, see ACCOUNT.generate_log_context() for more info.

        Raises
        --------
        RuntimeError
            Saving failed within n times or error recovery failed.
        """

        if self.reconnecting:
            # The SQL logger is in the middle of reconnection process
            return await logging.save_log(guild_context, message_context)

        for _ in range(SQL_MAX_SAVE_ATTEMPTS):
            try:
                async with self.session_maker() as session:
                    if message_context is not None:  # Message tracking
                        await self._save_log_message(session, guild_context, message_context, author_context)
                    else:  # Invite tracking
                        await self._save_log_invite(session, guild_context, invite_context)

                    await self._run_async(session.commit)

                return
            except SQLAlchemyError as exc:
                if not await self._handle_error(exc):
                    raise RuntimeError("Unable to handle SQL error") from exc

        raise RuntimeError(f"Unable to save invite log within {SQL_MAX_SAVE_ATTEMPTS} tries")

    async def _get_guild(self, id_: int, session: Union[AsyncSession, Session]):
        guilduser: GuildUSER = self.guild_user_cache.get(id_)
        if guilduser is not None:
            return guilduser

        try:
            _ret = (
                await self._run_async(session.execute, select(GuildUSER).where(GuildUSER.snowflake_id == id_))
            ).first()
            return _ret[0] if _ret is not None else None
        except SQLAlchemyError:
            return None

    async def analytic_get_num_messages(
        self,
        guild: Union[int, None] = None,
        author: Union[int, None] = None,
        after: datetime = datetime.min,
        before: datetime = datetime.max,
        guild_type: Union[Literal["USER", "GUILD"], None] = None,
        message_type: Union[Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"], None] = None,
        sort_by: Literal["successful", "failed", "guild_snow", "guild_name", "author_snow", "author_name"] = "successful",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
        group_by: Literal["year", "month", "day"] = "day"
    ) -> List[Tuple[date, int, int, int, str, int, str]]:
        """
        Counts all the messages in the configured group based on parameters.

        Parameters
        -----------
        guild: int
            The snowflake id of the guild.
        author: int
            The snowflake id of the author.
        after: Union[datetime, None] = None
            Only count messages sent after the datetime.
        before: Union[datetime, None]
            Only count messages sent before the datetime.
        guild_type: Literal["USER", "GUILD"] | None,
            Type of guild.
        message_type: Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"] | None,
            Type of message.
        sort_by: Literal["successful", "failed", "guild_snow", "guild_name", "author_snow", "author_name"],
            Sort items by selected.
            Defaults to "successful"
        sort_by_direction: Literal["asc", "desc"]
            Sort items by ``sort_by`` in selected direction (asc = ascending, desc = descending).
            Defaults to "desc"
        limit: int = 500
            Limit of the rows to return. Defaults to 500.
        group_by: Literal["year", "month", "day"]
            Results returned are grouped by ``group_by``

        Returns
        --------
        list[tuple[date, int, int, int, str, int, str]]
            List of tuples.

            Each tuple contains:

            - Date
            - Successfule sends
            - Failed sends
            - Guild snowflake id,
            - Guild name
            - Author snowflake id,
            - Author name

        Raises
        ------------
        SQLAlchemyError
            There was a problem with the database.
        """
        args = get_args(self.analytic_get_num_messages.__annotations__["sort_by"])
        if sort_by not in args:
            raise ValueError(f"sort_by expected any of {args}. Got '{sort_by}'")

        async with self.session_maker() as session:
            conditions = [MessageLOG.timestamp.between(after, before)]
            if guild is not None:
                conditions.append(MessageLOG.guild.has(GuildUSER.snowflake_id == guild))

            if author is not None:
                conditions.append(MessageLOG.author.has(GuildUSER.snowflake_id == author))

            if guild_type is not None:
                conditions.append(MessageLOG.guild.has(GuildUSER.guild_type.has(GuildTYPE.name == guild_type)))

            if message_type is not None:
                conditions.append(MessageLOG.message_type.has(MessageTYPE.name == message_type))

            return await self.__analytic_get_counts(
                session,
                group_by,
                [MessageLOG.guild_id, MessageLOG.author_id],
                conditions,
                limit,
                sort_by,
                sort_by_direction,
                [
                    func.sum(case((MessageLOG.success_rate > 0, 1), else_=0)).label("successful"),
                    func.sum(case((MessageLOG.success_rate == 0, 1), else_=0)).label("failed"),
                    select(GuildUSER.snowflake_id).where(GuildUSER.id == MessageLOG.guild_id).scalar_subquery().label("guild_snow"),
                    select(GuildUSER.name).where(GuildUSER.id == MessageLOG.guild_id).scalar_subquery().label("guild_name"),
                    select(GuildUSER.snowflake_id).where(GuildUSER.id == MessageLOG.author_id).scalar_subquery().label("author_snow"),
                    select(GuildUSER.name).where(GuildUSER.id == MessageLOG.author_id).scalar_subquery().label("author_name")
                ],
                [],
                MessageLOG
            )

    def analytic_get_message_log(
        self,
        guild: Union[int, None] = None,
        author: Union[int, None] = None,
        after: datetime = datetime.min,
        before: datetime = datetime.max,
        success_rate: Tuple[float, float] = (0, 100),
        guild_type: Union[Literal["USER", "GUILD"], None] = None,
        message_type: Union[Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"], None] = None,
        sort_by: Literal["timestamp", "success_rate"] = "timestamp",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
    ) -> List["MessageLOG"]:
        """
        Returns a list of :ref:`MessageLOG` objects (message logs) that match the parameters.

        Parameters
        --------------
        guild: Union[int, None]
            The snowflake id of the guild.
        author: Union[int, None]
            The snowflake id of the author.
        after: Union[datetime, None]
            Include only messages sent after this datetime.
        before: Union[datetime, None]
            Include only messages sent before this datetime.
        success_rate: tuple[int, int]
            Success rate tuple containing minimum success rate and maximum success
            rate the message log can have for it to be included.
            Success rate is measured in % and it is defined by:

            Successfully sent channels / all channels.
        guild_type: Literal["USER", "GUILD"] | None,
            Type of guild.
        message_type: Literal["TextMESSAGE", "VoiceMESSAGE", "DirectMESSAGE"] | None,
            Type of message.
        sort_by: Literal["timestamp", "success_rate", "data"],
            Sort items by selected.
            Defaults to "timestamp"
        sort_by_direction: Literal["asc", "desc"] = "desc"
            Sort items by ``sort_by`` in selected direction (asc = ascending, desc = descending).
            Defaults to "desc"
        limit: int = 500
            Limit of the message logs to return. Defaults to 500.

        Return
        ---------
        list[MessageLOG]
            List of the message logs.
        """
        conditions = [
            MessageLOG.timestamp.between(after, before),
            MessageLOG.success_rate.between(*success_rate)
        ]

        if guild is not None:
            conditions.append(MessageLOG.guild.has(GuildUSER.snowflake_id == guild))

        if author is not None:
            conditions.append(MessageLOG.author.has(GuildUSER.snowflake_id == author))

        if guild_type is not None:
            conditions.append(MessageLOG.guild.has(GuildUSER.guild_type.has(GuildTYPE.name == guild_type)))

        if message_type is not None:
            conditions.append(MessageLOG.message_type.has(MessageTYPE.name == message_type))

        return self.__analytic_get_log(
            MessageLOG,
            conditions,
            getattr(getattr(MessageLOG, sort_by), sort_by_direction)(),
            limit
        )

    async def analytic_get_num_invites(
        self,
        guild: Union[int, None] = None,
        after: datetime = datetime.min,
        before: datetime = datetime.max,
        sort_by: Literal["count", "guild_snow", "guild_name", "invite_id"] = "count",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
        group_by: Literal["year", "month", "day"] = "day"
    ) -> List[Tuple[date, int, str]]:
        """
        Returns invite link join counts.

        Parameters
        -----------
        guild: int
            The snowflake id of the guild.
        after: Union[datetime, None] = None
            Only count messages sent after the datetime.
        before: Union[datetime, None]
            Only count messages sent before the datetime.
        sort_by: Literal["count", "guild_snow", "guild_name", "invite_id"],
            Sort items by selected.
            Defaults to "successful"
        sort_by_direction: Literal["asc", "desc"]
            Sort items by ``sort_by`` in selected direction (asc = ascending, desc = descending).
            Defaults to "desc"
        limit: int = 500
            Limit of the rows to return. Defaults to 500.
        group_by: Literal["year", "month", "day"]
            Results returned are grouped by ``group_by``

        Returns
        --------
        list[Tuple[date, int, int, str, str]]
            List of tuples.

            Each tuple contains:

            - Date
            - Invite count
            - Invite ID

        Raises
        ------------
        SQLAlchemyError
            There was a problem with the database.
        """
        args = get_args(self.analytic_get_num_invites.__annotations__["sort_by"])
        if sort_by not in args:
            raise ValueError(f"sort_by expected any of {args}. Got '{sort_by}'")

        async with self.session_maker() as session:
            conditions = [InviteLOG.timestamp.between(after, before)]
            if guild is not None:
                conditions.append(
                    InviteLOG.invite.has(Invite.guild.has(GuildUSER.snowflake_id == guild))
                )

            return await self.__analytic_get_counts(
                session,
                group_by,
                [
                    Invite.discord_id,
                    GuildUSER.snowflake_id,
                    GuildUSER.name,
                ],
                conditions,
                limit,
                sort_by,
                sort_by_direction,
                [
                    func.count().label("count"),
                    GuildUSER.snowflake_id.label("guild_snow"),
                    GuildUSER.name.label("guild_name"),
                    Invite.discord_id,
                ],
                [
                    (Invite, InviteLOG.invite_id == Invite.id),
                    (GuildUSER, Invite.guild_id == GuildUSER.id)
                ],
                InviteLOG
            )

    async def __analytic_get_counts(
        self,
        session: Union[Session, AsyncSession],
        group_by: str,
        group_by_extra: List[Any],
        conditions: list,
        limit: int,
        sort_by: str,
        sort_by_direction: Literal["asc", "desc"],
        select_items: List[Any],
        joins: List[Tuple[Any, Any]],
        select_from: Any
    ):
        args = get_args(self.__analytic_get_counts.__annotations__["sort_by_direction"])
        if sort_by_direction not in args:
            raise ValueError(f"sort_by_direction expected any of {args}. Got '{sort_by_direction}'")

        regions = ["day", "month", "year"]
        regions = reversed(regions[regions.index(group_by):])
        extract_stms = []

        timestamp = getattr(select_from, "timestamp")
        for region_ in regions:
            extract_stms.append(func.extract(region_, timestamp).cast(Integer))

        select_stm = (select(*extract_stms, *select_items).where(*conditions).select_from(select_from))

        for join_table, condition in joins:
            select_stm = select_stm.join(join_table, condition)

        select_stm = (
            select_stm.group_by(*extract_stms, *group_by_extra)
            .limit(limit)
            .order_by(text(f"{sort_by} {sort_by_direction}"))
        )

        count = (await self._run_async(session.execute, select_stm)).all()
        extract_stm_len = len(extract_stms)
        count = [
            ("-".join("{:02d}".format(x) for x in s[:extract_stm_len]), *s[extract_stm_len:])
            for s in count
        ]

        return count

    def analytic_get_invite_log(
        self,
        guild: Union[int, None] = None,
        invite: Union[str, None] = None,
        after: datetime = datetime.min,
        before: datetime = datetime.max,
        sort_by: Literal["timestamp"] = "timestamp",
        sort_by_direction: Literal["asc", "desc"] = "desc",
        limit: int = 500,
    ) -> List["InviteLOG"]:
        """
        Returns a list of :ref:`InviteLOG` objects (invite logs) filtered by the given parameters.

        Parameters
        --------------
        guild: Union[int, None]
            The snowflake id of the guild.
        invite: Union[str, None]
            Discord invite ID (final part of URL).
        after: Union[datetime, None]
            Include only invites sent after this datetime.
        before: Union[datetime, None]
            Include only invites sent before this datetime.
        sort_by: Literal["timestamp"],
            Sort items by selected.
            Defaults to "timestamp"
        sort_by_direction: Literal["asc", "desc"] = "desc"
            Sort items by ``sort_by`` in selected direction (asc = ascending, desc = descending).
            Defaults to "desc"
        limit: int = 500
            Limit of the invite logs to return. Defaults to 500.

        Return
        ---------
        list[InviteLOG]
            List of the message logs.
        """
        conditions = [InviteLOG.timestamp.between(after, before)]
        if guild is not None:
            conditions.append(InviteLOG.invite.has(Invite.guild.has(GuildUSER.snowflake_id == guild)))
        if invite is not None:
            conditions.append(InviteLOG.invite.has(Invite.discord_id == invite))

        return self.__analytic_get_log(
            InviteLOG,
            conditions,
            getattr(getattr(InviteLOG, sort_by), sort_by_direction)(),
            limit
        )

    async def __analytic_get_log(
        self,
        select_items: Any,
        conditions: list,
        order_by: Any,
        limit: int
    ):
        """
        Common helper method universal for multiple log types.
        """
        async with self.session_maker() as session:
            logs = await self._run_async(
                session.execute,
                select(select_items).where(*conditions).order_by(order_by).limit(limit)
            )
            return list(*zip(*logs.unique().all()))

    async def delete_logs(self, logs: List[Union[MessageLOG, InviteLOG]]):
        """
        Method used to delete log objects objects.

        Parameters
        ------------
        table: MessageLOG | InviteLOG
            The logging table to delete from.
        primary_keys: List[int]
            List of Primary Key IDs that match the rows of the table to delete.
        """
        session: Union[AsyncSession, Session]
        table = type(logs[0])
        async with self.session_maker() as session:
            await self._run_async(session.execute, delete(table).where(table.id.in_([log.id for log in logs])))
            await self._run_async(session.commit)

    @async_util.with_semaphore("_mutex")
    async def update(self, **kwargs):
        """
        .. versionadded:: v2.0

        Used for changing the initialization parameters the object was initialized with.

        .. warning::
            Upon updating, the internal state of objects get's reset,
            meaning you basically have a brand new created object.
            It also resets the message objects.

        Parameters
        -------------
        **kwargs: Any
            Custom number of keyword parameters which you want to update,
            these can be anything that is available during the object creation.

        Raises
        -----------
        TypeError
            Invalid keyword argument was passed.
        Other
            Raised from .initialize() method.
        """
        try:
            await self._stop_engine()
            await async_util.update_obj_param(self, **kwargs)
        except Exception:
            # Reinitialize since engine was disconnected
            await self.initialize()
            raise
