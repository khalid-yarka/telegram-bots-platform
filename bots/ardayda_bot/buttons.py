# bots/ardayda_bot/buttons.py

from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ---------- MAIN MENU (HOME ONLY) ----------

def main_menu():
    """Main menu with upload, search, and profile options"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("📤 Upload"),
        KeyboardButton("🔍 Search")
    )
    markup.row(
        KeyboardButton("👤 Profile")
    )
    return markup


# ---------- CANCEL (ONLY DURING OPERATIONS) ----------

def cancel_button():
    """Simple cancel button for ongoing operations"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(
        KeyboardButton("❌ Cancel")
    )
    return markup


# ---------- SUBJECT SELECTION (INLINE) ----------

def subject_buttons(subjects):
    """
    Show subjects as inline buttons
    subjects: list[str]
    """
    markup = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton(
            text=f"📘 {subject}",
            callback_data=f"upload_subject:{subject}"  # Note: upload_subject prefix
        )
        for subject in subjects
    ]

    markup.add(*buttons)
    return markup


# ---------- TAG SELECTION (MULTI-SELECT INLINE) ----------

def tag_buttons(tags, selected_tags):
    """
    Show tags with checkmarks for selected ones
    tags: list[str]
    selected_tags: list[str]
    """
    markup = InlineKeyboardMarkup(row_width=3)

    for tag in tags:
        is_selected = tag in selected_tags
        text = f"✅ {tag}" if is_selected else f"🏷️ {tag}"

        markup.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"upload_tag:{tag}"  # Note: upload_tag prefix
            )
        )

    # Add action buttons
    markup.row(
        InlineKeyboardButton("⬆️ Upload PDF", callback_data="upload_done"),
        InlineKeyboardButton("❌ Cancel", callback_data="upload_cancel")
    )

    return markup


# ---------- SEARCH SUBJECT BUTTONS ----------

def search_subject_buttons(subjects):
    """
    Show subjects for search flow
    subjects: list[str]
    """
    markup = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton(
            text=f"🔍 {subject}",
            callback_data=f"search_subject:{subject}"  # Note: search_subject prefix
        )
        for subject in subjects
    ]

    markup.add(*buttons)
    return markup


# ---------- SEARCH TAG SELECTION ----------

def search_tag_buttons(tags, selected_tags):
    """
    Show tags for search with selection indicators
    tags: list[str]
    selected_tags: list[str]
    """
    markup = InlineKeyboardMarkup(row_width=3)

    for tag in tags:
        is_selected = tag in selected_tags
        text = f"✅ {tag}" if is_selected else f"🏷️ {tag}"

        markup.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"search_tag:{tag}"  # Note: search_tag prefix
            )
        )

    # Add action buttons
    markup.row(
        InlineKeyboardButton("🔍 Search", callback_data="search_done"),
        InlineKeyboardButton("⏭️ Skip Tags", callback_data="search_skip"),
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )

    return markup

# ---------- SEARCH ACTION BUTTONS ----------
def search_action_buttons():
    """Action buttons for search results"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton("🔍 New Search", callback_data="search_cancel"),
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )
    return markup

# ---------- PAGINATION BUTTONS (FOR SEARCH RESULTS) ----------

def pagination_buttons(current_page, total_pages):
    """
    Create pagination controls for search results
    current_page: int
    total_pages: int
    """
    markup = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    
    # Previous button
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{current_page-1}")
        )
    else:
        buttons.append(
            InlineKeyboardButton("⬅️", callback_data="noop")
        )
    
    # Page indicator
    buttons.append(
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop")
    )
    
    # Next button
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data=f"pdf_page:{current_page+1}")
        )
    else:
        buttons.append(
            InlineKeyboardButton("➡️", callback_data="noop")
        )
    
    markup.row(*buttons)
    
    # Cancel button
    markup.row(
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )
    
    return markup


# ---------- PDF RESULT BUTTONS (FOR SEARCH RESULTS) ----------

def pdf_result_buttons(pdfs, current_page, total_pages):
    """
    Create complete result page with PDF buttons and pagination
    pdfs: list of pdf dicts with 'id' and 'name'
    current_page: int
    total_pages: int
    """
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add PDF buttons
    for pdf in pdfs:
        markup.add(
            InlineKeyboardButton(
                text=f"📄 {pdf['name']}",
                callback_data=f"pdf_send:{pdf['id']}"
            )
        )
    
    # Add pagination
    pagination_buttons = []
    
    if current_page > 1:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{current_page-1}")
        )
    
    pagination_buttons.append(
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop")
    )
    
    if current_page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data=f"pdf_page:{current_page+1}")
        )
    
    if pagination_buttons:
        markup.row(*pagination_buttons)
    
    # Add cancel button
    markup.row(
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )
    
    return markup


# ---------- NOOP BUTTON (PLACEHOLDER) ----------

def noop_button(text="⚫"):
    """
    Create a non-functional button for placeholders
    """
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text, callback_data="noop")
    )
    return markup