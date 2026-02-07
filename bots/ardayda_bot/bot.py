import telebot
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from master_db.operations import add_log_entry
from bots.ardayda_bot.database import get_or_create_user,user_exists, get_all_users
from bots.handlers import complate_regestering

logger = logging.getLogger(__name__)

class ArdaydaBot:
    """Ardayda Education Bot - Improved interface + update message"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    # ==================== HANDLERS ====================

    def register_handlers(self):
        """Register commands with inline interface"""

        @self.bot.message_handler(
    func=lambda msg: not self.user_registred(msg.from_user.id),
    chat_types=['private']
)
        def complate_regestering_func(message):
            try:
                user_id = message.from_user.id
                user = get_or_create_user(user_id)
                if user.get('name', False):
                    complate_regestering(self.bot, message, name=True)

                elif user.get('school', False):
                    complate_regestering(self.bot, message, school=True)

                elif user.get('class_', False):
                    complate_regestering(self.bot, message, class_=True)
                    

            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                add_log_entry(self.bot_token, 'error', message.from_user.id, str(e))
                
                self.bot.reply_to(message, "Error while registering ... [ ! ]")

        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            self.send_main_menu(message)

        @self.bot.message_handler(commands=['about', 'info'])
        def handle_about(message):
            self.send_about(message)

        @self.bot.message_handler(commands=['users'])
        def handle_users(message):
            self.send_users(message)

        # Callback query for inline buttons
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.process_callback(call)

    # ==================== USER CHECK ====================

    def user_registred(self, user_id):
        user = get_or_create_user(user_id)
        return user is not None and user.get('complete', False)

    # ==================== SAFE REPLY & UPDATE ====================

    def safe_reply(self, message, text, reply_markup=None):
        """Send reply safely"""
        try:
            return self.bot.send_message(message.chat.id, text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Reply failed for user {message.from_user.id}: {str(e)}")
            add_log_entry(self.bot_token, 'error', message.from_user.id, str(e))
            return None

    def safe_edit(self, chat_id, message_id, text, reply_markup=None):
        """Edit a previously sent message safely"""
        try:
            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id}: {str(e)}")

    # ==================== INLINE INTERFACE ====================

    def build_main_menu(self):
        """Build main menu keyboard"""
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📚 Start", callback_data="menu_start"),
            InlineKeyboardButton("ℹ️ About", callback_data="menu_about"),
            InlineKeyboardButton("👥 Users", callback_data="menu_users"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        )
        return markup

    # ==================== COMMANDS ====================

    def send_main_menu(self, message):
        """Send main menu with inline keyboard"""
        text = f"📌 Hello {getattr(message.from_user, 'username', 'Student')}!\nChoose an option:"
        msg = self.safe_reply(message, text, reply_markup=self.build_main_menu())
        return msg

    def send_about(self, message):
        """Send About info"""
        text = (
            "📖 About Ardayda Bot\n\n"
            "Ardayda means 'Students' in Somali.\n\n"
            "This bot helps students with:\n"
            "• Centralized Exams\n"
            "• Free PDFs\n"
            "• Assignments\n"
            "• Books\n\n"
            "Made for Somali students in Puntland."
        )
        msg = self.safe_reply(message, text, reply_markup=self.build_main_menu())
        return msg

    def send_users(self, message):
        """Send users list safely"""
        try:
            users = get_all_users()
            if not users:
                text = "No users found."
            else:
                text = "👥 Users:\n" + "\n".join(str(u) for u in users)
            msg = self.safe_reply(message, text, reply_markup=self.build_main_menu())
            return msg
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            add_log_entry(self.bot_token, 'error', message.from_user.id, str(e))
            return self.safe_reply(message, "Unable to fetch users.", reply_markup=self.build_main_menu())

    # ==================== CALLBACK HANDLER ====================

    def process_callback(self, call):
        """Handle inline button clicks"""
        user_id = call.from_user.id
        data = call.data

        # Edit the original message to show the selected section
        if data == "menu_start" or data == "menu_help":
            self.safe_edit(call.message.chat.id, call.message.message_id, self.start_text(call.message), self.build_main_menu())
        elif data == "menu_about":
            self.safe_edit(call.message.chat.id, call.message.message_id, self.about_text(), self.build_main_menu())
        elif data == "menu_users":
            users_list = get_all_users()
            text = "👥 Users:\n" + ("\n".join(str(u) for u in users_list) if users_list else "No users found.")
            self.safe_edit(call.message.chat.id, call.message.message_id, text, self.build_main_menu())
        else:
            logger.warning(f"Unknown callback: {data}")

    # ==================== TEXT HELPERS ====================

    def start_text(self, message):
        username = getattr(message.from_user, 'username', 'Student')
        return f"📚 Welcome {username} to Ardayda Bot!\n\nUse the buttons below to navigate."

    def about_text(self):
        return (
            "📖 About Ardayda Bot\n\n"
            "Ardayda means 'Students' in Somali.\n\n"
            "This bot helps students with:\n"
            "• Centralized Exams\n"
            "• Free PDFs\n"
            "• Assignments\n"
            "• Books\n\n"
            "Made for Somali students in Puntland."
        )

    # ==================== UPDATE PROCESS ====================

    def process_update(self, update_json):
        """Process incoming webhook update safely"""
        try:
            if not isinstance(update_json, dict):
                raise ValueError("Invalid update format")
            update = telebot.types.Update.de_json(update_json)
            self.bot.process_new_updates([update])

            # Log command if exists
            if update.message:
                user_id = update.message.from_user.id
                command = (update.message.text or 'unknown').split()[0]
                add_log_entry(self.bot_token, 'command', user_id, command)

            return True

        except Exception as e:
            logger.error(f"Ardayda bot error: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# ==================== GLOBAL FUNCTION ====================

def process_ardayda_update(bot_token, update_json):
    """Process update for Ardayda bot"""
    try:
        bot = ArdaydaBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_ardayda_update: {str(e)}")
        return False