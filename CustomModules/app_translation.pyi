"""Type stubs for AppTranslation module."""
import discord.app_commands

class Translator(discord.app_commands.Translator):
    """Discord application translation utilities."""
    
    def __init__(self) -> None: ...
    
    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        context: discord.app_commands.TranslationContext
    ) -> str: ...

__all__ = ['Translator']
