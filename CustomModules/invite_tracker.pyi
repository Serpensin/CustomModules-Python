"""Type stubs for InviteTracker module."""
import discord
import logging
from typing import Optional

class Tracker:
    """Discord invite tracking."""
    
    bot: discord.Client
    logger: Optional[logging.Logger]
    db_path: str
    
    def __init__(
        self,
        bot: discord.Client,
        db_path: str,
        logger: Optional[logging.Logger] = None
    ) -> None: ...
    
    async def initialize(self) -> None: ...
    async def on_member_join(self, member: discord.Member) -> None: ...
    async def on_invite_create(self, invite: discord.Invite) -> None: ...
    async def on_invite_delete(self, invite: discord.Invite) -> None: ...

__all__ = ['Tracker']
