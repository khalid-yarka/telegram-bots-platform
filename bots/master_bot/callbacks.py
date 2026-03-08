import logging
from telebot import types

from master_db.operations import (
    get_bot_by_token, get_user_bots, get_webhook_status,
    get_bot_users
)
from utils.permissions import is_super_admin, can_manage_bot
from utils.webhook_manager import check_webhook

from bots.master_bot.keyboards import (
    main_menu_keyboard, get_bots_list_keyboard, get_bot_details_keyboard,
    get_webhook_keyboard, get_confirmation_keyboard, get_settings_keyboard
)
from bots.master_bot.flows.add_bot_flow import handle_add_bot_type
from bots.master_bot.flows.edit_bot_flow import start_edit_bot_name
from bots.master_bot.flows.delete_bot_flow import confirm_delete_bot, execute_delete_bot

logger = logging.getLogger(__name__)

def register_callback_handlers(bot_instance):
    """Register all callback query handlers"""

    @bot_instance.bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        """Main callback handler - routes to specific functions"""
        try:
            data = call.data
            user_id = call.from_user.id

            # Log callback
            bot_instance.log_action(user_id, 'callback', data[:50])

            # ==================== NAVIGATION ====================
            if data == "back_to_menu":
                handle_back_to_menu(bot_instance, call)
            elif data == "back_to_bots":
                handle_back_to_bots(bot_instance, call)
                
            # In the NAVIGATION section (around line 30-40), add:
            elif data == "back_to_settings":
                show_settings_menu(bot_instance, call.message)
            
            # In the BOT ACTIONS section (around line 120-130), add:
            elif data.startswith("add_user:"):
                bot_token = data.split(":")[1]
                handle_add_user(bot_instance, call, bot_token)
            
            # In the UNKNOWN section or as a new case (around line 150-160), add:
            elif data == "noop":
                bot_instance.safe_answer_callback(call.id, "🔘 Button disabled")

            # ==================== BOT LIST ====================
            elif data.startswith("bots_page:"):
                page = int(data.split(":")[1])
                handle_bots_page(bot_instance, call, page)
            elif data == "bots_refresh":
                handle_bots_refresh(bot_instance, call)

            # ==================== BOT DETAILS ====================
            elif data.startswith("view_bot:"):
                bot_token = data.split(":")[1]
                handle_view_bot(bot_instance, call, bot_token)

            # ==================== ADD BOT FLOW ====================
            elif data == "add_bot_start":
                from bots.master_bot.flows.add_bot_flow import start_add_bot_flow
                start_add_bot_flow(bot_instance, call.message)
            elif data.startswith("add_bot_type:"):
                bot_type = data.split(":")[1]
                handle_add_bot_type(bot_instance, call, bot_type)
            elif data == "add_bot_cancel":
                handle_add_bot_cancel(bot_instance, call)

            # ==================== EDIT BOT ====================
            elif data.startswith("edit_name:"):
                bot_token = data.split(":")[1]
                start_edit_bot_name(bot_instance, call, bot_token)
            elif data.startswith("edit_profile:"):
                bot_token = data.split(":")[1]
                handle_edit_profile(bot_instance, call, bot_token)

            # ==================== DELETE BOT ====================
            elif data.startswith("delete_confirm:"):
                bot_token = data.split(":")[1]
                confirm_delete_bot(bot_instance, call, bot_token)
            elif data.startswith("delete_bot:"):
                bot_token = data.split(":")[1]
                execute_delete_bot(bot_instance, call, bot_token)

            # ==================== WEBHOOK MANAGEMENT ====================
            elif data.startswith("webhook:"):
                bot_token = data.split(":")[1]
                handle_webhook_details(bot_instance, call, bot_token)
            elif data.startswith("webhook_check:"):
                bot_token = data.split(":")[1]
                handle_webhook_check(bot_instance, call, bot_token)
            elif data.startswith("webhook_config:"):
                bot_token = data.split(":")[1]
                handle_webhook_config(bot_instance, call, bot_token)
            elif data.startswith("webhook_delete:"):
                bot_token = data.split(":")[1]
                handle_webhook_delete(bot_instance, call, bot_token)

            # ==================== NEW: BOT ACTIONS ====================
            elif data.startswith("stats:"):
                bot_token = data.split(":")[1]
                handle_bot_stats(bot_instance, call, bot_token)
            elif data.startswith("users:"):
                bot_token = data.split(":")[1]
                handle_bot_users(bot_instance, call, bot_token)
            elif data.startswith("settings:"):
                bot_token = data.split(":")[1]
                handle_bot_settings(bot_instance, call, bot_token)
            elif data == "check_all_webhooks":
                handle_check_all_webhooks(bot_instance, call)

            # ==================== SETTINGS MENU ====================
            elif data.startswith("settings_"):
                handle_settings_option(bot_instance, call, data)

            # ==================== STATISTICS ====================
            elif data == "refresh_stats":
                handle_refresh_stats(bot_instance, call)

            # ==================== UNKNOWN ====================
            else:
                bot_instance.safe_answer_callback(
                    call.id,
                    "Unknown action",
                    show_alert=True
                )
                logger.warning(f"Unknown callback data: {data}")

        except Exception as e:
            logger.error(f"Error in callback handler: {e}", exc_info=True)
            bot_instance.safe_answer_callback(
                call.id,
                "❌ An error occurred",
                show_alert=True
            )

    logger.info("Callback handlers registered")


