"""
Module implements the Web layer of the framework.
It contains definitions related to the Selenium integration
and definitions responsible for making HTTP requests to find servers
the user might want to shill into.
"""
from __future__ import annotations
from typing import Dict, Tuple, Callable, List, Optional, Any
from contextlib import suppress
from enum import auto, Enum

from datetime import datetime, timedelta
from typeguard import typechecked

from . import misc
from .logging.tracing import trace, TraceLEVELS

import asyncio
import pathlib
import json
import random as rd
import aiohttp as http


class GLOBALS:
    "Global variables of the web module"
    selenium_installed = False


# ----------------- OPTIONAL ----------------- #
try:
    from undetected_chromedriver import Chrome
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support.expected_conditions import (
        presence_of_element_located,
        url_contains,
        url_changes
    )
    from selenium.common.exceptions import (
        NoSuchElementException,
        TimeoutException,
        WebDriverException
    )
    GLOBALS.selenium_installed = True
except ImportError:
    WebElement = object
    GLOBALS.selenium_installed = False
# -------------------------------------------- #


__all__ = (
    "SeleniumCLIENT",
    "GuildDISCOVERY",
    "QuerySortBy",
    "QueryMembers"
)


WD_TIMEOUT_SHORT = 5
WD_TIMEOUT_MED = 30
WD_TIMEOUT_LONG = 90
WD_RD_CLICK_UPPER_N = 5
WD_RD_CLICK_LOWER_N = 2
WD_OUTPUT_PATH = pathlib.Path("./daf_web_data")
WD_TOKEN_PATH = WD_OUTPUT_PATH.joinpath("tokens.json")
WD_PROFILES_PATH = WD_OUTPUT_PATH.joinpath("chrome_profiles")
WD_QUERY_SLEEP_S = 5

HOVER_CLICK_ACTION_TIME_MS = 500

DISCORD_LOGIN_URL = "https://discord.com/login"

TOP_GG_SEARCH_URL = "https://top.gg/api/client/entities/search"
TOP_GG_SERVER_JOIN_URL = "https://top.gg/servers/{id}/join"
TOP_GG_REFRESH_TIME = timedelta(hours=1)


