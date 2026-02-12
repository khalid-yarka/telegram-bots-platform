import telebot
from telebot.types import Message, Update
from bots.ardayda_bot import handlers, database


class ArdaydaBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)

        @self.bot.message_handler(content_types=["text"])
        def router(message: Message):
            user_id = message.from_user.id

            if not database.get_user(user_id):
                database.add_user(user_id)

            status = database.get_user_status(user_id)

            if status.startswith("reg:"):
                handlers.registration(self.bot, message)
            elif status.startswith("menu:"):
                handlers.menu_router(self.bot, message)
            else:
                handlers.start(self.bot, message)

    def process_update(self, update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True