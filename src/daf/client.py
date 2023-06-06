"""
    This modules contains definitions related to the client (for API)
"""
from typing import Optional, Union, List, Dict

from . import misc
from . import guild
from . import web

from .logging.tracing import TraceLEVELS, trace

from typeguard import typechecked

import _discord as discord
import asyncio
import copy


#######################################################################
# Globals
#######################################################################
LOGIN_TIMEOUT_S = 15
TOKEN_MAX_PRINT_LEN = 5
TASK_SLEEP_DELAY_S = 0.100
TASK_STARTUP_DELAY_S = 2


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


@misc.track_id
@misc.doc_category("Clients")
class ACCOUNT:
    """
    .. versionadded:: v2.4

    .. versionchanged:: v2.5
        Added ``username`` and ``password`` parameters.
        For logging in automatically

    Represents an individual Discord account.

    Each ACCOUNT instance runs it's own shilling task.

    Parameters
    -----------
    token : str
        The Discord account's token
    is_user : Optional[bool] =False
        Declares that the ``token`` is a user account token ("self-bot")
    intents: Optional[discord.Intents]=discord.Intents.default()
        Discord Intents (settings of events that the client will subscribe to)
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
    username: Optional[str]
        The username to login with.
    password: Optional[str]
        The password to login with.

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
        "_running",
        "tasks",
        "_servers",
        "_autoguilds",
        "_selenium",
        "_uiservers",
        "_client",
        "_deleted",
        "_update_sem",
    )

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
    ) -> None:

        if proxy is not None:
            if not GLOBALS.proxy_installed:
                raise ModuleNotFoundError("Install extra requirements: pip install discord-advert-framework[proxy]")

        if token is not None and username is not None:  # Only one parameter of these at a time
            raise ValueError("'token' parameter not allowed if 'username' is given.")

        if token is None and username is None:  # At least one of these
            raise ValueError("At lest one parameter of these is required: 'token' OR 'username' + 'password'")

        self._token = token
        self.is_user = is_user
        self.proxy = proxy
        # If intents not passed, enable default
        if intents is None:
            intents = discord.Intents.default()
            intents.members = True

        self.intents = intents
        self._running = False
        self.tasks: List[asyncio.Task] = []
        self._servers: List[guild._BaseGUILD] = []
        self._autoguilds: List[guild.AutoGUILD] = []  # To prevent __eq__ issues, use 2 lists
        self._selenium = web.SeleniumCLIENT(username, password, proxy) if username is not None else None

        if servers is None:
            servers = []

        self._uiservers = servers
        """Temporary list of uninitialized servers
        servers parameter gets stored into _servers to prevent the
        update method from re-initializing initializes objects.
        This gets deleted in the initialize method"""

        self._client = None
        self._deleted = False
        misc._write_attr_once(self, "_update_sem", asyncio.Semaphore(1))

    def __str__(self) -> str:
        return f"{type(self).__name__}(token={self._token}, is_user={self.is_user}, selenium={self._selenium})"

    def __eq__(self, other):
        if isinstance(other, ACCOUNT):
            return self._token == other._token

        raise NotImplementedError("Only comparison between 2 ACCOUNTs is supported")

    def __deepcopy__(self, *args):
        "Duplicates the object (for use in AutoGUILD)"
        new = copy.copy(self)
        for slot in misc.get_all_slots(type(self)):
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
    def servers(self):
        """
        Returns all guild like objects inside the account's s
        shilling list. This also includes :class:`~daf.guild.AutoGUILD`
        """
        return self._servers + self._autoguilds

    @property
    def client(self) -> discord.Client:
        "Returns the API wrapper client"
        return self._client

    def _delete(self):
        """
        Sets the internal _deleted flag to True,
        indicating the object should not be used.
        """
        self._deleted = True
        for server in self.servers:
            server._delete()

    async def initialize(self):
        """
        Initializes the API wrapper client layer.

        Raises
        ------------
        RuntimeError
            Unable to login to Discord.
        """
        self._deleted = False
        connector = None
        if self.proxy is not None:
            connector = ProxyConnector.from_url(self.proxy)

        self._client = discord.Client(intents=self.intents, connector=connector)

        if self._selenium is not None:
            trace("Logging in thru browser and obtaining token")
            self._token = await self._selenium.initialize()
            self.is_user = True

        # Login
        trace("Logging in...")
        _client_task = asyncio.create_task(self._client.start(self._token, bot=not self.is_user))
        try:
            await self._client.wait_for("ready", timeout=LOGIN_TIMEOUT_S)
            trace(f"Logged in as {self._client.user.display_name}")
        except asyncio.TimeoutError as exc:
            exc = _client_task.exception() if _client_task.done() else exc
            raise RuntimeError(f"Error logging in to Discord. (Token {self._token[:TOKEN_MAX_PRINT_LEN]}...)") from exc

        for server in self._uiservers:
            try:
                await self.add_server(server)
            except Exception as exc:
                trace("Unable to add server.", TraceLEVELS.ERROR, exc)

        # Invite link tracking
        async def on_member_join(member: discord.Member):
            server = self.get_server(member.guild)
            if server is not None:
                await server._on_member_join(member)

        async def on_invite_delete(invite: discord.Invite):
            guild_id = invite.guild.id
            server = self.get_server(guild_id)
            if server is None:  # Try AutoGUILDS
                for autoserver in self._autoguilds:
                    server = autoserver._get_server(guild_id)
                    if server is not None:
                        break

            if server is not None:
                await server._on_invite_delete(invite)

        self._client.event(on_member_join)
        self._client.event(on_invite_delete)

        self._uiservers.clear()  # Only needed for predefined initialization
        self.tasks.append(asyncio.create_task(self._loop()))
        self._running = True

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

    @typechecked
    async def add_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]):
        """
        Initializes a guild like object and
        adds it to the internal account shill list.

        Parameters
        --------------
        server: guild.GUILD | guild.USER | guild.AutoGUILD
            The guild like object to add

        Raises
        --------
        Any
            Raised in
            :py:meth:`daf.guild.GUILD.initialize()` |
            :py:meth:`daf.guild.USER.initialize()`  |
            :py:meth:`daf.guild.AutoGUILD.initialize()`
        """
        await server.initialize(parent=self)
        if isinstance(server, guild._BaseGUILD):
            self._servers.append(server)
        else:
            self._autoguilds.append(server)

    @typechecked
    def remove_server(self, server: Union[guild.GUILD, guild.USER, guild.AutoGUILD]):
        """
        Removes a guild like object from the shilling list.

        Parameters
        --------------
        server: guild.GUILD | guild.USER | guild.AutoGUILD
            The guild like object to remove

        Raises
        -----------
        ValueError
            ``server`` is not in the shilling list.
        """
        if isinstance(server, guild._BaseGUILD):
            server._delete()
            # Remove by ID
            ids = [id(s) for s in self._servers]
            try:
                index = ids.index(id(server))
            except ValueError:
                raise ValueError(f"{server} is not in list")

            del self._servers[index]
        else:
            self._autoguilds.remove(server)

        trace(f"Server {server} has been removed from account {self}", TraceLEVELS.NORMAL)

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

    async def _close(self, _delete = True):
        """
        Signals the tasks of this account to finish and
        waits for them.
        """
        if self.running:
            trace(f"Logging out of {self.client.user.display_name}...")
            self._running = False

        for exc in await asyncio.gather(*self.tasks, return_exceptions=True):
            if exc is not None:
                trace(
                    f"Error raised in for {self.client.user.display_name} (Token: {self._token[:TOKEN_MAX_PRINT_LEN]})",
                    TraceLEVELS.ERROR,
                    exc
                )

        self.tasks.clear()
        selenium = self.selenium
        if selenium is not None:
            selenium._close()

        for guild_ in self._autoguilds:
            await guild_._close()

        await self._client.close()
        self.client.clear()

        if _delete:
            self._delete()

    async def _loop(self):
        """
        Main task loop for advertising thru each guild.

        Runs while _running is set to True and afterwards
        closes the connection to Discord.
        """
        while self._running:
            ###############################################################
            @misc._async_safe(self._update_sem)
            async def __loop():
                to_remove = []
                to_advert: List[guild._BaseGUILD, guild.AutoGUILD] = []
                for server in self.servers:
                    if server._check_state():
                        to_remove.append(server)
                    else:
                        to_advert.append(server)

                for server in to_remove:
                    self.remove_server(server)

                for server in to_advert:
                    status = await server._advertise()
                    if status == guild.GUILD_ADVERT_STATUS_ERROR_REMOVE_ACCOUNT:
                        self._running = False
                    # If loop stop has been requested, stop asap
                    if not self._running:
                        return
            ###############################################################
            await __loop()
            await asyncio.sleep(TASK_SLEEP_DELAY_S)

    async def update(self, **kwargs):
        """
        Updates the object with new parameters and afterwards updates all lower layers (GUILD->MESSAGE->CHANNEL).

        .. WARNING::
            After calling this method the entire object is reset.
        """
        if self._deleted:
            raise ValueError("Account has been removed from the framework!")

        if self._running:
            await self._close(False)

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

        servers = kwargs.pop("servers", self.servers + self._uiservers)
        if servers is None:
            servers = []

        @misc._async_safe("_update_sem")
        async def update_servers(self_):
            _servers = []
            _autoguilds = []
            for server in servers:
                try:
                    await server.update(init_options={"parent": self})
                    if isinstance(server, guild._BaseGUILD):
                        _servers.append(server)
                    else:
                        _autoguilds.append(server)
                except Exception as exc:
                    trace(f"Could not update {server} after updating {self} - Skipping server.", TraceLEVELS.ERROR, exc)

            self._servers = _servers
            self._autoguilds = _autoguilds

        try:
            await misc._update(self, **kwargs)
            await update_servers(self)
        except Exception:
            await self.initialize()  # re-login
            servers = self.servers  # Only return initialized servers
            await update_servers(self)
            raise
