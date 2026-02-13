from bots.ardayda_bot import database, buttons, text
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import traceback

# Memory tracking
pdf_upload_stage = {}       # user_id -> {"file_id": str, "name": str}
selected_user_tags = {}     # user_id -> set(tag_name)


# ---------------- Registration & Menu ----------------

def is_registering(user_id):
    status = database.get_user_status(user_id)
    return bool(status and status.startswith("reg:"))

def is_editing(user_id):
    status = database.get_user_status(user_id)
    return status and status.startswith("edit:")

def is_uploading(user_id):
    status = database.get_user_status(user_id)
    return status and status.startswith("upload:")

def is_searching(user_id):
    status = database.get_user_status(user_id)
    return status and status.startswith("search:")


# ---------------- Registration Flow ----------------
def registration(bot, message):
    try:
        user_id = message.from_user.id
        msg = message.text.strip()
        status = database.get_user_status(user_id)
        step = status.split(":", 1)[1]

        # Back
        if msg == buttons.Main.BACK:
            go_back(bot, message, step)
            return

        if step == "name":
            if len(msg.split()) < 2:
                bot.send_message(message.chat.id, text.REG_NAME)
                return
            database.update_user(user_id, name=msg)
            database.set_status(user_id, "reg:region")
            bot.send_message(message.chat.id, text.REG_REGION, reply_markup=buttons.region_menu())

        elif step == "region":
            if msg not in text.form_four_schools_by_region:
                bot.send_message(message.chat.id, "❌ Select a region using keyboard.", reply_markup=buttons.region_menu())
                return
            database.update_user(user_id, region=msg)
            database.set_status(user_id, "reg:school")
            bot.send_message(message.chat.id, text.REG_SCHOOL, reply_markup=buttons.school_menu(msg))

        elif step == "school":
            user = database.get_user(user_id)
            if msg not in text.form_four_schools_by_region[user["region"]]:
                bot.send_message(message.chat.id, "❌ Select a school using keyboard.", reply_markup=buttons.school_menu(user["region"]))
                return
            database.update_user(user_id, school=msg)
            database.set_status(user_id, "reg:class")
            bot.send_message(message.chat.id, text.REG_CLASS, reply_markup=buttons.class_menu())

        elif step == "class":
            if msg not in ["F1","F2","F3","F4"]:
                bot.send_message(message.chat.id, "❌ Select a class using keyboard.", reply_markup=buttons.class_menu())
                return
            database.update_user(user_id, class_=msg)
            database.set_status(user_id, "menu:main")
            bot.send_message(message.chat.id, text.REG_DONE, reply_markup=buttons.main_menu())

    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")


def go_back(bot, message, step):
    user_id = message.from_user.id
    if step == "region":
        database.set_status(user_id, "reg:name")
        bot.send_message(message.chat.id, text.REG_NAME)
    elif step == "school":
        database.set_status(user_id, "reg:region")
        bot.send_message(message.chat.id, text.REG_REGION, reply_markup=buttons.region_menu())
    elif step == "class":
        user = database.get_user(user_id)
        database.set_status(user_id, "reg:school")
        bot.send_message(message.chat.id, text.REG_SCHOOL, reply_markup=buttons.school_menu(user["region"]))


# ---------------- Profile ----------------
def show_profile(bot, message):
    user = database.get_user(message.from_user.id)
    profile = (
        "👤 *My Profile*\n\n"
        f"📛 Name: {user['name']}\n"
        f"🌍 Region: {user['region']}\n"
        f"🏫 School: {user['school']}\n"
        f"🎓 Class: {user['class_']}"
    )
    bot.send_message(message.chat.id, profile, parse_mode="Markdown", reply_markup=buttons.main_menu())


# ---------------- Upload PDF Flow ----------------
def start_upload(bot, message):
    user_id = message.from_user.id
    database.set_status(user_id, "upload:waiting_file")
    bot.send_message(message.chat.id, "📄 Send the PDF file you want to upload:")

def handle_pdf_upload(bot, message):
    user_id = message.from_user.id
    if not message.document or message.document.mime_type != "application/pdf":
        bot.send_message(message.chat.id, "❌ Please send a valid PDF file.")
        return

    pdf_upload_stage[user_id] = {"file_id": message.document.file_id, "name": message.document.file_name}
    database.set_status(user_id, "upload:select_tags")
    selected_user_tags[user_id] = set()

    send_tag_selection(bot, message, "Select tags for your PDF:")


