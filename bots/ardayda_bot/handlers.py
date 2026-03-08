# bots/ardayda_bot/handlers.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot.helpers import safe_edit_message
from bots.ardayda_bot import (
    database,
    buttons,
    text,
    registration,
    upload_flow,
    search_flow,
    profile,
    admin_sql,
)
from bots.ardayda_bot.conflict_manager import (
    check_and_resolve_conflict, 
    clear_previous_operation,
    save_message_id,
    operation_ended
)
from bots.ardayda_bot.cache import temp_cache
from bots.ardayda_bot.admin import is_admin
from bots.ardayda_bot.admin_handlers import (
    show_admin_panel,
    show_users_list,
    show_user_details,
    show_user_pdfs,
    handle_warn_user,
    handle_suspend_user,
    handle_unsuspend_user,
    handle_make_admin,
    handle_remove_admin,
    show_pdfs_list,
    show_pdf_details,
    handle_delete_pdf,
    handle_pdf_user,
    handle_pdf_stats,
    show_stats,
    show_user_stats,
    show_pdf_stats,
    show_logs,
    handle_clear_logs,
    handle_confirmation,
    handle_cancellation
)

import logging

logger = logging.getLogger(__name__)

# ---------- FIRST MESSAGE (NEW USER) ----------
def handle_first_message(bot, message: Message):
    """Handle first message from a new user - start registration"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Add user to database (default status is menu:home)
    database.add_user(user_id)
    
    # Start registration flow
    registration.start(bot, user_id, chat_id)


# ---------- TEXT MESSAGES ----------
def handle_message(bot, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check suspension
    if database.get_user_suspended(user_id):
        bot.send_message(chat_id, "🚫 Your account has been suspended.")
        return
    
    text_msg = message.text.strip()
    status = database.get_user_status(user_id)
    
    # New user
    if not status:
        handle_first_message(bot, message)
        return
    
    # Handle admin SQL commands first (special case)
    if text_msg.startswith('/sql ') and is_admin(user_id):
        from bots.ardayda_bot.admin_sql import handle_sql_command
        handle_sql_command(bot, message)
        return
    
    # Check for cancel
    if text_msg in ["/cancel", "❌ Cancel"]:
        handle_cancel(bot, message)
        return
    
    # Route based on status
    if status.startswith("reg:"):
        registration.handle_message(bot, message)
    elif status.startswith("upload:"):
        bot.send_message(chat_id, "📤 Please send the PDF file.", 
                        reply_markup=buttons.cancel_button())
    elif status.startswith("search:"):
        bot.send_message(chat_id, "🔍 Please use the buttons below.",
                        reply_markup=buttons.cancel_button())
    elif status == database.STATUS_MENU_HOME:
        handle_menu_selection(bot, message)
    else:
        database.set_status(user_id, database.STATUS_MENU_HOME)
        bot.send_message(chat_id, "🔄 Reset to main menu.",
                        reply_markup=buttons.main_menu(user_id))


# ---------- DOCUMENTS (PDF FILES) ----------
def handle_document(bot, message: Message):
    """Route document messages based on user status"""
    user_id = message.from_user.id
    
    # Check if user is suspended
    if database.get_user_suspended(user_id):
        bot.send_message(
            message.chat.id,
            "🚫 Your account has been suspended. Please contact an admin: @mr_nuun"
        )
        return
    
    # Get current user status
    status = database.get_user_status(user_id)
    
    # Check if user is in upload flow
    if status and status.startswith("upload:"):
        upload_flow.handle_pdf_upload(bot, message)
        return
    
    # If user is in search flow but sends a document, handle it
    if status and status.startswith("search:"):
        bot.send_message(
            message.chat.id,
            "🔍 You're in search mode. Please use the buttons to search or tap ❌ Cancel.\n\nTo upload a PDF, please go back to main menu and select 'Upload'.",
            reply_markup=buttons.main_menu(user_id)
        )
        return
    
    # Not in upload flow
    bot.send_message(
        message.chat.id,
        "⚠️ Please start upload from the menu first.",
        reply_markup=buttons.main_menu(user_id)
    )


# ---------- CALLBACK QUERIES (INLINE BUTTONS) ----------
def handle_callback(bot, call: CallbackQuery):
    """Route all callback queries based on user status"""
    user_id = call.from_user.id
    data = call.data
    
    # Get current user status
    status = database.get_user_status(user_id)
    
    if not status:
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        database.set_status(user_id, database.STATUS_MENU_HOME)
        return
    
    # ==================== ADMIN CALLBACKS ====================
    # Check if this is an admin callback
    if data.startswith("admin_"):
        # Verify user is admin
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Admin access required!")
            return
        
        # Admin Panel Main
        if data == "admin_panel":
            show_admin_panel(bot, call)
        
        # User Management
        elif data.startswith("admin_users:"):
            page = int(data.split(":")[1])
            show_users_list(bot, call, page)
        
        elif data.startswith("admin_view_user:"):
            parts = data.split(":")
            target_user_id = int(parts[1])
            page = int(parts[2]) if len(parts) > 2 else 1
            show_user_details(bot, call, target_user_id, page)
        
        elif data.startswith("admin_user_pdfs:"):
            parts = data.split(":")
            target_user_id = int(parts[1])
            page = int(parts[2]) if len(parts) > 2 else 1
            show_user_pdfs(bot, call, target_user_id, page)
        
        elif data.startswith("admin_warn:"):
            target_user_id = int(data.split(":")[1])
            handle_warn_user(bot, call, target_user_id)
        
        elif data.startswith("admin_suspend:"):
            target_user_id = int(data.split(":")[1])
            if is_admin(target_user_id) or user_id == target_user_id:
                bot.answer_callback_query(call.id, "⛔ Action Denied !")
                return 
            handle_suspend_user(bot, call, target_user_id)
        
        elif data.startswith("admin_unsuspend:"):
            target_user_id = int(data.split(":")[1])
            handle_unsuspend_user(bot, call, target_user_id)
        
        elif data.startswith("admin_makeadmin:"):
            target_user_id = int(data.split(":")[1])
            handle_make_admin(bot, call, target_user_id)
        
        elif data.startswith("admin_removeadmin:"):
            target_user_id = int(data.split(":")[1])
            if target_user_id == 2094426161:
                bot.answer_callback_query(call.id, "Action Denied [×]")
                return
            handle_remove_admin(bot, call, target_user_id)
        
        # PDF Management
        elif data.startswith("admin_pdfs:"):
            page = int(data.split(":")[1])
            show_pdfs_list(bot, call, page)
        
        elif data.startswith("admin_view_pdf:"):
            parts = data.split(":")
            pdf_id = int(parts[1])
            page = int(parts[2]) if len(parts) > 2 else 1
            show_pdf_details(bot, call, pdf_id, page)
        
        elif data.startswith("admin_delete_pdf:"):
            pdf_id = int(data.split(":")[1])
            handle_delete_pdf(bot, call, pdf_id)
        
        elif data.startswith("admin_pdf_user:"):
            pdf_id = int(data.split(":")[1])
            handle_pdf_user(bot, call, pdf_id)
        
        elif data.startswith("admin_pdf_stats:"):
            pdf_id = int(data.split(":")[1])
            handle_pdf_stats(bot, call, pdf_id)
        
        # Statistics
        elif data == "admin_stats":
            show_stats(bot, call)
        
        elif data == "admin_stats_users":
            show_user_stats(bot, call)
        
        elif data == "admin_stats_pdfs":
            show_pdf_stats(bot, call)
        
        elif data == "admin_stats_subjects":
            bot.answer_callback_query(call.id, "Coming soon!")
        
        elif data == "admin_stats_tags":
            bot.answer_callback_query(call.id, "Coming soon!")
        
        elif data == "admin_stats_daily":
            bot.answer_callback_query(call.id, "Coming soon!")
        
        # Logs
        elif data.startswith("admin_logs:"):
            page = int(data.split(":")[1])
            show_logs(bot, call, page)
        
        elif data == "admin_clear_logs":
            handle_clear_logs(bot, call)
        
        # Confirmations
        elif data.startswith("admin_confirm_"):
            parts = data.replace("admin_confirm_", "").split(":")
            action = parts[0]
            target_id = int(parts[1])
            handle_confirmation(bot, call, action, target_id)
        
        elif data.startswith("admin_cancel_"):
            parts = data.replace("admin_cancel_", "").split(":")
            action = parts[0]
            target_id = int(parts[1])
            handle_cancellation(bot, call, action, target_id)
        
        # Back button
        elif data == "admin_back":
            try:
                logger.info(f"Admin {user_id} returning to main menu")
                database.set_status(user_id, database.STATUS_MENU_HOME)
                
                safe_edit_message(
                    bot=bot,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text.HOME_WELCOME,
                    reply_markup=buttons.main_menu(user_id),
                    parse_mode="Markdown"
                )
                
                logger.info(f"Successfully returned user {user_id} to main menu")
                
            except Exception as e:
                logger.error(f"Error in admin_back: {e}")
                try:
                    bot.send_message(
                        call.message.chat.id,
                        text.HOME_WELCOME,
                        reply_markup=buttons.main_menu(user_id),
                        parse_mode="Markdown"
                    )
                except:
                    pass
            
            bot.answer_callback_query(call.id)
            return
        else:
            bot.answer_callback_query(call.id, "Unknown admin action")
        
        return
    
    # ==================== REGULAR CALLBACKS ====================
    # ----- REGISTRATION CALLBACKS -----
    if status.startswith("reg:"):
        registration.handle_callback(bot, call)
        return
    
    # ----- UPLOAD CALLBACKS -----
    if status.startswith("upload:") and data.startswith("upload_"):
        upload_flow.handle_callback(bot, call)
        return
    
    # ----- SEARCH CALLBACKS -----
    if status.startswith("search:") and data.startswith(("search_", "pdf_page:", "pdf_send:")):
        search_flow.handle_callback(bot, call)
        return
    
    if data.startswith("sql_confirm:"):
      query = data[12:].strip()  # Remove 'sql_confirm:'
      chat_id = call.message.chat.id
      admin_sql.execute_and_send_result(bot, chat_id, query)
    # ----- STALE BUTTON -----
    bot.answer_callback_query(
        call.id, 
        "❌ This action is no longer available. Please start over."
    )


# ---------- MENU SELECTION ----------
def handle_menu_selection(bot, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text_msg = message.text.strip()
    
    # Map menu options to operations
    op_map = {
        "📤 Upload": "upload",
        "📤 Upload PDF": "upload",
        "🔍 Search": "search",
        "🔍 Search PDF": "search"
    }
    
    if text_msg in op_map:
        can_proceed, conflict_msg = check_and_resolve_conflict(
            bot, user_id, chat_id, op_map[text_msg]
        )
        
        if not can_proceed:
            bot.send_message(chat_id, conflict_msg, 
                           reply_markup=buttons.cancel_button())
            return
        
        # Clear previous operation
        clear_previous_operation(bot, user_id, chat_id)
    
    # Regular routing
    if text_msg in ["📤 Upload", "📤 Upload PDF"]:
        can_proceed, conflict_msg = check_and_resolve_conflict(bot, user_id, chat_id, "upload")
        if not can_proceed:
            bot.send_message(chat_id, conflict_msg, reply_markup=buttons.cancel_button())
            return
        clear_previous_operation(bot, user_id, chat_id)
        database.set_status(user_id, database.STATUS_UPLOAD_WAIT_PDF)
        msg = bot.send_message(chat_id, text.UPLOAD_START, reply_markup=buttons.cancel_button())
        save_message_id(user_id, msg.message_id)
        upload_flow.start(bot, message)
        
    elif text_msg in ["🔍 Search", "🔍 Search PDF"]:
        can_proceed, conflict_msg = check_and_resolve_conflict(bot, user_id, chat_id, "search")
        if not can_proceed:
            bot.send_message(chat_id, conflict_msg, reply_markup=buttons.cancel_button())
            return
        clear_previous_operation(bot, user_id, chat_id)
        database.set_status(user_id, database.STATUS_SEARCH_SUBJECT)
        msg = bot.send_message(chat_id, text.SEARCH_START,
                              reply_markup=buttons.search_subject_buttons(text.SUBJECTS))
        save_message_id(user_id, msg.message_id)
        search_flow.start(bot, message)


# ---------- CANCEL HANDLER ----------
def handle_cancel(bot, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    status = database.get_user_status(user_id)
    
    if status and status.startswith("reg:"):
        bot.send_message(chat_id, "❌ Registration cannot be cancelled.")
        return
    
    # Clean up and end operation
    operation_ended(bot, user_id, chat_id)
    
    bot.send_message(chat_id, text.CANCELLED,
                    reply_markup=buttons.main_menu(user_id))