"""Type stubs for stat_dock module."""
import logging
import sqlite3
from typing import Any, Optional

import discord

def setup(
    client: discord.Client,
    connection: Optional[sqlite3.Connection] = None,
    logger: Optional[logging.Logger] = None,
) -> None: ...
