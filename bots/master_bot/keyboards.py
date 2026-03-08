from telebot import types
from master_db.operations import get_webhook_status

def main_menu_keyboard(user_id):
    """Create main menu reply keyboard"""
    from utils.permissions import is_super_admin

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Main menu buttons
    btn1 = types.KeyboardButton("🤖 My Bots")
    btn2 = types.KeyboardButton("➕ Add Bot")
    btn3 = types.KeyboardButton("🌐 Webhooks")
    btn4 = types.KeyboardButton("📊 Statistics")
    btn5 = types.KeyboardButton("⚙️ Settings")
    btn6 = types.KeyboardButton("❓ Help")

    # Add buttons in rows
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5, btn6)

    # Add admin button if super admin
    if is_super_admin(user_id):
        admin_btn = types.KeyboardButton("👑 Admin Panel")
        markup.row(admin_btn)

    return markup


def get_bots_list_keyboard(bots, page=0):
    """Create inline keyboard for bots list with pagination"""
    items_per_page = 5
    total_pages = (len(bots) + items_per_page - 1) // items_per_page
    page = max(0, min(page, total_pages - 1))

    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(bots))
    current_bots = bots[start_idx:end_idx]

    # Create message text
    text = f"🤖 **Your Bots** (Page {page + 1}/{total_pages})\n\n"

    # Create inline keyboard
    markup = types.InlineKeyboardMarkup(row_width=1)

    # Add bot buttons
    for bot in current_bots:
        bot_name = bot.get('bot_name', 'Unnamed')
        bot_type = bot.get('bot_type', 'unknown')
        status = "🟢" if bot.get('is_active') else "🔴"

        # Get webhook status for icon
        webhook = get_webhook_status(bot['bot_token'])
        webhook_icon = "🔗" if webhook and webhook.get('status') == 'active' else "⚠️"

        btn_text = f"{status} {webhook_icon} {bot_name} ({bot_type})"

        btn = types.InlineKeyboardButton(
            text=btn_text,
            callback_data=f"view_bot:{bot['bot_token']}"
        )
        markup.add(btn)

    # Add pagination buttons
    nav_buttons = []

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("◀️ Prev", callback_data=f"bots_page:{page-1}"))

    nav_buttons.append(types.InlineKeyboardButton("🔄 Refresh", callback_data="bots_refresh"))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"bots_page:{page+1}"))

    if nav_buttons:
        markup.row(*nav_buttons)

    # Add action buttons
    action_row = [
        types.InlineKeyboardButton("➕ Add New", callback_data="add_bot_start"),
        types.InlineKeyboardButton("🌐 Check All", callback_data="check_all_webhooks")
    ]
    markup.row(*action_row)

    # Add back to menu
    markup.row(types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu"))

    return text, markup


def get_bot_details_keyboard(bot_token, user_id):
    """Create inline keyboard for bot details"""
    from utils.permissions import can_manage_bot

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Row 1: Basic actions
    markup.add(
        types.InlineKeyboardButton("🌐 Webhook", callback_data=f"webhook:{bot_token}"),
        types.InlineKeyboardButton("📊 Stats", callback_data=f"stats:{bot_token}")
    )

    # Row 2: Edit actions
    markup.add(
        types.InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_name:{bot_token}"),
        types.InlineKeyboardButton("🖼️ Edit Profile", callback_data=f"edit_profile:{bot_token}")
    )

    # Row 3: Settings and Users
    markup.add(
        types.InlineKeyboardButton("⚙️ Settings", callback_data=f"settings:{bot_token}"),
        types.InlineKeyboardButton("👥 Users", callback_data=f"users:{bot_token}")
    )

    # Row 4: Delete (only if can manage)
    if can_manage_bot(bot_token, user_id):
        markup.add(
            types.InlineKeyboardButton("🗑️ Delete Bot", callback_data=f"delete_confirm:{bot_token}")
        )

    # Row 5: Navigation
    markup.row(
        types.InlineKeyboardButton("🔙 Back to List", callback_data="back_to_bots"),
        types.InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")
    )

    return markup


def get_webhook_keyboard(bot_token):
    """Create inline keyboard for webhook management"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("🔄 Check Now", callback_data=f"webhook_check:{bot_token}"),
        types.InlineKeyboardButton("⚙️ Configure", callback_data=f"webhook_config:{bot_token}")
    )

    markup.add(
        types.InlineKeyboardButton("🗑️ Delete", callback_data=f"webhook_delete:{bot_token}"),
        types.InlineKeyboardButton("🔙 Back", callback_data=f"view_bot:{bot_token}")
    )

    return markup


def get_confirmation_keyboard(action, bot_token, cancel_action):
    """Create confirmation keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("✅ Yes, Confirm", callback_data=f"{action}:{bot_token}"),
        types.InlineKeyboardButton("❌ No, Cancel", callback_data=cancel_action)
    )

    return markup


def get_pagination_keyboard(current_page, total_pages, callback_prefix):
    """Create pagination keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=3)

    buttons = []

    if current_page > 0:
        buttons.append(types.InlineKeyboardButton(
            "◀️",
            callback_data=f"{callback_prefix}:{current_page-1}"
        ))

    buttons.append(types.InlineKeyboardButton(
        f"{current_page + 1}/{total_pages}",
        callback_data="noop"
    ))

    if current_page < total_pages - 1:
        buttons.append(types.InlineKeyboardButton(
            "▶️",
            callback_data=f"{callback_prefix}:{current_page+1}"
        ))

    markup.row(*buttons)
    return markup


def get_settings_keyboard():
    """Create settings menu keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("🤖 Bot Defaults", callback_data="settings_bot_defaults"),
        types.InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
        types.InlineKeyboardButton("🌐 Webhook Defaults", callback_data="settings_webhook"),
        types.InlineKeyboardButton("🔒 Privacy", callback_data="settings_privacy")
    )

    markup.row(
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")
    )

    return markup


def get_admin_keyboard():
    """Create admin panel keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        types.InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
        types.InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup")
    )
    
    markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu"))
    
    return markup


def get_bot_users_keyboard(bot_token):
    """Create keyboard for bot users management"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("➕ Add User", callback_data=f"add_user:{bot_token}"),
        types.InlineKeyboardButton("🔙 Back", callback_data=f"view_bot:{bot_token}")
    )
    
    return markup


def get_yes_no_keyboard(yes_callback, no_callback):
    """Create simple yes/no keyboard"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton("✅ Yes", callback_data=yes_callback),
        types.InlineKeyboardButton("❌ No", callback_data=no_callback)
    )
    
    return markup