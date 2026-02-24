# bots/ardayda_bot/upload_flow.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot import database, buttons, text
from bots.ardayda_bot.session_manager import get_session, update_session, end_session

# Example static data (can come from DB later)
SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
TAGS = ["Exam", "Notes", "Lecture", "Assignment", "Revision"]


# ---------- START UPLOAD ----------

def start(bot, message: Message):
    user_id = message.from_user.id

    database.set_status(user_id, "upload:wait_pdf")

    bot.send_message(
        message.chat.id,
        text.UPLOAD_START,
        reply_markup=buttons.cancel_button(),
        parse_mode="Markdown"
    )


# ---------- HANDLE PDF MESSAGE ----------

def handle_pdf(bot, message: Message):
    user_id = message.from_user.id
    session = get_session(user_id)

    if not session:
        bot.send_message(message.chat.id, text.SESSION_EXPIRED)
        return

    doc = message.document

    if not doc or not doc.mime_type or not doc.mime_type.endswith("pdf"):
        bot.send_message(message.chat.id, text.UPLOAD_INVALID_FILE, parse_mode="Markdown")
        return

    # Optional: check duplicate by file_unique_id
    if database.pdf_exists(doc.file_unique_id):
        bot.send_message(message.chat.id, text.UPLOAD_ALREADY_EXISTS)
        end_session(user_id)
        database.set_status(user_id, "menu:home")
        return

    # Store temporarily
    update_session(user_id, "pdf_temp", {
        "file_id": doc.file_id,
        "unique_id": doc.file_unique_id,
        "name": doc.file_name
    })

    database.set_status(user_id, "upload:subject")

    bot.send_message(
        message.chat.id,
        text.UPLOAD_SUBJECT,
        reply_markup=buttons.subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )


# ---------- CALLBACK HANDLER ----------

def handle_callback(bot, call: CallbackQuery):
    user_id = call.from_user.id
    data = call.data
    session = get_session(user_id)

    if not session:
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # ----- SUBJECT SELECT -----
    if data.startswith("upload_subject:"):
        subject = data.split(":", 1)[1]

        update_session(user_id, "subject", subject)
        database.set_status(user_id, "upload:tags")

        bot.edit_message_text(
            text.UPLOAD_TAGS,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.tag_buttons(TAGS, []),
            parse_mode="Markdown"
        )
        return

    # ----- TAG TOGGLE -----
    if data.startswith("upload_tag:"):
        tag = data.split(":", 1)[1]
        tags = session["tags"]

        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)

        update_session(user_id, "tags", tags)

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.tag_buttons(TAGS, tags)
        )
        return

    # ----- FINAL UPLOAD -----
    if data == "upload_done":
        try:
            _finalize_upload(bot, call)
        except Exception:
            bot.send_message(call.message.chat.id, text.UPLOAD_FAILED)
        return

    # ----- CANCEL -----
    if data == "upload_cancel":
        end_session(user_id)
        database.set_status(user_id, "menu:home")

        bot.edit_message_text(
            text.CANCELLED,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.main_menu(),
            parse_mode="Markdown"
        )


# ---------- FINALIZE ----------

def _finalize_upload(bot, call: CallbackQuery):
    user_id = call.from_user.id
    session = get_session(user_id)

    if not session or not session.get("pdf_temp") or not session.get("subject"):
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    pdf = session["pdf_temp"]

    pdf_id = database.insert_pdf(
        uploader_id=user_id,
        file_id=pdf["file_id"],
        unique_id=pdf["unique_id"],
        subject=session["subject"]
    )

    for tag in session["tags"]:
        database.insert_pdf_tag(pdf_id, tag)

    end_session(user_id)
    database.set_status(user_id, "menu:home")

    bot.edit_message_text(
        text.UPLOAD_SUCCESS,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )