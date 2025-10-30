import asyncio
import logging
from typing import Optional

import aiohttp


class Stats:
    # Constants for repeated string literals
    CONTENT_TYPE_JSON = "application/json"
    CONTENT_TYPE_JSON_UTF8 = "application/json; charset=utf-8"

    def __init__(
        self,
        bot,
        logger: Optional[logging.Logger] = None,
        topgg_token: str = "",
        discordbots_token: str = "",
        discordbotlistcom_token: str = "",
        discordlist_token: str = "",
    ):
        # Setup logger with child hierarchy: parent -> CustomModules -> BotDirectory
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("BotDirectory")
        else:
            self.logger = logging.getLogger("CustomModules.BotDirectory")

        self.logger.debug("Initializing Stats module")

        self.bot = bot
        self.topgg_token = topgg_token
        self.discordbots_token = discordbots_token
        self.discordbotlistcom_token = discordbotlistcom_token
        self.discordlist_token = discordlist_token

        self._tasks = []

        active_tokens = sum(
            [
                bool(topgg_token),
                bool(discordbots_token),
                bool(discordbotlistcom_token),
                bool(discordlist_token),
            ]
        )
        self.logger.info(
            f"Stats initialized with {active_tokens} active bot directory tokens"
        )

    async def _post_stats(self, url, headers, json_data):
        """Post statistics to a given URL with error logging."""
        self.logger.debug(f"Posting stats to {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=json_data) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        self.logger.error(
                            f"Failed to update {url}: {resp.status} {text}"
                        )
                    else:
                        self.logger.debug(f"Successfully posted stats to {url}")
        except Exception as e:
            self.logger.error(f"Exception while posting stats to {url}: {e}")

    async def _loop_post(self, url, headers, json_func, interval=60 * 30):
        """Generic loop for posting stats periodically."""
        self.logger.debug(
            f"Starting stats update loop for {url} (interval: {interval}s)"
        )
        while True:
            try:
                json_data = json_func()
                await self._post_stats(url, headers, json_data)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                self.logger.debug(f"Stats loop for {url} cancelled")
                raise  # Re-raise to properly handle cancellation
            except Exception as e:
                self.logger.error(f"Exception in stats loop for {url}: {e}")
                await asyncio.sleep(interval)

    def _topgg_data(self):
        return {
            "server_count": len(self.bot.guilds),
            "shard_count": len(self.bot.shards),
        }

    def _discordbots_data(self):
        return {"guildCount": len(self.bot.guilds), "shardCount": len(self.bot.shards)}

    def _discordbotlist_com_data(self):
        return {
            "guilds": len(self.bot.guilds),
            "users": sum(guild.member_count for guild in self.bot.guilds),
        }

    def _discordlist_data(self):
        return {"count": len(self.bot.guilds)}

    def start_stats_update(self):
        """Start all stats update tasks in parallel."""
        self.logger.info("Starting stats update tasks")

        if self.topgg_token:
            self.logger.debug("Configuring top.gg stats updates")
            url = f"https://top.gg/api/bots/{self.bot.user.id}/stats"
            headers = {
                "Authorization": self.topgg_token,
                "Content-Type": self.CONTENT_TYPE_JSON,
            }
            self._tasks.append(
                asyncio.create_task(self._loop_post(url, headers, self._topgg_data))
            )

        if self.discordbots_token:
            self.logger.debug("Configuring discord.bots.gg stats updates")
            url = f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats"
            headers = {
                "Authorization": self.discordbots_token,
                "Content-Type": self.CONTENT_TYPE_JSON,
            }
            self._tasks.append(
                asyncio.create_task(
                    self._loop_post(url, headers, self._discordbots_data)
                )
            )

        if self.discordbotlistcom_token:
            self.logger.debug("Configuring discordbotlist.com stats updates")
            url = f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats"
            headers = {
                "Authorization": self.discordbotlistcom_token,
                "Content-Type": self.CONTENT_TYPE_JSON,
            }
            self._tasks.append(
                asyncio.create_task(
                    self._loop_post(url, headers, self._discordbotlist_com_data)
                )
            )

        if self.discordlist_token:
            self.logger.debug("Configuring discordlist.gg stats updates")
            url = f"https://api.discordlist.gg/v0/bots/{self.bot.user.id}/guilds"
            headers = {
                "Authorization": f"Bearer {self.discordlist_token}",
                "Content-Type": self.CONTENT_TYPE_JSON_UTF8,
            }
            self._tasks.append(
                asyncio.create_task(
                    self._loop_post(url, headers, self._discordlist_data)
                )
            )

        self.logger.info(f"Started {len(self._tasks)} stats update tasks")
        return self._tasks

    async def stop_stats_update(self):
        """Cancel all running stats update tasks."""
        self.logger.info(f"Stopping {len(self._tasks)} stats update tasks")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self.logger.debug("All stats update tasks stopped")


if __name__ == "__main__":
    print("This is a module. Do not run it directly.")
