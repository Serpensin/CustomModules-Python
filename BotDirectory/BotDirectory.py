import aiohttp
import asyncio


class Stats:
    def __init__(self, bot, logger=None, TOPGG_TOKEN='', DISCORDBOTS_TOKEN='', DISCORDBOTLISTCOM_TOKEN='', DISCORDLIST_TOKEN=''):
        """Initialize the Stats class.

        Args:
            bot: The Discord bot instance.
            logger: The logger instance for logging messages.
            TOPGG_TOKEN: Token for top.gg API.
            DISCORDBOTS_TOKEN: Token for discord.bots.gg API.
            DISCORDBOTLISTCOM_TOKEN: Token for discordbotlist.com API.
            DISCORDLIST_TOKEN: Token for discordlist.gg API.
        """
        self.bot = bot
        self.logger = logger
        self.TOPGG_TOKEN = TOPGG_TOKEN
        self.DISCORDBOTS_TOKEN = DISCORDBOTS_TOKEN
        self.DISCORDBOTLISTCOM_TOKEN = DISCORDBOTLISTCOM_TOKEN
        self.DISCORDLIST_TOKEN = DISCORDLIST_TOKEN

    async def _post_stats(self, url, headers, json_data):
        """Post statistics to a given URL.

        Args:
            url (str): The URL to post the statistics to.
            headers (dict): The headers to include in the request.
            json_data (dict): The JSON data to include in the request.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json_data) as resp:
                if resp.status != 200 and self.logger:
                    self.logger.error(f'Failed to update {url}: {resp.status} {resp.reason}')

    async def _topgg(self):
        """Update statistics on top.gg."""
        if not self.TOPGG_TOKEN:
            return
        headers = {
            'Authorization': self.TOPGG_TOKEN,
            'Content-Type': 'application/json'
        }
        url = f'https://top.gg/api/bots/{self.bot.user.id}/stats'
        json_data = {'server_count': len(self.bot.guilds), 'shard_count': len(self.bot.shards)}
        while True:
            await self._post_stats(url, headers, json_data)
            try:
                await asyncio.sleep(60 * 30)
            except asyncio.CancelledError:
                break

    async def _discordbots(self):
        """Update statistics on discord.bots.gg."""
        if not self.DISCORDBOTS_TOKEN:
            return
        headers = {
            'Authorization': self.DISCORDBOTS_TOKEN,
            'Content-Type': 'application/json'
        }
        url = f'https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats'
        json_data = {'guildCount': len(self.bot.guilds), 'shardCount': len(self.bot.shards)}
        while True:
            await self._post_stats(url, headers, json_data)
            try:
                await asyncio.sleep(60 * 30)
            except asyncio.CancelledError:
                break

    async def _discordbotlist_com(self):
        """Update statistics on discordbotlist.com."""
        if not self.DISCORDBOTLISTCOM_TOKEN:
            return
        headers = {
            'Authorization': self.DISCORDBOTLISTCOM_TOKEN,
            'Content-Type': 'application/json'
        }
        url = f'https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats'
        json_data = {'guilds': len(self.bot.guilds), 'users': sum(guild.member_count for guild in self.bot.guilds)}
        while True:
            await self._post_stats(url, headers, json_data)
            try:
                await asyncio.sleep(60 * 30)
            except asyncio.CancelledError:
                break

    async def _discordlist(self):
        """Update statistics on discordlist.gg."""
        if not self.DISCORDLIST_TOKEN:
            return
        headers = {
            'Authorization': f'Bearer {self.DISCORDLIST_TOKEN}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        url = f'https://api.discordlist.gg/v0/bots/{self.bot.user.id}/guilds'
        json_data = {"count": len(self.bot.guilds)}
        while True:
            await self._post_stats(url, headers, json_data)
            try:
                await asyncio.sleep(60 * 30)
            except asyncio.CancelledError:
                break

    async def start_stats_update(self):
        """Start updating statistics on various bot listing sites."""
        updates = [self._topgg(), self._discordbots(), self._discordbotlist_com(), self._discordlist()]
        await asyncio.gather(*updates)

    async def task(self):
        """Start the task for periodic statistics updates."""
        while True:
            await self.start_stats_update()
            try:
                await asyncio.sleep(60 * 30)
            except asyncio.CancelledError:
                break


if __name__ == '__main__':
    print('This is a module. Do not run it directly.')