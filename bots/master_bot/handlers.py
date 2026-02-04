import logging
from telebot import types
from utils.helpers import truncate_text
from master_db.operations import get_user_bots, get_bot_users
from utils.permissions import is_super_admin, can_manage_bot

logger = logging.getLogger(__name__)

def setup_callback_handlers(bot, bot_token):
    """Setup callback query handlers for master bot"""

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        """Handle all callback queries"""
        try:
            user_id = call.from_user.id
            data = call.data

            if data == 'delete_cancel':
                bot.answer_callback_query(call.id, "Deletion cancelled")
                bot.edit_message_text(
                    "❌ Deletion cancelled.",
                    call.message.chat.id,
                    call.message.message_id
                )

            elif data.startswith('delete_confirm:'):
                bot_token_to_delete = data.split(":")[1]
                handle_delete_confirmation(bot, call, bot_token_to_delete, user_id)

            elif data == 'refresh_bots':
                bot.answer_callback_query(call.id, "Refreshing bot list...")
                handle_refresh_bots(bot, call, user_id)

            elif data.startswith('bot_detail:'):
                bot_token_detail = data.split(":")[1]
                bot.answer_callback_query(call.id, "Loading bot details...")
                handle_bot_detail(bot, call, bot_token_detail, user_id)

            elif data.startswith('webhook_check:'):
                bot_token_webhook = data.split(":")[1]
                bot.answer_callback_query(call.id, "Checking webhook...")
                handle_webhook_check(bot, call, bot_token_webhook, user_id)

            else:
                bot.answer_callback_query(call.id, "Action processed")

        except Exception as e:
            logger.error(f"Callback query error: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Error processing request")

def handle_delete_confirmation(bot, call, bot_token_to_delete, user_id):
    """Handle bot deletion confirmation"""
    from master_db.operations import delete_bot, get_bot_by_token
    from utils.webhook_manager import delete_webhook
    from master_db.operations import add_log_entry

    # Get bot info before deletion
    bot_info = get_bot_by_token(bot_token_to_delete)
    bot_name = bot_info.get('bot_name', 'Unnamed') if bot_info else 'Unknown'

    # Delete webhook first
    delete_webhook(bot_token_to_delete)

    # Delete from database
    success = delete_bot(bot_token_to_delete, user_id)

    if success:
        bot.answer_callback_query(call.id, "Bot deleted successfully")
        bot.edit_message_text(
            f"✅ Bot '{bot_name}' deleted successfully.",
            call.message.chat.id,
            call.message.message_id
        )
        # Log the deletion
        add_log_entry(call.bot.token, 'delete_bot', user_id, f"Deleted bot: {bot_name}")
    else:
        bot.answer_callback_query(call.id, "Failed to delete bot")
        bot.edit_message_text(
            f"❌ Failed to delete bot '{bot_name}'.",
            call.message.chat.id,
            call.message.message_id
        )

def handle_refresh_bots(bot, call, user_id):
    """Handle refresh bots button"""
    from master_db.operations import get_user_bots, get_webhook_status

    bots = get_user_bots(user_id)

    if not bots:
        response = "🤷 You don't have any bots yet.\nUse /addbot to add one."
    else:
        response = f"🤖 Your Bots ({len(bots)}):\n\n"

        for i, bot_info in enumerate(bots, 1):
            bot_name = bot_info.get('bot_name', 'Unnamed')
            bot_type = bot_info.get('bot_type', 'unknown')
            is_active = bot_info.get('is_active', False)
            webhook_status = get_webhook_status(bot_info['bot_token'])

            status_icon = "✅" if is_active else "⏸️"
            webhook_icon = "🔗" if webhook_status and webhook_status.get('status') == 'active' else "❌"

            response += f"{i}. {bot_name} ({bot_type})\n"
            response += f"   Status: {status_icon} Active | Webhook: {webhook_icon}\n\n"

        response += "Use /botinfo <name> for details"

    # Update the message
    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_bot_list_keyboard(bots)
        )
    except:
        # If message content is the same, just send a new one
        bot.send_message(
            call.message.chat.id,
            "✅ Bot list refreshed!\nUse /mybots to see updated list."
        )

