from bots.ardayda_bot import database, buttons, text


def is_registering(user_id):
    status = database.get_user_status(user_id)
    return bool(status and status.startswith("reg:"))


def registration(bot, message):
    try:
        user_id = message.from_user.id
        msg = message.text.strip()
        status = database.get_user_status(user_id)
        step = status.split(":", 1)[1]

        # ---------- BACK ----------
        if msg == buttons.BACK:
            go_back(bot, message, step)
            return

        # ---------- NAME ----------
        if step == "name":
            if len(msg.split()) < 2:
                bot.send_message(message.chat.id, text.REG_NAME)
                return

            database.update_user(user_id, name=msg)
            database.set_status(user_id, "reg:region")
            bot.send_message(
                message.chat.id,
                text.REG_REGION,
                reply_markup=buttons.region_menu()
            )

        # ---------- REGION ----------
        elif step == "region":
            if msg not in text.form_four_schools_by_region:
                bot.send_message(
                    message.chat.id,
                    "❌ Select a region using the keyboard.",
                    reply_markup=buttons.region_menu()
                )
                return

            database.update_user(user_id, region=msg)
            database.set_status(user_id, "reg:school")
            bot.send_message(
                message.chat.id,
                text.REG_SCHOOL,
                reply_markup=buttons.school_menu(msg)
            )

        # ---------- SCHOOL ----------
        elif step == "school":
            user = database.get_user(user_id)
            schools = text.form_four_schools_by_region[user.region]

            if msg not in schools:
                bot.send_message(
                    message.chat.id,
                    "❌ Select a school using the keyboard.",
                    reply_markup=buttons.school_menu(user.region)
                )
                return

            database.update_user(user_id, school=msg)
            database.set_status(user_id, "reg:class")
            bot.send_message(
                message.chat.id,
                text.REG_CLASS,
                reply_markup=buttons.class_menu()
            )

        # ---------- CLASS ----------
        elif step == "class":
            if msg not in {"F1", "F2", "F3", "F4"}:
                bot.send_message(
                    message.chat.id,
                    "❌ Select a class using the keyboard.",
                    reply_markup=buttons.class_menu()
                )
                return

            database.update_user(user_id, class_=msg)
            database.set_status(user_id, "menu:main")
            bot.send_message(
                message.chat.id,
                text.REG_DONE,
                reply_markup=buttons.main_menu()
            )

    except Exception as e:
        print("REGISTRATION ERROR:", e)
        bot.send_message(
            message.chat.id,
            "⚠️ Something went wrong. Please try again."
        )


def go_back(bot, message, step):
    user_id = message.from_user.id

    if step == "region":
        database.set_status(user_id, "reg:name")
        bot.send_message(message.chat.id, text.REG_NAME)

    elif step == "school":
        database.set_status(user_id, "reg:region")
        bot.send_message(
            message.chat.id,
            text.REG_REGION,
            reply_markup=buttons.region_menu()
        )

    elif step == "class":
        user = database.get_user(user_id)
        database.set_status(user_id, "reg:school")
        bot.send_message(
            message.chat.id,
            text.REG_SCHOOL,
            reply_markup=buttons.school_menu(user.region)
        )


def menu_router(bot, message):
    if message.text == buttons.Main.PROFILE:
        show_profile(bot, message)
        return

    bot.send_message(
        message.chat.id,
        "📋 Main menu",
        reply_markup=buttons.main_menu()
    )


def show_profile(bot, message):
    user = database.get_user(message.from_user.id)

    profile = (
        "👤 *My Profile*\n\n"
        f"📛 Name: {user.name}\n"
        f"🌍 Region: {user.region}\n"
        f"🏫 School: {user.school}\n"
        f"🎓 Class: {user.class_}"
    )

    bot.send_message(
        message.chat.id,
        profile,
        parse_mode="Markdown",
        reply_markup=buttons.main_menu()
    )