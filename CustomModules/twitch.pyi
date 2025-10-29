"""Type stubs for Twitch module."""
from typing import Dict, Any, Optional

class TwitchAPI:
    """Twitch API wrapper."""
    
    client_id: str
    client_secret: str
    access_token: Optional[str]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str
    ) -> None: ...
    
    async def get_access_token(self) -> str: ...
    
    async def get_user(self, username: str) -> Dict[str, Any]: ...
    
    async def get_stream(self, user_id: str) -> Optional[Dict[str, Any]]: ...
    
    async def get_game(self, game_id: str) -> Dict[str, Any]: ...

__all__ = ['TwitchAPI']
