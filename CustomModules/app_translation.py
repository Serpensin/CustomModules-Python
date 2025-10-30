import logging
from typing import Optional

import discord


class Translator(discord.app_commands.Translator):
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initializes the Translator class with predefined translations for German and Japanese locales.

        Args:
            logger (Optional[logging.Logger]): Parent logger. If provided, creates a child logger
            under CustomModules.AppTranslation. Defaults to None.
        """
        # Setup logger with child hierarchy: parent -> CustomModules -> AppTranslation
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("AppTranslation")
        else:
            self.logger = logging.getLogger("CustomModules.AppTranslation")

        self.logger.debug("Initializing AppTranslation Translator")

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
            },
        }

        total_translations = sum(len(trans) for trans in self.translations.values())
        self.logger.info(
            f"Translator initialized with {len(self.translations)} locales and {total_translations} total translations"
        )

    async def load(self) -> None:
        """
        Placeholder method for loading translations.
        Currently does nothing.
        """
        self.logger.debug("Load method called (currently no-op)")

    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        context: discord.app_commands.TranslationContext,
    ) -> Optional[str]:
        """
        Translates a given string to the specified locale.

        Parameters:
        string (discord.app_commands.locale_str): The string that is requesting to be translated.
        locale (discord.Locale): The target language to translate to.
        context (discord.app_commands.TranslationContext): The origin of this string, e.g., TranslationContext.command_name, etc.

        Returns:
        Optional[str]: The translated string if available, otherwise the original string.
        """
        original = string.message
        translated = self.translations.get(locale, {}).get(original, original)

        if translated != original:
            self.logger.debug(
                f"Translated '{original}' to '{translated}' for locale {locale.value}"
            )
        else:
            self.logger.debug(
                f"No translation found for '{original}' in locale {locale.value}, using original"
            )

        return translated
