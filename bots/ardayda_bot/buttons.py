# bots/ardayda_bot/buttons.py

from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ---------- MAIN MENU (HOME ONLY) ----------

def main_menu():
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
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(
        KeyboardButton("❌ Cancel")
    )
    return markup


# ---------- SUBJECT SELECTION (INLINE) ----------

def subject_buttons(subjects):
    """
    subjects: list[str]
    """
    markup = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton(
            text=f"📘 {subject}",
            callback_data=f"upload_subject:{subject}"
        )
        for subject in subjects
    ]

    markup.add(*buttons)
    return markup


# ---------- TAG SELECTION (MULTI-SELECT INLINE) ----------

def tag_buttons(tags, selected_tags):
    """
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
                callback_data=f"upload_tag:{tag}"
            )
        )

    markup.row(
        InlineKeyboardButton("⬆️ Upload PDF", callback_data="upload_done"),
        InlineKeyboardButton("❌ Cancel", callback_data="upload_cancel")
    )

    return markup


# ---------- SEARCH TAG SELECTION ----------

def search_tag_buttons(tags, selected_tags):
    markup = InlineKeyboardMarkup(row_width=3)

    for tag in tags:
        is_selected = tag in selected_tags
        text = f"🔎 {tag}" if is_selected else f"🏷️ {tag}"

        markup.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"search_tag:{tag}"
            )
        )

    markup.row(
        InlineKeyboardButton("🔍 Search", callback_data="search_done"),
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )

    return markup


# ---------- PAGINATION BUTTONS ----------

def pagination_buttons(page, total_pages):
    markup = InlineKeyboardMarkup(row_width=3)

    if page > 1:
        markup.add(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{page-1}")
        )

    markup.add(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        markup.add(
            InlineKeyboardButton("➡️ Next", callback_data=f"pdf_page:{page+1}")
        )

    markup.row(
        InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")
    )

    return markup