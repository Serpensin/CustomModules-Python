"""Type stubs for BotDirectory module."""
import discord
import logging
from typing import Optional

class Stats:
    """Bot directory statistics management."""
    
    bot: discord.Client
    logger: Optional[logging.Logger]
    TOPGG_TOKEN: str
    DISCORDBOTS_TOKEN: str
    DISCORDBOTLISTCOM_TOKEN: str
    DISCORDLIST_TOKEN: str
    
    def __init__(
        self,
        bot: discord.Client,
        logger: Optional[logging.Logger] = None,
        TOPGG_TOKEN: str = "",
        DISCORDBOTS_TOKEN: str = "",
        DISCORDBOTLISTCOM_TOKEN: str = "",
        DISCORDLIST_TOKEN: str = ""
    ) -> None: ...
    
    async def start_all(self) -> None: ...
    async def stop_all(self) -> None: ...

__all__ = ['Stats']
