import discord
from typing import Optional


class Translator(discord.app_commands.Translator):
    def __init__(self):
        """
        Initializes the Translator class with predefined translations for German and Japanese locales.
        """
        self.translations = {
            discord.Locale.german: {
                "Test, if the bot is responding.": "Teste, ob der Bot antwortet.",
                "Get information about the bot.": "Erhalte Informationen über den Bot.",
                "change_nickname": "nickname_ändern",
            },
            discord.Locale.japanese: {
                "ping": "ピング",
                "Test, if the bot is responding.": "ボットが応答しているかテストします。",
                "botinfo": "ボット情報",
                "Get information about the bot.": "ボットに関する情報を取得します。",
                "change_nickname": "ニックネームを変更する",
            }
        }

    async def load(self):
        """
        Placeholder method for loading translations.
        Currently does nothing.
        """
        pass

    async def translate(self,
                        string: discord.app_commands.locale_str,
                        locale: discord.Locale,
                        context: discord.app_commands.TranslationContext) -> Optional[str]:
        """
        Translates a given string to the specified locale.

        Parameters:
        string (discord.app_commands.locale_str): The string that is requesting to be translated.
        locale (discord.Locale): The target language to translate to.
        context (discord.app_commands.TranslationContext): The origin of this string, e.g., TranslationContext.command_name, etc.

        Returns:
        Optional[str]: The translated string if available, otherwise the original string.
        """
        return self.translations.get(locale, {}).get(string.message, string.message)