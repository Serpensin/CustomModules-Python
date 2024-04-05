import discord
from typing import Optional


class Translator(discord.app_commands.Translator):
    def __init__(self):
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
        print("App Translator initialized.")

    async def translate(self,
                        string: discord.app_commands.locale_str,
                        locale: discord.Locale,
                        context: discord.app_commands.TranslationContext) -> Optional[str]:
        """
        `locale_str` is the string that is requesting to be translated
        `locale` is the target language to translate to
        `context` is the origin of this string, eg TranslationContext.command_name, etc
        This function must return a string (that's been translated), or `None` to signal no available translation available, and will default to the original.
        """
        string = string.message
        return self.translations.get(locale, {}).get(string, string)