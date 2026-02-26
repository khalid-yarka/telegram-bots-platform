# bots/ardayda_bot/handlers.py

from telebot.types import Message, CallbackQuery

from bots.ardayda_bot import (
    database,
    buttons,
    text,
    registration,
    upload_flow,
    search_flow,
    profile,
)

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
        # If user sends text, remind them to send PDF or cancel
        bot.send_message(
            message.chat.id,
            "📤 Please send the PDF file or tap ❌ Cancel",
            reply_markup=buttons.cancel_button()
        )
        return
    
    # ----- SEARCH FLOW -----
    if status.startswith("search:"):
        # During search, text might be for something else
        bot.send_message(
            message.chat.id,
            "🔍 Use the buttons to search or tap ❌ Cancel",
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
        reply_markup=buttons.main_menu()
    )


# ---------- DOCUMENTS (PDF FILES) ----------
def handle_document(bot, message: Message):
    """Route document messages based on user status"""
    user_id = message.from_user.id
    
    # Get current user status
    status = database.get_user_status(user_id)
    
    # Check if user is in upload flow
    if status and status.startswith("upload:"):
        upload_flow.handle_pdf_upload(bot, message)
        return
    
    # Not in upload flow
    bot.send_message(
        message.chat.id,
        "⚠️ Please start upload from the menu first.",
        reply_markup=buttons.main_menu()
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
        
    else:
        # Unknown input
        bot.send_message(
            message.chat.id,
            text.UNKNOWN_INPUT,
            reply_markup=buttons.main_menu()
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
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )