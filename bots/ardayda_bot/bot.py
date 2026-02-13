import telebot
from telebot.types import Update, Message
from bots.ardayda_bot import handlers, database, text


class ArdaydaBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)

        # New user → start registration
        @self.bot.message_handler(
            func=lambda msg: database.get_user(msg.from_user.id) is None,
            chat_types=["private"],
            content_types=["text", "photo", "video", "document", "audio", "voice", "sticker"]
        )
        def first_message_handler(message: Message):
            user_id = message.from_user.id
            database.add_user(user_id)
            database.set_status(user_id, "reg:name")
            self.bot.send_message(message.chat.id, text.REG_NAME)

        # Reject non-text during registration
        @self.bot.message_handler(
            func=lambda msg: handlers.is_registering(msg.from_user.id),
            content_types=["photo", "video", "document", "audio", "voice", "sticker"]
        )
        def registration_non_text(message: Message):
            self.bot.send_message(
                message.chat.id,
                "❌ Please use the buttons or send text to continue registration."
            )

        # Registration handler
        @self.bot.message_handler(
            func=lambda msg: handlers.is_registering(msg.from_user.id),
            content_types=["text"]
        )
        def registration_handler(message: Message):
            handlers.registration(self.bot, message)

        # Menu
        @self.bot.message_handler(
            func=lambda msg: (
                database.get_user_status(msg.from_user.id)
                and database.get_user_status(msg.from_user.id).startswith("menu:")
            ),
            content_types=["text"]
        )
        def menu_handler(message: Message):
            handlers.menu_router(self.bot, message)

    def process_update(self, update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True


active_bots = {}


def process_ardayda_update(bot_token, update_json):
    if bot_token not in active_bots:
        active_bots[bot_token] = ArdaydaBot(bot_token)

    return active_bots[bot_token].process_update(update_json)