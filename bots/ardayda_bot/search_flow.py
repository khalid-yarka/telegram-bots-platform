# bots/ardayda_bot/search_flow.py

from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bots.ardayda_bot import database, buttons, text

# Example static data (can come from DB later)
SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
TAGS = ["Exam", "Notes", "Lecture", "Assignment", "Revision"]

RESULTS_PER_PAGE = 5


# ---------- START SEARCH ----------
def start(bot, message: Message):
    """Initialize search flow"""
    user_id = message.from_user.id
    
    # Clear any previous search temp data
    database.clear_search_temp(user_id)
    
    # Status already set to search:subject by handlers.py

    bot.send_message(
        message.chat.id,
        text.SEARCH_START,
        reply_markup=buttons.subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )


# ---------- CALLBACK HANDLER ----------
def handle_callback(bot, call: CallbackQuery):
    """Handle search flow callbacks"""
    user_id = call.from_user.id
    data = call.data
    status = database.get_user_status(user_id)

    if not status or not status.startswith("search:"):
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # ----- SUBJECT SELECT -----
    if status == database.STATUS_SEARCH_SUBJECT and data.startswith("search_subject:"):
        subject = data.split(":", 1)[1]
        
        # Save subject to database
        database.save_search_temp(user_id, subject, "")
        
        # Move to tags selection
        database.set_status(user_id, database.STATUS_SEARCH_TAGS)
        
        # Get current tags (empty initially)
        search_data = database.get_search_temp(user_id)
        current_tags = search_data.get("tags", []) if search_data else []

        bot.edit_message_text(
            "🏷️ *Select optional tags for this subject*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buttons.search_tag_buttons(TAGS, current_tags),
            parse_mode="Markdown"
        )
        return

    # ----- TAG TOGGLE -----
    if status == database.STATUS_SEARCH_TAGS and data.startswith("search_tag:"):
        tag = data.split(":", 1)[1]
        
        # Get current search data
        search_data = database.get_search_temp(user_id)
        if not search_data:
            bot.answer_callback_query(call.id, "Session expired. Please start over.")
            return
            
        current_tags = search_data.get("tags", [])
        
        # Toggle tag
        if tag in current_tags:
            current_tags.remove(tag)
        else:
            current_tags.append(tag)
        
        # Save updated tags
        tags_string = ",".join(current_tags)
        database.save_search_temp(
            user_id, 
            search_data.get("subject"), 
            tags_string,
            search_data.get("page", 1)
        )

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=buttons.search_tag_buttons(TAGS, current_tags)
        )
        return

    # ----- FINAL SEARCH / SKIP -----
    if data in ["search_done", "search_skip"]:
        search_data = database.get_search_temp(user_id)
        if not search_data or not search_data.get("subject"):
            bot.answer_callback_query(call.id, "No subject selected. Please start over.")
            return
            
        subject = search_data.get("subject")
        tags = search_data.get("tags", [])
        
        # Perform search
        results = database.search_pdfs(subject, tags)
        
        # Store results in a way we can paginate
        # For now, we'll use the page field and assume we can search again if needed
        database.save_search_temp(
            user_id,
            subject,
            ",".join(tags),
            1  # Start at page 1
        )
        
        # Store results in a temporary place - we'll need to add this to database
        # For now, we'll just use the results directly and re-search if paginating
        _send_results(bot, call.message.chat.id, user_id, subject, tags, results, 1, call.message.message_id)
        return

    # ----- PAGINATION -----
    if data.startswith("pdf_page:"):
        page = int(data.split(":", 1)[1])
        
        search_data = database.get_search_temp(user_id)
        if not search_data:
            bot.answer_callback_query(call.id, "Session expired. Please start over.")
            return
            
        subject = search_data.get("subject")
        tags = search_data.get("tags", [])
        
        # Re-search to get fresh results
        results = database.search_pdfs(subject, tags)
        
        # Update page in database
        database.save_search_temp(
            user_id,
            subject,
            ",".join(tags),
            page
        )
        
        _send_results(bot, call.message.chat.id, user_id, subject, tags, results, page, call.message.message_id)
        return

    # ----- PDF SEND -----
    if data.startswith("pdf_send:"):
        pdf_id = int(data.split(":", 1)[1])
        pdf = database.get_pdf_by_id(pdf_id)

        if not pdf:
            bot.answer_callback_query(call.id, "❌ PDF not found.")
            return

        # Get tags for caption
        tags = database.get_pdf_tags(pdf_id)
        tags_text = f"\nTags: {', '.join(tags)}" if tags else ""
        
        caption = f"📄 *{pdf['name']}*\nSubject: {pdf['subject']}{tags_text}"
        
        bot.send_document(
            call.message.chat.id, 
            pdf['file_id'], 
            caption=caption,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "✅ PDF sent")
        return

    # ----- CANCEL -----
    if data == "search_cancel":
        # Clear search data and reset to main menu
        database.clear_search_temp(user_id)
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
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
def _send_results(bot, chat_id, user_id, subject, tags, results, page, message_id=None):
    """Display search results with pagination"""
    
    if not results:
        # Clear search data and reset
        database.clear_search_temp(user_id)
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
        bot.send_message(
            chat_id, 
            f"😕 No PDFs found for {subject}.",
            reply_markup=buttons.main_menu()
        )
        return

    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_results = results[start:end]

    tags_text = f" with tags: {', '.join(tags)}" if tags else ""
    text_msg = f"📚 *Search Results for {subject}*{tags_text}\nPage {page} of {total_pages}\n\nChoose a document to receive:"

    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add PDF buttons
    for pdf in page_results:
        markup.add(
            InlineKeyboardButton(
                f"📄 {pdf['name']}",
                callback_data=f"pdf_send:{pdf['id']}"
            )
        )

    # Pagination row
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{page-1}")
        )
    
    pagination_buttons.append(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data=f"pdf_page:{page+1}")
        )
    
    markup.row(*pagination_buttons)
    
    # Cancel button
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