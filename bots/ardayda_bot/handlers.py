# bots/ardayda_bot/handlers.py
import logging
from telebot import types
from bots.ardayda_bot.database import(
    create_user_record,
    get_user_status,
    set_user_name)


logger = logging.getLogger(__name__)

# ============ VALIDATION HELPERS ============
def validate_name(name):
    """Validate user name"""
    if len(name.split()) < 3:
        return False, "Fadlan Magacaga oo 3addexan gali."
    if len(name) > 30:
        return False, "Iska hubi magaca !"
        
    return True, "Good"


        
# ============ REGESTRINT OPERATIONS ============
# Regeater New User
def complate_regestering(bot, message):
    user_id = message.from_user.id
    if not user_exists(user_id):
        create_user_record(user_id)
        
    if get_user_status == "name":
        if validate_name[0]:
            if set_user_name(user_id, message.text)[0]:
                bot.reply_to(mesaage, "complated Login [✓]\n\n/help")
            else:
                bot.reply_to(mesaage, "Error To Update !")
        else:
            bot.reply_to(mesaage, validate_name[1])