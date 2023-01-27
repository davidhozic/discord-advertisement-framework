"""
Module implements the Web layer of the framework.
It contains definitions related to the Selenium integration
and definitions responsible for making HTTP requests to find servers
the user might want to shill into.
"""
from __future__ import annotations
from typing import Dict, Tuple, Callable, List
from contextlib import suppress
from enum import auto, Enum
from random import random
from datetime import datetime, timedelta

from . import misc

import asyncio
import pathlib
import json
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
    from selenium.webdriver.support.expected_conditions import presence_of_element_located, url_changes
    from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
    GLOBALS.selenium_installed = True
except ImportError:
    WebElement = object()
    GLOBALS.selenium_installed = False
# -------------------------------------------- #


__all__ = (
    "SeleniumCLIENT",
    "GuildDiscoveryCLIENT",
    "SortBy"
)


WD_TIMEOUT_SHORT = 5
WD_TIMEOUT_MED = 30
WD_TIMEOUT_LONG = 90
WD_WINDOW_SIZE = (1280, 720)

WD_OUTPUT_PATH = pathlib.Path("./daf_web_data")
WD_TOKEN_PATH = WD_OUTPUT_PATH.joinpath("tokens.json")
WD_PROFILES_PATH = WD_OUTPUT_PATH.joinpath("chrome_profiles")

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

    This is created in the ACCOUNT object in case ``web`` parameter inside ACCOUNT is True.

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
                f"Install them with: pip install discord-advert-framework[web]"
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
        token: str =  driver.execute_script(
            """
            const f = document.createElement('iframe');
            document.head.append(f);
            const desc = Object.getOwnPropertyDescriptor(f.contentWindow, 'localStorage');
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
        await asyncio.sleep(bottom + (upper - bottom)*random())

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

    async def fetch_redirect_url(self, url: str):
        """
        Fetches the last URL on route.

        Parameters
        -------------
        url: str
            The url to check for redirects.
        """
        driver = self.driver
        main_window_handle = driver.current_window_handle
        driver.switch_to.new_window("tab")
        await self.async_execute(driver.get, url)
        await asyncio.sleep(2)
        while True:
            try:
                await self.async_execute(
                    WebDriverWait(driver, WD_TIMEOUT_SHORT).until,
                    url_changes(driver.current_url)
                )
            except TimeoutException:
                return driver.current_url
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
        await self.await_load()
        actions = ActionChains(self.driver)

        actions.move_to_element(form).perform()
        await self.random_sleep(0.25, 1)
        actions.click(form).perform()

        for char in text:
            form.send_keys(char)
            await self.random_sleep(0.05, 0.10)

    async def await_load(self):
        """
        Waits for the Discord spinning logo to disappear,
        which means that the content has finished loading.

        Raises
        -------------
        TimeoutError
            The page loading timed-out.
        """
        loop = asyncio.get_event_loop()
        await self.random_sleep(1, 2)
        try:
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located((By.XPATH, "//*[@* = 'app-spinner']"))
            )
        except TimeoutException as exc:
            raise TimeoutError(f"Page loading took too long.") from exc

    async def await_login_location(self):
        """
        Waits for the user to confirm the login location via email, and
        then logs in manually.

        Raises
        ----------
        TimeoutError
            User failed to verify new login location.
        """
        loop = asyncio.get_event_loop()
        await self.random_sleep(1, 2)
        try:
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located((By.XPATH, "//*[contains(text(), 'login location')]"))
            )    
        except TimeoutException as exc:
            raise TimeoutError("New login location not confirmed in time.") from exc

    async def await_captcha(self):
        """
        Waits for CAPTCHA to be completed.

        Raises
        ------------
        TimeoutError
            CAPTCHA was not solved in time.
        """
        loop = asyncio.get_event_loop()
        driver = self.driver
        await asyncio.sleep(WD_TIMEOUT_SHORT)

        # Find all CAPTCHA iframes
        captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
        challenge_container = None
        captcha_button = None
        captcha_button_frame = None
        # Go search all captcha frames to find images container and the captcha button
        for frame in captcha_frames:
            driver.switch_to.frame(frame)
            if challenge_container is None:
                with suppress(NoSuchElementException):
                    challenge_container = driver.find_element(By.XPATH, "//div[@class='challenge-container']/div[@class='challenge']")

            if captcha_button is None:
                with suppress(NoSuchElementException):
                    captcha_button = driver.find_element(By.XPATH, "//div[@id='checkbox']")
                    captcha_button_frame = frame
            
            driver.switch_to.default_content()

        if challenge_container is None and captcha_button is None:
            return # No CAPTCHA action required

        # Challenge container not found -> click the button to open it
            # Sometimes CAPTCHA just requires a click on the button and no image selection
        if challenge_container is None and captcha_button is not None:
            driver.switch_to.frame(captcha_button_frame)
            await self.hover_click(captcha_button)
            driver.switch_to.default_content()

        try:
            # CAPTCHA detected, wait until it is solved by the user
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'captcha')]"))
            )
        except TimeoutException as exc:
            raise TimeoutError(f"CAPTCHA was not solved by the user") from exc

    async def await_two_factor(self):
        """
        Awaits for user to enter 2-factor authorization key.

        Raises
        --------------
        TimeoutError
            2-Factor authentication timed-out.
        """
        loop = asyncio.get_event_loop()
        await asyncio.sleep(WD_TIMEOUT_SHORT)
        try:
            await self.async_execute(
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not,
                presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Two-factor')]"))
            )
        except TimeoutException as exc:
            raise TimeoutError("2-Factor authentication was not completed in time.") from exc

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
        opts.add_argument(f"--no-sandbox")

        if self._proxy is not None:
            opts.add_argument(f"--proxy-server={self._proxy}")

        driver = Chrome(options=opts)
        driver.set_window_size(*WD_WINDOW_SIZE)
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
            await asyncio.sleep(WD_TIMEOUT_SHORT)

            # Check if already logged in
            if driver.current_url == DISCORD_LOGIN_URL:
                # Check previous accounts
                with suppress(NoSuchElementException):
                    login_bnt = driver.find_element(By.XPATH, "//button[@type='button']//div[contains(text(), 'Add an account')]")
                    await self.hover_click(login_bnt)

                # Not logged in
                email_entry = driver.find_element(By.XPATH, "//input[@name='email']")
                pass_entry = driver.find_element(By.XPATH, "//input[@type='password']")

                await self.slow_type(email_entry, self._username)
                await self.slow_type(pass_entry, self._password)

                await self.random_sleep(1, 2)
                ActionChains(driver).send_keys(Keys.ENTER).perform()

                await self.await_captcha()
                await self.await_login_location()
                await self.await_two_factor()
                await self.await_load()

            return self.update_token_file()

        except TimeoutError:
            raise
        except (WebDriverException, OSError) as exc:
            raise RuntimeError("Unable to login due to internal exception.") from exc

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
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        await self.random_sleep(0.25, 1)
        actions.click(element).perform()
        await self.random_sleep(1, 2)

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
        TimeoutError
            Timed out while waiting for actions to complete.
        """
        loop = asyncio.get_event_loop()
        driver = self.driver
        await self.await_load()

        # Join server
        try:
            join_bnt = driver.find_element(By.XPATH, "//div[@aria-label='Add a Server']")
            await self.hover_click(join_bnt)

            add_server_bnt = driver.find_element(By.XPATH, "//button[div[text()='Join a Server']]")
            await self.hover_click(add_server_bnt)

            link_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'discord.gg')]")
            await self.slow_type(link_input, invite)
            await self.random_sleep(2, 5)

            join_bnt = driver.find_element(By.XPATH, "//button[@type='button' and div[contains(text(), 'Join')]]")
            await self.hover_click(join_bnt)
            await self.random_sleep(3, 5) # Wait for any CAPTCHA to appear

            await self.await_captcha()

            with suppress(TimeoutException): 
                await self.async_execute(
                    WebDriverWait(driver, WD_TIMEOUT_SHORT).until_not,
                    presence_of_element_located((By.XPATH, "//button[@type='button' and div[contains(text(), 'Join')]]"))
                )

            # Complete rules
            ActionChains(driver).send_keys(Keys.ESCAPE).perform() # To ensure there is not already an open menu
            with suppress(NoSuchElementException):
                complete_rules_bnt = driver.find_element(By.XPATH, "//button[div[contains(text(), 'Complete')]]")
                await self.hover_click(complete_rules_bnt)

            with suppress(NoSuchElementException):
                checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
                await self.hover_click(checkbox)

            with suppress(NoSuchElementException):
                submit_bnt = driver.find_element(By.XPATH, "//button[@type='submit']")
                await self.hover_click(submit_bnt)
        except WebDriverException as exc:
            raise RuntimeError("Unable to join guild due to internal error.") from exc


