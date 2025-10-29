"""Type stubs for PrivateVoice module."""
import discord
import logging
from typing import Optional

def setup(
    bot: discord.Client,
    db_path: str,
    logger: Optional[logging.Logger] = None,
    category_name: str = "Private Voice"
) -> None:
    """Setup PrivateVoice module."""
    ...

async def add_listener() -> None:
    """Add event listeners for private voice channels."""
    ...

async def start_garbage_collector() -> None:
    """Start the garbage collector for cleaning up empty channels."""
    ...

__all__ = ['setup', 'add_listener', 'start_garbage_collector']
