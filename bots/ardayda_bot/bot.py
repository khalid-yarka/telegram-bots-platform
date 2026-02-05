#bots/ardayda_bot/bot.py
import telebot
import logging
from master_db.operations import add_log_entry
from text import commands
from bots.ardayda.database import (
    user_exists,
    get_user_status,
    get_all_users
    )
from bots.handlers import(
    complate_regestering)


logger = logging.getLogger(__name__)

class ArdaydaBot:
    """Ardayda Education Bot - Simple bot for students"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    def register_handlers(self):
        """Register Ardayda bot command handlers"""
        
        # New 🆕 User or Non comaplate info
        @self.bot.message_handler(func=lambda message: not user_exists(message.from_user.id) or not get_user_status(message.from_user.id)['complate'],chat_types=['private'])
        def complate_regestering_func(message):
            complate_regestering(self.bot, message)
        
        
        # Start command
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.handle_start(message)
            
        # help command
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            self.handle_help(message)

        # About command
        @self.bot.message_handler(commands=['about', 'info'])
        def handle_about(message):
            self.handle_about(message)
            
        # users command
        @self.bot.message_handler(commands=['user'])
        def handle_users(message):
            self.handle_users(message)

    def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username
        welcome = f"📚 Welcome {username} to Ardayda  Bot!\n\n"
        welcome += "/help"
        self.bot.reply_to(message, welcome)
        
    def handle_help(self, message):
        """Handle /help command"""
        user_id = message.from_user.id
        username = message.from_user.username 

        welcome = f"📚 Welcome {username} to Ardayda  Bot!\n\n"
        welcome += "Available commands:\n"
        welcome += "/start - start the bot.\n"
        welcome += "/help - get guids\n"
        welcome += "/about or /info - See info of this bot\n"
        welcome += "/users - Show list of users"

        self.bot.reply_to(message, welcome)


    def handle_about(self, message):
        """Handle /about command"""
        user_id = message.from_user.id

        response = "📖 About Ardayda Bot\n\n"
        response += "Ardayda means 'Students' in Somali.\n\n"
        response += "This bot helps students with:\n"
        response += "• Get Centerlised Exams\n"
        response += "• Get Free PDFs\n"
        response += "• GET assignments\n"
        response += "• Get Books\n\n"
        response += "Made for Somali students in Puntland."

        self.bot.reply_to(message, response)
        
    def handle_users(self, message):
        """Handle /users command"""
        user_id = message.from_user.id
        username = message.from_user.username
        all_users = get_all_users()
        self.bot.reply_to(message, all_users)
        
        
    def process_update(self, update_json):
        """Process incoming update from webhook"""
        try:
            update = telebot.types.Update.de_json(update_json)
            self.bot.process_new_updates([update])

            # Log the update
            if update.message:
                user_id = update.message.from_user.id
                command = update.message.text.split()[0] if update.message.text else 'unknown'
                add_log_entry(self.bot_token, 'command', user_id, command)

            return True

        except Exception as e:
            logger.error(f"Ardayda bot error: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# Global function to process Ardayda bot updates
def process_ardayda_update(bot_token, update_json):
    """Process update for Ardayda bot"""
    try:
        bot = ArdaydaBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_ardayda_update: {str(e)}")
        return False