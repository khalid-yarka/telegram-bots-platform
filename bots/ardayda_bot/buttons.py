from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class Main:
    SEARCH = "🔍 Search PDFs"
    UPLOAD = "📄 Upload PDF"
    PROFILE = "👤 My Profile"
    SETTINGS = "⚙️ Settings"


def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(Main.SEARCH, Main.UPLOAD)
    kb.row(Main.PROFILE, Main.SETTINGS)
    return kb


def region_menu(regions):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for r in regions:
        kb.add(KeyboardButton(r))
    return kb


def school_menu(schools):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for s in schools:
        kb.add(KeyboardButton(s))
    return kb


def class_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for c in ["F1", "F2", "F3", "F4"]:
        kb.add(KeyboardButton(c))
    return kb