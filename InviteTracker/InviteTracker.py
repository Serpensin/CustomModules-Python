import asyncio
from datetime import datetime
from discord import AuditLogAction
from discord.errors import Forbidden


class Tracker:
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
            tasks = [self._cache_guild_invites(guild) for guild in self.bot.guilds]
            await asyncio.gather(*tasks)

    async def _cache_guild_invites(self, guild):
        """
        Helper method to cache invites for a single guild.
        """
        try:
            self._cache[guild.id] = {invite.code: invite for invite in await guild.invites()}
        except Forbidden:
            pass

    async def update_invite_cache(self, invite):
        """
        Update the invite cache with a new or modified invite.

        Parameters:
            invite (discord.Invite): The invite to update the cache with.
        """
        async with self._lock:
            self._cache.setdefault(invite.guild.id, {})[invite.code] = invite

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
            self._cache[guild.id] = {invite.code: invite for invite in await guild.invites()}

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
            new_invites = {invite.code: invite for invite in await member.guild.invites()}
            for code, new_invite in new_invites.items():
                cached_invite = self._cache[guild_id].get(code)
                if cached_invite and (new_invite.uses - cached_invite.uses == 1 or cached_invite.revoked):
                    if cached_invite.revoked:
                        self._cache[guild_id].pop(code, None)
                    elif new_invite.inviter == cached_invite.inviter:
                        self._cache[guild_id][code] = new_invite
                    else:
                        self._cache[guild_id][code].uses += 1
                    inviter_id = cached_invite.inviter.id
                    if inviter_id is not None:
                        return member.guild.get_member(inviter_id)
                    else:
                        return None  # Handle the case when inviter_id is None (vanity link)
