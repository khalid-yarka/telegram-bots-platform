import telebot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove, InputTextMessageContent, InlineQueryResultArticle
)

# ===== Main Menu Keyboard =====
def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    # 🔍 Searching and 📄 Uploading PDFs
    kb.add(
        KeyboardButton("🔍 Searching PDFs"),
        KeyboardButton("📄 Upload PDF")
    )

    # 👤 Profile and ⚙️ Settings
    kb.add(
        KeyboardButton("👤 My Profile"),
        KeyboardButton("⚙️ Settings")
    )

    return kb

# ===== INLINE KEYBOARD =====
def inline_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("URL Button 🌐", url="https://www.google.com"),
        InlineKeyboardButton("Callback Hello", callback_data="hello")
    )
    kb.add(
        InlineKeyboardButton("Switch Inline Query", switch_inline_query="search query")
    )
    kb.add(
        InlineKeyboardButton("Switch Inline Current Chat", switch_inline_query_current_chat="search here")
    )
    return kb