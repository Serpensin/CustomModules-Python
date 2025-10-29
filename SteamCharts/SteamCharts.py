import http

import aiohttp
from bs4 import BeautifulSoup


async def playercount(gameid) -> dict[str, str]:
    """
    Gets the current player count of the given game.

    Parameters
    ----------
    gameid : int
        The Steam ID of the game.

    Returns
    -------
    dict
        A dictionary containing the current player count, the peak player count in the last 24 hours and the peak player count of all time.
    200: The request was successful.
    400: The request was invalid.
    500: The server encountered an error.

    Notes
    -----
    The player count is retrieved from https://steamcharts.com/app/{gameid}.
    """
    url = f"https://steamcharts.com/app/{gameid}"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62"
    }

    async with aiohttp.ClientSession(headers=header) as session:
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
    data = {}
    stats = soup.find_all("div", class_="app-stat")
    if len(stats) >= 3:
        data["Current Players"] = stats[0].find("span", class_="num").text
        data["Peak Players 24h"] = stats[1].find("span", class_="num").text
        data["Peak Players All Time"] = stats[2].find("span", class_="num").text
    return data


if __name__ == "__main__":
    import asyncio

    input_id = input("Enter the Steam ID of the game: ")
    data = asyncio.run(playercount(input_id))
    if "error" in data:
        print(f'Error: {data["error"]["message"]}')
    else:
        print(f'Current Players: {data["Current Players"]}')
        print(f'Peak Players 24h: {data["Peak Players 24h"]}')
        print(f'Peak Players All Time: {data["Peak Players All Time"]}')
