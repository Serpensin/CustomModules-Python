"""Type stubs for bot_directory module."""
import asyncio
import logging
from typing import Any, List, Optional

class Stats:
    logger: logging.Logger
    bot: Any
    topgg_token: str
    discordbots_token: str
    discordbotlistcom_token: str
    discordlist_token: str
    _tasks: List[asyncio.Task]
    def __init__(
        self,
        bot: Any,
        logger: Optional[logging.Logger] = None,
        topgg_token: str = "",
        discordbots_token: str = "",
        discordbotlistcom_token: str = "",
        discordlist_token: str = "",
    ) -> None: ...
    def start_stats_update(self) -> List[asyncio.Task]: ...
    async def stop_stats_update(self) -> None: ...
