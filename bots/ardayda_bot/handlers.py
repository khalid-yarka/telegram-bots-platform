from bots.ardayda_bot import database, buttons, text


def is_registering(user_id):
    status = database.get_user_status(user_id)
    return status and status.startswith("reg:")


def start(bot, message):
    user_id = message.from_user.id
    database.add_user(user_id)
    status = database.get_user_status(user_id)

    if status == "menu:main":
        bot.send_message(message.chat.id, text.WELCOME_BACK,
                         reply_markup=buttons.main_menu())
    else:
        bot.send_message(message.chat.id, text.REG_NAME)


def registration(bot, message):
    user_id = message.from_user.id
    msg = message.text.strip()
    status = database.get_user_status(user_id)
    step = status.split(":")[1]

    if step == "name":
        if len(msg.split()) < 2:
            bot.send_message(message.chat.id, text.REG_NAME)
            return
        database.update_user(user_id, name=msg)
        database.set_status(user_id, "reg:region")
        bot.send_message(
            message.chat.id,
            text.REG_REGION,
            reply_markup=buttons.region_menu(text.form_four_schools_by_region)
        )

    elif step == "region":
        if msg not in text.form_four_schools_by_region:
            return
        database.update_user(user_id, region=msg)
        database.set_status(user_id, "reg:school")
        bot.send_message(
            message.chat.id,
            text.REG_SCHOOL,
            reply_markup=buttons.school_menu(
                text.form_four_schools_by_region[msg]
            )
        )

    elif step == "school":
        database.update_user(user_id, school=msg)
        database.set_status(user_id, "reg:class")
        bot.send_message(
            message.chat.id,
            text.REG_CLASS,
            reply_markup=buttons.class_menu()
        )

    elif step == "class":
        database.update_user(user_id, class_=msg.upper())
        database.set_status(user_id, "menu:main")
        bot.send_message(
            message.chat.id,
            text.REG_DONE,
            reply_markup=buttons.main_menu()
        )


def menu_router(bot, message):
    bot.send_message(
        message.chat.id,
        "📋 Main menu",
        reply_markup=buttons.main_menu()
    )