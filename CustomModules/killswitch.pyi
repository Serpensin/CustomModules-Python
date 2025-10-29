"""Type stubs for Killswitch module."""
from typing import Optional

async def get_killswitch(return_type: str = "html") -> Optional[str]:
    """Get Dead by Daylight killswitch information."""
    ...

__all__ = ['get_killswitch']
