import telebot
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from master_db.operations import add_log_entry

logger = logging.getLogger(__name__)

class DhalinyaroBot:
    """Dhalinyaro Youth Bot - Improved interface + safe updates"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    # ==================== HANDLERS ====================
    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            self.send_main_menu(message)

        @self.bot.message_handler(commands=['events', 'activities'])
        def handle_events(message):
            self.send_events(message)

        @self.bot.message_handler(commands=['groups', 'community'])
        def handle_groups(message):
            self.send_groups(message)

        @self.bot.message_handler(commands=['meetup', 'meet'])
        def handle_meetup(message):
            self.send_meetup(message)

        @self.bot.message_handler(commands=['about', 'info'])
        def handle_about(message):
            self.send_about(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.process_callback(call)

    # ==================== SAFE REPLY / EDIT ====================
    def safe_reply(self, message, text, reply_markup=None):
        try:
            return self.bot.send_message(message.chat.id, text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Reply failed for {message.from_user.id}: {str(e)}")
            add_log_entry(self.bot_token, 'error', message.from_user.id, str(e))
            return None

    def safe_edit(self, chat_id, message_id, text, reply_markup=None):
        try:
            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            logger.warning(f"Edit failed {message_id}: {str(e)}")

    # ==================== INLINE INTERFACE ====================
    def build_main_menu(self):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📅 Events", callback_data="menu_events"),
            InlineKeyboardButton("👥 Groups", callback_data="menu_groups"),
            InlineKeyboardButton("🤝 Meetup", callback_data="menu_meetup"),
            InlineKeyboardButton("ℹ️ About", callback_data="menu_about")
        )
        return markup

    # ==================== COMMANDS ====================
    def send_main_menu(self, message):
        username = message.from_user.username or "Friend"
        text = f"🎉 Hello {username}!\nWelcome to Dhalinyaro Youth Bot.\nUse the buttons below to navigate:"
        self.safe_reply(message, text, self.build_main_menu())
        add_log_entry(self.bot_token, 'command', message.from_user.id, '/start')

    def send_events(self, message):
        events = [
            "🎯 Youth Leadership Workshop - Jan 15",
            "⚽ Football Tournament - Jan 20",
            "💻 Tech Skills Training - Jan 25",
            "🎨 Art & Culture Festival - Feb 1",
            "📚 Study Group Session - Feb 5"
        ]
        text = "📅 Upcoming Youth Events:\n\n" + "\n".join(events)
        text += "\n\nUse /meetup to organize your own event!"
        self.safe_reply(message, text, self.build_main_menu())
        add_log_entry(self.bot_token, 'command', message.from_user.id, '/events')

    def send_groups(self, message):
        groups = [
            "👥 Tech Enthusiasts Group",
            "⚽ Sports & Fitness Club",
            "🎨 Arts & Culture Community",
            "📚 Study & Career Network",
            "🌍 Social Change Activists"
        ]
        text = "👥 Youth Groups & Communities:\n\n" + "\n".join(groups)
        text += "\n\nJoin groups to connect with peers!"
        self.safe_reply(message, text, self.build_main_menu())
        add_log_entry(self.bot_token, 'command', message.from_user.id, '/groups')

    def send_meetup(self, message):
        text = (
            "🤝 Organize a Meetup\n\n"
            "Steps to organize a meetup:\n"
            "1. Choose a topic/activity\n"
            "2. Select date & time\n"
            "3. Choose location\n"
            "4. Share with community\n\n"
            "Example topics:\n"
            "• Study sessions\n• Sports activities\n• Tech workshops\n• Cultural events\n\n"
            "Start by typing: 'I want to organize...'"
        )
        self.safe_reply(message, text, self.build_main_menu())
        add_log_entry(self.bot_token, 'command', message.from_user.id, '/meetup')

    def send_about(self, message):
        text = (
            "🌟 About Dhalinyaro Bot\n\n"
            "Dhalinyaro connects Somali youth worldwide.\n\n"
            "Our mission:\n"
            "• Connect youth globally\n"
            "• Share opportunities\n"
            "• Organize events\n"
            "• Build community\n\n"
            "For youth, by youth!"
        )
        self.safe_reply(message, text, self.build_main_menu())
        add_log_entry(self.bot_token, 'command', message.from_user.id, '/about')

    # ==================== CALLBACK HANDLER ====================
    def process_callback(self, call):
        data = call.data
        if data == "menu_events":
            self.safe_edit(call.message.chat.id, call.message.message_id, "Fetching events...", self.build_main_menu())
            self.send_events(call.message)
        elif data == "menu_groups":
            self.safe_edit(call.message.chat.id, call.message.message_id, "Fetching groups...", self.build_main_menu())
            self.send_groups(call.message)
        elif data == "menu_meetup":
            self.safe_edit(call.message.chat.id, call.message.message_id, "Meetup info...", self.build_main_menu())
            self.send_meetup(call.message)
        elif data == "menu_about":
            self.safe_edit(call.message.chat.id, call.message.message_id, "About Dhalinyaro...", self.build_main_menu())
            self.send_about(call.message)
        else:
            logger.warning(f"Unknown callback: {data}")

    # ==================== PROCESS UPDATE ====================
    def process_update(self, update_json):
        try:
            update = telebot.types.Update.de_json(update_json)
            self.bot.process_new_updates([update])
            if update.message:
                user_id = update.message.from_user.id
                command = (update.message.text or 'unknown').split()[0]
                add_log_entry(self.bot_token, 'command', user_id, command)
            return True
        except Exception as e:
            logger.error(f"Dhalinyaro bot error: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# ==================== GLOBAL FUNCTION ====================
def process_dhalinyaro_update(bot_token, update_json):
    try:
        bot = DhalinyaroBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_dhalinyaro_update: {str(e)}")
        return False