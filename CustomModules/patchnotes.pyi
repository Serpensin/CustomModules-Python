"""Type stubs for Patchnotes module."""
from typing import Optional

async def get_update_content(
    version: str,
    return_type: str = "html"
) -> Optional[str]:
    """Get Dead by Daylight patch notes."""
    ...

__all__ = ['get_update_content']
