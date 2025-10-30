import asyncio
import http
import logging
from typing import Optional, Union

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
    # Error message constant
    ERR_INVALID_STEAMID = "Invalid steamid or link."

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
            self.logger = logger.getChild("CustomModules").getChild("Steam")
        else:
            self.logger = logging.getLogger("CustomModules.Steam")

        self.logger.debug("Initializing Steam API")

        self.KEY = key
        self.url_get_owned_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&steamid="
        self.url_resolve_vanity = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={key}&vanityurl="
        self.url_get_player_achievements = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={key}&steamid="
        self.url_get_player_summeries = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={key}&steamids="
        self.url_get_app_details = (
            "https://store.steampowered.com/api/appdetails?appids="
        )

        if not asyncio.run(self.key_is_valid()):
            self.logger.error("Invalid Steam API key provided")
            raise Errors.InvalidKey()

        self.logger.info("Steam API initialized successfully")

    async def key_is_valid(self) -> bool:
        """
        Check if the provided API key is valid.

        Returns:
            bool: True if the key is valid, False otherwise.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.url_get_player_summeries}76561198889439823"
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
        resolved_ids = []
        for sid in steamids:
            resolved_id = await self.link_to_id(sid.strip())
            if resolved_id is None:
                raise ValueError(self.ERR_INVALID_STEAMID)
            resolved_ids.append(resolved_id)
        cleaned_steamids = ",".join(resolved_ids)
        url = f"{self.url_get_player_summeries}{cleaned_steamids}"
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
            raise ValueError(self.ERR_INVALID_STEAMID)
        url = f"{self.url_get_player_achievements}{steamid}&appid={appid}"
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

    async def link_to_id(self, link) -> Optional[str]:
        """
        Convert a Steam profile link to a Steam ID.

        Args:
            link (str): Steam profile link or vanity URL.

        Returns:
            Optional[str]: Steam ID, or None if conversion fails.
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
        url = f"{self.url_resolve_vanity}{link}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise Errors.RateLimit()
                if response.status != 200:
                    raise ValueError(self.ERR_INVALID_STEAMID)
                data = await response.json()
        return data["response"]["steamid"] if data["response"]["success"] == 1 else None

    async def owns_game(self, steamid, appid) -> Union[bool, dict]:
        """
        Check if the player owns a specific game.

        Args:
            steamid (str): Steam ID of the player.
            appid (int): App ID of the game.

        Returns:
            Union[bool, dict]: True if the player owns the game, False otherwise.
                               Returns a dict with error details if request fails.
        Raises:
            Errors.RateLimit: If the API rate limit is exceeded.
            ValueError: If the provided Steam ID or link is invalid.
            Errors.Private: If the profile is private.
        """
        steamid = await self.link_to_id(steamid)
        if steamid is None:
            raise ValueError(self.ERR_INVALID_STEAMID)
        url = f"{self.url_get_owned_games}{steamid}"
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
        url = f"{self.url_get_app_details}{appid}"
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


async def get_free_promotions() -> Union[list, dict]:
    """
    Fetches a list of free games currently on promotion from the Steam store.

    This function makes an asynchronous HTTP GET request to the Steam store's search page,
    looking for games that are both free and on special promotion. It then parses the HTML
    response to extract the app IDs of the games.

    Returns:
        Union[list, dict]: A list of app IDs of the free promotional games.
                           Returns a dict with error details if request fails.

    Example:
        >>> import asyncio
        >>> ids = asyncio.run(get_free_promotions())
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
    api = None
    try:
        api = API("")
    except Errors.InvalidKey as e:
        print(e)

    if api:
        try:
            print(
                asyncio.run(
                    api.get_player_summeries("Schlangensuende, 76561197969978546")
                )
            )
            print(asyncio.run(api.get_app_details(570)))
        except Errors.Private as e:
            print(e)
    print(asyncio.run(get_free_promotions()))
