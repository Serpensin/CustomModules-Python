"""Type stubs for StatDock module."""
import discord
import logging
from typing import Optional, List

def setup(
    bot: discord.Client,
    db_path: str,
    logger: Optional[logging.Logger] = None,
    interval: int = 300
) -> None:
    """Setup StatDock module."""
    ...

async def task() -> None:
    """Run the statistics update task."""
    ...

async def timezone_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[discord.app_commands.Choice[str]]:
    """Autocomplete for timezone selection."""
    ...

__all__ = ['setup', 'task', 'timezone_autocomplete']
