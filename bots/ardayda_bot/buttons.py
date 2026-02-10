# bots/ardayda_bot/buttons.py
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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


class Buttons:
    """All bot buttons organized in class structure"""

    # ---------------- Main Menu ----------------
    class MainMenu:
        SEARCH = "🔍 Search PDFs"
        UPLOAD = "📤 Upload PDF"
        PROFILE = "👤 My Profile"
        SETTINGS = "⚙️ Settings"

        @staticmethod
        def keyboard():
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(Buttons.MainMenu.SEARCH), KeyboardButton(Buttons.MainMenu.UPLOAD))
            kb.add(KeyboardButton(Buttons.MainMenu.PROFILE), KeyboardButton(Buttons.MainMenu.SETTINGS))
            return kb

    # ---------------- Settings Submenu ----------------
    class Settings:
        NOTIFICATIONS = "🔔 Notifications"
        LANGUAGE = "🌐 Language"
        BACK = "⬅️ Back"

        @staticmethod
        def keyboard():
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(Buttons.Settings.NOTIFICATIONS))
            kb.add(KeyboardButton(Buttons.Settings.LANGUAGE))
            kb.add(KeyboardButton(Buttons.Settings.BACK))
            return kb

    # ---------------- Profile Submenu ----------------
    class Profile:
        VIEW = "👁️ View Profile"
        EDIT = "✏️ Edit Profile"
        BACK = "⬅️ Back"

        @staticmethod
        def keyboard():
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(Buttons.Profile.VIEW), KeyboardButton(Buttons.Profile.EDIT))
            kb.add(KeyboardButton(Buttons.Profile.BACK))
            return kb