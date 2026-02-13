from bots.ardayda_bot import database, buttons

selected_user_tags = {}
pdf_upload_stage = {}  # track PDF name before uploading

def is_registering(user_id):
    status = database.get_user_status(user_id)
    return bool(status and status.startswith("reg:"))

def registration(bot,message):
    user_id = message.from_user.id
    msg = message.text.strip()
    step = database.get_user_status(user_id).split(":",1)[1]

    if msg==buttons.BACK:
        go_back(bot,message,step)
        return

    if step=="name":
        database.update_user(user_id,name=msg)
        database.set_status(user_id,"reg:region")
        bot.send_message(message.chat.id,"Enter region:",reply_markup=buttons.region_menu())
    elif step=="region":
        database.update_user(user_id,region=msg)
        database.set_status(user_id,"reg:school")
        bot.send_message(message.chat.id,"Select school:",reply_markup=buttons.school_menu(msg))
    elif step=="school":
        database.update_user(user_id,school=msg)
        database.set_status(user_id,"reg:class")
        bot.send_message(message.chat.id,"Select class:",reply_markup=buttons.class_menu())
    elif step=="class":
        database.update_user(user_id,class_=msg)
        database.set_status(user_id,"menu:main")
        bot.send_message(message.chat.id,"✅ Registration complete",reply_markup=buttons.main_menu())

def go_back(bot,message,step):
    user_id = message.from_user.id
    if step=="region":
        database.set_status(user_id,"reg:name")
        bot.send_message(message.chat.id,"Enter name:")
    elif step=="school":
        database.set_status(user_id,"reg:region")
        bot.send_message(message.chat.id,"Select region:",reply_markup=buttons.region_menu())
    elif step=="class":
        database.set_status(user_id,"reg:school")
        bot.send_message(message.chat.id,"Select school:",reply_markup=buttons.school_menu("North"))


def menu_router(bot,message):
    user_id = message.from_user.id
    text_msg = message.text
    if text_msg==buttons.PROFILE:
        show_profile(bot,message)
        return
    elif text_msg==buttons.SEARCH:
        bot.send_message(message.chat.id,"Select tags to search:",reply_markup=buttons.search_tags_menu())
        return
    elif text_msg==buttons.UPLOAD:
        bot.send_message(message.chat.id,"Send me the PDF file to upload:")
        database.set_status(user_id,"upload:waiting_file")
        return
    bot.send_message(message.chat.id,"📋 Main menu",reply_markup=buttons.main_menu())

def show_profile(bot,message):
    user = database.get_user(message.from_user.id)
    profile = f"👤 *My Profile*\n\n📛 Name: {user['name']}\n🌍 Region: {user['region']}\n🏫 School: {user['school']}\n🎓 Class: {user['class_']}"
    bot.send_message(message.chat.id,profile,parse_mode="Markdown",reply_markup=buttons.main_menu())