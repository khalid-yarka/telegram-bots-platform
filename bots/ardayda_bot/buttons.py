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

def region_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for r in ["North","South","East","West"]: kb.add(r)
    kb.add(BACK)
    return kb

def school_menu(region):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    schools = {"North":["S1","S2"],"South":["S3","S4"]}.get(region,[])
    for s in schools: kb.add(s)
    kb.add(BACK)
    return kb

def class_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("F1","F2","F3","F4")
    kb.add(BACK)
    return kb

def search_tags_menu(selected_tags=None):
    selected_tags = selected_tags or []
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for tag in PDF_TAGS:
        mark = "✓" if tag in selected_tags else "×"
        buttons.append(InlineKeyboardButton(f"{mark} {tag}", callback_data=f"tag:{tag}"))
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("🔍 Find PDFs", callback_data="find_pdfs"))
    kb.add(InlineKeyboardButton(BACK, callback_data="cancel_search"))
    return kb

def pdf_like_menu(pdf_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❤️ Like", callback_data=f"like:{pdf_id}"))
    return kb