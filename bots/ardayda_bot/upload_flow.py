# bots/ardayda_bot/upload_flow.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot import database, buttons, text

# Example static data (can come from DB later)
SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
TAGS = ["Exam", "Notes", "Lecture", "Assignment", "Revision"]


# ---------- START UPLOAD ----------
def start(bot, message: Message):
    """Initialize upload flow"""
    user_id = message.from_user.id
    
    # Clear any previous temp data
    database.clear_upload_temp(user_id)
    
    # Status already set to upload:wait_pdf by handlers.py
    
    bot.send_message(
        message.chat.id,
        text.UPLOAD_START,
        reply_markup=buttons.cancel_button(),
        parse_mode="Markdown"
    )


# ---------- HANDLE PDF MESSAGE ----------
def handle_pdf_upload(bot, message: Message):
    """Process received PDF document"""
    user_id = message.from_user.id
    status = database.get_user_status(user_id)

    # Verify we're in the correct state
    if status != database.STATUS_UPLOAD_WAIT_PDF:
        bot.send_message(
            message.chat.id,
            "⚠️ Please start upload from the menu first.",
            reply_markup=buttons.main_menu()
        )
        return

    doc = message.document

    # Check if it's a PDF
    if not doc or not doc.mime_type or not doc.mime_type.endswith("pdf"):
        bot.send_message(
            message.chat.id, 
            text.UPLOAD_INVALID_FILE, 
            parse_mode="Markdown"
        )
        return

    # Check for duplicate using file_unique_id
    if database.pdf_exists(doc.file_unique_id):
        bot.send_message(message.chat.id, text.UPLOAD_ALREADY_EXISTS)
        # Reset to main menu
        database.set_status(user_id, database.STATUS_MENU_HOME)
        database.clear_upload_temp(user_id)
        return

    # Store PDF temporarily in database
    database.save_upload_temp(
        user_id, 
        doc.file_id, 
        doc.file_unique_id, 
        doc.file_name
    )
    
    # Move to subject selection
    database.set_status(user_id, database.STATUS_UPLOAD_SUBJECT)

    bot.send_message(
        message.chat.id,
        text.UPLOAD_SUBJECT,
        reply_markup=buttons.subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )


# ---------- CALLBACK HANDLER ----------
def handle_callback(bot, call: CallbackQuery):
    """Handle upload flow callbacks"""
    user_id = call.from_user.id
    data = call.data
    status = database.get_user_status(user_id)

    if not status or not status.startswith("upload:"):
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # ----- SUBJECT SELECT -----
    if status == database.STATUS_UPLOAD_SUBJECT and data.startswith("upload_subject:"):
        subject = data.split(":", 1)[1]

        # Save subject to database
        database.save_upload_subject(user_id, subject)
        
        # Move to tags selection
        database.set_status(user_id, database.STATUS_UPLOAD_TAGS)

        # Get current tags (empty initially)
        temp_data = database.get_upload_temp(user_id)
        current_tags = temp_data.get("tags", []) if temp_data else []

        bot.edit_message_text(
            text.UPLOAD_TAGS,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.tag_buttons(TAGS, current_tags),
            parse_mode="Markdown"
        )
        return

    # ----- TAG TOGGLE -----
    if status == database.STATUS_UPLOAD_TAGS and data.startswith("upload_tag:"):
        tag = data.split(":", 1)[1]
        
        # Get current tags
        temp_data = database.get_upload_temp(user_id)
        current_tags = temp_data.get("tags", []) if temp_data else []
        
        # Toggle tag
        if tag in current_tags:
            current_tags.remove(tag)
        else:
            current_tags.append(tag)
        
        # Save updated tags
        tags_string = ",".join(current_tags)
        database.save_upload_tags(user_id, tags_string)

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.tag_buttons(TAGS, current_tags)
        )
        return

    # ----- FINAL UPLOAD -----
    if data == "upload_done":
        # Verify we have all required data
        temp_data = database.get_upload_temp(user_id)
        
        if not temp_data or not temp_data.get("file_id") or not temp_data.get("subject"):
            bot.answer_callback_query(
                call.id, 
                "❌ Missing PDF or subject. Please start over."
            )
            return
        
        try:
            _finalize_upload(bot, call, temp_data)
        except Exception as e:
            print(f"Upload error: {e}")  # Log error
            bot.send_message(call.message.chat.id, text.UPLOAD_FAILED)
            # Reset on error
            database.set_status(user_id, database.STATUS_MENU_HOME)
            database.clear_upload_temp(user_id)
        return

    # ----- CANCEL -----
    if data == "upload_cancel":
        # Clear temp data and reset to main menu
        database.clear_upload_temp(user_id)
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
        bot.edit_message_text(
            text.CANCELLED,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.main_menu(),
            parse_mode="Markdown"
        )


# ---------- FINALIZE ----------
def _finalize_upload(bot, call: CallbackQuery, temp_data):
    """Complete the upload process"""
    user_id = call.from_user.id

    # Insert PDF into database
    pdf_id = database.insert_pdf(
        file_id=temp_data["file_id"],
        name=temp_data["name"],
        subject=temp_data["subject"],
        uploader_id=user_id
    )

    # Add tags
    for tag in temp_data.get("tags", []):
        if tag:  # Make sure tag is not empty
            database.add_pdf_tag(pdf_id, tag)

    # Clear temp data and reset status
    database.clear_upload_temp(user_id)
    database.set_status(user_id, database.STATUS_MENU_HOME)

    # Confirm success
    bot.edit_message_text(
        text.UPLOAD_SUCCESS,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )