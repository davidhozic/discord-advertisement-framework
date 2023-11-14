"""
    This modules contains definitions related to the client (for API)
"""
from typing import Optional, Union, List, Dict
from contextlib import suppress

from . import guild
from . import web

from .logging.tracing import TraceLEVELS, trace
from .misc import async_util, instance_track, doc, attributes
from .events import *

from typeguard import typechecked

import _discord as discord
import asyncio
import copy


#######################################################################
# Globals
#######################################################################
LOGIN_TIMEOUT_S = 15
TOKEN_MAX_PRINT_LEN = 5


__all__ = (
    "ACCOUNT",
)


class GLOBALS:
    "Storage class used for storing global variables"
    proxy_installed = False


# ----------------- OPTIONAL ----------------- #
try:
    from aiohttp_socks import ProxyConnector
    GLOBALS.proxy_installed = True
except ImportError:
    GLOBALS.proxy_installed = False
# -------------------------------------------- #


@instance_track.track_id
@doc.doc_category("Clients")
class ACCOUNT:
    """
    .. versionadded:: v2.4

    .. versionchanged:: v2.5
        Added ``username`` and ``password`` parameters.
        For logging in automatically

    .. versionchanged:: v3.0

        When servers are added directly through account initialization,
        they will be removed upon errors and available withing ``removed_servers`` property.

    Represents an individual Discord account.

    Each ACCOUNT instance runs it's own shilling task.

    Parameters
    -----------
    token : str
        The Discord account's token
    is_user : Optional[bool] =False
        Declares that the ``token`` is a user account token ("self-bot")
    intents: Optional[discord.Intents]
        Discord Intents (settings of events that the client will subscribe to).
        Defeaults to everything enabled except ``members``, ``presence`` and ``message_content``, as those
        are privileged events, which need to be enabled though Discord's developer settings for each bot.

        .. warning::

            For invite link tracking to work, it is required to set ``members`` intents to True.
            Invites intent is also needed. Enable it by setting ``invites`` to True inside
            the ``intents`` parameter of :class:`~daf.client.ACCOUNT`.

            Intent ``guilds`` is also required for AutoGUILD and AutoCHANNEL, however it is automatically forced
            to True, as it is not a priveleged intent.

    proxy: Optional[str]=None
        The proxy to use when connecting to Discord.

        .. IMPORTANT::
            It is **RECOMMENDED** to use a proxy if you are running **MULTIPLE** accounts.
            Running multiple accounts from the same IP address, can result in Discord
            detecting self-bots.

            Running multiple bot accounts on the other hand is perfectly fine without
            a proxy.
    servers: Optional[List[guild.GUILD | guild.USER | guild.AutoGUILD]]=[]
        Predefined list of servers (guilds, users, auto-guilds).
        If initializing a server fails (eg. server doesn't exist on Discord), it will be removed
        and added to :py:attr:`daf.client.ACCOUNT.removed_servers` property.
    username: Optional[str]
        The username to login with.
    password: Optional[str]
        The password to login with.
    removal_buffer_length: Optional[int]
        Maximum number of servers to keep in the removed_servers buffer.

        .. versionadded:: 3.0

    Raises
    ---------------
    ModuleNotFoundError
        'proxy' parameter was provided but requirements are not installed.
    ValueError
        'token' is not allowed if 'username' is provided and vice versa.
    """
    __slots__ = (
        "_token",
        "is_user",
        "proxy",
        "intents",
        "removal_buffer_length",
        "_running",
        "_ws_task",
        "_servers",
        "_selenium",
        "_client",
        "_deleted",
        "_removed_servers",
        "_event_ctrl"
    )

    _removed_servers: List[Union[guild.BaseGUILD, guild.AutoGUILD]]

    __passwords__ = ("token",)
    
    @typechecked
    def __init__(
        self,
        token: Optional[str] = None,
        is_user: Optional[bool] = False,
        intents: Optional[discord.Intents] = None,
        proxy: Optional[str] = None,
        servers: Optional[List[Union[guild.GUILD, guild.USER, guild.AutoGUILD]]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        removal_buffer_length: int = 50
    ) -> None:

        if proxy is not None:
            if not GLOBALS.proxy_installed:
                raise ModuleNotFoundError("Install extra requirements: pip install discord-advert-framework[proxy]")

        if token is not None and username is not None:  # Only one parameter of these at a time
            raise ValueError("'token' parameter not allowed if 'username' is given.")

        if token is None and username is None:  # At least one of these
            raise ValueError("At lest one parameter of these is required: 'token' OR 'username' + 'password'")

        # If intents not passed, enable default
        if intents is None:
            intents = discord.Intents.default()

        if servers is None:
            servers = []

        self._token = token
        self.is_user = is_user
        self.proxy = proxy
        self.intents = intents
        self.removal_buffer_length = removal_buffer_length
        self._running = False
        self._servers = servers
        self._selenium = web.SeleniumCLIENT(username, password, proxy) if username is not None else None
        self._client = None
        self._deleted = False
        self._ws_task = None
        self._event_ctrl = EventController()
        attributes.write_non_exist(self, "_removed_servers", [])

    def __str__(self) -> str:
        return f"{type(self).__name__}(token={self._token[:10] if self._token is not None else None}, is_user={self.is_user}, selenium={self._selenium})"

    def __eq__(self, other):
        if isinstance(other, ACCOUNT):
            return self._token == other._token

        raise NotImplementedError("Only comparison between 2 ACCOUNTs is supported")

    def __deepcopy__(self, *args):
        "Duplicates the object (for use in AutoGUILD)"
        new = copy.copy(self)
        for slot in attributes.get_all_slots(type(self)):
            self_val = getattr(self, slot)
            if isinstance(self_val, (asyncio.Semaphore, asyncio.Lock)):
                # Hack to copy semaphores since not all of it can be copied directly
                copied = type(self_val)(self_val._value)
            else:
                copied = copy.deepcopy((self_val))

            setattr(new, slot, copied)

        return new

    @property
    def selenium(self) -> web.SeleniumCLIENT:
        """
        .. versionadded:: v2.5

        Returns the, bound to account, Selenium client
        """
        return self._selenium

    @property
    def running(self) -> bool:
        """
        Is the account still running?

        Returns
        -----------
        True
            The account is logged in and shilling is active.
        False
            The shilling has ended or not begun.
        """
        return self._running

    @property
    def deleted(self) -> bool:
        """
        Indicates the status of deletion.

        Returns
        -----------
        True
            The object is no longer in the framework and should no longer
            be used.
        False
            Object is in the framework in normal operation.
        """
        return self._deleted

    @property
    def servers(self) -> List[Union[guild.GUILD, guild.AutoGUILD, guild.USER]]:
        """
        Returns all guild like objects inside the account's s
        shilling list. This also includes :class:`~daf.guild.AutoGUILD`
        """
        return self._servers[:]

    @property
    def removed_servers(self) -> List[Union[guild.GUILD, guild.AutoGUILD, guild.USER]]:
        "Returns a list of servers that were removed from account (last ``removal_buffer_length`` servers)."
        return self._removed_servers[:]

    @property
    def client(self) -> discord.Client:
        "Returns the API wrapper client"
        return self._client

    # API methods
    @typechecked
    def add_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]) -> asyncio.Future:
        """
        Initializes a guild like object and
        adds it to the internal account shill list.

        |ASYNC_API|

        Parameters
        --------------
        server: guild.GUILD | guild.USER | guild.AutoGUILD
            The guild like object to add

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        --------
        ValueError
            Invalid ``snowflake`` (eg. server doesn't exist).
        RuntimeError
            Could not query Discord.
        """
        return self._event_ctrl.emit(EventID.server_added, server)

    @typechecked
    def remove_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]) -> asyncio.Future:
        """
        Removes a guild like object from the shilling list.
        
        |ASYNC_API|

        .. versionchanged:: 3.0

            Removal is now asynchronous.

        Parameters
        --------------
        server: guild.GUILD | guild.USER | guild.AutoGUILD
            The guild like object to remove

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.

        Raises
        -----------
        ValueError
            ``server`` is not in the shilling list.
        """
        return self._event_ctrl.emit(EventID.server_removed, server)

    @typechecked
    def get_server(
        self,
        snowflake: Union[int, discord.Guild, discord.User, discord.Object],
    ) -> Union[guild.GUILD, guild.USER, None]:
        """
        Retrieves the server based on the snowflake id or discord API object.

        Parameters
        -------------
        snowflake: Union[int, discord.Guild, discord.User, discord.Object]
            Snowflake ID or Discord API object.

        Returns
        ---------
        Union[guild.GUILD, guild.USER]
            The DAF server object.
        None
            The object was not found.
        """
        if not isinstance(snowflake, int):
            snowflake = snowflake.id

        for server in self._servers:
            if server.snowflake == snowflake:
                return server

        return None

    def update(self, **kwargs) -> asyncio.Future:
        """
        Updates the object with new parameters and afterwards updates all lower layers (GUILD->MESSAGE->CHANNEL).

        |ASYNC_API|

        .. WARNING::
            After calling this method the entire object is reset.

        Returns
        --------
        Awaitable
            An awaitable object which can be used to await for execution to finish.
            To wait for the execution to finish, use ``await`` like so: ``await method_name()``.
        
        Raises
        --------
        ValueError
            The account is no longer running.
        Exception
            Other exceptions returned from :class:`daf.client.ACCOUNT` constructor
            or from :func:`daf.client.ACCOUNT.initialize`.
        """
        if self._deleted:
            raise ValueError("Account has been removed from the framework!")

        if self._running:
            return self._event_ctrl.emit(EventID.account_update, **kwargs)
        else:
            return self._on_update(**kwargs)

    # Non public methods
    def _delete(self):
        """
        Sets the internal _deleted flag to True,
        indicating the object should not be used.
        """
        self._deleted = True

    @async_util.except_return
    async def initialize(self):
        """
        Initializes the API wrapper client layer.
        """
        intents = self.intents
        if not intents.members:
            trace("Members intent is disabled, it is needed for invite link tracking", TraceLEVELS.WARNING)

        if not intents.invites:
            trace("Invites intent is disabled, it is needed for invite link tracking", TraceLEVELS.WARNING)

        if not intents.guilds:
            self.intents.guilds = True
            trace("Guilds intent is disabled. Enabling it since it's needed.", TraceLEVELS.WARNING)

        if self._selenium is not None:
            trace("Logging in thru browser and obtaining token")
            if isinstance(result := await self._selenium.initialize(), Exception):
                trace(f"Could not initialize browser in {self}.", TraceLEVELS.ERROR, result)
                raise result

            self._token = result
            self.is_user = True

        self._deleted = False
        connector = None
        if self.proxy is not None:
            connector = ProxyConnector.from_url(self.proxy)

        self._client = discord.Client(intents=self.intents, connector=connector)

        # Login
        trace("Logging in...")
        ws_task = None
        try:
            await self._client.login(self._token, not self.is_user)
            ws_task = asyncio.create_task(self._client.connect())
            self._ws_task = ws_task
            await self._client.wait_for("ready", timeout=LOGIN_TIMEOUT_S)
            trace(f"Logged in as {self._client.user.display_name}")
        except Exception as exc:
            exc = ws_task.exception() if ws_task is not None and ws_task.done() else exc
            trace(f"Could not login to Discord - {self}", TraceLEVELS.ERROR, exc)
            raise exc

        self._event_ctrl.add_listener(EventID.account_update, self._on_update)
        self._event_ctrl.add_listener(EventID.server_removed, self._on_remove_server)
        self._event_ctrl.add_listener(EventID.server_added, self._on_add_server)
        self._event_ctrl.start()
        self._running = True
        async with self._event_ctrl.critical():
            for server in self._servers:
                if (await server.initialize(self, self._event_ctrl)) is not None:
                    await self._on_remove_server(server)


    def generate_log_context(self) -> Dict[str, Union[str, int]]:
        """
        Generates a dictionary of the user's context,
        which is then used for logging.

        Returns
        ---------
        Dict[str, Union[str, int]]
        """
        return {
            "name": self._client.user.name,
            "id": self._client.user.id,
        }

    # API event handlers
    async def _on_add_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]):
        "Event handler for adding new servers"
        if (exc := await server.initialize(parent=self, event_ctrl=self._event_ctrl)) is not None:
            raise exc

        self._servers.append(server)
        with suppress(ValueError):
            self._removed_servers.remove(server)

    async def _on_remove_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]):
        "Event handler for removing the guild / server"
        if isinstance(server, guild.BaseGUILD):
            # Remove by ID
            ids = [id(s) for s in self._servers]
            try:
                index = ids.index(id(server))
            except ValueError:
                raise ValueError(f"{server} is not in list")

            del self._servers[index]
        else:
            self._servers.remove(server)

        await server._close()
        self._removed_servers.append(server)
        if len(self._removed_servers) > self.removal_buffer_length:
            trace(f"Removing oldest record of removed servers {self._removed_servers[0]}", TraceLEVELS.DEBUG)
            del self._removed_servers[0]

        trace(f"Server {server} has been removed from account {self}", TraceLEVELS.NORMAL)

    async def _on_update(self, **kwargs):
        await self._close()

        selenium = self._selenium
        if "token" not in kwargs:
            kwargs["token"] = self._token if selenium is None and "username" not in kwargs else None
        if "username" not in kwargs:
            kwargs["username"] = selenium._username if selenium is not None else None
        if "password" not in kwargs:
            kwargs["password"] = selenium._password if selenium is not None else None

        if "intents" in kwargs:
            intents: discord.Intents = kwargs["intents"]
            if isinstance(intents, discord.Intents) and intents.value == 0:
                kwargs["intents"] = None

        kwargs["servers"] = kwargs.pop("servers", self.servers)
        try:
            await async_util.update_obj_param(self, **kwargs)
        except Exception:
            await self.initialize()  # re-login
            raise


    # Cleanup
    async def _close(self):
        """
        Signals the tasks of this account to finish and
        waits for them.
        """
        if not self.running:
            return

        trace(f"Logging out of {self.client.user.display_name}...")
        self._running = False

        self._event_ctrl.remove_listener(EventID.server_removed, self._on_remove_server)
        self._event_ctrl.remove_listener(EventID.server_added, self._on_add_server)
        self._event_ctrl.remove_listener(EventID.server_update, self._on_remove_server)

        for guild_ in self.servers:
            await guild_._close()

        selenium = self.selenium
        if selenium is not None:
            selenium._close()

        await self._client.close()
        await asyncio.gather(self._ws_task, return_exceptions=True)
        return self._event_ctrl.stop()