def send_tag_selection(bot, message, text_msg):
    try:
        kb = InlineKeyboardMarkup(row_width=3)
        user_id = message.from_user.id
        all_tags = database.get_all_tags()
    
        for t in all_tags:
            tag = t["name"]
            mark = "✓" if tag in selected_user_tags.get(user_id, set()) else "×"
            kb.add(
                InlineKeyboardButton(
                    f"{mark} {tag}",
                    callback_data=f"upload_tag:{tag}"
                )
            )
    
        kb.add(InlineKeyboardButton("✅ Done", callback_data="upload_done"))
        kb.add(InlineKeyboardButton("⬅️ Cancel", callback_data="upload_cancel"))
        bot.send_message(message.chat.id, text_msg, reply_markup=kb)
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

def handle_upload_callback(bot, call):
    try:
        user_id = call.from_user.id
        data = call.data
    
        if data.startswith("upload_tag:"):
            tag = data.split(":",1)[1]
            selected_user_tags.setdefault(user_id, set())
            if tag in selected_user_tags[user_id]:
                selected_user_tags[user_id].remove(tag)
            else:
                selected_user_tags[user_id].add(tag)
            send_tag_selection(bot, call.message, "Select tags for your PDF:")
    
        elif data == "upload_done":
            info = pdf_upload_stage.pop(user_id, None)
            tags = selected_user_tags.pop(user_id, None)
        
            if not info or not tags:
                bot.answer_callback_query(call.id, "Select at least one tag.")
                return
        
            pdf_id = database.add_pdf(info["name"], info["file_id"], user_id)
            database.assign_tags_to_pdf(pdf_id, tags)
        
            database.set_status(user_id, "menu:main")
            bot.edit_message_text(
                "✅ PDF uploaded successfully!",
                call.message.chat.id,
                call.message.message_id
            )
    
        elif data == "upload_cancel":
            pdf_upload_stage.pop(user_id, None)
            selected_user_tags.pop(user_id, None)
            database.set_status(user_id, "menu:main")
            bot.edit_message_text("❌ Upload cancelled.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

# ---------------- Search PDF Flow ----------------
def start_search(bot, message):
    user_id = message.from_user.id
    database.set_status(user_id, "search:select_tags")
    selected_user_tags[user_id] = set()
    send_search_tag_selection(bot, message, "Select tags to search PDFs:")


def send_search_tag_selection(bot, message, text_msg):
    try:
        kb = InlineKeyboardMarkup(row_width=3)
        all_tags = database.get_all_tags()  # list of tag names
        user_id = message.from_user.id
        for t in all_tags:
            tag_name = t["name"]
            mark = "✓" if tag_name in selected_user_tags.get(user_id, set()) else "×"
            kb.add(InlineKeyboardButton(
                f"{mark} {tag_name}",
                callback_data=f"upload_tag:{tag_name}"
            ))
        kb.add(InlineKeyboardButton("✅ Done", callback_data="search_done"))
        kb.add(InlineKeyboardButton("⬅️ Cancel", callback_data="search_cancel"))
        bot.send_message(message.chat.id, text_msg, reply_markup=kb)
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

def handle_search_callback(bot, call):
    try:
        user_id = call.from_user.id
        data = call.data
    
        if data.startswith("search_tag:"):
            tag = data.split(":",1)[1]
            selected_user_tags.setdefault(user_id, set())
            if tag in selected_user_tags[user_id]:
                selected_user_tags[user_id].remove(tag)
            else:
                selected_user_tags[user_id].add(tag)
            send_search_tag_selection(bot, call.message, "Select tags to search PDFs:")
    
        elif data == "search_done":
            if not selected_user_tags.get(user_id):
                bot.answer_callback_query(call.id, "Select at least one tag.")
                return
            tags = selected_user_tags.pop(user_id)
            pdfs = database.get_pdfs_by_tags(list(tags))
            if not pdfs:
                bot.edit_message_text("❌ No PDFs found.", call.message.chat.id, call.message.message_id)
                database.set_status(user_id, "menu:main")
                return
    
            for p in pdfs:
                caption = f"{p['name']} (⬇️ {p['downloads']} | ❤️ {p['likes']})"
                bot.send_document(call.message.chat.id, p['file_id'], caption=caption)
                database.increment_download(p['id'])
    
            database.set_status(user_id, "menu:main")
            bot.edit_message_text("✅ Search complete.", call.message.chat.id, call.message.message_id)
    
        elif data == "search_cancel":
            selected_user_tags.pop(user_id, None)
            database.set_status(user_id, "menu:main")
            bot.edit_message_text("❌ Search cancelled.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

# ---------------- Menu Router ----------------
def menu_router(bot, message):
    try:
        text_msg = message.text
        if text_msg == buttons.Main.PROFILE:
            show_profile(bot, message)
            return
        if text_msg == buttons.Main.UPLOAD:
            start_upload(bot, message)
            return
        if text_msg == buttons.Main.SEARCH:
            start_search(bot, message)
            return
    
        bot.send_message(message.chat.id, "📋 Main menu", reply_markup=buttons.main_menu())
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")