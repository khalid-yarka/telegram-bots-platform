# bots/ardayda_bot/registration.py

from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bots.ardayda_bot import database, buttons, text

# Constants
SCHOOLS_PER_PAGE = 5

# We don't need in-memory state anymore - everything in database
# But we need to track current page for school pagination temporarily
# This is acceptable because it's temporary UI state, not critical data
registration_pages = {}


# ---------- CHECK IF REGISTERING ----------
def is_registering(user_id):
    """Check if user is in registration flow by checking database status"""
    status = database.get_user_status(user_id)
    return status and status.startswith("reg:")


# ---------- START REGISTRATION ----------
def start(bot, user_id, chat_id):
    """Start registration for new user"""
    # Set status to registration: name
    database.set_status(user_id, database.STATUS_REG_NAME)
    
    # Initialize page tracking (temporary, not in DB)
    registration_pages[user_id] = 0
    
    bot.send_message(
        chat_id,
        text.REG_NAME,
        parse_mode="Markdown"
    )


# ---------- HANDLE TEXT MESSAGES ----------
def handle_message(bot, message: Message):
    """Handle text messages during registration flow"""
    user_id = message.from_user.id
    status = database.get_user_status(user_id)
    text_msg = message.text.strip()

    # ----- STEP 1: ENTER NAME -----
    if status == database.STATUS_REG_NAME:
        # Save name to database
        database.set_user_name(user_id, text_msg)
        
        # Move to region selection
        database.set_status(user_id, database.STATUS_REG_REGION)
        
        # Ask for region
        _ask_region(bot, message.chat.id)
        return

    # ----- STEP 3: ENTER CLASS (optional) -----
    elif status == database.STATUS_REG_CLASS:
        # Save class (can be "skip" or actual class)
        if text_msg.lower() == "skip":
            database.set_user_class(user_id, None)
        else:
            database.set_user_class(user_id, text_msg)
        
        # Finalize registration
        _finalize_registration(bot, message.chat.id, user_id)
        return

    # Should not happen
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ Unexpected registration state. Please start over with /cancel"
        )


# ---------- ASK REGION (Inline Keyboard) ----------
def _ask_region(bot, chat_id):
    """Show region selection buttons"""
    kb = InlineKeyboardMarkup(row_width=2)
    
    for region in text.form_four_schools_by_region.keys():
        kb.add(
            InlineKeyboardButton(
                f"🏫 {region}", 
                callback_data=f"reg_region:{region}"
            )
        )
    
    bot.send_message(
        chat_id, 
        "Please select your region:", 
        reply_markup=kb
    )


# ---------- ASK SCHOOL (with pagination) ----------
def _ask_school(bot, chat_id, user_id, region):
    """Show school selection with pagination"""
    
    schools = text.form_four_schools_by_region[region]
    page = registration_pages.get(user_id, 0)
    start = page * SCHOOLS_PER_PAGE
    end = start + SCHOOLS_PER_PAGE
    page_schools = schools[start:end]
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # Add school buttons
    for school in page_schools:
        kb.add(
            InlineKeyboardButton(
                f"🏫 {school}", 
                callback_data=f"reg_school:{school}"
            )
        )
    
    # Pagination buttons
    pagination_buttons = []
    if start > 0:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data="school_prev")
        )
    
    pagination_buttons.append(
        InlineKeyboardButton(f"📄 {page+1}/{(len(schools)-1)//SCHOOLS_PER_PAGE+1}", callback_data="noop")
    )
    
    if end < len(schools):
        pagination_buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data="school_next")
        )
    
    if pagination_buttons:
        kb.row(*pagination_buttons)
    
    bot.send_message(
        chat_id,
        "Select your school:",
        reply_markup=kb
    )


