import telebot
import logging
from master_db.operations import add_log_entry

logger = logging.getLogger(__name__)

class ArdaydaBot:
    """Ardayda Education Bot - Simple bot for students"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    def register_handlers(self):
        """Register Ardayda bot command handlers"""

        # Start command
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            self.handle_start(message)

        # Courses command
        @self.bot.message_handler(commands=['courses', 'subjects'])
        def handle_courses(message):
            self.handle_courses(message)

        # Materials command
        @self.bot.message_handler(commands=['materials', 'books'])
        def handle_materials(message):
            self.handle_materials(message)

        # Questions command
        @self.bot.message_handler(commands=['questions', 'ask'])
        def handle_questions(message):
            self.handle_questions(message)

        # About command
        @self.bot.message_handler(commands=['about', 'info'])
        def handle_about(message):
            self.handle_about(message)

    def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Student"

        welcome = f"📚 Welcome {username} to Ardayda Education Bot!\n\n"
        welcome += "Available commands:\n"
        welcome += "/courses - View available courses\n"
        welcome += "/materials - Access study materials\n"
        welcome += "/questions - Ask academic questions\n"
        welcome += "/about - About Ardayda bot\n"
        welcome += "/help - Show this message"

        self.bot.reply_to(message, welcome)
        add_log_entry(self.bot_token, 'command', user_id, '/start')

    def handle_courses(self, message):
        """Handle /courses command"""
        user_id = message.from_user.id

        courses = [
            "📘 Computer Science",
            "📗 Mathematics",
            "📕 Physics",
            "📙 Chemistry",
            "📓 Biology",
            "📔 Engineering"
        ]

        response = "🎓 Available Courses:\n\n"
        for course in courses:
            response += f"{course}\n"

        response += "\nSelect a course to get materials."

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/courses')

    def handle_materials(self, message):
        """Handle /materials command"""
        user_id = message.from_user.id

        response = "📚 Study Materials\n\n"
        response += "Available materials:\n"
        response += "1. Lecture notes\n"
        response += "2. Past papers\n"
        response += "3. Video tutorials\n"
        response += "4. Reference books\n\n"
        response += "More materials coming soon!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/materials')

    def handle_questions(self, message):
        """Handle /questions command"""
        user_id = message.from_user.id

        response = "❓ Academic Questions\n\n"
        response += "You can ask questions about:\n"
        response += "• Course content\n"
        response += "• Assignments\n"
        response += "• Exams\n"
        response += "• Study tips\n\n"
        response += "Just type your question and our tutors will help you."

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/questions')

    def handle_about(self, message):
        """Handle /about command"""
        user_id = message.from_user.id

        response = "📖 About Ardayda Bot\n\n"
        response += "Ardayda means 'Students' in Somali.\n\n"
        response += "This bot helps students with:\n"
        response += "• Course materials\n"
        response += "• Academic questions\n"
        response += "• Study resources\n"
        response += "• Educational support\n\n"
        response += "Made for Somali students worldwide."

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