# ==================== NAVIGATION HANDLERS ====================

def handle_back_to_menu(bot_instance, call):
    """Handle back to main menu"""
    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        "🔙 Returning to main menu...",
        reply_markup=None
    )

    bot_instance.safe_send(
        call.message.chat.id,
        "👋 Main Menu:",
        reply_markup=main_menu_keyboard(call.from_user.id)
    )

    bot_instance.safe_answer_callback(call.id, "Main menu")


def handle_back_to_bots(bot_instance, call):
    """Handle back to bots list"""
    user_id = call.from_user.id
    bots = get_user_bots(user_id)

    text, markup = get_bots_list_keyboard(bots, page=0)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

    bot_instance.safe_answer_callback(call.id, "Back to bots list")


# ==================== BOT LIST HANDLERS ====================

def handle_bots_page(bot_instance, call, page):
    """Handle pagination in bots list"""
    user_id = call.from_user.id
    bots = get_user_bots(user_id)

    text, markup = get_bots_list_keyboard(bots, page)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

    bot_instance.safe_answer_callback(call.id, f"Page {page + 1}")


def handle_bots_refresh(bot_instance, call):
    """Handle refresh bots list"""
    user_id = call.from_user.id
    bots = get_user_bots(user_id)

    text, markup = get_bots_list_keyboard(bots, page=0)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

    bot_instance.safe_answer_callback(call.id, "🔄 Refreshed")


# ==================== BOT DETAILS HANDLERS ====================

