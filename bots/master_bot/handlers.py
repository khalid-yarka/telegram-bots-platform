import logging
from telebot import types

from master_db.operations import get_user_bots
from utils.permissions import is_super_admin

from bots.master_bot.keyboards import main_menu_keyboard, get_bots_list_keyboard
from bots.master_bot.flows.add_bot_flow import start_add_bot_flow
from bots.master_bot.callbacks import show_webhook_menu, show_settings_menu, show_statistics
from bots.master_bot.admin_commands import AdminCommands

logger = logging.getLogger(__name__)

def register_message_handlers(bot_instance):
    """Register all message handlers (commands + reply keyboard)"""

    @bot_instance.bot.message_handler(commands=['start', 'help', 'menu'])
    def handle_start(message):
        """Handle /start, /help, /menu commands"""
        user_id = message.from_user.id
        username = message.from_user.first_name or "User"

        welcome = f"👋 Welcome {username} to Master Bot Controller!\n\n"
        welcome += "Use the buttons below or type commands:\n"
        welcome += "• /mybots - List your bots\n"
        welcome += "• /addbot - Add new bot\n"
        welcome += "• /webhook - Manage webhooks"

        bot_instance.safe_send(
            message.chat.id,
            welcome,
            reply_markup=main_menu_keyboard(user_id)
        )

        bot_instance.log_action(user_id, 'main_menu')

    @bot_instance.bot.message_handler(commands=['mybots', 'bots'])
    def handle_mybots(message):
        """Handle /mybots command - show user's bots"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        bots = get_user_bots(user_id)

        if not bots:
            # No bots - show add button
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "➕ Add Your First Bot",
                callback_data="add_bot_start"
            ))

            bot_instance.safe_send(
                chat_id,
                "🤷 You don't have any bots yet.\nClick below to add your first bot!",
                reply_markup=markup
            )
            return

        # Show bots list with inline keyboard
        text, markup = get_bots_list_keyboard(bots, page=0)
        bot_instance.safe_send(chat_id, text, reply_markup=markup, parse_mode='Markdown')
        bot_instance.log_action(user_id, 'list_bots')

    @bot_instance.bot.message_handler(commands=['addbot'])
    def handle_addbot_command(message):
        """Handle /addbot command - start add bot flow"""
        start_add_bot_flow(bot_instance, message)

    @bot_instance.bot.message_handler(commands=['webhook'])
    def handle_webhook_command(message):
        """Handle /webhook command"""
        show_webhook_menu(bot_instance, message)

    @bot_instance.bot.message_handler(commands=['settings'])
    def handle_settings_command(message):
        """Handle /settings command"""
        show_settings_menu(bot_instance, message)

    @bot_instance.bot.message_handler(commands=['stats'])
    def handle_stats_command(message):
        """Handle /stats command"""
        show_statistics(bot_instance, message)

    # ==================== REPLY KEYBOARD HANDLERS ====================

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "🤖 My Bots")
    def handle_reply_mybots(message):
        """Handle My Bots button from reply keyboard"""
        handle_mybots(message)

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "➕ Add Bot")
    def handle_reply_addbot(message):
        """Handle Add Bot button from reply keyboard"""
        start_add_bot_flow(bot_instance, message)

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "🌐 Webhooks")
    def handle_reply_webhooks(message):
        """Handle Webhooks button from reply keyboard"""
        show_webhook_menu(bot_instance, message)

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "📊 Statistics")
    def handle_reply_stats(message):
        """Handle Statistics button from reply keyboard"""
        show_statistics(bot_instance, message)

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "⚙️ Settings")
    def handle_reply_settings(message):
        """Handle Settings button from reply keyboard"""
        show_settings_menu(bot_instance, message)

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "❓ Help")
    def handle_reply_help(message):
        """Handle Help button from reply keyboard"""
        help_text = (
            "📚 **Help Menu**\n\n"
            "**Commands:**\n"
            "/mybots - List your bots\n"
            "/addbot - Add a new bot\n"
            "/webhook - Manage webhooks\n"
            "/stats - View statistics\n"
            "/settings - Configure settings\n\n"
            "**Need more help?** Contact @your_support"
        )
        
        bot_instance.safe_send(
            message.chat.id,
            help_text,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard(message.from_user.id)
        )

    @bot_instance.bot.message_handler(func=lambda msg: msg.text == "👑 Admin Panel")
    def handle_reply_admin(message):
        """Handle Admin Panel button (super admins only)"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            bot_instance.safe_send(
                message.chat.id,
                "❌ This area is for super admins only."
            )
            return

        # Create admin commands instance and show panel
        admin_cmd = AdminCommands(bot_instance.bot, bot_instance.bot_token)
        admin_cmd.show_admin_panel(message)

    logger.info("Message handlers registered")