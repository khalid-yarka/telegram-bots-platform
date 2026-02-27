# bots/ardayda_bot/upload_flow.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot import database, buttons, text
from bots.ardayda_bot.helpers import safe_edit_message
from bots.ardayda_bot.cache import temp_cache  # Import the cache
import logging
import time

logger = logging.getLogger(__name__)

SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "ICT", "Arabic","Islamic","English","Somali","G.P","Geography","History","Agriculture","Business"]
TAGS = ["Exam", "Notes", "Summery", "Assignment", "Chapter Reviews"]


def start(bot, message: Message):
    """Initialize upload flow"""
    user_id = message.from_user.id
    
    # Clear any previous temp data for this user (from cache)
    temp_cache.delete(f"upload:{user_id}")
    
    bot.send_message(
        message.chat.id,
        text.UPLOAD_START,
        reply_markup=buttons.cancel_button(),
        parse_mode="Markdown"
    )


def handle_pdf_upload(bot, message: Message):
    """Process received PDF document"""
    user_id = message.from_user.id
    status = database.get_user_status(user_id)

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

    # CRITICAL FIX: Check if file_unique_id exists
    if not doc.file_unique_id:
        logger.error(f"Document missing file_unique_id: {doc}")
        bot.send_message(
            message.chat.id,
            "❌ Invalid PDF file. Please try another file.",
            parse_mode="Markdown"
        )
        return

    # Check for duplicate
    if database.pdf_exists(doc.file_unique_id):
        bot.send_message(
            message.chat.id, 
            "⚠️ This PDF already exists in the system!"
        )
        database.set_status(user_id, database.STATUS_MENU_HOME)
        return

    # Store in CACHE with ALL required fields
    temp_data = {
        'file_id': doc.file_id,
        'file_unique_id': doc.file_unique_id,  # Make sure to save this!
        'name': doc.file_name or f"PDF_{int(time.time())}.pdf",
        'subject': None,
        'tags': []
    }
    
    # Log the data for debugging
    logger.info(f"Saving temp data: {temp_data}")
    
    temp_cache.set(f"upload:{user_id}", temp_data, ttl=3600)
    
    database.set_status(user_id, database.STATUS_UPLOAD_SUBJECT)

    bot.send_message(
        message.chat.id,
        text.UPLOAD_SUBJECT,
        reply_markup=buttons.subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )


def handle_callback(bot, call: CallbackQuery):
    """Handle upload flow callbacks"""
    user_id = call.from_user.id
    data = call.data
    status = database.get_user_status(user_id)

    if not status or not status.startswith("upload:"):
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # Get temp data from CACHE
    temp_data = temp_cache.get(f"upload:{user_id}") or {'tags': []}

    # ----- SUBJECT SELECT -----
    if status == database.STATUS_UPLOAD_SUBJECT and data.startswith("upload_subject:"):
        subject = data.split(":", 1)[1]

        # Update in CACHE
        temp_data['subject'] = subject
        temp_cache.set(f"upload:{user_id}", temp_data)
        
        database.set_status(user_id, database.STATUS_UPLOAD_TAGS)

        current_tags = temp_data.get("tags", [])
        safe_edit_message(
            bot,
            call.message.chat.id,
            call.message.message_id,
            text.UPLOAD_TAGS,
            reply_markup=buttons.tag_buttons(TAGS, current_tags),
            parse_mode="Markdown"
        )
        
        return

    # ----- TAG TOGGLE -----
    if status == database.STATUS_UPLOAD_TAGS and data.startswith("upload_tag:"):
        tag = data.split(":", 1)[1]
        
        current_tags = temp_data.get("tags", [])
        
        if tag in current_tags:
            current_tags.remove(tag)
        else:
            current_tags.append(tag)
        
        temp_data['tags'] = current_tags
        temp_cache.set(f"upload:{user_id}", temp_data)
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.tag_buttons(TAGS, current_tags)
        )
        return

    # ----- FINAL UPLOAD -----
    if data == "upload_done":
        logger.info(f"Upload temp_data for user {user_id}: {temp_data}")
        
        if not temp_data.get("file_id"):
            bot.answer_callback_query(call.id, "❌ Missing PDF file. Please start over.")
            return
            
        if not temp_data.get("subject"):
            bot.answer_callback_query(call.id, "❌ Missing subject. Please select a subject.")
            return
        
        try:
            _finalize_upload(bot, call, temp_data)
        except Exception as e:
            logger.error(f"Upload error for user {user_id}: {str(e)}", exc_info=True)
            bot.send_message(
                call.message.chat.id, 
                f"❌ Upload failed: {str(e)}\nPlease try again later."
            )
            database.set_status(user_id, database.STATUS_MENU_HOME)
            temp_cache.delete(f"upload:{user_id}")
        return

    # ----- CANCEL -----
    if data == "upload_cancel":
        temp_cache.delete(f"upload:{user_id}")
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
        safe_edit_message(
            bot,
            call.message.chat.id,
            call.message.message_id,
            text.CANCELLED,
            reply_markup=buttons.main_menu(),
            parse_mode="Markdown"
        )


def _finalize_upload(bot, call: CallbackQuery, temp_data):
    """Complete the upload process"""
    user_id = call.from_user.id

    logger.info(f"Finalizing upload for user {user_id}: {temp_data.get('name')}")
    
    # CRITICAL: Verify we have file_unique_id
    if not temp_data.get('file_unique_id'):
        raise Exception("Missing file_unique_id in temp data")

    # Insert PDF into database
    pdf_id = database.insert_pdf(
        file_id=temp_data["file_id"],
        file_unique_id=temp_data["file_unique_id"],  # Pass this!
        name=temp_data["name"],
        subject=temp_data["subject"],
        uploader_id=user_id
    )

    if not pdf_id:
        raise Exception("Failed to insert PDF into database")

    # Add tags
    tags_added = 0
    for tag in temp_data.get("tags", []):
        if tag:
            database.add_pdf_tag(pdf_id, tag)
            tags_added += 1

    logger.info(f"PDF uploaded successfully: ID={pdf_id}, tags={tags_added}")

    # Clear from cache
    temp_cache.delete(f"upload:{user_id}")
    database.set_status(user_id, database.STATUS_MENU_HOME)
    
    safe_edit_message(
        bot,
        call.message.chat.id,
        call.message.message_id,
        text.UPLOAD_SUCCESS,
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)