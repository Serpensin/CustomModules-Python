"""Type stubs for app_translation module."""
import logging
from typing import Optional

import discord

class Translator(discord.app_commands.Translator):
    logger: logging.Logger
    translations: dict
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    async def load(self) -> None: ...
    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        context: discord.app_commands.TranslationContext,
    ) -> Optional[str]: ...
