import asyncio
import http
import logging
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup


class Errors:
    class Private(Exception):
        """Custom error indicating an attempt to access a private profile."""

        def __init__(self, message="This profile is private."):
            super().__init__(message)

    class RateLimit(Exception):
        """Custom error indicating the exceeding of a rate limit."""

        def __init__(self, message="Rate limit exceeded."):
            super().__init__(message)

    class InvalidKey(Exception):
        """Custom error indicating that the key is invalid."""

        def __init__(self, message="Invalid key."):
            super().__init__(message)


class API:
    def __init__(self, key, logger: Optional[logging.Logger] = None):
        """
        Initialize the API object with the given API key.

        Args:
            key (str): The Steam API key.
            logger (Optional[logging.Logger]): Parent logger. Defaults to None.
        Raises:
            Errors.InvalidKey: If the provided API key is invalid.
        """
        # Setup logger with child hierarchy
        if logger:
            self.logger = logger.getChild('CustomModules').getChild('Steam')
        else:
            self.logger = logging.getLogger('CustomModules.Steam')
        
        self.logger.debug("Initializing Steam API")
        
        self.KEY = key
        self.URL_GetOwnedGames = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&steamid="
        self.URL_ResolveVanity = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={key}&vanityurl="
        self.URL_GetPlayerAchievements = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={key}&steamid="
        self.URL_GetPlayerSummeries = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={key}&steamids="
        self.URL_GetAppDetails = "https://store.steampowered.com/api/appdetails?appids="

        if not asyncio.run(self.keyIsValid()):
            self.logger.error("Invalid Steam API key provided")
            raise Errors.InvalidKey()
        
        self.logger.info("Steam API initialized successfully")

    async def keyIsValid(self) -> bool:
        """
        Check if the provided API key is valid.

        Returns:
            bool: True if the key is valid, False otherwise.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.URL_GetPlayerSummeries}76561198889439823"
            ) as response:
                if response.status != 200:
                    return False
                data = await response.json()
        return "response" in data and "players" in data["response"]

    async def get_player_summeries(self, steamid) -> dict:
        """
        Get player summaries for the given Steam IDs.

        Args:
            steamid (str): Comma-separated list of Steam IDs.

        Returns:
            dict: Player summaries data.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
            ValueError: If the provided Steam ID or link is invalid.
        """
        steamids = steamid.split(",")
        cleaned_steamids = ",".join(
            [await self.link_to_id(sid.strip()) for sid in steamids]
        )
        url = f"{self.URL_GetPlayerSummeries}{cleaned_steamids}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    return {
                        "error": {
                            "code": response.status,
                            "message": http.HTTPStatus(response.status).phrase,
                        }
                    }
                return await response.json()

    async def get_player_achievements(self, steamid, appid) -> dict:
        """
        Get player achievements for the given Steam ID and App ID.

        Args:
            steamid (str): Steam ID of the player.
            appid (int): App ID of the game.

        Returns:
            dict: Player achievements data.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
            ValueError: If the provided Steam ID or link is invalid.
        """
        steamid = await self.link_to_id(steamid)
        if steamid is None:
            raise ValueError("Invalid steamid or link.")
        url = f"{self.URL_GetPlayerAchievements}{steamid}&appid={appid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    return {
                        "error": {
                            "code": response.status,
                            "message": http.HTTPStatus(response.status).phrase,
                        }
                    }
                return await response.json()

    async def link_to_id(self, link) -> str:
        """
        Convert a Steam profile link to a Steam ID.

        Args:
            link (str): Steam profile link or vanity URL.

        Returns:
            str: Steam ID.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
            ValueError: If the provided Steam ID or link is invalid.
        """
        link = (
            link.replace("https://steamcommunity.com/profiles/", "")
            .replace("https://steamcommunity.com/id/", "")
            .replace("/", "")
        )
        if len(link) == 17 and link.isdigit():
            return link
        url = f"{self.URL_ResolveVanity}{link}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    raise ValueError("Invalid steamid or link.")
                data = await response.json()
        return data["response"]["steamid"] if data["response"]["success"] == 1 else None

    async def ownsGame(self, steamid, appid) -> bool:
        """
        Check if the player owns a specific game.

        Args:
            steamid (str): Steam ID of the player.
            appid (int): App ID of the game.

        Returns:
            bool: True if the player owns the game, False otherwise.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
            ValueError: If the provided Steam ID or link is invalid.
            Errors.Private: If the profile is private.
        """
        steamid = await self.link_to_id(steamid)
        if steamid is None:
            raise ValueError("Invalid steamid or link.")
        url = f"{self.URL_GetOwnedGames}{steamid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    return {
                        "error": {
                            "code": response.status,
                            "message": http.HTTPStatus(response.status).phrase,
                        }
                    }
                data = await response.json()
        try:
            return any(game["appid"] == appid for game in data["response"]["games"])
        except KeyError:
            if data == {"response": {}}:
                raise Errors.Private()
            return False

    async def get_app_details(self, appid) -> dict:
        """
        Get details of a specific app.

        Args:
            appid (int): App ID of the game.

        Returns:
            dict: App details.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
        """
        url = f"{self.URL_GetAppDetails}{appid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    return {
                        "error": {
                            "code": response.status,
                            "message": http.HTTPStatus(response.status).phrase,
                        }
                    }
                return await response.json()


async def GetFreePromotions() -> list:
    """
    Fetches a list of free games currently on promotion from the Steam store.

    This function makes an asynchronous HTTP GET request to the Steam store's search page,
    looking for games that are both free and on special promotion. It then parses the HTML
    response to extract the app IDs of the games.

    Returns:
        list: A list of app IDs of the free promotional games. If an error occurs, returns
              a dictionary with an error code and message.

    Example:
        >>> import asyncio
        >>> ids = asyncio.run(GetFreePromotions())
        >>> print(ids)
        ['12345', '67890', ...]
    """
    url = "https://store.steampowered.com/search/?maxprice=free&specials=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return {
                    "error": {
                        "code": response.status,
                        "message": http.HTTPStatus(response.status).phrase,
                    }
                }
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    return [
        game.get("data-ds-appid")
        for game in soup.find_all("a", class_="search_result_row")
        if game.get("data-ds-appid")
    ]


if __name__ == "__main__":
    try:
        api = API("")
    except Errors.InvalidKey as e:
        print(e)
    try:
        print(
            asyncio.run(api.get_player_summeries("Schlangensuende, 76561197969978546"))
        )
        print(asyncio.run(api.get_app_details(570)))
    except Errors.Private as e:
        print(e)
    print(asyncio.run(GetFreePromotions()))