def handle_view_bot(bot_instance, call, bot_token):
    """Handle view bot details"""
    user_id = call.from_user.id

    # Check permission
    if not (is_super_admin(user_id) or can_manage_bot(bot_token, user_id)):
        bot_instance.safe_answer_callback(call.id, "❌ No permission", show_alert=True)
        return

    bot_info = get_bot_by_token(bot_token)
    if not bot_info:
        bot_instance.safe_answer_callback(call.id, "❌ Bot not found", show_alert=True)
        return

    webhook_status = get_webhook_status(bot_token)
    users = get_bot_users(bot_token)

    # Format bot info
    status_emoji = "🟢" if bot_info.get('is_active') else "🔴"
    webhook_emoji = "✅" if webhook_status and webhook_status.get('status') == 'active' else "❌"

    text = f"📋 **{bot_info.get('bot_name', 'Unnamed')}**\n\n"
    text += f"{status_emoji} **Status:** {'Active' if bot_info.get('is_active') else 'Inactive'}\n"
    text += f"🤖 **Type:** {bot_info.get('bot_type', 'unknown')}\n"
    text += f"🔑 **Token:** `{bot_token[:10]}...{bot_token[-5:]}`\n"
    text += f"👤 **Owner ID:** `{bot_info.get('owner_id', 'N/A')}`\n"
    text += f"📅 **Created:** {bot_info.get('created_at', 'N/A')}\n"
    text += f"👥 **Users:** {len(users) if users else 0}\n\n"

    text += f"🌐 **Webhook:** {webhook_emoji}\n"
    if webhook_status and webhook_status.get('last_error'):
        text += f"⚠️ Last error: {webhook_status['last_error'][:50]}\n"

    markup = get_bot_details_keyboard(bot_token, user_id)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

    bot_instance.safe_answer_callback(call.id, f"Viewing {bot_info.get('bot_name')}")


# ==================== ADD BOT HANDLERS ====================

def handle_add_bot_cancel(bot_instance, call):
    """Handle cancel add bot"""
    bot_instance.state_manager.clear_state(call.message.chat.id)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        "❌ Bot addition cancelled.",
        reply_markup=None
    )

    bot_instance.safe_send(
        call.message.chat.id,
        "👋 Main Menu:",
        reply_markup=main_menu_keyboard(call.from_user.id)
    )

    bot_instance.safe_answer_callback(call.id, "Cancelled")


# ==================== WEBHOOK HANDLERS ====================

def handle_webhook_details(bot_instance, call, bot_token):
    """Handle view webhook details"""
    bot_info = get_bot_by_token(bot_token)
    if not bot_info:
        bot_instance.safe_answer_callback(call.id, "❌ Bot not found", show_alert=True)
        return

    webhook_info = get_webhook_status(bot_token)
    bot_name = bot_info.get('bot_name', 'Unnamed')

    text = f"🌐 **Webhook: {bot_name}**\n\n"

    if webhook_info:
        status = webhook_info.get('status', 'unknown')
        status_emoji = "✅" if status == 'active' else "❌" if status == 'failed' else "⏳"

        text += f"{status_emoji} **Status:** {status}\n"

        if webhook_info.get('url'):
            text += f"🔗 **URL:** `{webhook_info['url']}`\n"

        if webhook_info.get('last_success'):
            text += f"✅ **Last Success:** {webhook_info['last_success']}\n"

        if webhook_info.get('last_error'):
            text += f"⚠️ **Last Error:** {webhook_info['last_error']}\n"
    else:
        text += "No webhook information available.\n"

    markup = get_webhook_keyboard(bot_token)

    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

    bot_instance.safe_answer_callback(call.id, "Webhook details")


def handle_webhook_check(bot_instance, call, bot_token):
    """Handle check webhook now"""
    bot_instance.safe_answer_callback(call.id, "🔄 Checking webhook...")

    result = check_webhook(bot_token)

    if result.get('success'):
        bot_instance.safe_send(
            call.message.chat.id,
            f"✅ Webhook check completed.\nStatus: {result.get('status', 'unknown')}"
        )
    else:
        bot_instance.safe_send(
            call.message.chat.id,
            f"❌ Webhook check failed: {result.get('error', 'Unknown error')}"
        )

    # Refresh webhook view
    handle_webhook_details(bot_instance, call, bot_token)


def handle_webhook_config(bot_instance, call, bot_token):
    """Handle webhook configuration (placeholder)"""
    bot_instance.safe_answer_callback(
        call.id,
        "Webhook config coming soon!",
        show_alert=True
    )


