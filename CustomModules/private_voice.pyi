"""Type stubs for private_voice module."""
import logging
import sqlite3
from typing import Any, Optional

import discord

_bot: discord.Client
_logger: logging.Logger

def setup(
    client: discord.Client,
    tree: discord.app_commands.CommandTree,
    connection: Optional[sqlite3.Connection] = None,
    logger: Optional[logging.Logger] = None,
) -> None: ...
