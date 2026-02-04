import telebot
import logging
from master_db.operations import add_log_entry

logger = logging.getLogger(__name__)

class DhalinyaroBot:
    """Dhalinyaro Youth Bot - Simple bot for youth activities"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    def register_handlers(self):
        """Register Dhalinyaro bot command handlers"""

        # Start command
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            self.handle_start(message)

        # Events command
        @self.bot.message_handler(commands=['events', 'activities'])
        def handle_events(message):
            self.handle_events(message)

        # Groups command
        @self.bot.message_handler(commands=['groups', 'community'])
        def handle_groups(message):
            self.handle_groups(message)

        # Meetup command
        @self.bot.message_handler(commands=['meetup', 'meet'])
        def handle_meetup(message):
            self.handle_meetup(message)

        # About command
        @self.bot.message_handler(commands=['about', 'info'])
        def handle_about(message):
            self.handle_about(message)

    def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Friend"

        welcome = f"🎉 Welcome {username} to Dhalinyaro Youth Bot!\n\n"
        welcome += "Dhalinyaro means 'Youth' in Somali.\n\n"
        welcome += "Available commands:\n"
        welcome += "/events - View upcoming events\n"
        welcome += "/groups - Join youth groups\n"
        welcome += "/meetup - Organize meetups\n"
        welcome += "/about - About Dhalinyaro bot\n"
        welcome += "/help - Show this message"

        self.bot.reply_to(message, welcome)
        add_log_entry(self.bot_token, 'command', user_id, '/start')

    def handle_events(self, message):
        """Handle /events command"""
        user_id = message.from_user.id

        events = [
            "🎯 Youth Leadership Workshop - Jan 15",
            "⚽ Football Tournament - Jan 20",
            "💻 Tech Skills Training - Jan 25",
            "🎨 Art & Culture Festival - Feb 1",
            "📚 Study Group Session - Feb 5"
        ]

        response = "📅 Upcoming Youth Events:\n\n"
        for event in events:
            response += f"{event}\n"

        response += "\nUse /meetup to organize your own event!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/events')

    def handle_groups(self, message):
        """Handle /groups command"""
        user_id = message.from_user.id

        groups = [
            "👥 Tech Enthusiasts Group",
            "⚽ Sports & Fitness Club",
            "🎨 Arts & Culture Community",
            "📚 Study & Career Network",
            "🌍 Social Change Activists"
        ]

        response = "👥 Youth Groups & Communities:\n\n"
        for group in groups:
            response += f"{group}\n"

        response += "\nJoin groups to connect with peers!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/groups')

    def handle_meetup(self, message):
        """Handle /meetup command"""
        user_id = message.from_user.id

        response = "🤝 Organize a Meetup\n\n"
        response += "To organize a meetup:\n"
        response += "1. Choose a topic/activity\n"
        response += "2. Select date & time\n"
        response += "3. Choose location\n"
        response += "4. Share with community\n\n"
        response += "Example topics:\n"
        response += "• Study sessions\n"
        response += "• Sports activities\n"
        response += "• Tech workshops\n"
        response += "• Cultural events\n\n"
        response += "Start by typing: 'I want to organize...'"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/meetup')

    def handle_about(self, message):
        """Handle /about command"""
        user_id = message.from_user.id

        response = "🌟 About Dhalinyaro Bot\n\n"
        response += "Dhalinyaro connects Somali youth worldwide.\n\n"
        response += "Our mission:\n"
        response += "• Connect youth globally\n"
        response += "• Share opportunities\n"
        response += "• Organize events\n"
        response += "• Build community\n\n"
        response += "For youth, by youth!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/about')

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
            logger.error(f"Dhalinyaro bot error: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# Global function to process Dhalinyaro bot updates
def process_dhalinyaro_update(bot_token, update_json):
    """Process update for Dhalinyaro bot"""
    try:
        bot = DhalinyaroBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_dhalinyaro_update: {str(e)}")
        return False