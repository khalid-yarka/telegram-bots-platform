# bots/ardayda_bot/search_flow.py

from telebot.types import Message, CallbackQuery
from bots.ardayda_bot import database, buttons, text
from bots.ardayda_bot.session_manager import get_session, update_session, end_session

# Example static subjects/tags (can load from DB)
SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
TAGS = ["Exam", "Notes", "Lecture", "Assignment", "Revision"]

RESULTS_PER_PAGE = 5  # change as needed


# ---------- START SEARCH ----------
def start(bot, message: Message):
    user_id = message.from_user.id
    update_session(user_id, "tags", [])
    update_session(user_id, "page", 1)
    update_session(user_id, "subject", None)
    update_session(user_id, "status", "search_subject")

    bot.send_message(
        message.chat.id,
        text.SEARCH_START,
        reply_markup=buttons.subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )


# ---------- CALLBACK HANDLER ----------
def handle_callback(bot, call: CallbackQuery):
    user_id = call.from_user.id
    session = get_session(user_id)

    if not session:
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    data = call.data

    # ----- SUBJECT SELECT -----
    if session["status"] == "search_subject" and data.startswith("search_subject:"):
        subject = data.split(":", 1)[1]
        update_session(user_id, "subject", subject)
        update_session(user_id, "status", "search_tags")

        bot.edit_message_text(
            text="🏷️ *Select optional tags for this subject*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buttons.search_tag_buttons(TAGS, []),
            parse_mode="Markdown"
        )
        return

    # ----- TAG TOGGLE -----
    if session["status"] == "search_tags" and data.startswith("search_tag:"):
        tag = data.split(":", 1)[1]
        tags = session.get("tags", [])

        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)

        update_session(user_id, "tags", tags)

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buttons.search_tag_buttons(TAGS, tags)
        )
        return

    # ----- FINAL SEARCH -----
    if data in ["search_done", "search_skip"]:
        subject = session.get("subject")
        tags = session.get("tags", [])

        results = database.search_pdfs(subject, tags)
        update_session(user_id, "results", results)
        update_session(user_id, "page", 1)
        update_session(user_id, "status", "search_results")

        send_results(bot, call.message.chat.id, user_id)
        return

    # ----- PAGINATION -----
    if data.startswith("pdf_page:"):
        page = int(data.split(":", 1)[1])
        update_session(user_id, "page", page)
        send_results(bot, call.message.chat.id, user_id, call.message.message_id)
        return

    # ----- PDF SEND -----
    if data.startswith("pdf_send:"):
        pdf_id = int(data.split(":", 1)[1])
        pdf = database.get_pdf_by_id(pdf_id)

        if not pdf:
            bot.answer_callback_query(call.id, "❌ PDF not found.")
            return

        caption = f"📄 {pdf['name']}\nSubject: {pdf['subject']}\nTags: {', '.join(database.get_pdf_tags(pdf_id))}"
        bot.send_document(call.message.chat.id, pdf['file_id'], caption=caption)
        bot.answer_callback_query(call.id, "✅ PDF sent")
        return

    # ----- CANCEL -----
    if data == "search_cancel":
        end_session(user_id)
        database.set_status(user_id, "menu:home")
        bot.edit_message_text(
            text.CANCELLED,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buttons.main_menu(),
            parse_mode="Markdown"
        )
        return

    # ----- STALE BUTTON -----
    bot.answer_callback_query(call.id, "❌ This action is no longer available.")


# ---------- SEND RESULTS WITH PAGINATION ----------
def send_results(bot, chat_id, user_id, message_id=None):
    session = get_session(user_id)
    results = session.get("results", [])
    page = session.get("page", 1)
    subject = session.get("subject")

    if not results:
        bot.send_message(chat_id, f"😕 No PDFs found for {subject}.")
        return

    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_results = results[start:end]

    text_msg = f"📚 *Search Results ({subject})*\nPage {page} of {total_pages}\nChoose a document to receive:"

    markup = InlineKeyboardMarkup(row_width=1)
    for pdf in page_results:
        markup.add(
            InlineKeyboardButton(
                f"📄 {pdf['name']}",
                callback_data=f"pdf_send:{pdf['id']}"
            )
        )

    # Pagination buttons
    markup.row(
        InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{page-1}") if page > 1 else None,
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton("➡️ Next", callback_data=f"pdf_page:{page+1}") if page < total_pages else None
    )

    markup.row(
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )

    if message_id:
        bot.edit_message_text(
            text=text_msg,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            chat_id,
            text=text_msg,
            reply_markup=markup,
            parse_mode="Markdown"
        )