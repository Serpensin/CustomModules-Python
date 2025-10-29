"""Type stubs for Steam module."""
from typing import List, Dict, Any, Optional

class Errors:
    """Steam API error definitions."""
    INVALID_API_KEY: str
    STEAM_API_ERROR: str
    INVALID_STEAM_ID: str

class API:
    """Steam API wrapper."""
    
    api_key: str
    
    def __init__(self, api_key: str) -> None: ...
    
    async def get_player_summaries(
        self,
        steamids: List[str]
    ) -> Dict[str, Any]: ...
    
    async def get_owned_games(
        self,
        steamid: str,
        include_appinfo: bool = True,
        include_played_free_games: bool = False
    ) -> Dict[str, Any]: ...
    
    async def get_app_details(self, appid: int) -> Dict[str, Any]: ...

async def GetFreePromotions() -> List[Dict[str, Any]]:
    """Get current free promotions on Steam."""
    ...

__all__ = ['Errors', 'API', 'GetFreePromotions']