def handle_webhook_delete(bot_instance, call, bot_token):
    """Handle delete webhook"""
    from utils.webhook_manager import delete_webhook

    bot_instance.safe_answer_callback(call.id, "🗑️ Deleting webhook...")

    success = delete_webhook(bot_token)

    if success:
        bot_instance.safe_send(
            call.message.chat.id,
            f"✅ Webhook deleted successfully for {bot_token[:10]}..."
        )
    else:
        bot_instance.safe_send(
            call.message.chat.id,
            f"❌ Failed to delete webhook"
        )

    # Refresh webhook view
    handle_webhook_details(bot_instance, call, bot_token)


def handle_check_all_webhooks(bot_instance, call):
    """Handle check all webhooks button"""
    user_id = call.from_user.id
    bots = get_user_bots(user_id)
    
    if not bots:
        bot_instance.safe_answer_callback(call.id, "No bots to check")
        return
    
    bot_instance.safe_answer_callback(call.id, "🔍 Checking all webhooks...")
    
    working = 0
    failed = 0
    
    for bot in bots[:10]:  # Check first 10 only
        status = get_webhook_status(bot['bot_token'])
        if status and status.get('status') == 'active':
            working += 1
        else:
            failed += 1
    
    bot_instance.safe_send(
        call.message.chat.id,
        f"🌐 **Webhook Summary**\n\n"
        f"✅ Working: {working}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(bots)}"
    )


# ==================== BOT ACTION HANDLERS (NEW) ====================

def handle_bot_stats(bot_instance, call, bot_token):
    """Handle bot statistics button"""
    bot_info = get_bot_by_token(bot_token)
    if not bot_info:
        bot_instance.safe_answer_callback(call.id, "❌ Bot not found", show_alert=True)
        return
    
    bot_name = bot_info.get('bot_name', 'Unnamed')
    
    # Placeholder stats
    text = f"📊 **Statistics for {bot_name}**\n\n"
    text += "Coming soon!\n\n"
    text += "• Messages today: 0\n"
    text += "• Active users: 0\n"
    text += "• Commands used: 0"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔙 Back", 
        callback_data=f"view_bot:{bot_token}"
    ))
    
    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    bot_instance.safe_answer_callback(call.id, "Bot statistics")


def handle_bot_users(bot_instance, call, bot_token):
    """Handle bot users button"""
    bot_info = get_bot_by_token(bot_token)
    if not bot_info:
        bot_instance.safe_answer_callback(call.id, "❌ Bot not found", show_alert=True)
        return
    
    users = get_bot_users(bot_token)
    bot_name = bot_info.get('bot_name', 'Unnamed')
    
    if not users:
        text = f"👥 **Users for {bot_name}**\n\nNo users found."
    else:
        text = f"👥 **Users for {bot_name}** ({len(users)})\n\n"
        for i, user in enumerate(users[:10], 1):
            permission = user.get('permission', 'user')
            user_id = user.get('user_id', 'Unknown')
            text += f"{i}. `{user_id}` - {permission}\n"
        
        if len(users) > 10:
            text += f"\n... and {len(users) - 10} more"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "➕ Add User", 
        callback_data=f"add_user:{bot_token}"
    ))
    markup.add(types.InlineKeyboardButton(
        "🔙 Back", 
        callback_data=f"view_bot:{bot_token}"
    ))
    
    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    bot_instance.safe_answer_callback(call.id, "Bot users")


def handle_bot_settings(bot_instance, call, bot_token):
    """Handle bot settings button"""
    bot_info = get_bot_by_token(bot_token)
    if not bot_info:
        bot_instance.safe_answer_callback(call.id, "❌ Bot not found", show_alert=True)
        return
    
    bot_name = bot_info.get('bot_name', 'Unnamed')
    
    text = f"⚙️ **Settings for {bot_name}**\n\n"
    text += "Select a setting to configure:"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🤖 Bot Name", callback_data=f"edit_name:{bot_token}"),
        types.InlineKeyboardButton("🖼️ Profile", callback_data=f"edit_profile:{bot_token}"),
        types.InlineKeyboardButton("🌐 Webhook", callback_data=f"webhook:{bot_token}"),
        types.InlineKeyboardButton("🔙 Back", callback_data=f"view_bot:{bot_token}")
    )
    
    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    bot_instance.safe_answer_callback(call.id, "Bot settings")