class SortBy(Enum):
    TEXT_RELEVANCY = 0
    TOP = auto()
    RECENTLY_CREATED = auto()
    TOP_VOTED = auto()
    TOTAL_USERS = auto()

class QueryResult:
    """
    Contains result of the queries.
    """
    __slots__ = (
        "id",
        "invite",
        "updated",
    )

    def __init__(self, id: int, invite: str) -> None:
        self.id = id
        self.invite = invite
        self.updated = datetime.now()

    @property
    def pending_refresh(self):
        return datetime.now() - self.updated > TOP_GG_REFRESH_TIME


@misc.doc_category("Clients")
class GuildDiscoveryCLIENT:
    """
    Client used for searching servers.

    Parameters
    ------------
    prompt: str
        Query parameter for server search.
    sort_by: SortBy
        Query parameter for sorting method for results.
    total_members: int
        Query parameter for member limit.
    limit: int
        The maximum amount of servers to query.
    """
    cache: Dict[Tuple[str, SortBy, int], QueryResult] = {}

    __slots__ = (
        "prompt",
        "sort_by",
        "total_members",
        "limit",
        "session",
        "_browser"
    )

    def __init__(self, prompt: str, sort_by: SortBy, total_members: int, limit: int) -> None:
        self.prompt = prompt
        self.sort_by = sort_by
        self.total_members = total_members
        self.limit = limit

    async def initialize(self, browser: SeleniumCLIENT):
        self.session = http.ClientSession()
        self._browser = browser

    async def _query_request(self) -> List[QueryResult]:
        """
        Makes actual HTTP requests.

        Returns
        -----------
        List[QueryResult]
            List of guilds found.        
        """
        params = {
            "amount": self.limit,
            "nsfwLevel": "1",
            "platform": "discord",
            "entityType": "server",
            "newSortingOrder": self.sort_by.name,
            "query": self.prompt,
            "isMature": "false"
        }
        total_members = self.total_members
        if total_members is not None:
            params["minUsers"] = total_members//10 if total_members > 100 else 0
            params["maxUsers"] = total_members

        ret = []
        data = None
        async with self.session.get(TOP_GG_SEARCH_URL, params=params) as result:
            if result.status != 200:
                return ret

            data = await result.json()
            if data is None or "results" not in data:
                return ret

        # Get invite links
        for item in data["results"]:
            id_ = int(item["id"])
            url = await self._browser.fetch_redirect_url(TOP_GG_SERVER_JOIN_URL.format(id=id_))
            ret.append(QueryResult(id_, url))

        return ret

    async def _query(self):
        """
        Generator that yields QueryResult objects.
        
        Returns
        -----------
        List[QueryResult]
            List of guilds found.  
        """
        cache_key = (self.prompt, self.sort_by, self.total_members)
        result: List[QueryResult] = self.cache.get(cache_key, None)
        # List[ { 'id': int, 'name': str, 'invite': str } ]"
        if result is None or result[0].pending_refresh:
            # Update result
            result = await self._query_request()
            self.cache[cache_key] = result

        limit = self.limit
        for i, item in enumerate(result):
            if i == limit:
                raise StopIteration

            yield item
