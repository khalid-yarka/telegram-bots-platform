import telebot
from telebot.types import Message, Update
from bots.ardayda_bot import handlers, database, text


class ArdaydaBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)

        @self.bot.message_handler(content_types=["text"])
        def router(message: Message):
            user_id = message.from_user.id

            if not database.get_user(user_id):
                database.add_user(user_id)
                self.bot.reply_to(message,text.REG_NAME)
                return
            
            status = database.get_user_status(user_id) or "reg:name"
            
            # 🚫 Commands should never be treated as form input
            if text_msg.startswith("/"):
                handlers.start(self.bot, message)
                return
            
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
        


active_bots = {}

def process_ardayda_update(bot_token, update_json):
    if bot_token not in active_bots:
        active_bots[bot_token] = ArdaydaBot(bot_token)

    bot = active_bots[bot_token]
    return bot.process_update(update_json)