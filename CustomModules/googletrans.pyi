"""Type stubs for Googletrans module."""
from typing import Optional, Dict, Any

class API:
    """Google Translate API wrapper."""
    
    def __init__(self) -> None: ...
    
    async def translate(
        self,
        text: str,
        dest: str = "en",
        src: str = "auto"
    ) -> Dict[str, Any]: ...
    
    async def detect(self, text: str) -> Dict[str, Any]: ...

__all__ = ['API']
