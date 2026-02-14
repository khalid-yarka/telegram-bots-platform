from bots.ardayda_bot import database, buttons, text
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import traceback

# Memory tracking
pdf_upload_stage = {}       # user_id -> {"file_id": str, "name": str}
selected_user_tags = {}     # user_id -> set(tag_name)

pdf_search_results = {}  # user_id -> list of PDFs from last search

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
    selected_user_tags.pop(user_id, None)
    pdf_upload_stage.pop(user_id, None)
    database.set_status(user_id, "upload:waiting_file")
    bot.send_message(message.chat.id, "📄 Send the PDF file you want to upload:\n\n/cancel - to cancel uploading operation.")

def handle_pdf_upload(bot, message):
    user_id = message.from_user.id
    if not message.document or message.document.mime_type != "application/pdf":
        bot.send_message(message.chat.id, "❌ Please send a valid PDF file.")
        return

    pdf_upload_stage[user_id] = {"file_id": message.document.file_id, "name": message.document.file_name}
    database.set_status(user_id, "upload:select_tags")
    
    selected_user_tags[user_id] = set()

    send_tag_selection(bot, message, "Select tags for your PDF:", edit=False)


def send_tag_selection(bot, message, text_msg, *, edit=False, user_id=None):
    kb = InlineKeyboardMarkup(row_width=3)

    if user_id is None:
        user_id = message.from_user.id

    for t in database.get_all_tags():
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

    if edit:
        bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=kb
        )
    else:
        bot.send_message(message.chat.id, text_msg, reply_markup=kb)

def handle_upload_callback(bot, call):
    try:
        user_id = call.from_user.id
        data = call.data

        # -------- TAG TOGGLE --------
        if data.startswith("upload_tag:"):
            tag = data.split(":", 1)[1]

            selected_user_tags.setdefault(user_id, set())

            if tag in selected_user_tags[user_id]:
                selected_user_tags[user_id].remove(tag)
            else:
                selected_user_tags[user_id].add(tag)

            send_tag_selection(
                bot,
                call.message,
                "Select tags for your PDF:",
                edit=True,
                user_id=user_id
            )

            bot.answer_callback_query(call.id)
            return

        # -------- DONE --------
        if data == "upload_done":
            info = pdf_upload_stage.get(user_id)
            tags = selected_user_tags.get(user_id)
            
            if not info or not tags:
                bot.answer_callback_query(call.id, "Select at least one tag.")
                return
            
            pdf_upload_stage.pop(user_id, None)
            selected_user_tags.pop(user_id, None)

            pdf_id = database.add_pdf(...)
            if not pdf_id:
                bot.answer_callback_query(call.id, "❌ Upload failed.")
                return
            database.assign_tags_to_pdf(pdf_id, tags)

            database.set_status(user_id, "menu:main")
            bot.edit_message_text(
                "✅ PDF uploaded successfully!",
                call.message.chat.id,
                call.message.message_id
            )
            return

        # -------- CANCEL --------
        if data == "upload_cancel":
            pdf_upload_stage.pop(user_id, None)
            selected_user_tags.pop(user_id, None)
            database.set_status(user_id, "menu:main")
            bot.edit_message_text(
                "❌ Upload cancelled.",
                call.message.chat.id,
                call.message.message_id
            )
            return

    except Exception as e:
        print("UPLOAD CALLBACK ERROR:", e)
        traceback.print_exc()
        bot.send_message(
            call.message.chat.id,
            "⚠️ Something went wrong. Try again."
        )

# ---------------- Search PDF Flow ----------------
def start_search(bot, message):
    try:
        user_id = message.from_user.id
        selected_user_tags.pop(user_id, None)
        database.set_status(user_id, "search:select_tags")
        selected_user_tags[user_id] = set()
        send_search_tag_selection(bot, message, "Select tags to search PDFs:")
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

def send_search_tag_selection(bot, message, text_msg, *, edit=False, user_id=None):
    try:
        kb = InlineKeyboardMarkup(row_width=3)

        if user_id is None:
            user_id = message.from_user.id

        all_tags = database.get_all_tags()

        for t in all_tags:
            tag_name = t["name"]
            mark = "✓" if tag_name in selected_user_tags.get(user_id, set()) else "×"
            kb.add(InlineKeyboardButton(
                f"{mark} {tag_name}",
                callback_data=f"search_tag:{tag_name}"
            ))

        kb.add(InlineKeyboardButton("✅ Done", callback_data="search_done"))
        kb.add(InlineKeyboardButton("⬅️ Cancel", callback_data="search_cancel"))

        if edit:
            bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=kb
            )
        else:
            bot.send_message(message.chat.id, text_msg, reply_markup=kb)

    except Exception as e:
        print("SEARCH TAG ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")
        
