# bots/ardayda_bot/handlers.py
import logging
from telebot import types
from bots.ardayda_bot.database import(
    create_user_record,
    set_user_name,
    user_exists,
    set_coulmn)


logger = logging.getLogger(__name__)

# ============ VALIDATION HELPERS ============
def validate_field(field, content):
    """Validate user name"""
    
    if field == "name":
        if len(name.split()) < 3:
            return False, "Fadlan Magacaga oo 3addexan gali."
        if len(name) > 30:
            return False, "Iska hubi magaca !"
        
        return True, "Valid Name [✓]"
    elif check == "school":
        return True, "good"
        


        
# ============ REGESTRINT OPERATIONS ============
# Regeater New User
def complate_regestering(bot, message, name=False, school=False, class_=False):
    user_id = message.from_user.id
    text = message.text
    if not user_exists(user_id):
        create_user_record(user_id)
        
        
    column = "name" if name else "school" if school else "class" if class_ else None
    next_step = "school" if name else "class" if school else "complate" if class_
    
    Validity = validate_field(field=column , content=text)
    
    # invalid types
    if not Validity[0]:
        bot.reply_to(mesaage, Validity[1])
    else:
        set_coulmn(id_=user_id, column=name, value=text,next_step=next_step)
        respond = "[✓] you've done you loging.\n\n/help - for helping..." if next_step == "complate" else "[!] let's to the next step.\n\nEnter Your {next_step.capital()} ↓"
        bot.reply_to(mesaage, respond)
        
