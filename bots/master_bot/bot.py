import telebot
import logging
from datetime import datetime

# Import from our modules
from utils.permissions import is_super_admin, can_add_bot
from utils.webhook_manager import set_webhook, delete_webhook, check_webhook
from master_db.operations import (
    add_bot, get_bot_by_token, get_all_bots, get_user_bots,
    delete_bot, add_log_entry, get_webhook_status,
    check_permission, can_manage_bot,
    update_webhook_status
)
from config import config

logger = logging.getLogger(__name__)

class MasterBot:
    """Master bot to control all other bots"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    def register_handlers(self):
        """Register all command handlers"""

        # Start command
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            self.handle_start(message)

        # Bot management commands
        @self.bot.message_handler(commands=['addbot'])
        def handle_addbot(message):
            self.handle_addbot(message)

        @self.bot.message_handler(commands=['mybots', 'bots'])
        def handle_mybots(message):
            self.handle_mybots(message)

        @self.bot.message_handler(commands=['botinfo'])
        def handle_botinfo(message):
            self.handle_botinfo(message)

        @self.bot.message_handler(commands=['removebot', 'deletebot'])
        def handle_removebot(message):
            self.handle_removebot(message)

        # Webhook commands
        @self.bot.message_handler(commands=['webhook', 'webhooks'])
        def handle_webhook_cmd(message):
            self.handle_webhook_cmd(message)

        # Log commands
        @self.bot.message_handler(commands=['logs'])
        def handle_logs(message):
            self.handle_logs(message)

        # User management
        @self.bot.message_handler(commands=['users'])
        def handle_users(message):
            self.handle_users(message)

        # Settings
        @self.bot.message_handler(commands=['settings'])
        def handle_settings(message):
            self.handle_settings(message)

    def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or "User"

        # Check if super admin
        if is_super_admin(user_id):
            welcome = f"👑 Welcome, SUPER ADMIN {username}!\n\n"
            welcome += "You have full control over all bots.\n"
        else:
            welcome = f"👋 Welcome {username} to Master Bot!\n"

        welcome += "Commands:\n"
        welcome += "/mybots - List your bots\n"
        welcome += "/addbot - Add new bot\n"
        welcome += "/webhook - Check webhook status\n"

        if is_super_admin(user_id):
            welcome += "/admin - Super admin panel\n"

        self.bot.reply_to(message, welcome)
        add_log_entry(self.bot_token, 'command', user_id, '/start')

    def handle_addbot(self, message):
        """Handle /addbot command"""
        user_id = message.from_user.id

        # Parse command: /addbot <token> <type> <name>
        parts = message.text.split()
        if len(parts) < 4:
            self.bot.reply_to(
                message,
                "Usage: /addbot <bot_token> <bot_type> <bot_name>\n\n"
                "Example: /addbot 123456:ABCdef master \"My Master Bot\"\n"
                "Bot types: master, ardayda, dhalinyaro"
            )
            return

        bot_token = parts[1]
        bot_type = parts[2].lower()
        bot_name = ' '.join(parts[3:])

        # Validate bot type
        if bot_type not in ['master', 'ardayda', 'dhalinyaro']:
            self.bot.reply_to(
                message,
                "❌ Invalid bot type. Choose from: master, ardayda, dhalinyaro"
            )
            return

        # Check if user can add more bots
        if not can_add_bot(user_id):
            self.bot.reply_to(message, "❌ You have reached the maximum number of bots.")
            return

        # Add bot to database
        success = add_bot(bot_token, bot_name, bot_type, user_id)

        if success:
            # Set webhook
            webhook_success = set_webhook(bot_token, bot_type)

            if webhook_success:
                response = f"✅ Bot '{bot_name}' ({bot_type}) added successfully!\n"
                response += "✅ Webhook configured."
            else:
                response = f"⚠️ Bot '{bot_name}' added but webhook setup failed.\n"
                response += "Use /webhook to retry."

            self.bot.reply_to(message, response)
            add_log_entry(self.bot_token, 'add_bot', user_id, f"Added {bot_type} bot: {bot_name}")
        else:
            self.bot.reply_to(
                message,
                "❌ Failed to add bot. Possible reasons:\n"
                "1. Bot token already exists\n"
                "2. Invalid bot token\n"
                "3. Database error"
            )

    def handle_mybots(self, message):
        """Handle /mybots command"""
        user_id = message.from_user.id

        # Get user's bots
        bots = get_user_bots(user_id)

        if not bots:
            self.bot.reply_to(message, "🤷 You don't have any bots yet.\nUse /addbot to add one.")
            return

        response = f"🤖 Your Bots ({len(bots)}):\n\n"

        for i, bot in enumerate(bots, 1):
            bot_name = bot.get('bot_name', 'Unnamed')
            bot_type = bot.get('bot_type', 'unknown')
            is_active = bot.get('is_active', False)
            webhook_status = get_webhook_status(bot['bot_token'])

            status_icon = "✅" if is_active else "⏸️"
            webhook_icon = "🔗" if webhook_status and webhook_status.get('status') == 'active' else "❌"

            response += f"{i}. {bot_name} ({bot_type})\n"
            response += f"   Status: {status_icon} Active | Webhook: {webhook_icon}\n\n"

        response += "More features coming soon!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/mybots')

    def handle_botinfo(self, message):
        """Handle /botinfo command"""
        user_id = message.from_user.id

        self.bot.reply_to(
            message,
            "🤖 Bot Info\n\n"
            "Use /mybots to see all your bots.\n"
            "Detailed bot information coming soon!"
        )
        add_log_entry(self.bot_token, 'command', user_id, '/botinfo')

    def handle_removebot(self, message):
        """Handle /removebot command"""
        user_id = message.from_user.id

        self.bot.reply_to(
            message,
            "🗑️ Remove Bot\n\n"
            "To delete a bot:\n"
            "1. Go to @BotFather on Telegram\n"
            "2. Use /deletebot command\n"
            "3. Select your bot\n"
            "4. Then use /mybots here to refresh list"
        )
        add_log_entry(self.bot_token, 'command', user_id, '/removebot')

    def handle_webhook_cmd(self, message):
        """Handle /webhook command"""
        user_id = message.from_user.id

        # Get user's bots
        bots = get_user_bots(user_id)

        if not bots:
            response = "🤷 You don't have any bots to check."
        else:
            response = f"🌐 Webhook Status ({len(bots)} bots):\n\n"

            for bot in bots[:5]:  # Show first 5
                webhook_info = get_webhook_status(bot['bot_token'])
                status = webhook_info.get('status', 'unknown') if webhook_info else 'unknown'

                if status == 'active':
                    icon = "✅"
                elif status == 'failed':
                    icon = "❌"
                else:
                    icon = "⏳"

                response += f"{icon} {bot.get('bot_name', 'Unnamed')}: {status}\n"

            if len(bots) > 5:
                response += f"\n... and {len(bots) - 5} more bots"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'command', user_id, '/webhook')

    def handle_logs(self, message):
        """Handle /logs command"""
        user_id = message.from_user.id

        # Only super admins can view logs
        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Only super admins can view system logs.")
            return

        self.bot.reply_to(
            message,
            "📋 System Logs\n\n"
            "Log viewing feature coming soon!\n"
            "Check web app dashboard for now."
        )
        add_log_entry(self.bot_token, 'command', user_id, '/logs')

    def handle_users(self, message):
        """Handle /users command"""
        user_id = message.from_user.id

        self.bot.reply_to(
            message,
            "👤 User Management\n\n"
            "User management features coming soon!\n"
            "Currently, only bot owners can manage their bots."
        )
        add_log_entry(self.bot_token, 'command', user_id, '/users')

    def handle_settings(self, message):
        """Handle /settings command"""
        user_id = message.from_user.id

        self.bot.reply_to(
            message,
            "⚙️ Settings Management\n\n"
            "Bot settings management coming soon!\n"
            "For now, basic features are available."
        )
        add_log_entry(self.bot_token, 'command', user_id, '/settings')

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
            logger.error(f"Error processing update: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# Global function to process master bot updates
def process_master_update(bot_token, update_json):
    """Process update for master bot"""
    try:
        bot = MasterBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_master_update: {str(e)}")
        return False