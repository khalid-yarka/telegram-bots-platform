# bots/ardayda_bot/bot.py
import logging
import telebot
from telebot.types import Message, Update

from bots.ardayda_bot import handlers, buttons

logger = logging.getLogger(__name__)


class ArdaydaBot:
    def __init__(self, bot_token: str):
        self.bot = telebot.TeleBot(bot_token, threaded=False)

        # ========= DECORATORS ONLY =========

        @self.bot.message_handler(commands=["start", "help"])
        def start_cmd(message: Message):
            handlers.start(self.bot, message)

        @self.bot.message_handler(func=lambda m: m.text == buttons.Buttons.MainMenu.SETTINGS)
        def settings_menu(message: Message):
            handlers.settings(self.bot, message)

        @self.bot.message_handler(func=lambda m: m.text in [
            buttons.Buttons.MainMenu.SEARCH,
            buttons.Buttons.MainMenu.UPLOAD,
            buttons.Buttons.MainMenu.PROFILE
        ])
        def main_menu(message: Message):
            handlers.main_menu(self.bot, message)

        # registration flow only
        @self.bot.message_handler(func=lambda m: handlers.is_registering(m.from_user.id))
        def registration(message: Message):
            handlers.registration(self.bot, message)

    # ========= WEBHOOK =========
    def process_update(self, update_json):
        try:
            update = Update.de_json(update_json)
            self.bot.process_new_updates([update])
            return True
        except Exception as e:
            logger.error(f"Bot error: {e}")
            return False


def process_ardayda_update(bot_token, update_json):
    bot = ArdaydaBot(bot_token)
    return bot.process_update(update_json)