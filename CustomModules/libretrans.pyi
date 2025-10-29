"""Type stubs for Libretrans module."""
from typing import List, Dict, Any, Optional

class Errors:
    """LibreTranslate error definitions."""
    INVALID_API_KEY: str
    TRANSLATION_ERROR: str
    INVALID_LANGUAGE: str

class API:
    """LibreTranslate API wrapper."""
    
    api_url: str
    api_key: Optional[str]
    
    def __init__(
        self,
        api_url: str = "https://libretranslate.com",
        api_key: Optional[str] = None
    ) -> None: ...
    
    async def translate(
        self,
        text: str,
        source: str,
        target: str
    ) -> Dict[str, Any]: ...
    
    async def detect(self, text: str) -> List[Dict[str, Any]]: ...
    
    async def languages(self) -> List[Dict[str, str]]: ...

__all__ = ['Errors', 'API']
