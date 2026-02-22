"""Type stubs for steam_charts module."""
import logging
from typing import Optional, Union

def set_logger(logger: Optional[logging.Logger] = None) -> None: ...
async def playercount(
    gameid: int
) -> Union[dict[str, str], dict[str, dict[str, Union[int, str]]]]: ...