def handle_search_callback(bot, call):
    try:
        user_id = call.from_user.id
        data = call.data

        # -------- TAG TOGGLE --------
        if data.startswith("search_tag:"):
            tag = data.split(":", 1)[1]

            selected_user_tags.setdefault(user_id, set())

            if tag in selected_user_tags[user_id]:
                selected_user_tags[user_id].remove(tag)
            else:
                selected_user_tags[user_id].add(tag)

            send_search_tag_selection(
                bot,
                call.message,
                "Select tags to search PDFs:",
                edit=True,
                user_id=user_id
            )

            bot.answer_callback_query(call.id)
            return

        # -------- DONE --------
        if data == "search_done":
            tags = selected_user_tags.pop(user_id, None)
        
            if not tags:
                bot.answer_callback_query(call.id, "Select at least one tag.")
                return
        
            pdfs = database.get_pdfs_by_tags(list(tags))
            if not pdfs:
                bot.edit_message_text("❌ No PDFs found.", call.message.chat.id, call.message.message_id)
                database.set_status(user_id, "menu:main")
                return
        
            # send first page of search results with pagination
            send_pdf_results(bot, call, pdfs, page=0)
        
            # store search context in memory so pagination works
            pdf_search_results[user_id] = pdfs
        
            database.set_status(user_id, "search:results")
            return

        # -------- CANCEL --------
        if data == "search_cancel":
            pdf_search_results.pop(user_id, None)
            selected_user_tags.pop(user_id, None)
            database.set_status(user_id, "menu:main")
            bot.edit_message_text("❌ Search cancelled.", call.message.chat.id, call.message.message_id)
            return

    except Exception as e:
        print("SEARCH CALLBACK ERROR:", e)
        traceback.print_exc()
        bot.send_message(call.message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

# ---------------- PDF SEARCH HELPERS ----------------
def send_pdf_results(bot, call, pdfs, page=0, page_size=5):
    start = page * page_size
    end = start + page_size
    current_pdfs = pdfs[start:end]

    kb = InlineKeyboardMarkup(row_width=1)
    for p in current_pdfs:
        kb.add(InlineKeyboardButton(
            p["name"],
            callback_data=f"pdf_send:{p['id']}"
        ))

    # Pagination buttons
    pag_buttons = []
    if start > 0:
        pag_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{page-1}"))
    if end < len(pdfs):
        pag_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"pdf_page:{page+1}"))
    if pag_buttons:
        kb.row(*pag_buttons)

    bot.edit_message_text(
        "📄 Select a PDF:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=kb
    )


def send_pdf_with_inline(bot, pdf, chat_id):
    """Send PDF document with downloads in caption and like button inline"""
    caption = (
        f"{pdf['name']}\n"
        "-----------------\n"
        f"⬇️ {pdf['downloads']} downloads"
    )

    bot.send_document(chat_id, pdf['file_id'], caption=caption)

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(f"❤️ {pdf['likes']}", callback_data=f"like_pdf:{pdf['id']}"))
    bot.send_message(chat_id, "👍 Like this PDF", reply_markup=kb)

    # Increment downloads only when sending PDF
    database.increment_download(pdf['id'])


def handle_pdf_interaction(bot, call):
    """Handle callback queries for sending PDFs, likes, and pagination"""
    user_id = call.from_user.id
    data = call.data

    # ---------- Send PDF ----------
    if data.startswith("pdf_send:"):
        pdf_id = int(data.split(":", 1)[1])
        pdf = database.get_pdf_by_id(pdf_id)
        if pdf:
            send_pdf_with_inline(bot, pdf, call.message.chat.id)
        bot.answer_callback_query(call.id)
        return

    # ---------- Like button ----------
    if data.startswith("like_pdf:"):
        pdf_id = int(data.split(":", 1)[1])
        database.like_pdf(pdf_id)
        pdf = database.get_pdf_by_id(pdf_id)
        if pdf:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(f"❤️ {pdf['likes']}", callback_data=f"like_pdf:{pdf_id}"))
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb
                )
            except Exception:
                pass
        bot.answer_callback_query(call.id, "❤️ Liked!")
        return

    # ---------- Pagination ----------
    if data.startswith("pdf_page:"):
        search_results = pdf_search_results.get(user_id)
        if not search_results:
            bot.answer_callback_query(call.id, "❌ No search context!")
            return

        page = int(data.split(":", 1)[1])
        send_pdf_results(bot, call, search_results, page=page)
        bot.answer_callback_query(call.id)
        return

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