# bots/ardayda_bot/conflict_manager.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot import database, buttons
import logging

logger = logging.getLogger(__name__)

# Store last message IDs to clean up
user_last_messages = {}

def check_and_resolve_conflict(bot, user_id, chat_id, new_operation):
    """
    Check if user is in another operation and resolve conflicts
    Returns: (can_proceed, message_to_send)
    """
    current_status = database.get_user_status(user_id)
    
    # No conflict if at main menu
    if current_status == database.STATUS_MENU_HOME:
        return True, None
    
    # Check if trying to start same operation
    current_op = current_status.split(':')[0] if ':' in current_status else current_status
    
    if current_op == new_operation:
        # Already in this operation
        return False, f"⚠️ You're already in {new_operation} mode. Please finish or cancel it first."
    
    # Different operation conflict
    conflict_messages = {
        'upload': "📤 You're currently uploading a PDF. Please finish or cancel it first.",
        'search': "🔍 You're currently searching. Please finish or cancel it first.",
        'reg': "📝 Please complete your registration first."
    }
    
    for op, msg in conflict_messages.items():
        if current_op == op:
            return False, msg
    
    return True, None

def clear_previous_operation(bot, user_id, chat_id):
    """Clean up previous operation data and messages"""
    # Clear any temp data
    database.clear_upload_temp(user_id)
    database.clear_search_temp(user_id)
    
    # Try to delete last operation message if exists
    if user_id in user_last_messages:
        try:
            bot.delete_message(chat_id, user_last_messages[user_id])
        except:
            pass
        del user_last_messages[user_id]

def save_message_id(user_id, message_id):
    """Save last message ID for cleanup"""
    user_last_messages[user_id] = message_id

def operation_ended(bot, user_id, chat_id, final_message_id=None):
    """Call this when an operation ends"""
    # Clear status
    database.set_status(user_id, database.STATUS_MENU_HOME)
    
    # Clean up temp data
    database.clear_upload_temp(user_id)
    database.clear_search_temp(user_id)
    
    # Delete the last operation message if different from final
    if user_id in user_last_messages:
        last_msg_id = user_last_messages[user_id]
        if final_message_id and last_msg_id != final_message_id:
            try:
                bot.delete_message(chat_id, last_msg_id)
            except:
                pass
        del user_last_messages[user_id]