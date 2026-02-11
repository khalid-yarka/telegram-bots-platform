# bots/ardayda_bot/bot.py
import logging
import telebot
from telebot.types import Message

from bots.ardayda_bot import database, buttons, text  # text.py contains your regions & schools

logger = logging.getLogger(__name__)


class ArdaydaBot:
    """ok, Ardayda Education Bot - registration + main menu"""

    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.bot = telebot.TeleBot(bot_token, threaded=False)
        self.user_steps = {}  # store temp registration data per user
        self.register_handlers()

    # ==================== HANDLERS ====================
    def register_handlers(self):

        # Start / Help command
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message: Message):
            user_id = message.from_user.id
            database.add_user(user_id)
            self.user_steps[user_id] = {}
            self.ask_name(message)

        # Settings command
        @self.bot.message_handler(commands=['settings'])
        @self.bot.message_handler(func=lambda msg: msg.text == "⚙️ Settings")
        def handle_settings(message: Message):
            self.bot.send_message(message.chat.id, "⚙️ Settings", reply_markup=buttons.Buttons.Settings.keyboard())

        # Main menu command
        @self.bot.message_handler(func=lambda msg: msg.text in [
            buttons.Buttons.MainMenu.SEARCH,
            buttons.Buttons.MainMenu.UPLOAD,
            buttons.Buttons.MainMenu.PROFILE
        ])
        def handle_main_menu_buttons(message: Message):
            self.bot.send_message(message.chat.id, "Main Menu Action Triggered", reply_markup=buttons.Buttons.MainMenu.keyboard())

        # Catch all for registration flow
        @self.bot.message_handler(func=lambda msg: True)
        def handle_registration(message: Message):
            user_id = message.from_user.id
            if user_id not in self.user_steps:
                return  # user not in registration flow

            step = self.user_steps[user_id].get("step", "name")
            text_msg = message.text.strip()

            # ---- Step: Name ----
            if step == "name":
                self.user_steps[user_id]["name"] = text_msg
                self.user_steps[user_id]["step"] = "region"
                self.ask_region(message)
                return

            # ---- Step: Region ----
            if step == "region":
                if text_msg.upper() not in text.form_four_schools_by_region:
                    self.bot.send_message(message.chat.id, "❌ Invalid region. Please choose from the keyboard.")
                    self.ask_region(message)
                    return

                self.user_steps[user_id]["region"] = text_msg.upper()
                self.user_steps[user_id]["step"] = "school"
                self.ask_school(message, text_msg.upper())
                return

            # ---- Step: School ----
            if step == "school":
                region = self.user_steps[user_id]["region"]
                schools = text.form_four_schools_by_region.get(region, [])
                if text_msg not in schools:
                    self.bot.send_message(message.chat.id, "❌ Invalid school. Please choose from the keyboard.")
                    self.ask_school(message, region)
                    return

                self.user_steps[user_id]["school"] = text_msg
                self.user_steps[user_id]["step"] = "class"
                self.ask_class(message)
                return

            # ---- Step: Class ----
            if step == "class":
                if text_msg.upper() not in ["F1", "F2", "F3", "F4"]:
                    self.bot.send_message(message.chat.id, "❌ Invalid class. Use F1, F2, F3, or F4.")
                    self.ask_class(message)
                    return

                self.user_steps[user_id]["class"] = text_msg.upper()
                # ---- Registration complete ----
                data = self.user_steps.pop(user_id)
                database.update_user(user_id,
                                     name=data["name"],
                                     school=data["school"],
                                     class_=data["class"])
                self.bot.send_message(message.chat.id, "✅ Registration complete!", reply_markup=buttons.Buttons.MainMenu.keyboard())
                return

    # ==================== REGISTRATION QUESTIONS ====================
    def ask_name(self, message: Message):
        self.user_steps[message.from_user.id]["step"] = "name"
        self.bot.send_message(message.chat.id, "👋 Welcome! Please enter your full name:")

    def ask_region(self, message: Message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for region in text.form_four_schools_by_region.keys():
            markup.add(region)
        self.bot.send_message(message.chat.id, "📍 Select your region:", reply_markup=markup)

    def ask_school(self, message: Message, region: str):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        schools = text.form_four_schools_by_region.get(region, [])
        for i in range(0, len(schools), 2):
            row = schools[i:i + 2]
            markup.add(*row)
        self.bot.send_message(message.chat.id, "🏫 Select your school:", reply_markup=markup)

    def ask_class(self, message: Message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        for cls in ["F1", "F2", "F3", "F4"]:
            markup.add(cls)
        self.bot.send_message(message.chat.id, "📚 Select your class:", reply_markup=markup)

    # ==================== UPDATE WEBHOOK/JSON ====================
    def process_update(self, update_json):
        try:
            if not isinstance(update_json, dict):
                raise ValueError("Invalid update format")
            update = telebot.types.Update.de_json(update_json)
            self.bot.process_new_updates([update])
            return True
        except Exception as e:
            logger.error(f"Ardayda bot error: {str(e)}")
            return False


# ==================== GLOBAL FUNCTION ====================
def process_ardayda_update(bot_token, update_json):
    try:
        bot = ArdaydaBot(bot_token)
        return bot.process_update(update_json)
    except Exception as e:
        logger.error(f"Error in process_ardayda_update: {str(e)}")
        return False