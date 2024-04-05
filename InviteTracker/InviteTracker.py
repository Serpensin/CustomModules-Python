import asyncio
from datetime import datetime
from discord import AuditLogAction
from discord.errors import Forbidden



class Tracker():
    """
    A class for tracking invites and managing their cache.
    """
    def __init__(self, bot):
        """
        Initialize the Tracker class.

        Parameters:
            bot (discord.Client/discord.AutoShardedClient): The Discord bot instance.
        """
        self.bot = bot
        self._cache = {}
        self._lock = asyncio.Lock()

    async def cache_invites(self):
        """
        Cache invites for all guilds the bot is currently in.
        """
        async with self._lock:
            for guild in self.bot.guilds:
                try:
                    self._cache[guild.id] = {}
                    for invite in await guild.invites():
                        self._cache[guild.id][invite.code] = invite
                except Forbidden:
                    continue

    async def update_invite_cache(self, invite):
        """
        Update the invite cache with a new or modified invite.

        Parameters:
            invite (discord.Invite): The invite to update the cache with.
        """
        async with self._lock:
            guild_id = invite.guild.id
            if guild_id not in self._cache:
                self._cache[guild_id] = {}
            self._cache[guild_id][invite.code] = invite

    async def remove_invite_cache(self, invite):
        """
        Remove an invite from the cache when it's deleted or expired.

        Parameters:
            invite (discord.Invite): The invite to remove from the cache.
        """
        async with self._lock:
            guild_id = invite.guild.id
            if guild_id not in self._cache:
                return
            ref_invite = self._cache[guild_id].get(invite.code)
            if not ref_invite:
                return
            if (ref_invite.created_at.timestamp() + ref_invite.max_age > datetime.utcnow().timestamp() or
                    ref_invite.max_age == 0) and ref_invite.max_uses > 0 and ref_invite.uses == ref_invite.max_uses - 1:
                try:
                    async for entry in invite.guild.audit_logs(limit=1, action=AuditLogAction.invite_delete):
                        if entry.target.code != invite.code:
                            self._cache[guild_id][ref_invite.code].revoked = True
                            return
                    else:
                        self._cache[guild_id][ref_invite.code].revoked = True
                        return
                except Forbidden:
                    self._cache[guild_id][ref_invite.code].revoked = True
                    return
            else:
                self._cache[guild_id].pop(invite.code, None)

    async def add_guild_cache(self, guild):
        """
        Add guild invites to the cache.

        Parameters:
            guild (discord.Guild): The guild to add invites from to the cache.
        """
        async with self._lock:
            self._cache[guild.id] = {}
            for invite in await guild.invites():
                self._cache[guild.id][invite.code] = invite

    async def remove_guild_cache(self, guild):
        """
        Remove guild invites from the cache.

        Parameters:
            guild (discord.Guild): The guild to remove invites from the cache.
        """
        async with self._lock:
            self._cache.pop(guild.id, None)

    async def fetch_inviter(self, member):
        """
        Fetch the inviter of a member by comparing current and cached invites.

        Parameters:
            member (discord.Member): The member whose inviter is to be fetched.

        Returns:
            discord.Member: The inviter of the member.
        """
        await asyncio.sleep(self.bot.latency)
        async with self._lock:
            guild_id = member.guild.id
            for new_invite in await member.guild.invites():
                for cached_invite in self._cache[guild_id].values():
                    if (new_invite.code == cached_invite.code and new_invite.uses - cached_invite.uses == 1) or cached_invite.revoked:
                        if cached_invite.revoked:
                            self._cache[guild_id].pop(cached_invite.code, None)
                        elif new_invite.inviter == cached_invite.inviter:
                            self._cache[guild_id][cached_invite.code] = new_invite
                        else:
                            self._cache[guild_id][cached_invite.code].uses += 1
                        inviter_id = cached_invite.inviter.id
                        if inviter_id is not None:
                            inviter = member.guild.get_member(inviter_id)
                            return inviter
                        else:
                            return None  # Handle the case when inviter_id is None (vanity link)