def handle_bot_detail(bot, call, bot_token_detail, user_id):
    """Handle bot detail view"""
    from master_db.operations import get_bot_by_token, get_webhook_status

    bot_info = get_bot_by_token(bot_token_detail)

    if not bot_info:
        bot.answer_callback_query(call.id, "Bot not found")
        return

    # Check if user has access
    if not is_super_admin(user_id):
        user_bots = get_user_bots(user_id)
        user_bot_tokens = [b['bot_token'] for b in user_bots]
        if bot_token_detail not in user_bot_tokens:
            bot.answer_callback_query(call.id, "No access to this bot")
            return

    bot_name = bot_info.get('bot_name', 'Unnamed')
    webhook_info = get_webhook_status(bot_token_detail)

    response = f"🤖 Bot Details: {bot_name}\n\n"
    response += f"Token: {bot_token_detail[:20]}...\n"
    response += f"Type: {bot_info.get('bot_type', 'unknown')}\n"
    response += f"Owner: {bot_info.get('owner_id', 'N/A')}\n"
    response += f"Created: {bot_info.get('created_at', 'N/A')}\n"
    response += f"Status: {'✅ Active' if bot_info.get('is_active') else '⏸️ Inactive'}\n"

    if webhook_info:
        response += f"\n🌐 Webhook:\n"
        response += f"Status: {webhook_info.get('status', 'unknown')}\n"
        if webhook_info.get('last_error'):
            response += f"Last error: {webhook_info.get('last_error')[:50]}...\n"

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_bot_detail_keyboard(bot_token_detail, user_id)
        )
    except Exception as e:
        logger.error(f"Error editing message: {str(e)}")
        bot.answer_callback_query(call.id, "Error showing details")

def handle_webhook_check(bot, call, bot_token_webhook, user_id):
    """Handle webhook check button"""
    from utils.webhook_manager import check_webhook
    from master_db.operations import get_bot_by_token

    bot_info = get_bot_by_token(bot_token_webhook)
    if not bot_info:
        bot.answer_callback_query(call.id, "Bot not found")
        return

    result = check_webhook(bot_token_webhook)
    bot_name = bot_info.get('bot_name', 'Unnamed')

    if result.get('success'):
        webhook_info = result
        response = f"🔍 Webhook for {bot_name}:\n\n"
        response += f"Status: {webhook_info.get('status', 'unknown')}\n"
        response += f"URL: {webhook_info.get('url', 'Not set')}\n"

        if webhook_info.get('last_error_message'):
            response += f"Last error: {webhook_info.get('last_error_message')}\n"
    else:
        response = f"❌ Error checking webhook for {bot_name}:\n{result.get('error')}"

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_webhook_control_keyboard(bot_token_webhook)
        )
    except:
        bot.send_message(
            call.message.chat.id,
            response,
            reply_markup=create_webhook_control_keyboard(bot_token_webhook)
        )

def create_bot_list_keyboard(bots):
    """Create inline keyboard for bot list"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for bot in bots[:8]:  # Max 8 buttons
        bot_name = truncate_text(bot.get('bot_name', 'Unnamed'), 15)
        button = types.InlineKeyboardButton(
            text=f"🤖 {bot_name}",
            callback_data=f"bot_detail:{bot['bot_token']}"
        )
        keyboard.add(button)

    # Add refresh button
    refresh_btn = types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_bots")
    keyboard.add(refresh_btn)

    return keyboard

def create_bot_detail_keyboard(bot_token, user_id):
    """Create keyboard for bot details"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Check if user can manage this bot
    from utils.permissions import can_manage_bot

    webhook_btn = types.InlineKeyboardButton(
        "🌐 Webhook",
        callback_data=f"webhook_check:{bot_token}"
    )
    keyboard.add(webhook_btn)

    if can_manage_bot(bot_token, user_id):
        delete_btn = types.InlineKeyboardButton(
            "🗑️ Delete",
            callback_data=f"delete_confirm:{bot_token}"
        )
        keyboard.add(delete_btn)

    back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="refresh_bots")
    keyboard.add(back_btn)

    return keyboard

def create_webhook_control_keyboard(bot_token):
    """Create keyboard for webhook controls"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    check_btn = types.InlineKeyboardButton("🔍 Check", callback_data=f"webhook_check:{bot_token}")
    back_btn = types.InlineKeyboardButton("🔙 Back", callback_data=f"bot_detail:{bot_token}")

    keyboard.add(check_btn, back_btn)

    return keyboard

def create_admin_keyboard():
    """Create keyboard for admin actions"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    stats_btn = types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
    users_btn = types.InlineKeyboardButton("👥 Users", callback_data="admin_users")
    logs_btn = types.InlineKeyboardButton("📋 Logs", callback_data="admin_logs")

    keyboard.add(stats_btn, users_btn, logs_btn)

    return keyboard