@misc.doc_category("Clients")
class SeleniumCLIENT:
    """
    .. versionadded:: v2.5

    Client used to control the Discord web client for things such as
    logging in, joining guilds, passing "Complete" for guild rules.

    This is created in the ACCOUNT object in case ``web`` parameter
    inside ACCOUNT is True.

    .. note::

        This is automatically created in :class:`~daf.client.ACCOUNT`
        and is also bound to the :class:`~daf.client.ACCOUNT` instance.

        To retrieve it from :class:`~daf.client.ACCOUNT`, use
        :py:attr:`~daf.client.ACCOUNT.selenium`.


    Parameters
    -------------
    username: str
        The Discord username to login with.
    password: str
        The Discord password to login with.
    proxy: str
        The proxy url to use when connecting to Chrome.
    """
    def __init__(self,
                 username: str,
                 password: str,
                 proxy: str) -> None:

        if not GLOBALS.selenium_installed:
            raise ModuleNotFoundError(
                "This feature requires additional packages to be installed!\n"
                "Install them with: pip install discord-advert-framework[web]"
            )

        self._username = username
        self._password = password
        self._proxy = proxy
        self.driver = None
        self._token = None

    def _parse_token(self) -> str:
        """
        Get's the token from local storage.
        First it gets the object descriptor that was deleted from Discord.

        Returns
        ----------
        str
            The account token.

        Raises
        ------------
        LookupError
            Could not extract token from local storage.
        """
        driver = self.driver
        token: str = driver.execute_script(
            """
            const f = document.createElement('iframe');
            document.head.append(f);
            const desc = Object.getOwnPropertyDescriptor(
                f.contentWindow,
                'localStorage'
            );
            f.remove();
            const localStorage = desc.get.call(window);
            return localStorage["token"];
            """
        )
        if token is None:
            raise LookupError("Could not extract token from local storage.")

        return token.strip('"').strip("'")

    @property
    def token(self) -> str:
        "Returns accounts's token"
        return self._token

    def _close(self):
        "Closes the window"
        self.driver.quit()

    def update_token_file(self) -> str:
        """
        Updates the tokens JSON file.

        Raises
        -----------
        OSError
            There was an error saving/reading the file.

        Returns
        ----------
        str
            The token.
        """
        # Save token
        WD_TOKEN_PATH.touch(exist_ok=True)
        tokens = {}
        with open(WD_TOKEN_PATH, "r") as token_f:
            with suppress(json.JSONDecodeError):
                tokens = json.load(token_f)

        token = self._parse_token()
        tokens[self._username] = token

        with open(WD_TOKEN_PATH, "w") as token_f:
            json.dump(tokens, token_f, indent=2)

        self._token = token
        return token

    async def random_sleep(self, bottom: int, upper: int):
        """
        Sleeps randomly to prevent detection.
        """
        await asyncio.sleep(bottom + (upper - bottom) * rd.random())

    async def async_execute(self, method: Callable, *args):
        """
        Runs method in executor to force async.

        Parameters
        ----------
        method: Callable
            Callable to execute in async thread executor.
        args:
            Variadic arguments passed to ``method``.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, method, *args)

    async def random_server_click(self):
        """
        Randomly clicks on the servers panel to avoid CAPTCHA
        triggering.
        """
        trace("Clicking server list to trick CAPTCHA.", TraceLEVELS.DEBUG)
        driver = self.driver
        server_tree = driver.find_element(
            By.XPATH,
            "//div[@aria-label = 'Servers']"
        )
        servers = server_tree.find_elements(
            By.XPATH,
            "//div[@draggable = 'true']"
        )
        rd.shuffle(servers)
        num_to_click = rd.randrange(WD_RD_CLICK_LOWER_N, WD_RD_CLICK_UPPER_N + 1)
        for i, server in enumerate(servers):
            if i == num_to_click:
                return

            await self.hover_click(server)
            await self.random_sleep(0.25, 1)

    async def fetch_invite_link(self, url: str):
        """
        Fetches the invite link in case it is valid.

        Parameters
        -------------
        url: str | None
            The url to check or None if error ocurred/invalid link.
        """
        trace(f"Fetching invite link from {url}", TraceLEVELS.DEBUG)
        driver = self.driver
        main_window_handle = driver.current_window_handle
        driver.switch_to.new_window("tab")
        await self.async_execute(driver.get, url)
        await self.random_sleep(0.5, 1)
        try:
            await self.async_execute(
                WebDriverWait(driver, WD_TIMEOUT_SHORT).until,
                url_contains("discord.com")
            )
            await self.await_load()

            with suppress(NoSuchElementException):
                driver.find_element(
                    By.XPATH,
                    "//div[contains(text(), 'expired')]"
                )
                return None

            return driver.current_url
        except (TimeoutException, TimeoutError):
            return None
        finally:
            driver.close()
            driver.switch_to.window(main_window_handle)

    async def slow_type(self, form: WebElement, text: str):
        """
        Slowly types into a form to prevent detection.

        Parameters
        -------------
        form: WebElement
            The form to type ``text`` into.
        text: str
            The text to type in the ``form``.
        """
        await self.hover_click(form)
        trace("Slow typing into a form.", TraceLEVELS.DEBUG)
        for char in text:
            form.send_keys(char)
            await self.random_sleep(0.05, 0.10)

    async def slow_clear(self, form: WebElement):
        """
        Slowly deletes the text from an input

        Parameters
        -------------
        form: WebElement
            The form to delete ``text`` from.
        """
        await self.hover_click(form)
        form.send_keys(Keys.HOME)
        await self.random_sleep(0.1, 0.5)
        while form.text:
            form.send_keys(Keys.DELETE)
            await self.random_sleep(0.05, 0.25)

    async def await_url_change(self):
        """
        Waits for url to change.

        Raises
        --------
        TimeoutError
            Waited for too long.
        """
        try:
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until,
                url_changes(self.driver.current_url)
            )
        except TimeoutException:
            raise TimeoutError("Waiting for url to change took too long.")

    async def await_load(self):
        """
        Waits for the Discord spinning logo to disappear,
        which means that the content has finished loading.

        Raises
        -------------
        TimeoutError
            The page loading timed-out.
        """
        await self.random_sleep(2, 3)
        trace("Awaiting Discord load", TraceLEVELS.DEBUG)
        try:
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located(
                    (By.XPATH, "//span[contains(@class, 'wanderingCubes')]")
                )
            )
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located(
                    (By.XPATH, "//*[@* = 'app-spinner']")
                )
            )
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Opening')]")
                )
            )
        except TimeoutException as exc:
            raise TimeoutError("Page loading took too long.") from exc

    async def await_captcha(self):
        """
        Waits for CAPTCHA to be completed.

        Raises
        ------------
        TimeoutError
            CAPTCHA was not solved in time.
        """
        trace("Awaiting CAPTCHA", TraceLEVELS.DEBUG)
        driver = self.driver
        await asyncio.sleep(WD_TIMEOUT_SHORT)

        # Find all CAPTCHA iframes
        captcha_frames = driver.find_elements(
            By.XPATH,
            "//iframe[contains(@src, 'captcha')]"
        )
        challenge_container = None
        captcha_button = None
        captcha_button_frame = None
        # Find images container and the CAPTCHA button
        for frame in captcha_frames:
            driver.switch_to.frame(frame)
            if challenge_container is None:
                with suppress(NoSuchElementException):
                    challenge_container = driver.find_element(
                        By.XPATH,
                        "//div[@class='challenge-container']"
                        "/div[@class='challenge']"
                    )

            if captcha_button is None:
                with suppress(NoSuchElementException):
                    captcha_button = driver.find_element(
                        By.XPATH,
                        "//div[@id='checkbox']"
                    )
                    captcha_button_frame = frame

            driver.switch_to.default_content()

        if challenge_container is None and captcha_button is None:
            return  # No CAPTCHA action required

        # Challenge container not found -> click the button to open it
        if challenge_container is None and captcha_button is not None:
            driver.switch_to.frame(captcha_button_frame)
            await self.hover_click(captcha_button)
            driver.switch_to.default_content()

        try:
            # CAPTCHA detected, wait until it is solved by the user
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located(
                    (By.XPATH, "//iframe[contains(@src, 'captcha')]")
                )
            )
        except TimeoutException as exc:
            raise TimeoutError("CAPTCHA was not solved by the user") from exc

    async def initialize(self) -> None:
        """
        Starts the webdriver whenever the framework is started.

        Raises
        ----------
        Any
            Raised in :py:meth:`~SeleniumCLIENT.login` method.
        """
        WD_OUTPUT_PATH.mkdir(exist_ok=True)
        web_data_path = pathlib.Path(WD_PROFILES_PATH, self._username)

        opts = Options()
        opts.add_argument(f"--user-data-dir={web_data_path.absolute()}")
        opts.add_argument("--profile-directory=Profile 1")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--mute-audio")

        if self._proxy is not None:
            proxy = self._proxy.split("://")  # protocol, url
            if '@' in proxy[1]:
                proxy[1] = proxy[1][proxy[1].find('@') + 1:]

            proxy = f"{proxy[0]}://{proxy[1]}"
            opts.add_argument(f"--proxy-server={proxy}")

        driver = Chrome(options=opts)
        driver.maximize_window()
        self.driver = driver
        return await self.login()

    async def login(self) -> str:
        """
        Logins to Discord using the webdriver
        and saves the account token to JSON file.

        Returns
        ----------
        str
            Token belonging to provided username.

        Raises
        ----------
        TimeoutError
            Raised when any of the ``await_*`` methods timed-out.
        RuntimeError
            Unable to login due to internal exception.
        """
        try:
            driver = self.driver
            driver.get(DISCORD_LOGIN_URL)
            await self.await_load()
            await self.random_sleep(2, 3)
            # Check if already logged in
            if driver.current_url == DISCORD_LOGIN_URL:
                # Check previous accounts
                with suppress(NoSuchElementException):
                    login_bnt = driver.find_element(
                        By.XPATH,
                        "//button[@type='button']"
                        "//div[contains(text(), 'Add an account')]"
                    )
                    await self.hover_click(login_bnt)

                # Not logged in
                email_entry = driver.find_element(
                    By.XPATH,
                    "//input[@name='email']"
                )
                pass_entry = driver.find_element(
                    By.XPATH,
                    "//input[@type='password']"
                )

                await self.slow_type(email_entry, self._username)
                await self.slow_type(pass_entry, self._password)

                await self.random_sleep(2, 3)
                ActionChains(driver).send_keys(Keys.ENTER).perform()

                await self.await_url_change()
                await self.await_load()

            return self.update_token_file()
        except (WebDriverException, OSError) as exc:
            raise RuntimeError(
                "Unable to login due to internal exception."
            ) from exc

    async def logout(self):
        raise NotImplementedError("TODO: Implement logout!")

    async def hover_click(self, element: WebElement):
        """
        Hovers an element and clicks on it.

        Parameters
        -------------
        element: WebElement
            The element to hover click.
        """
        trace("Hover clicking element.", TraceLEVELS.DEBUG)
        actions = ActionChains(self.driver, HOVER_CLICK_ACTION_TIME_MS)
        await self.async_execute(
            actions
            .move_to_element(element)
            .pause(HOVER_CLICK_ACTION_TIME_MS / 1000)
            .click(element)
            .perform
        )

    async def join_guild(self, invite: str) -> None:
        """
        Joins the guild thru the browser.

        Parameters
        ------------
        invite: str
            The invite link/code of the guild to join.

        Raises
        ----------
        RuntimeError
            Internal error ocurred.
        RuntimeError
            The user is banned from the guild.
        TimeoutError
            Timed out while waiting for actions to complete.
        """
        driver = self.driver
        await self.await_load()

        # Join server
        trace(f"Joining guild {invite}", TraceLEVELS.DEBUG)
        try:
            join_bnt = driver.find_element(
                By.XPATH,
                "//div[@aria-label='Add a Server']"
            )
            await self.hover_click(join_bnt)

            await self.random_sleep(2, 3)
            add_server_bnt = driver.find_element(
                By.XPATH,
                "//button[div[text()='Join a Server']]"
            )
            await self.hover_click(add_server_bnt)

            await self.random_sleep(2, 3)
            link_input = driver.find_element(
                By.XPATH,
                "//input[contains(@placeholder, 'discord.gg')]"
            )
            await self.slow_type(link_input, invite)
            await self.random_sleep(2, 5)

            join_bnt = driver.find_element(
                By.XPATH,
                "//button[@type='button']/div[contains(text(), 'Join')]"
            )
            await self.hover_click(join_bnt)
            await self.random_sleep(3, 5)  # Wait for any CAPTCHA to appear

            await self.await_captcha()

            # Check if there is error message printed
            with suppress(NoSuchElementException):
                driver.find_element(
                    By.XPATH,
                    "//span[contains(text() , 'Unable to accept')]"
                )
                # Element found -> join error
                raise RuntimeError(f"The user appears to be banned from the guild w/ invite {invite}")

            await self.random_sleep(2, 3)
            with suppress(TimeoutException):
                await self.async_execute(
                    WebDriverWait(driver, WD_TIMEOUT_SHORT).until_not,
                    presence_of_element_located(
                        (
                            By.XPATH,
                            "//button[@type='button']"
                            "/div[contains(text(), 'Join')]"
                        )
                    )
                )

            # Complete rules
            await self.random_sleep(2, 3)
            # To ensure there is not already an open menu
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            with suppress(NoSuchElementException):
                complete_rules_bnt = driver.find_element(
                    By.XPATH,
                    "//button[div[contains(text(), 'Complete')]]"
                )
                await self.hover_click(complete_rules_bnt)

            await self.random_sleep(2, 3)
            with suppress(NoSuchElementException):
                checkbox = driver.find_element(
                    By.XPATH,
                    "//input[@type='checkbox']"
                )
                await self.hover_click(checkbox)

            await self.random_sleep(2, 3)
            with suppress(NoSuchElementException):
                submit_bnt = driver.find_element(
                    By.XPATH,
                    "//button[@type='submit']"
                )
                await self.hover_click(submit_bnt)

            await self.random_sleep(2, 3)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            trace(f"Joined guild with invite: {invite}", TraceLEVELS.DEBUG)

        except WebDriverException as exc:
            raise RuntimeError(
                "Unable to join guild due to internal error."
            ) from exc


@misc.doc_category("Web")
class QuerySortBy(Enum):
    """
    Enumerated options that can be passed to the ``sort_by``
    parameter of :class:`daf.web.GuildDISCOVERY`.
    """
    TEXT_RELEVANCY = 0
    TOP = auto()
    RECENTLY_CREATED = auto()
    TOP_VOTED = auto()
    TOTAL_USERS = auto()


@misc.doc_category("Web")
class QueryMembers(Enum):
    """
    Enumerated options that can be passed to the ``total_members``
    parameter of :class:`daf.web.GuildDISCOVERY`.
    """
    ALL = 0
    SUB_100 = (0, 100)
    B100_1k = (100, 1000)
    B1k_10k = (1000, 10000)
    ABV_10k = 1


class QueryResult:
    """
    Contains result of the queries.
    """
    __slots__ = (
        "id",
        "name",
        "invite",
        "updated",
    )

    def __init__(self, id: int, name: str, invite: str) -> None:
        self.id = id
        self.name = name
        self.invite = invite
        self.updated = datetime.now()

    @property
    def pending_refresh(self):
        return datetime.now() - self.updated > TOP_GG_REFRESH_TIME


@misc.doc_category("Web")
class GuildDISCOVERY:
    """
    Client used for searching servers.
    To be used with :class:`daf.guild.AutoGUILD`.

    Parameters
    ------------
    prompt: str
        Query parameter for server search.
    sort_by: Optional[QuerySortBy]
        Query parameter for sorting method for results.
    total_members: Optional[QueryMembers]
        Query parameter for member limit.
    limit: Optional[int]
        The maximum amount of servers to query.
        Defaults to 15 servers.
    """
    query_cache: Dict[Tuple[str, QuerySortBy, int], QueryResult] = {}

    __slots__ = (
        "prompt",
        "sort_by",
        "total_members",
        "limit",
        "session",
        "browser",
    )

    @typechecked
    def __init__(self,
                 prompt: str,
                 sort_by: Optional[QuerySortBy] = QuerySortBy.TOP,
                 total_members: Optional[QueryMembers] = QueryMembers.ALL,
                 limit: Optional[int] = 15) -> None:
        self.prompt = prompt
        self.sort_by = sort_by
        self.total_members = total_members
        self.limit = limit
        self.session = None
        self.browser = None

    async def initialize(self, parent: Any):
        self.session = http.ClientSession()
        self.browser: SeleniumCLIENT = parent.parent.selenium
        if self.browser is None:
            raise ValueError(
                "To use auto-join functionality,"
                " the account must be provided with username and password."
            )

    async def _close(self):
        """
        Closes under-laying async coroutines.
        """
        ses = self.session
        if ses is not None and not ses.closed:
            await ses.close()

    async def _query_request(self):
        """
        Makes actual HTTP requests.

        Returns
        -----------
        List[QueryResult]
            List of guilds found.
        """
        cache_key = (self.prompt, self.sort_by, self.total_members, self.limit)
        cache_result: List[QueryResult] = self.query_cache.get(cache_key, None)
        # List[ { 'id': int, 'name': str, 'invite': str } ]"
        if not (cache_result is None or cache_result[0].pending_refresh):
            for cached in cache_result:
                yield cached

            return

        # Update result
        result_list = []
        self.query_cache[cache_key] = result_list

        params = {
            "amount": 10,
            "nsfwLevel": "1",
            "platform": "discord",
            "entityType": "server",
            "newSortingOrder": self.sort_by.name,
            "query": self.prompt,
            "isMature": "false",
            "skip": 0
        }
        total_members = self.total_members
        if total_members is not QueryMembers.ALL:
            if total_members is QueryMembers.ABV_10k:
                params["minUsers"] = 10000
            else:
                min_, max_ = total_members.value
                params["minUsers"] = min_
                params["maxUsers"] = max_

        for i in range(0, 1000, 10):
            params["skip"] = i
            async with self.session.get(TOP_GG_SEARCH_URL, params=params) as result:
                if result.status != 200:
                    return

                data = await result.json()
                if (
                    data is None or
                    "results" not in data or not data["results"]
                ):
                    return

            # Get invite links
            for item in data["results"]:
                id_ = int(item["id"])
                name = item["name"]
                url = await self.browser.fetch_invite_link(
                    TOP_GG_SERVER_JOIN_URL.format(id=id_)
                )
                if url is not None:
                    qr = QueryResult(id_, name, url)
                    result_list.append(qr)
                    yield qr
                else:
                    await asyncio.sleep(WD_QUERY_SLEEP_S)
