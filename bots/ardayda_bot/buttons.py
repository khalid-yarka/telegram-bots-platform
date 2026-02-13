from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

BACK = "⬅️ Back"
UPLOAD = "📄 Upload PDF"
SEARCH = "🔍 Search PDFs"
PROFILE = "👤 My Profile"
SETTINGS = "⚙️ Settings"

PDF_TAGS = ["bio","phy","his","math","chem"]

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(SEARCH, UPLOAD)
    kb.row(PROFILE, SETTINGS)
    return kb

def tag_inline_menu(selected_tags=None, confirm_button=True):
    selected_tags = selected_tags or []
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for tag in PDF_TAGS:
        mark = "✓" if tag in selected_tags else "×"
        buttons.append(InlineKeyboardButton(f"{mark} {tag}", callback_data=f"tag:{tag}"))
    kb.add(*buttons)
    if confirm_button:
        kb.add(InlineKeyboardButton("✅ Done", callback_data="tag_done"))
    kb.add(InlineKeyboardButton(BACK, callback_data="cancel"))
    return kb

def pdf_like_menu(pdf_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❤️ Like", callback_data=f"like:{pdf_id}"))
    return kb