# ---------- HANDLE CALLBACKS ----------
def handle_callback(bot, call: CallbackQuery):
    """Handle registration callbacks"""
    user_id = call.from_user.id
    data = call.data
    status = database.get_user_status(user_id)

    if not status or not status.startswith("reg:"):
        bot.answer_callback_query(call.id, "Registration session expired")
        return

    # ----- REGION SELECTED -----
    if status == database.STATUS_REG_REGION and data.startswith("reg_region:"):
        region = data.split(":", 1)[1]
        
        # Save region to database
        database.set_user_region(user_id, region)
        
        # Move to school selection
        database.set_status(user_id, database.STATUS_REG_SCHOOL)
        
        # Initialize page for this user
        registration_pages[user_id] = 0
        
        # Edit the message to remove buttons
        bot.edit_message_text(
            f"✅ Selected region: {region}\n\nNow select your school:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        
        # Ask for school (new message)
        _ask_school(bot, call.message.chat.id, user_id, region)
        
        bot.answer_callback_query(call.id)
        return

    # ----- SCHOOL SELECTED -----
    if status == database.STATUS_REG_SCHOOL and data.startswith("reg_school:"):
        school = data.split(":", 1)[1]
        
        # Save school to database
        database.set_user_school(user_id, school)
        
        # Move to class entry
        database.set_status(user_id, database.STATUS_REG_CLASS)
        
        # Clear page tracking
        registration_pages.pop(user_id, None)
        
        # Edit the message to remove buttons
        bot.edit_message_text(
            f"✅ Selected school: {school}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        
        # Ask for class
        bot.send_message(
            call.message.chat.id,
            "✅ Great! Enter your class (optional e.g., F4, F3) or type 'skip':",
            reply_markup=buttons.cancel_button()
        )
        
        bot.answer_callback_query(call.id)
        return

    # ----- SCHOOL PAGINATION -----
    if status == database.STATUS_REG_SCHOOL:
        if data == "school_next":
            registration_pages[user_id] = registration_pages.get(user_id, 0) + 1
            
            # Get region from database
            user = database.get_user(user_id)
            region = user.get("region") if user else None
            
            if region:
                # Update the message with new schools
                schools = text.form_four_schools_by_region[region]
                page = registration_pages[user_id]
                start = page * SCHOOLS_PER_PAGE
                end = start + SCHOOLS_PER_PAGE
                page_schools = schools[start:end]
                
                # Build new keyboard
                kb = InlineKeyboardMarkup(row_width=1)
                for school in page_schools:
                    kb.add(InlineKeyboardButton(f"🏫 {school}", callback_data=f"reg_school:{school}"))
                
                pagination_buttons = []
                if start > 0:
                    pagination_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="school_prev"))
                
                pagination_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{(len(schools)-1)//SCHOOLS_PER_PAGE+1}", callback_data="noop"))
                
                if end < len(schools):
                    pagination_buttons.append(InlineKeyboardButton("➡️ Next", callback_data="school_next"))
                
                if pagination_buttons:
                    kb.row(*pagination_buttons)
                
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=kb
                )
            
            bot.answer_callback_query(call.id)
            return
            
        elif data == "school_prev":
            registration_pages[user_id] = max(0, registration_pages.get(user_id, 0) - 1)
            
            # Get region from database
            user = database.get_user(user_id)
            region = user.get("region") if user else None
            
            if region:
                # Update the message with new schools
                schools = text.form_four_schools_by_region[region]
                page = registration_pages[user_id]
                start = page * SCHOOLS_PER_PAGE
                end = start + SCHOOLS_PER_PAGE
                page_schools = schools[start:end]
                
                # Build new keyboard
                kb = InlineKeyboardMarkup(row_width=1)
                for school in page_schools:
                    kb.add(InlineKeyboardButton(f"🏫 {school}", callback_data=f"reg_school:{school}"))
                
                pagination_buttons = []
                if start > 0:
                    pagination_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="school_prev"))
                
                pagination_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{(len(schools)-1)//SCHOOLS_PER_PAGE+1}", callback_data="noop"))
                
                if end < len(schools):
                    pagination_buttons.append(InlineKeyboardButton("➡️ Next", callback_data="school_next"))
                
                if pagination_buttons:
                    kb.row(*pagination_buttons)
                
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=kb
                )
            
            bot.answer_callback_query(call.id)
            return

    # ----- FALLBACK -----
    bot.answer_callback_query(call.id, "Invalid registration action")


# ---------- FINALIZE REGISTRATION ----------
def _finalize_registration(bot, chat_id, user_id):
    """Complete registration and show main menu"""
    
    # Set status to main menu
    database.set_status(user_id, database.STATUS_MENU_HOME)
    
    # Get user data for welcome message
    user = database.get_user(user_id)
    name = user.get("name", "User") if user else "User"
    
    bot.send_message(
        chat_id,
        f"✅ Registration completed successfully, {name}!\n\nYou can now upload and search PDFs using the menu below.",
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )