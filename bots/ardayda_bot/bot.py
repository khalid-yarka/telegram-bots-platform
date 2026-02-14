import telebot
from telebot.types import Update, Message, CallbackQuery
from bots.ardayda_bot import handlers, database, buttons, text

active_bots = {}

class ArdaydaBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, threaded=False)

        # Unknown user → registration start
        @self.bot.message_handler(
            func=lambda m: database.get_user(m.from_user.id) is None,
            content_types=["text","document","photo","video","audio","voice","sticker"]
        )
        def first_message_handler(message: Message):
            user_id = message.from_user.id
            database.add_user(user_id)
            database.set_status(user_id, "reg:name")
            self.bot.send_message(message.chat.id, text.REG_NAME)

        # Registration
        @self.bot.message_handler(func=lambda m: handlers.is_registering(m.from_user.id), content_types=["text"])
        def registration_handler(message: Message):
            handlers.registration(self.bot, message)
            
        #cancel any operations
        @self.bot.message_handler(commands=["cancel"])
        def cancel_handler(message):
            user_id = message.from_user.id
            handlers.pdf_upload_stage.pop(user_id, None)
            handlers.selected_user_tags.pop(user_id, None)
            handlers.pdf_search_results.pop(user_id, None)
            database.set_status(user_id, "menu:main")
            self.bot.send_message(
                message.chat.id,
                "❌ Operation cancelled.",
                reply_markup=buttons.main_menu()
            )
        
        # Upload PDF
        @self.bot.message_handler(func=lambda m: handlers.is_uploading(m.from_user.id), content_types=["document"])
        def upload_handler(message: Message):
            handlers.handle_pdf_upload(self.bot, message)

        # Menu router
        @self.bot.message_handler(
            func=lambda m: database.get_user_status(m.from_user.id) and database.get_user_status(m.from_user.id).startswith("menu:"),
            content_types=["text"]
        )
        def menu_handler(message: Message):
            handlers.menu_router(self.bot, message)

        # Callback Query handler
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call: CallbackQuery):
            user_id = call.from_user.id
            data = call.data
            status = database.get_user_status(user_id)
        
            # No status? No buttons.
            if not status:
                self.bot.answer_callback_query(call.id, "❌ Session expired.")
                return
        
            # -------- UPLOAD FLOW --------
            if data.startswith("upload_"):
                if not status.startswith("upload:"):
                    self.bot.answer_callback_query(call.id, "❌ Upload cancelled or expired.")
                    return
                handlers.handle_upload_callback(self.bot, call)
                return
        
            # -------- PDF SEARCH / LIKE / PAGINATION FLOW --------
            if data.startswith(("pdf_send:", "like_pdf:", "pdf_page:")):
                search_results = handlers.pdf_search_results.get(user_id) if hasattr(handlers, "pdf_search_results") else None
                handlers.handle_pdf_interaction(self.bot, call)
                return
            
            # -------- SEARCH FLOW --------
            if data.startswith("search_"):
                if not status.startswith("search:"):
                    self.bot.answer_callback_query(call.id, "❌ Search cancelled or expired.")
                    return
                handlers.handle_search_callback(self.bot, call)
                return
        
            # -------- UNKNOWN / STALE BUTTON --------
            self.bot.answer_callback_query(call.id, "❌ This button is no longer active.")

    def process_update(self, update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True


def process_ardayda_update(bot_token, update_json):
    if bot_token not in active_bots:
        active_bots[bot_token] = ArdaydaBot(bot_token)
    return active_bots[bot_token].process_update(update_json)