import telebot
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from master_db.operations import (
    add_bot, get_bot_by_token, get_all_bots, get_user_bots,
    delete_bot, add_log_entry, get_webhook_status
)
from utils.permissions import is_super_admin, can_add_bot
from utils.webhook_manager import set_webhook
from config import config

logger = logging.getLogger(__name__)

class MasterBot:
    """Master bot - Improved interface + update message"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.register_handlers()

    # ==================== HANDLERS ====================

    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            self.send_main_menu(message)

        @self.bot.message_handler(commands=['mybots', 'bots'])
        def handle_mybots(message):
            self.send_my_bots(message)

        @self.bot.message_handler(commands=['addbot'])
        def handle_addbot(message):
            self.handle_add_bot(message)

        @self.bot.message_handler(commands=['webhook'])
        def handle_webhook_cmd(message):
            self.send_webhook_status(message)

        @self.bot.message_handler(commands=['logs'])
        def handle_logs(message):
            self.send_logs(message)

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

    def build_main_menu(self, user_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🤖 My Bots", callback_data="menu_mybots"),
            InlineKeyboardButton("➕ Add Bot", callback_data="menu_addbot"),
            InlineKeyboardButton("🌐 Webhooks", callback_data="menu_webhook"),
            InlineKeyboardButton("📋 Logs", callback_data="menu_logs")
        )
        if is_super_admin(user_id):
            markup.add(InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"))
        return markup

    # ==================== COMMANDS ====================

    def send_main_menu(self, message):
        user_id = message.from_user.id
        username = message.from_user.username or "User"
        text = f"👋 Hello {username}!\nMaster Bot Menu:"
        self.safe_reply(message, text, self.build_main_menu(user_id))
        add_log_entry(self.bot_token, 'command', user_id, '/start')

    def send_my_bots(self, message):
        user_id = message.from_user.id
        bots = get_user_bots(user_id)
        if not bots:
            text = "🤷 You don't have any bots yet.\nUse /addbot or the button below."
        else:
            text = f"🤖 Your Bots ({len(bots)}):\n\n"
            for i, bot in enumerate(bots, 1):
                status = "✅ Active" if bot.get('is_active') else "⏸️ Inactive"
                webhook = get_webhook_status(bot['bot_token'])
                webhook_icon = "🔗" if webhook and webhook.get('status') == 'active' else "❌"
                text += f"{i}. {bot.get('bot_name','Unnamed')} ({bot.get('bot_type','unknown')})\n"
                text += f"   Status: {status} | Webhook: {webhook_icon}\n\n"
        self.safe_reply(message, text, self.build_main_menu(user_id))
        add_log_entry(self.bot_token, 'command', user_id, '/mybots')

    def handle_add_bot(self, message):
        user_id = message.from_user.id
        parts = message.text.split()
        if len(parts) < 4:
            self.safe_reply(message, "Usage: /addbot <token> <type> <name>")
            return
        bot_token, bot_type = parts[1], parts[2].lower()
        bot_name = ' '.join(parts[3:])
        if bot_type not in ['master', 'ardayda', 'dhalinyaro']:
            self.safe_reply(message, "❌ Invalid bot type. Choose: master, ardayda, dhalinyaro")
            return
        if not can_add_bot(user_id):
            self.safe_reply(message, "❌ You reached max bots")
            return
        success = add_bot(bot_token, bot_name, bot_type, user_id)
        if success:
            webhook_success = set_webhook(bot_token, bot_type)
            msg = f"✅ Bot '{bot_name}' added successfully!\n"
            msg += "✅ Webhook configured." if webhook_success else "⚠️ Webhook setup failed."
            self.safe_reply(message, msg, self.build_main_menu(user_id))
            add_log_entry(self.bot_token, 'add_bot', user_id, f"Added {bot_type} bot: {bot_name}")
        else:
            self.safe_reply(message, "❌ Failed to add bot. Check token or DB.")

    def send_webhook_status(self, message):
        user_id = message.from_user.id
        bots = get_user_bots(user_id)
        if not bots:
            text = "🤷 No bots to check."
        else:
            text = f"🌐 Webhook Status ({len(bots)} bots):\n"
            for bot in bots[:5]:
                webhook = get_webhook_status(bot['bot_token'])
                status = webhook.get('status', 'unknown') if webhook else 'unknown'
                icon = "✅" if status == 'active' else "❌" if status == 'failed' else "⏳"
                text += f"{icon} {bot.get('bot_name','Unnamed')}: {status}\n"
            if len(bots) > 5:
                text += f"... and {len(bots)-5} more bots"
        self.safe_reply(message, text, self.build_main_menu(user_id))
        add_log_entry(self.bot_token, 'command', user_id, '/webhook')

    def send_logs(self, message):
        user_id = message.from_user.id
        if not is_super_admin(user_id):
            self.safe_reply(message, "❌ Only super admins can view logs.")
            return
        self.safe_reply(message, "📋 Logs viewing coming soon.", self.build_main_menu(user_id))
        add_log_entry(self.bot_token, 'command', user_id, '/logs')

    # ==================== CALLBACK HANDLER ====================

    def process_callback(self, call):
        user_id = call.from_user.id
        data = call.data

        if data == "menu_mybots":
            self.safe_edit(call.message.chat.id, call.message.message_id, "Fetching your bots...", self.build_main_menu(user_id))
            self.send_my_bots(call.message)
        elif data == "menu_addbot":
            self.safe_edit(call.message.chat.id, call.message.message_id, "Use /addbot <token> <type> <name>", self.build_main_menu(user_id))
        elif data == "menu_webhook":
            self.send_webhook_status(call.message)
        elif data == "menu_logs":
            self.send_logs(call.message)
        elif data == "menu_settings" and is_super_admin(user_id):
            self.safe_edit(call.message.chat.id, call.message.message_id, "⚙️ Settings coming soon", self.build_main_menu(user_id))
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
            logger.error(f"Master bot error: {str(e)}")
            add_log_entry(self.bot_token, 'error', None, str(e))
            return False


# ==================== GLOBAL FUNCTION ====================

def process_master_update(bot_token, update_json):
    try:
        bot = MasterBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_master_update: {str(e)}")
        return False