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
    """Route all text messages to appropriate handler based on user status"""
    user_id = message.from_user.id
    
    # Check if user is suspended
    if database.get_user_suspended(user_id):
        bot.send_message(
            message.chat.id,
            "🚫 Your account has been suspended. Please contact an admin: @mr_nuun"
        )
        return
    
    text_msg = message.text.strip()
    
    # Get current user status from database
    status = database.get_user_status(user_id)
    
    # If user doesn't exist (shouldn't happen, but just in case)
    if not status:
        handle_first_message(bot, message)
        return
    
    # ----- REGISTRATION FLOW -----
    if status.startswith("reg:"):
        registration.handle_message(bot, message)
        return
    
    # ----- CANCEL COMMAND -----
    if text_msg == "/cancel" or text_msg == "❌ Cancel":
        handle_cancel(bot, message)
        return
    
    # ----- UPLOAD FLOW -----
    if status.startswith("upload:"):
        # During upload, only PDF documents are expected
        # But we should allow cancel command (already handled above)
        if text_msg == "❌ Cancel":
            return
        
        # For any other text during upload, remind them to send PDF
        bot.send_message(
            message.chat.id,
            "📤 Please send the PDF file or tap ❌ Cancel",
            reply_markup=buttons.cancel_button()
        )
        return
    
    # ----- SEARCH FLOW -----
    if status.startswith("search:"):
        # During search, only button interactions are expected
        # But we should allow cancel command (already handled above)
        if text_msg == "❌ Cancel":
            return
        
        # For any other text during search, remind them to use buttons
        bot.send_message(
            message.chat.id,
            "🔍 Please use the buttons below to search or tap ❌ Cancel",
            reply_markup=buttons.cancel_button()
        )
        return
    
    # ----- MAIN MENU (status = menu:home) -----
    if status == database.STATUS_MENU_HOME:
        handle_menu_selection(bot, message)
        return
    
    # ----- FALLBACK (unknown status) -----
    database.set_status(user_id, database.STATUS_MENU_HOME)
    bot.send_message(
        message.chat.id,
        "🔄 Resetting to main menu due to unknown status.",
        reply_markup=buttons.main_menu(user_id)
    )


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
    
    # ----- STALE BUTTON -----
    bot.answer_callback_query(
        call.id, 
        "❌ This action is no longer available. Please start over."
    )


# ---------- MENU SELECTION ----------
def handle_menu_selection(bot, message: Message):
    """Handle main menu selections"""
    user_id = message.from_user.id
    text_msg = message.text.strip()
    
    # Check if user is admin
    admin_status = is_admin(user_id)
    
    # Route based on menu option
    if text_msg == "📤 Upload" or text_msg == "📤 Upload PDF":
        # Start upload flow - set status in database
        database.set_status(user_id, database.STATUS_UPLOAD_WAIT_PDF)
        upload_flow.start(bot, message)
        
    elif text_msg == "🔍 Search" or text_msg == "🔍 Search PDF":
        # Start search flow - set status in database
        database.set_status(user_id, database.STATUS_SEARCH_SUBJECT)
        search_flow.start(bot, message)
        
    elif text_msg == "👤 Profile":
        # Show profile (doesn't change status)
        profile.show(bot, message)

    elif text_msg == "⚙️ Admin Panel" and admin_status:
        # Admin panel - edit the current message to show admin panel
        from bots.ardayda_bot.admin_handlers import show_admin_panel
        
        # Create a fake callback using the current message
        class FakeCall:
            def __init__(self, user_id, message):
                self.from_user = type('User', (), {'id': user_id})()
                self.message = message
                self.data = "admin_panel"
                self.id = "fake"
                def answer_callback_query(self, text=None):
                    pass
                self.answer_callback_query = answer_callback_query
        
        fake_call = FakeCall(user_id, message)
        show_admin_panel(bot, fake_call)
        
    else:
        # Unknown input
        bot.send_message(
            message.chat.id,
            text.UNKNOWN_INPUT,
            reply_markup=buttons.main_menu(user_id)
        )


# ---------- CANCEL HANDLER ----------
def handle_cancel(bot, message: Message):
    """Handle cancel command/button"""
    user_id = message.from_user.id
    status = database.get_user_status(user_id)
    
    if status and status.startswith("reg:"):
        bot.send_message(
            message.chat.id,
            "❌ Registration cannot be cancelled.\nPlease complete it first."
        )
        return
    
    # Clear from CACHE instead of database
    if status and status.startswith("upload:"):
        temp_cache.delete(f"upload:{user_id}")
    elif status and status.startswith("search:"):
        temp_cache.delete(f"search:{user_id}")
    
    database.set_status(user_id, database.STATUS_MENU_HOME)
    
    bot.send_message(
        message.chat.id,
        text.CANCELLED,
        reply_markup=buttons.main_menu(user_id),
        parse_mode="Markdown"
    )