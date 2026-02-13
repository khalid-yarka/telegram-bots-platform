from telebot.types import ReplyKeyboardMarkup

BACK = "⬅️ Back"


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


def region_menu():
    from bots.ardayda_bot import text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for r in text.form_four_schools_by_region.keys():
        kb.add(r)
    kb.add(BACK)
    return kb


def school_menu(region):
    from bots.ardayda_bot import text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    schools = text.form_four_schools_by_region[region]
    for i in range(0, len(schools), 2):
        kb.add(*schools[i:i + 2])
    kb.add(BACK)
    return kb


def class_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("F1", "F2", "F3", "F4")
    kb.add(BACK)
    return kb