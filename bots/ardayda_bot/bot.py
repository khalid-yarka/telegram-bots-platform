import telebot
from telebot.types import Update, Message, CallbackQuery
from bots.ardayda_bot import handlers, database, buttons, text

active_bots = {}

class ArdaydaBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)

        # New user registration
        @self.bot.message_handler(
            func=lambda m: database.get_user(m.from_user.id) is None,
            content_types=["text"]
        )
        def first_message_handler(message):
            user_id = message.from_user.id
        
            if database.get_user(user_id):
                return
        
            database.add_user(user_id)
            self.bot.send_message(message.chat.id, text.REG_NAME)
<<<<<<< HEAD
    
        # Registration
        @self.bot.message_handler(func=lambda m: handlers.is_registering(m.from_user.id), content_types=["text"])
        def registration_handler(message: Message):
=======

        # Registration flow
        @self.bot.message_handler(
            func=lambda m: handlers.is_registering(m.from_user.id),
            content_types=["text"]
        )
        def registration_handler(message):
>>>>>>> Advance catogry  but un solved
            handlers.registration(self.bot, message)

        # Cancel
        @self.bot.message_handler(commands=["cancel"])
        def cancel_handler(message):
            user_id = message.from_user.id
<<<<<<< HEAD
            if handlers.is_registering(user_id):
                self.bot.send_message(message.chat.id, "❌ Registration cannot be cancelled. Please complete it first.")
                return
        
            handlers.finalize_user(user_id)
            self.bot.send_message(
                message.chat.id,
                "❌ Operation cancelled. You are now back at the main menu.",
=======

            if handlers.is_registering(user_id):
                self.bot.send_message(
                    message.chat.id,
                    "❌ Registration cannot be cancelled."
                )
                return

            handlers.finalize_user(user_id)
            database.set_status(user_id, "menu:main")

            self.bot.send_message(
                message.chat.id,
                "❌ Operation cancelled.\n\nMain menu:",
>>>>>>> Advance catogry  but un solved
                reply_markup=buttons.main_menu()
            )

        # Upload PDF document
        @self.bot.message_handler(
            func=lambda m: handlers.is_uploading(m.from_user.id),
            content_types=["document"]
        )
        def upload_handler(message):
            user_id = message.from_user.id
            status = database.get_user_status(user_id)
            if status != "upload:waiting_file":
                return
            handlers.handle_pdf_upload(self.bot, message)

        # Menu router
        @self.bot.message_handler(
            func=lambda m: (database.get_user_status(m.from_user.id) or "").startswith("menu:"),
            content_types=["text"]
        )
        def menu_handler(message):
            handlers.menu_router(self.bot, message)

        # Callback router
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            user_id = call.from_user.id
            data = call.data

            if data.startswith("upload_"):
                if user_id not in handlers.pdf_upload_stage:
                    self.bot.answer_callback_query(call.id, "❌ Upload expired.")
                    return
                handlers.handle_pdf_upload_callback(self.bot, call)
                return

            if data.startswith(("pdf_send:", "like_pdf:", "pdf_page:")):
                handlers.handle_pdf_interaction(self.bot, call)
                return

            if data.startswith("search_"):
                handlers.handle_search_callback(self.bot, call)
                return

            self.bot.answer_callback_query(call.id, "❌ Button expired.")

    def process_update(self, update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True


def process_ardayda_update(bot_token, update_json):
    if bot_token not in active_bots:
        active_bots[bot_token] = ArdaydaBot(bot_token)
    return active_bots[bot_token].process_update(update_json)