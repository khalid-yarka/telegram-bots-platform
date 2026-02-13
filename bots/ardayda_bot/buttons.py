from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from bots.ardayda_bot import text

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
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,row_width=2)
    for r in text.form_four_schools_by_region.keys():
        kb.add(r)
    return kb
    

def school_menu(region):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    schools = text.form_four_schools_by_region[region]
    for i in range(0, len(schools), 2):
        kb.add(*schools[i:i+2])
    return kb


def class_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,row_width=4)
    for c in ["F1", "F2", "F3", "F4"]:
        kb.add(KeyboardButton(c))
    return kb