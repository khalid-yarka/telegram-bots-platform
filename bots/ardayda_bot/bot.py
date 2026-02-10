# bots/ardayda_bot/bot.py
import telebot
import logging
from bots.ardayda_bot import registration
from bots.ardayda_bot.buttons import Buttons

logger = logging.getLogger(__name__)

class ArdaydaBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            registration.start_registration(self.bot, message.from_user.id)

        @self.bot.message_handler(func=lambda msg: True)
        def handle_registration_messages(message):
            handled = registration.handle_message(self.bot, message)
            if not handled:
                pass  # other message handling

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_registration_callbacks(call):
            handled = registration.handle_callback(self.bot, call)
            if not handled:
                pass  # other callback handling

    def process_update(self, update_json):
        try:
            update = telebot.types.Update.de_json(update_json)
            self.bot.process_new_updates([update])
            return True
        except Exception as e:
            logger.error(f"Bot error: {e}")
            return False