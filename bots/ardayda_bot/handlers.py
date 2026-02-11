# bots/ardayda_bot/handlers.py
import telebot
from telebot.types import Message

from bots.ardayda_bot import database, buttons, text

# ----------- in-memory registration state -----------
_user_steps = {}

# ----------- helpers -----------

def is_registering(user_id: int) -> bool:
    return user_id in _user_steps

def start(bot, message):
    user_id = message.from_user.id

    # Fetch user from database
    user = database.get_user(user_id)

    # If user exists and has all required fields → skip registration
    if user and user.get("name") and user.get("school") and user.get("class_"):
        # Fully registered
        if user_id in _user_steps:
            _user_steps.pop(user_id)  # remove any leftover step
        bot.send_message(
            message.chat.id,
            "👋 Welcome back! Choose an option:",
            reply_markup=buttons.Buttons.MainMenu.keyboard()
        )
        return

    # Otherwise, start registration flow
    if user_id not in _user_steps:
        _user_steps[user_id] = {"step": "name"}

    # Make sure user exists in DB (adds row if not exists)
    database.add_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 Welcome!\n\nPlease enter your *full name*:",
        parse_mode="Markdown"
    )


def settings(bot, message: Message):
    bot.send_message(
        message.chat.id,
        "⚙️ Settings",
        reply_markup=buttons.Buttons.Settings.keyboard()
    )


def main_menu(bot, message: Message):
    bot.send_message(
        message.chat.id,
        "Choose an option:",
        reply_markup=buttons.Buttons.MainMenu.keyboard()
    )


# ----------- registration flow -----------

def registration(bot: telebot.TeleBot, message: Message):
    user_id = message.from_user.id
    step = _user_steps[user_id]["step"]
    text_msg = message.text.strip()

    # -------- NAME --------
    if step == "name":
        if len(text_msg.split()) < 2:
            bot.send_message(message.chat.id, "❌ Please enter your full name (at least 2 words).")
            return

        _user_steps[user_id]["name"] = text_msg
        _user_steps[user_id]["step"] = "region"
        ask_region(bot, message)
        return

    # -------- REGION --------
    if step == "region":
        region = text_msg.upper()
        if region not in text.form_four_schools_by_region:
            bot.send_message(message.chat.id, "❌ Select a region from the keyboard.")
            ask_region(bot, message)
            return

        _user_steps[user_id]["region"] = region
        _user_steps[user_id]["step"] = "school"
        ask_school(bot, message, region)
        return

    # -------- SCHOOL --------
    if step == "school":
        region = _user_steps[user_id]["region"]
        if text_msg not in text.form_four_schools_by_region[region]:
            bot.send_message(message.chat.id, "❌ Select a valid school from the keyboard.")
            ask_school(bot, message, region)
            return

        _user_steps[user_id]["school"] = text_msg
        _user_steps[user_id]["step"] = "class"
        ask_class(bot, message)
        return

    # -------- CLASS --------
    if step == "class":
        if text_msg.upper() not in ["F1", "F2", "F3", "F4"]:
            bot.send_message(message.chat.id, "❌ Use F1, F2, F3, or F4.")
            ask_class(bot, message)
            return
        
        #data = _user_steps.pop(user_id)
        
        #bot.reply_to(message, data[user_id])
        
        # Save to DB
        success, msg = database.update_user(
            user_id,
            name=data["name"],
            school=data["school"],
            class_=data["class"]   # or class if your DB column is class
        )
        
        if success:
            _user_steps.pop(user_id, None)
            bot.send_message(
                message.chat.id,
                "✅ Registration complete!",
                reply_markup=buttons.Buttons.MainMenu.keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Failed to save registration: {msg}"
            )


# ----------- keyboards -----------

def ask_region(bot, message):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for r in text.form_four_schools_by_region.keys():
        kb.add(r)
    bot.send_message(message.chat.id, "📍 Select your region:", reply_markup=kb)


def ask_school(bot, message, region):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for s in text.form_four_schools_by_region[region]:
        kb.add(s)
    bot.send_message(message.chat.id, "🏫 Select your school:", reply_markup=kb)


def ask_class(bot, message):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    for cls in ["F1", "F2", "F3", "F4"]:
        kb.add(cls)
    bot.send_message(message.chat.id, "📚 Select your class:", reply_markup=kb)