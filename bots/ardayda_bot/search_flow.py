# bots/ardayda_bot/search_flow.py

from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bots.ardayda_bot import database, buttons, text
from bots.ardayda_bot.cache import temp_cache
from bots.ardayda_bot.helpers import safe_edit_message
import logging

logger = logging.getLogger(__name__)

SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "ICT", "Arabic", "Islamic", "English", "Somali", "G.P", "Geography", "History", "Agriculture", "Business"]
TAGS = ["Exam", "Notes", "Summary", "Assignment", "Chapter Reviews", "Revision", "Past Papers", "Exercises"]

RESULTS_PER_PAGE = 5


def start(bot, message: Message):
    """Initialize search flow"""
    user_id = message.from_user.id
    
    # Clear any previous search temp data from cache
    temp_cache.delete(f"search:{user_id}")
    
    bot.send_message(
        message.chat.id,
        text.SEARCH_START,
        reply_markup=buttons.search_subject_buttons(SUBJECTS),
        parse_mode="Markdown"
    )
    
    logger.info(f"User {user_id} started search flow")


def handle_callback(bot, call: CallbackQuery):
    """Handle search flow callbacks"""
    user_id = call.from_user.id
    data = call.data
    status = database.get_user_status(user_id)

    logger.debug(f"Search callback - User: {user_id}, Data: {data}, Status: {status}")

    if not status or not status.startswith("search:"):
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # Get search data from cache
    search_data = temp_cache.get(f"search:{user_id}")
    if search_data is None:
        search_data = {}
    
    logger.debug(f"Search data for user {user_id}: {search_data}")

    # ----- SUBJECT SELECT -----
    if status == database.STATUS_SEARCH_SUBJECT and data.startswith("search_subject:"):
        subject = data.split(":", 1)[1]
        
        # Save subject to cache
        search_data = {
            'subject': subject,
            'tags': [],
            'page': 1,
            'results': None
        }
        temp_cache.set(f"search:{user_id}", search_data, ttl=1800)
        
        # Move to tags selection
        database.set_status(user_id, database.STATUS_SEARCH_TAGS)
        
        current_tags = search_data.get("tags", [])

        # Edit message to show tags
        try:
            bot.edit_message_text(
                "🏷️ *Select optional tags for this subject*\n\nYou can select multiple tags or click 'Skip Tags':",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=buttons.search_tag_buttons(TAGS, current_tags),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Could not edit message: {e}")
            bot.send_message(
                call.message.chat.id,
                "🏷️ *Select optional tags for this subject*\n\nYou can select multiple tags or click 'Skip Tags':",
                reply_markup=buttons.search_tag_buttons(TAGS, current_tags),
                parse_mode="Markdown"
            )
        
        logger.info(f"User {user_id} selected subject: {subject}")
        bot.answer_callback_query(call.id)
        return

    # ----- TAG TOGGLE -----
    if status == database.STATUS_SEARCH_TAGS and data.startswith("search_tag:"):
        tag = data.split(":", 1)[1]
        
        if not search_data:
            bot.answer_callback_query(call.id, "Session expired. Please start over.")
            return
            
        current_tags = search_data.get("tags", [])
        
        # Toggle tag
        if tag in current_tags:
            current_tags.remove(tag)
            action = "removed"
        else:
            current_tags.append(tag)
            action = "added"
        
        # Update in cache
        search_data['tags'] = current_tags
        temp_cache.set(f"search:{user_id}", search_data)

        # Update only the keyboard
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=buttons.search_tag_buttons(TAGS, current_tags)
            )
        except Exception as e:
            logger.warning(f"Could not edit keyboard: {e}")
        
        logger.debug(f"User {user_id} {action} tag: {tag}")
        bot.answer_callback_query(call.id)
        return

    # ----- FINAL SEARCH -----
    if data == "search_done":
        if not search_data or not search_data.get("subject"):
            bot.answer_callback_query(call.id, "No subject selected. Please start over.")
            return
            
        subject = search_data.get("subject")
        tags = search_data.get("tags", [])
        
        logger.info(f"User {user_id} searching: subject={subject}, tags={tags}")
        
        # Show loading message
        try:
            bot.edit_message_text(
                "🔍 Searching for PDFs...",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        except:
            bot.send_message(
                call.message.chat.id,
                "🔍 Searching for PDFs..."
            )
        
        # Perform search
        results = database.search_pdfs(subject, tags)
        
        logger.info(f"Search found {len(results)} results for user {user_id}")
        
        # Update in cache
        search_data['page'] = 1
        search_data['results'] = results
        temp_cache.set(f"search:{user_id}", search_data)
        
        # Send results
        _send_results(bot, call.message.chat.id, user_id, subject, tags, results, 1, call.message.message_id)
        
        bot.answer_callback_query(call.id)
        return

    # ----- SKIP TAGS -----
    if data == "search_skip":
        if not search_data or not search_data.get("subject"):
            bot.answer_callback_query(call.id, "No subject selected. Please start over.")
            return
            
        subject = search_data.get("subject")
        tags = []
        
        logger.info(f"User {user_id} searching (skip tags): subject={subject}")
        
        # Show loading message
        try:
            bot.edit_message_text(
                "🔍 Searching for PDFs...",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        except:
            bot.send_message(
                call.message.chat.id,
                "🔍 Searching for PDFs..."
            )
        
        # Perform search with no tags
        results = database.search_pdfs(subject, [])
        
        logger.info(f"Search found {len(results)} results for user {user_id}")
        
        # Update in cache
        search_data['tags'] = []
        search_data['page'] = 1
        search_data['results'] = results
        temp_cache.set(f"search:{user_id}", search_data)
        
        # Send results
        _send_results(bot, call.message.chat.id, user_id, subject, [], results, 1, call.message.message_id)
        
        bot.answer_callback_query(call.id)
        return

    # ----- PAGINATION -----
    if data.startswith("pdf_page:"):
        page = int(data.split(":", 1)[1])
        
        if not search_data:
            bot.answer_callback_query(call.id, "Session expired. Please start over.")
            return
            
        subject = search_data.get("subject")
        tags = search_data.get("tags", [])
        
        # Get results from cache or search again
        results = search_data.get('results')
        if not results:
            results = database.search_pdfs(subject, tags)
        
        # Update page in cache
        search_data['page'] = page
        search_data['results'] = results
        temp_cache.set(f"search:{user_id}", search_data)
        
        _send_results(bot, call.message.chat.id, user_id, subject, tags, results, page, call.message.message_id)
        
        bot.answer_callback_query(call.id)
        return

    # ----- PDF SEND -----
    if data.startswith("pdf_send:"):
        try:
            pdf_id = int(data.split(":", 1)[1])
            pdf = database.get_pdf_by_id(pdf_id)

            if not pdf:
                bot.answer_callback_query(call.id, "❌ PDF not found.")
                return

            # Get tags for caption
            tags = database.get_pdf_tags(pdf_id)
            tags_text = f"\n🏷️ Tags: {', '.join(tags)}" if tags else ""
            
            caption = (
                f"📄 *{pdf['name']}*\n"
                f"📚 Subject: {pdf['subject']}"
                f"{tags_text}"
            )
            
            bot.send_document(
                call.message.chat.id, 
                pdf['file_id'], 
                caption=caption,
                parse_mode="Markdown"
            )
            
            logger.info(f"User {user_id} downloaded PDF ID: {pdf_id}")
            bot.answer_callback_query(call.id, "✅ PDF sent successfully!")
            
        except Exception as e:
            logger.error(f"Error sending PDF: {e}")
            bot.answer_callback_query(call.id, "❌ Error sending PDF")
        return

    # ----- CANCEL -----
    if data == "search_cancel":
        logger.info(f"User {user_id} cancelled search")
        temp_cache.delete(f"search:{user_id}")
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
        try:
            bot.edit_message_text(
                text.CANCELLED,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=buttons.main_menu(user_id),
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                call.message.chat.id,
                text.CANCELLED,
                reply_markup=buttons.main_menu(user_id),
                parse_mode="Markdown"
            )
        
        bot.answer_callback_query(call.id)
        return

    # ----- NOOP -----
    if data == "noop":
        bot.answer_callback_query(call.id)
        return

    # ----- STALE BUTTON -----
    logger.warning(f"Stale button clicked by user {user_id}: {data}")
    bot.answer_callback_query(call.id, "❌ This action is no longer available. Please start over.")


def _send_results(bot, chat_id, user_id, subject, tags, results, page, message_id=None):
    """Display search results with pagination"""
    
    if not results:
        temp_cache.delete(f"search:{user_id}")
        database.set_status(user_id, database.STATUS_MENU_HOME)
        
        tags_text = f" with tags: {', '.join(tags)}" if tags else ""
        no_results_msg = (
            f"😕 *No PDFs Found*\n\n"
            f"No PDFs found for {subject}{tags_text}.\n\n"
            f"Try different tags or subject, or upload some PDFs!"
        )
        
        if message_id:
            try:
                bot.edit_message_text(
                    text=no_results_msg,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=buttons.main_menu(user_id),
                    parse_mode="Markdown"
                )
            except:
                bot.send_message(
                    chat_id,
                    no_results_msg,
                    reply_markup=buttons.main_menu(user_id),
                    parse_mode="Markdown"
                )
        else:
            bot.send_message(
                chat_id,
                no_results_msg,
                reply_markup=buttons.main_menu(user_id),
                parse_mode="Markdown"
            )
        return

    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start = (page - 1) * RESULTS_PER_PAGE
    end = min(start + RESULTS_PER_PAGE, len(results))
    page_results = results[start:end]

    tags_text = f" with tags: {', '.join(tags)}" if tags else ""
    
    if page > total_pages:
        page = total_pages
    
    text_msg = (
        f"📚 *Search Results*\n\n"
        f"📖 Subject: *{subject}*\n"
        f"{tags_text}\n"
        f"📄 Found: *{len(results)}* PDFs\n"
        f"📑 Page *{page}* of *{total_pages}*\n\n"
        f"Choose a document to download:"
    )

    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add PDF buttons
    for pdf in page_results:
        display_name = pdf['name']
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."
            
        markup.add(
            InlineKeyboardButton(
                f"📄 {display_name}",
                callback_data=f"pdf_send:{pdf['id']}"
            )
        )

    # Pagination row
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"pdf_page:{page-1}")
        )
    
    pagination_buttons.append(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"pdf_page:{page+1}")
        )
    
    if pagination_buttons:
        markup.row(*pagination_buttons)
    
    # Cancel/New Search button
    markup.row(
        InlineKeyboardButton("🔍 New Search", callback_data="search_cancel"),
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )

    try:
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
    except Exception as e:
        logger.error(f"Error sending results: {e}")
        if message_id:
            bot.send_message(
                chat_id,
                text=text_msg,
                reply_markup=markup,
                parse_mode="Markdown"
            )