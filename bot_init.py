from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tomato.core.settings import SETTINGS


class BotSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotSingleton, cls).__new__(cls)
            cls._instance.bot = Bot(token=SETTINGS.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        return cls._instance

    def get_bot(self):
        return self.bot


bot_singleton = BotSingleton()
bot = bot_singleton.get_bot()
