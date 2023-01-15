from contextlib import suppress
from random import random

import asyncio



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
    from selenium.webdriver.common.proxy import Proxy, ProxyType
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support.expected_conditions import presence_of_element_located
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    GLOBALS.selenium_installed = True
except:
    GLOBALS.selenium_installed = False
# -------------------------------------------- #


__all__ = (
    "SeleniumCLIENT",
)


WD_TIMEOUT_SHORT = 5
WD_TIMEOUT_LONG = 90


class SeleniumCLIENT:
    """
    Client used to control the Discord web client for things such as 
    logging in, joining guilds, passing "Complete" for guild rules.

    This is created in the ACCOUNT object in case ``web`` parameter inside ACCOUNT is True.

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
        self._username = username
        self._password = password
        opts = Options()
        if proxy is not None:
            opts.add_argument(f"--proxy-server={proxy}")

        self.driver = Chrome(options=opts)
    
    def extract_token(self):
        """
        Get's the token from local storage.
        First it gets the object descriptor that was deleted from Discord.
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
        return token.replace('"', "").replace("'", "")

    async def random_sleep(self, bottom: int, upper: int):
        """
        Sleeps randomly to prevent detection.
        """
        await asyncio.sleep(bottom + (upper - bottom)*random())
    
    async def slow_type(self, form: WebElement, text: str):
        """
        Slowly types into a form to prevent detection
        """
        for char in text:
            form.send_keys(char)
            await self.random_sleep(0.05, 0.10)
    
    async def await_captcha(self):
        loop = asyncio.get_event_loop()
        try:
            # CAPTCHA detected, wait until it is solved by the user 
            await self.random_sleep(1, 3)
            await loop.run_in_executor(None, lambda:
                WebDriverWait(self.driver, WD_TIMEOUT_LONG).until_not(
                    presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'captcha')]"))
                )
            )
        except TimeoutException as exc:
            raise RuntimeError(f"CAPTCHA was not solved by the user") from exc

    async def login(self) -> str:
        """
        Logins to Discord.

        Returns
        ----------
        str
            The account's token
        """
        driver = self.driver
        loop = asyncio.get_event_loop()
        driver.get("https://discord.com/login")
        email_entry = driver.find_element(By.XPATH, "//input[@name='email']")
        pass_entry = driver.find_element(By.XPATH, "//input[@type='password']")
        login_bnt = driver.find_element(By.XPATH, "//button[@type='submit']")

        await self.random_sleep(1, 3)
        await self.slow_type(email_entry, self._username)
        await self.random_sleep(1, 3)
        await self.slow_type(pass_entry, self._password)
        await self.random_sleep(1, 3)
        await self.hover_click(login_bnt)

        await self.await_captcha()
        await self.random_sleep(1, 3)

        with suppress(TimeoutException):
            await loop.run_in_executor(None, lambda:
                WebDriverWait(driver, WD_TIMEOUT_LONG).until_not(
                    presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Two-factor')]"))
                )
        )

        await self.await_captcha()
        with suppress(TimeoutException):
            await loop.run_in_executor(None, lambda:
                WebDriverWait(driver, WD_TIMEOUT_SHORT).until(
                    presence_of_element_located((By.XPATH, '//*[@id="app-mount"]/div[2]/div/div[1]/div/div[2]/div/div[1]/nav/ul/div[2]'))
                )
        )
        await self.random_sleep(1, 3)
        return self.extract_token()

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
        WebDriverException
            Could not join the guild.
        """
        loop = asyncio.get_event_loop()
        driver = self.driver
        # Join server
        join_bnt = driver.find_element(By.XPATH, "//div[@aria-label='Add a Server']")
        await self.hover_click(join_bnt)

        add_server_bnt = driver.find_element(By.XPATH, "//button[div[text()='Join a Server']]")
        await self.hover_click(add_server_bnt)

        link_input = driver.find_element(By.XPATH, "//input[@type='text']")
        await self.slow_type(link_input, invite)
        await self.random_sleep(2, 5)

        join_bnt = driver.find_element(By.XPATH, "//button[@type='button' and div[contains(text(), 'Join')]]")
        await self.hover_click(join_bnt)
        await self.random_sleep(3, 5) # Wait for any CAPTCHA to appear

        await self.await_captcha()

        with suppress(TimeoutException): 
            await loop.run_in_executor(None, lambda:
                WebDriverWait(driver, WD_TIMEOUT_SHORT).until_not(
                    presence_of_element_located((By.XPATH, "//button[@type='button' and div[contains(text(), 'Join')]]"))
                )
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

