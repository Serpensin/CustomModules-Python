"""Type stubs for SteamCharts module."""
from typing import Dict

async def playercount(gameid: int) -> Dict[str, str]:
    """Get Steam Charts player count data."""
    ...

__all__ = ['playercount']
