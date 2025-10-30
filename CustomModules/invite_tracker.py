import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from discord import AuditLogAction
from discord.errors import Forbidden


class Tracker:
    """
    A class for tracking invites and managing their cache.
    """

    def __init__(self, bot, logger: Optional[logging.Logger] = None):
        """
        Initialize the Tracker class.

        Parameters:
            bot (discord.Client/discord.AutoShardedClient): The Discord bot instance.
            logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
            under CustomModules.InviteTracker. Defaults to None.
        """
        # Setup logger with child hierarchy: parent -> CustomModules -> InviteTracker
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("InviteTracker")
        else:
            self.logger = logging.getLogger("CustomModules.InviteTracker")

        self.logger.debug("Initializing InviteTracker")

        self.bot = bot
        self._cache = {}
        self._lock = asyncio.Lock()

        self.logger.info("InviteTracker initialized")

    async def cache_invites(self) -> None:
        """
        Cache invites for all guilds the bot is currently in.
        """
        self.logger.info(f"Caching invites for {len(self.bot.guilds)} guilds")
        async with self._lock:
            tasks = [self._cache_guild_invites(guild) for guild in self.bot.guilds]
            await asyncio.gather(*tasks)
        self.logger.debug(f"Cached invites for {len(self._cache)} guilds")

    async def _cache_guild_invites(self, guild) -> None:
        """
        Helper method to cache invites for a single guild.
        """
        try:
            invites = await guild.invites()
            self._cache[guild.id] = {invite.code: invite for invite in invites}
            self.logger.debug(f"Cached {len(invites)} invites for guild {guild.id}")
        except Forbidden:
            self.logger.warning(
                f"Missing permissions to fetch invites for guild {guild.id}"
            )

    async def update_invite_cache(self, invite) -> None:
        """
        Update the invite cache with a new or modified invite.

        Parameters:
            invite (discord.Invite): The invite to update the cache with.
        """
        async with self._lock:
            self._cache.setdefault(invite.guild.id, {})[invite.code] = invite
            self.logger.debug(
                f"Updated invite cache for code {invite.code} in guild {invite.guild.id}"
            )

    async def remove_invite_cache(self, invite) -> None:
        """
        Remove an invite from the cache when it's deleted or expired.

        Parameters:
            invite (discord.Invite): The invite to remove from the cache.
        """
        self.logger.debug(
            f"Removing invite {invite.code} from cache for guild {invite.guild.id}"
        )
        async with self._lock:
            guild_id = invite.guild.id
            if guild_id not in self._cache:
                self.logger.debug(f"Guild {guild_id} not in cache")
                return
            ref_invite = self._cache[guild_id].get(invite.code)
            if not ref_invite:
                self.logger.debug(f"Invite code {invite.code} not found in cache")
                return
            if (
                (
                    ref_invite.created_at.timestamp() + ref_invite.max_age
                    > datetime.now(timezone.utc).timestamp()
                    or ref_invite.max_age == 0
                )
                and ref_invite.max_uses > 0
                and ref_invite.uses == ref_invite.max_uses - 1
            ):
                try:
                    async for entry in invite.guild.audit_logs(
                        limit=1, action=AuditLogAction.invite_delete
                    ):
                        if entry.target.code != invite.code:
                            self._cache[guild_id][ref_invite.code].revoked = True
                            self.logger.debug(f"Marked invite {invite.code} as revoked")
                            return
                        break
                    self._cache[guild_id][ref_invite.code].revoked = True
                    self.logger.debug(
                        f"Marked invite {invite.code} as revoked after audit log check"
                    )
                    return
                except Forbidden:
                    self._cache[guild_id][ref_invite.code].revoked = True
                    self.logger.warning(
                        f"Missing audit log permissions for guild {guild_id}, marked invite as revoked"
                    )
                    return
            else:
                self._cache[guild_id].pop(invite.code, None)
                self.logger.debug(f"Removed invite {invite.code} from cache")

    async def add_guild_cache(self, guild) -> None:
        """
        Add guild invites to the cache.

        Parameters:
            guild (discord.Guild): The guild to add invites from to the cache.
        """
        self.logger.debug(f"Adding guild {guild.id} to invite cache")
        async with self._lock:
            invites = await guild.invites()
            self._cache[guild.id] = {invite.code: invite for invite in invites}
            self.logger.info(
                f"Added {len(invites)} invites for guild {guild.id} to cache"
            )

    async def remove_guild_cache(self, guild) -> None:
        """
        Remove guild invites from the cache.

        Parameters:
            guild (discord.Guild): The guild to remove invites from the cache.
        """
        async with self._lock:
            removed = self._cache.pop(guild.id, None)
            if removed:
                self.logger.info(f"Removed guild {guild.id} from invite cache")
            else:
                self.logger.debug(f"Guild {guild.id} was not in invite cache")

    async def fetch_inviter(self, member):
        """
        Fetch the inviter of a member by comparing current and cached invites.

        Parameters:
            member (discord.Member): The member whose inviter is to be fetched.

        Returns:
            discord.Member | None: The inviter of the member.
        """
        self.logger.debug(
            f"Fetching inviter for member {member.id} in guild {member.guild.id}"
        )
        await asyncio.sleep(self.bot.latency)
        async with self._lock:
            guild_id = member.guild.id
            new_invites = {
                invite.code: invite for invite in await member.guild.invites()
            }
            for code, new_invite in new_invites.items():
                cached_invite = self._cache[guild_id].get(code)
                if cached_invite and (
                    new_invite.uses - cached_invite.uses == 1 or cached_invite.revoked
                ):
                    if cached_invite.revoked:
                        self._cache[guild_id].pop(code, None)
                        self.logger.debug(f"Removed revoked invite {code} from cache")
                    elif new_invite.inviter == cached_invite.inviter:
                        self._cache[guild_id][code] = new_invite
                        self.logger.debug(f"Updated invite {code} uses in cache")
                    else:
                        self._cache[guild_id][code].uses += 1
                        self.logger.debug(f"Incremented uses for invite {code}")
                    inviter_id = cached_invite.inviter.id
                    if inviter_id is not None:
                        inviter = member.guild.get_member(inviter_id)
                        self.logger.info(
                            f"Found inviter {inviter_id} for member {member.id}"
                        )
                        return inviter
                    else:
                        self.logger.debug(
                            f"No inviter found for member {member.id} (likely vanity link)"
                        )
                        return None  # Handle the case when inviter_id is None (vanity link)

            self.logger.warning(f"Could not determine inviter for member {member.id}")
            return None
