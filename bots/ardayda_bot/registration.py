# bots/ardayda_bot/registration.py
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bots.ardayda_bot import database
from bots.ardayda_bot import text
from bots.ardayda_bot.buttons import Buttons

# In-memory registration state
registration_state = {}
SCHOOLS_PER_PAGE = 5

def start_registration(bot, user_id):
    registration_state[user_id] = {
        "step": "name",
        "data": {},
        "page": 0
    }
    bot.send_message(user_id, "👋 Welcome! Please enter your **full name**:")


def handle_message(bot, message):
    user_id = message.from_user.id
    state = registration_state.get(user_id)
    if not state:
        return False

    text_msg = message.text.strip()
    step = state["step"]

    if step == "name":
        state["data"]["name"] = text_msg
        state["step"] = "region"
        ask_region(bot, user_id)
        return True

    elif step == "class":
        if text_msg.lower() == "skip":
            state["data"]["class"] = None
        else:
            state["data"]["class"] = text_msg
        finalize_registration(bot, user_id)
        return True

    return False


def ask_region(bot, user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    for region in text.form_four_schools_by_region.keys():
        kb.add(InlineKeyboardButton(f"🏫 {region}", callback_data=f"reg_region|{region}"))
    bot.send_message(user_id, "Please select your region:", reply_markup=kb)


def ask_school(bot, user_id):
    state = registration_state[user_id]
    region = state["data"]["region"]
    schools = text.form_four_schools_by_region[region]
    page = state["page"]
    start = page * SCHOOLS_PER_PAGE
    end = start + SCHOOLS_PER_PAGE
    kb = InlineKeyboardMarkup(row_width=1)
    for school in schools[start:end]:
        kb.add(InlineKeyboardButton(f"🏫 {school}", callback_data=f"reg_school|{school}"))

    # Pagination
    buttons = []
    if start > 0:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="school_prev"))
    if end < len(schools):
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data="school_next"))
    if buttons:
        kb.add(*buttons)

    bot.send_message(user_id, "Select your school:", reply_markup=kb)


def handle_callback(bot, call):
    user_id = call.from_user.id
    state = registration_state.get(user_id)
    if not state:
        return False

    data = call.data
    step = state["step"]

    if data.startswith("reg_region|"):
        region = data.split("|")[1]
        state["data"]["region"] = region
        state["step"] = "school"
        state["page"] = 0
        ask_school(bot, user_id)
        bot.answer_callback_query(call.id)
        return True

    elif data.startswith("reg_school|"):
        school = data.split("|")[1]
        state["data"]["school"] = school
        state["step"] = "class"
        bot.send_message(user_id, "✅ Great! Enter your class (optional e.g., F4, F3) or type 'skip':")
        bot.answer_callback_query(call.id)
        return True

    elif data == "school_next":
        state["page"] += 1
        ask_school(bot, user_id)
        bot.answer_callback_query(call.id)
        return True

    elif data == "school_prev":
        state["page"] -= 1
        ask_school(bot, user_id)
        bot.answer_callback_query(call.id)
        return True

    return False


def finalize_registration(bot, user_id):
    state = registration_state[user_id]
    data = state["data"]
    database.update_user(
        user_id,
        name=data.get("name"),
        school=data.get("school"),
        class=data.get("class")
    )
    bot.send_message(user_id, "🎉 Registration complete! Here is your main menu:")
    bot.send_message(user_id, "Choose an option:", reply_markup=Buttons.MainMenu.keyboard())
    registration_state.pop(user_id, None)