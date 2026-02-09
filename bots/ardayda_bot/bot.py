import telebot
import logging
"""
from master_db.operations import add_log_entry
from bots.ardayda_bot.database import get_or_create_user,user_exists, get_all_users
"""
from bots.ardayda_bot.handlers import complate_regestering,main_menu

logger = logging.getLogger(__name__)

class ArdaydaBot:
    """Ardayda Education Bot - Improved interface + update message"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    # ==================== HANDLERS ====================

    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            send_main_menu(self.bot, message)
        

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