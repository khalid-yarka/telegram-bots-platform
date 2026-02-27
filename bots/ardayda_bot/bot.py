# bots/ardayda_bot/bot.py

import telebot
from telebot.types import Update, Message, CallbackQuery

from bots.ardayda_bot import (
    database,
    handlers,
)

from bots.ardayda_bot.database import init_connection_pool


active_bots = {}

class ArdaydaBot:
    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token, threaded=False)

        # -------------------------
        # 1. FIRST MESSAGE → HAND OFF TO HANDLERS
        # -------------------------
        @self.bot.message_handler(
            func=lambda m: database.get_user(m.from_user.id) is None,
            content_types=["text", "document"]
        )
        def first_message_handler(message: Message):
            # New user - pass to handlers for registration
            handlers.handle_first_message(self.bot, message)

        # -------------------------
        # 2. ALL TEXT MESSAGES → HAND OFF TO HANDLERS
        # -------------------------
        @self.bot.message_handler(content_types=["text"])
        def text_message_handler(message: Message):
            handlers.handle_message(self.bot, message)

        # -------------------------
        # 3. ALL DOCUMENTS → HAND OFF TO HANDLERS
        # -------------------------
        @self.bot.message_handler(content_types=["document"])
        def document_handler(message: Message):
            handlers.handle_document(self.bot, message)

        # -------------------------
        # 4. ALL CALLBACK QUERIES → HAND OFF TO HANDLERS
        # -------------------------
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call: CallbackQuery):
            handlers.handle_callback(self.bot, call)

    # -------------------------
    # PROCESS TELEGRAM UPDATE
    # -------------------------
    def process_update(self, update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True


# -------------------------
# FLASK DISPATCH ENTRY
# -------------------------
def process_ardayda_update(bot_token, update_json):
    if bot_token not in active_bots:
        active_bots[bot_token] = ArdaydaBot(bot_token)
    return active_bots[bot_token].process_update(update_json)
    
# Initialize connection pool when module loads
init_connection_pool()