# ==================== SETTINGS HANDLERS ====================

def handle_settings_option(bot_instance, call, data):
    """Handle settings menu options"""
    settings_map = {
        "settings_bot_defaults": "🤖 Bot Defaults",
        "settings_notifications": "🔔 Notifications",
        "settings_webhook": "🌐 Webhook Defaults", 
        "settings_privacy": "🔒 Privacy"
    }
    
    setting_name = settings_map.get(data, "Settings")
    
    text = f"⚙️ **{setting_name}**\n\nComing soon in Phase 2!"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔙 Back to Settings", 
        callback_data="back_to_settings"
    ))
    
    bot_instance.safe_edit(
        call.message.chat.id,
        call.message.message_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    bot_instance.safe_answer_callback(call.id, setting_name)


# ==================== STATISTICS HANDLERS ====================

def handle_refresh_stats(bot_instance, call):
    """Handle refresh statistics"""
    show_statistics(bot_instance, call.message)


# ==================== MISSING FUNCTIONS (FIXED) ====================

def show_webhook_menu(bot_instance, message):
    """Show webhook management menu"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    bots = get_user_bots(user_id)
    
    if not bots:
        bot_instance.safe_send(
            chat_id,
            "🤷 No bots to manage webhooks.\nAdd a bot first with /addbot",
            reply_markup=main_menu_keyboard(user_id)
        )
        return
    
    text = "🌐 **Webhook Management**\n\nSelect a bot:"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for bot in bots[:5]:
        bot_name = bot.get('bot_name', 'Unnamed')
        webhook = get_webhook_status(bot['bot_token'])
        status = "✅" if webhook and webhook.get('status') == 'active' else "❌"
        
        markup.add(types.InlineKeyboardButton(
            f"{status} {bot_name}",
            callback_data=f"webhook:{bot['bot_token']}"
        ))
    
    markup.add(types.InlineKeyboardButton(
        "🔙 Main Menu",
        callback_data="back_to_menu"
    ))
    
    bot_instance.safe_send(
        chat_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )


def show_settings_menu(bot_instance, message):
    """Show settings menu"""
    chat_id = message.chat.id
    
    text = "⚙️ **Settings**\n\nSelect a category:"
    
    bot_instance.safe_send(
        chat_id,
        text,
        reply_markup=get_settings_keyboard(),
        parse_mode='Markdown'
    )


def show_statistics(bot_instance, message):
    """Show system statistics"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    from master_db.connection import test_connection
    from master_db.operations import get_all_bots
    
    bots = get_all_bots()
    user_bots = get_user_bots(user_id)
    db_status = test_connection()
    
    total_bots = len(bots)
    active_bots = sum(1 for b in bots if b.get('is_active', False))
    
    text = "📊 **System Statistics**\n\n"
    text += f"**Your Stats:**\n"
    text += f"• Your bots: {len(user_bots)}\n\n"
    text += f"**Global Stats:**\n"
    text += f"• Total bots: {total_bots}\n"
    text += f"• Active bots: {active_bots}\n"
    text += f"• Database: {'✅ Connected' if db_status else '❌ Disconnected'}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")
    )
    
    bot_instance.safe_send(
        chat_id,
        text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

def handle_add_user(bot_instance, call, bot_token):
    """Handle add user button"""
    bot_instance.safe_answer_callback(
        call.id,
        "Add user coming in Phase 2!",
        show_alert=True
    )

def handle_edit_profile(bot_instance, call, bot_token):
    """Handle edit bot profile (placeholder)"""
    bot_instance.safe_answer_callback(
        call.id,
        "Profile editing coming in Phase 2!",
        show_alert=True
    )