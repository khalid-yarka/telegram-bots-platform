# bots/ardayda_bot/handlers.py
import logging
from telebot import types
from bots.ardayda_bot.database import(
    user_not_exists,
    get_user,
    create_user_record,
    set_user_name,
    user_exists,
    set_coulmn)
from bots.ardayda_bot.buttons import (
    schools,
    main_menu_keyboard,
    Buttons)
    
from bots.ardayda_bot.text import (
    main_menu_text,)

logger = logging.getLogger(__name__)

# ============ VALIDATION HELPERS ============
def validate_field(field, content):
    """Validate user name"""
    
    if field == "name":
        if len(content.split()) < 3 or len(content) > 30:
            return False
        else:
            return True
    
    
    elif field == "school":
        if len(content.split()) =< 2:
            return False
        else:
            return True
""""
def validate_field(field, content):
    #Validate user name
    
    if field == "name":
        if len(content.split()) < 3:
            return False, "Fadlan Magacaga oo 3addexan gali."
        if len(content) > 30:
            return False, "Iska hubi magaca !"
        
        return True, "Valid Name [✓]"
    elif field == "school":
        return True, "good"
"""
def new_user(bot, message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        return True
    elif not user["name"]:
        return True
    elif not user["school"]:
        return True
    else:
        return False
    
""""
    
    
    
    if user_not_exist:
        return True
        
    elif user["name"] is None:
        return True
        
    elif user["school"] is None:
        return True
    else:
        return False
    
    
    
    
    
    
    
    
    
    if notuser_not_exist or user.get("name", False) or not user.get("school", False):
    if not user:
        return True
    elif not user.get("name", False) or not user.get("school", False):
        return True
    else:
        return False
"""
# ============ REGESTRINT OPERATIONS ============
def register_new_user(bot, message):
    user_id = message.from_user.id
    user = get_user(user_id, create=True)
    content = message.text
    if not user:
        add_user_info(user_id)
        bot.reply_to(message, "Send Your Full Name :")
        
    elif not user["name"]:
        if validate_field("name", content):
            add_user_info(user_id, content=content, name=True)
            bot.reply_to(message, "Send Your Full Name :")
        else:
            bot.reply_to(message, "[×] invalid name!\ne.g: Ahmed Ali Mohammed\n\nSend Your Full Name :")
    elif not user["school"]:
        if validate_field("school", content):
            add_user_info(user_id, content=content, school=True)
            bot.reply_to(message, "[✓] Done Regestrition\n\nsend /start command.")
        else:
            bot.reply_to(message, "[×] invalid school!\ne.g: Imamu Al-Nawawi Bosaso\n\nSend Your Full School Name :")
"""
    
    if not user["name"]:
        if validate_field("name", content):
            set_user_name(user_id, content)
            bot.reply_to(message, "Now Choose Your School:",reply_markup=schools())
        else:
            bot.reply_to(message, "Invalid Name [×]")
        
        
"""
"""
# Regeater New User
def complate_regestering(bot, message, name=False, school=False, class__=False):
    user_id = message.from_user.id
    text = message.text
    if not user_exists(user_id):
        create_user_record(user_id)
        
        
    column = "name" if name else "school" if school else "class_" if class__ else None
    next_step = "school" if name else "class_" if school else "complate" if class__ else None
    
    Validity = validate_field(field=column , content=text)
    
    # invalid types
    if not Validity[0]:
        bot.reply_to(message, Validity[1])
    else:
        set_coulmn(id_=user_id, column=name, value=text,next_step=next_step)
        respond = "[✓] you've done you loging.\n\n/help - for helping..." if next_step == "complate" else "[!] let's to the next step.\n\nEnter Your {next_step.capital()} ↓"
        bot.reply_to(message, respond)
        
"""
        
        
#----------------------- Message handlers -----------------------#
# send main menu
def main_menu(bot,message):
    user_id = message.from_user.id
    bot.reply_to(message, "Choose an option:", reply_markup=Buttons.MainMenu.keyboard())

# send settings menu
def settings_menu(bot, message):
    bot.reply_to(message, "Settings:", reply_markup=Buttons.Settings.keyboard())



