from bots.ardayda_bot import database, buttons, text
<<<<<<< HEAD
from telebot.types import InlineKeyboardMarkup,ReplyKeyboardMarkup, InlineKeyboardButton
import traceback

# ---------------- Memory Tracking ----------------
pdf_upload_stage = {}       # user_id -> {"file_id": str, "name": str}
selected_user_tags = {}     # user_id -> set(tag_name)
pdf_search_results = {}     # user_id -> list of PDFs from last search

=======
from telebot.types import InlineKeyboardMarkup,ReplyKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardRemove
import traceback

# ---------------- Memory Tracking ----------------
pdf_search_results = {}     # user_id -> list of PDFs from last search
pdf_upload_stage = {} # user_id -> {"file_id":..., "name":..., "tags":{"subject":set(), "type":None, "chapters":set(), "exam_year":set()}}

search_selected_tags = {}




>>>>>>> Advance catogry  but un solved
# ---------------- Helper Functions ----------------
def finalize_user(user_id):
    """
    Reset any temporary memory and return user to main menu.
    """
    pdf_upload_stage.pop(user_id, None)
<<<<<<< HEAD
    selected_user_tags.pop(user_id, None)
=======
    search_selected_tags.pop(user_id, None)
>>>>>>> Advance catogry  but un solved
    pdf_search_results.pop(user_id, None)
    database.set_status(user_id, "menu:main")

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
        if not status or ":" not in status:
            database.set_status(user_id, "reg:name")
            bot.send_message(message.chat.id, text.REG_NAME)
            return
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

# ---------------- New Updated for advance tag section ----------------
def send_pdf_tag_selection(bot, message, user_id=None, edit=False, mode="upload"):
    """
    Unified tag selector UI for upload & search
    mode = "upload" | "search"
    """

<<<<<<< HEAD
# ---------------- Upload PDF Flow ----------------
def start_upload(bot, message):
    user_id = message.from_user.id
    selected_user_tags.pop(user_id, None)
    pdf_upload_stage.pop(user_id, None)
    database.set_status(user_id, "upload:waiting_file")
    bot.send_message(
        message.chat.id, 
        "📄 Please send the PDF you want to upload.\n\nType /cancel to stop this operation.", 
        reply_markup=ReplyKeyboardRemove()
    )

def handle_pdf_upload(bot, message):
    user_id = message.from_user.id
    if not message.document or message.document.mime_type != "application/pdf":
        bot.send_message(message.chat.id, "❌ Please send a valid PDF file (must be .pdf). /cancel to stop.")
        return

    pdf_upload_stage[user_id] = {"file_id": message.document.file_id, "name": message.document.file_name}
    database.set_status(user_id, "upload:select_tags")
    
    selected_user_tags[user_id] = set()

    send_tag_selection(bot, message, "📄 Select tags for your PDF. Tap ✅ Done when finished or ⬅️ Cancel to stop.", edit=False)
=======
    if user_id is None:
        user_id = message.from_user.id

    store = pdf_upload_stage if mode == "upload" else search_selected_tags
    stage = store.get(user_id)
>>>>>>> Advance catogry  but un solved

    if not stage:
        bot.send_message(
            message.chat.id,
            "❌ Session expired. Please start again.",
            reply_markup=buttons.main_menu()
        )
        return

    tags = stage["tags"] if mode == "upload" else stage

<<<<<<< HEAD
    if user_id is None:
        user_id = message.from_user.id
        
    buttons = []
    
    for t in database.get_all_tags():
        tag = t["name"]
        mark = "✓" if tag in selected_user_tags.get(user_id, set()) else "×"
        buttons.append(
=======
    kb = InlineKeyboardMarkup()

    # ---------- SUBJECTS ----------
    subs = ["phy", "bio", "chem", "math", "his"]
    row = []
    for sub in subs:
        mark = "✅" if sub in tags["subject"] else "❎"
        row.append(
>>>>>>> Advance catogry  but un solved
            InlineKeyboardButton(
                f"{mark} {sub.upper()}",
                callback_data=f"{mode}_subject:{sub}"
            )
        )
<<<<<<< HEAD
    
    for i in range(0, len(buttons), 3):
        kb.row(*buttons[i:i+3])
=======
        if len(row) == 3:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)

    # ---------- TYPE ----------
    kb.row(
        InlineKeyboardButton(
            f"{'✅' if tags['type']=='book' else '❎'} BOOK",
            callback_data=f"{mode}_type:book"
        ),
        InlineKeyboardButton(
            f"{'✅' if tags['type']=='exam' else '❎'} EXAM",
            callback_data=f"{mode}_type:exam"
        ),
        InlineKeyboardButton(
            f"{'✅' if tags['type']=='assignment' else '❎'} ASSIGN",
            callback_data=f"{mode}_type:assignment"
        ),
    )
>>>>>>> Advance catogry  but un solved

    # ---------- CHAPTERS ----------
    if tags["type"] in ("book", "assignment"):
        row = []
        for ch in range(1, 9):
            mark = "✅" if str(ch) in tags["chapters"] else "❎"
            row.append(
                InlineKeyboardButton(
                    f"{mark} Ch {ch}",
                    callback_data=f"{mode}_chapter:{ch}"
                )
            )
            if len(row) == 4:
                kb.row(*row)
                row = []
        if row:
            kb.row(*row)

    # ---------- EXAM YEARS ----------
    if tags["type"] == "exam":
        kb.row(
            InlineKeyboardButton(
                f"{'✅' if '2010' in tags['exam_year'] else '❎'} 2010",
                callback_data=f"{mode}_exam:2010"
            ),
            InlineKeyboardButton(
                f"{'✅' if '2015' in tags['exam_year'] else '❎'} 2015",
                callback_data=f"{mode}_exam:2015"
            ),
            InlineKeyboardButton(
                f"{'✅' if '2025' in tags['exam_year'] else '❎'} 2025",
                callback_data=f"{mode}_exam:2025"
            ),
        )

    # ---------- ACTIONS ----------
    kb.row(
        InlineKeyboardButton("✅ DONE", callback_data=f"{mode}_done"),
        InlineKeyboardButton("❌ CANCEL", callback_data=f"{mode}_cancel")
    )

    # ---------- SEND / EDIT ----------
    try:
<<<<<<< HEAD
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
                "📄 Select tags for your PDF. Tap ✅ Done when finished or ⬅️ Cancel to stop.",
                edit=True,
                user_id=user_id
            )

            bot.answer_callback_query(call.id)
            return

        # -------- DONE --------
        if data == "upload_done":
            info = pdf_upload_stage.get(user_id)
            tags = selected_user_tags.get(user_id)

            # validate before destroying state
            if not info or not tags:
                bot.answer_callback_query(call.id, "❌ Please select at least one tag before continuing.")
                return

            pdf_id = database.add_pdf(
                info["name"],
                info["file_id"],
                user_id
            )

            if not pdf_id:
                bot.answer_callback_query(call.id, "❌ Upload failed. Try again.")
                finalize_user(user_id)
                bot.edit_message_text(
                    "❌ Upload Invaild and  cancelled. You are now back at the main menu.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=buttons.main_menu()
                )
                return

            database.assign_tags_to_pdf(pdf_id, tags)

            # cleanup only after success
            finalize_user(user_id)  # clean memory & set status


            database.set_status(user_id, "menu:main")
            bot.edit_message_text(
                "✅ PDF uploaded successfully! You are now back at the main menu.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=buttons.main_menu()
=======
        if edit:
            bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=kb
            )
        else:
            bot.send_message(
                message.chat.id,
                "📄 Select tags below:",
                reply_markup=kb
>>>>>>> Advance catogry  but un solved
            )
    except Exception:
        bot.send_message(
            message.chat.id,
            "📄 Select tags below:",
            reply_markup=kb
        )

<<<<<<< HEAD
        # -------- CANCEL --------
        if data == "upload_cancel":
            finalize_user(user_id)
            bot.edit_message_text(
                "❌ Upload cancelled. You are now back at the main menu.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=buttons.main_menu()
            )
            return
=======
# ---------------- Upload PDF Flow ----------------
def start_upload(bot, message):
    user_id = message.from_user.id
    pdf_upload_stage.pop(user_id, None)
    database.set_status(user_id, "upload:waiting_file")
    bot.send_message(
        message.chat.id,
        "📄 Please send the PDF you want to upload.\n\nType /cancel to stop this operation.",
        reply_markup=ReplyKeyboardRemove()
    )
>>>>>>> Advance catogry  but un solved

def handle_pdf_upload(bot, message):
    user_id = message.from_user.id

    if not message.document or message.document.mime_type != "application/pdf":
        bot.send_message(
            message.chat.id,
            "❌ Please send a valid PDF file."
        )
        return

<<<<<<< HEAD
# ---------------- Search PDF Flow ----------------
def start_search(bot, message):
    try:
        user_id = message.from_user.id
        selected_user_tags.pop(user_id, None)
        database.set_status(user_id, "search:select_tags")
        selected_user_tags[user_id] = set()
        send_search_tag_selection(bot, message, "🔍 Select tags to search PDFs. Tap ✅ Done to view results or ⬅️ Cancel to stop.")
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        traceback.print_exc()
        bot.send_message(message.chat.id, f"⚠️ Something went wrong. Try again. {e}")

def send_search_tag_selection(bot, message, text_msg, *, edit=False, user_id=None):
    kb = InlineKeyboardMarkup(row_width=3)

    if user_id is None:
        user_id = message.from_user.id

    buttons = []

    for t in database.get_all_tags():
        tag = t["name"]
        mark = "✓" if tag in selected_user_tags.get(user_id, set()) else "×"
        buttons.append(
            InlineKeyboardButton(
                f"{mark} {tag}",
                callback_data=f"search_tag:{tag}"
            )
        )

    for i in range(0, len(buttons), 3):
        kb.row(*buttons[i:i+3])

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
                "🔍 Select tags to search PDFs. Tap ✅ Done to view results or ⬅️ Cancel to stop.",
                edit=True,
                user_id=user_id
            )
=======
    pdf_upload_stage[user_id] = {
        "file_id": message.document.file_id,
        "name": message.document.file_name,
        "tags": {
            "subject": set(),
            "type": None,
            "chapters": set(),
            "exam_year": set()
        }
    }

    database.set_status(user_id, "upload:select_tags")
    send_pdf_tag_selection(bot, message)



#----------------- advance upload callback with tag catogory
def handle_pdf_upload_callback(bot, call):
    user_id = call.from_user.id
    data = call.data
    stage = pdf_upload_stage.get(user_id)
    if not stage:
        bot.answer_callback_query(call.id, "❌ Upload session expired")
        return

    if database.get_user_status(user_id) != "upload:select_tags":
        bot.answer_callback_query(call.id, "❌ Upload expired")
        return

    tags = stage.setdefault("tags", {"subject": set(), "type": None, "chapters": set(), "exam_year": set()})

    if data.startswith("upload_subject:"):
        sub = data.split(":",1)[1]
        if sub in tags["subject"]:
            tags["subject"].remove(sub)
        else:
            tags["subject"].add(sub)

    elif data.startswith("upload_type:"):
        t = data.split(":",1)[1]
        tags["type"] = t
        # reset conditional selections
        tags["chapters"] = set()
        tags["exam_year"] = set()

    elif data.startswith("upload_chapter:"):
        ch = data.split(":",1)[1]
        if ch in tags["chapters"]:
            tags["chapters"].remove(ch)
        else:
            tags["chapters"].add(ch)

    elif data.startswith("upload_exam:"):
        y = data.split(":",1)[1]
        if y in tags["exam_year"]:
            tags["exam_year"].remove(y)
        else:
            tags["exam_year"].add(y)
>>>>>>> Advance catogry  but un solved

    elif data=="upload_done":
        info = stage
        if not info["tags"]["subject"] or not info["tags"]["type"]:
            bot.answer_callback_query(call.id, "❌ Must select subject and type")
            return
<<<<<<< HEAD

        # -------- DONE --------
        if data == "search_done":
            tags = selected_user_tags.pop(user_id, None)
        
            if not tags:
                bot.answer_callback_query(call.id, "❌ Select at least one tag to search PDFs.")
                return
        
            pdfs = database.get_pdfs_by_tags(list(tags))
            if not pdfs:
                finalize_user(user_id)
                bot.edit_message_text(
                    "❌ No PDFs found for the selected tags. Back to main menu.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=buttons.main_menu()
                )
                database.set_status(user_id, "menu:main")
                return
        
            # send first page of search results with pagination
            send_pdf_results(bot, call, pdfs, page=0)
        
            # store search context in memory so pagination works
            pdf_search_results[user_id] = pdfs
        
            database.set_status(user_id, "search:results")
=======
        pdf_id = database.add_pdf(info["name"], info["file_id"], user_id)
        if not pdf_id:
            bot.answer_callback_query(call.id, "❌ Failed to upload PDF")
>>>>>>> Advance catogry  but un solved
            return
        database.assign_multilevel_tags(pdf_id, info["tags"])
        pdf_upload_stage.pop(user_id, None)
        database.set_status(user_id, "menu:main")
        bot.edit_message_text(
            "✅ PDF uploaded successfully",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.main_menu()
        )
        return

<<<<<<< HEAD
        # -------- CANCEL --------
        if data == "search_cancel":
            finalize_user(user_id)
            bot.edit_message_text(
                "❌ Search cancelled. You are now back at the main menu.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=buttons.main_menu()
            )
            return
=======
    elif data=="upload_cancel":
        database.set_status(user_id, "menu:main")
        pdf_upload_stage.pop(user_id, None)
        bot.edit_message_text("❌ Upload cancelled", call.message.chat.id, call.message.message_id)
        return
>>>>>>> Advance catogry  but un solved

    send_pdf_tag_selection(bot, call.message, user_id=user_id, edit=True, mode="upload")
    bot.answer_callback_query(call.id)




# ---------------- Search PDF Flow ----------------
def start_search(bot, message):
    user_id = message.from_user.id

    search_selected_tags[user_id] = {
        "subject": set(),
        "type": None,
        "chapters": set(),
        "exam_year": set()
    }

    database.set_status(user_id, "search:select_tags")
    send_pdf_tag_selection(bot, message, user_id=user_id, mode="search")

def send_pdf_results(bot, call, pdfs, page=0, page_size=5):
    start = page * page_size
    end = start + page_size
    current_pdfs = pdfs[start:end]

    kb = InlineKeyboardMarkup(row_width=1)

    for p in current_pdfs:
        kb.add(
            InlineKeyboardButton(
                p["name"],
                callback_data=f"pdf_send:{p['id']}"
            )
        )

    pag_buttons = []
    if start > 0:
        pag_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"pdf_page:{page-1}")
        )
    if end < len(pdfs):
        pag_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"pdf_page:{page+1}")
        )

    if pag_buttons:
        kb.row(*pag_buttons)

    try:
        bot.edit_message_text(
            "📄 Select a PDF:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
    except Exception:
        bot.send_message(
            call.message.chat.id,
            "📄 Select a PDF:",
            reply_markup=kb
        )

def handle_search_callback(bot, call):
    user_id = call.from_user.id
    data = call.data

    tags = search_selected_tags.get(user_id)
    if not tags:
        bot.answer_callback_query(call.id, "❌ Search expired")
        database.set_status(user_id, "menu:main")
        bot.edit_message_text(
            "❌ Search expired.\n\nBack to main menu:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.main_menu()
        )
        return

    def toggle(set_obj, value):
        if value in set_obj:
            set_obj.remove(value)
        else:
            set_obj.add(value)

    if data.startswith("search_subject:"):
        toggle(tags["subject"], data.split(":", 1)[1])

    elif data.startswith("search_type:"):
        tags["type"] = data.split(":", 1)[1]
        tags["chapters"].clear()
        tags["exam_year"].clear()

    elif data.startswith("search_chapter:"):
        toggle(tags["chapters"], data.split(":", 1)[1])

    elif data.startswith("search_exam:"):
        toggle(tags["exam_year"], data.split(":", 1)[1])

    elif data == "search_done":
        if not tags["subject"] or not tags["type"]:
            bot.answer_callback_query(call.id, "❌ Select subject and type")
            return

        pdfs = database.get_pdfs_by_multilevel_tags(tags)

        if not pdfs:
            finalize_user(user_id)
            bot.edit_message_text(
                "❌ No PDFs found.\n\nBack to the main menu:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=buttons.main_menu()
            )
            return

        pdf_search_results[user_id] = pdfs
        database.set_status(user_id, "search:results")
        send_pdf_results(bot, call, pdfs, page=0)
        return

    elif data == "search_cancel":
        finalize_user(user_id)
        bot.edit_message_text(
            "❌ Search cancelled.\n\nBack to the main menu:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=buttons.main_menu()
        )
        return

    send_pdf_tag_selection(
        bot,
        call.message,
        user_id=user_id,
        edit=True,
        mode="search"
    )
    bot.answer_callback_query(call.id)


def send_pdf_with_inline(bot, pdf, chat_id):
    caption = (
        f"{pdf['name']}\n"
        "-----------------\n"
        f"⬇️ {pdf['downloads']} downloads"
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(f"❤️ {pdf['likes']}", callback_data=f"like_pdf:{pdf['id']}"))

    bot.send_document(
        chat_id,
        pdf['file_id'],
        caption=caption,
        reply_markup=kb
    )

    database.increment_download(pdf['id'])


def handle_pdf_interaction(bot, call):
    """Handle callback queries for sending PDFs, likes, and pagination"""
    user_id = call.from_user.id
    data = call.data

    # ---------- Send PDF ----------
    if data.startswith("pdf_send:"):
        pdf_id = int(data.split(":", 1)[1])
        pdf = database.get_pdf_by_id(pdf_id)
<<<<<<< HEAD
    
        if pdf:
            send_pdf_with_inline(bot, pdf, call.message.chat.id)
    
=======

        if pdf:
            send_pdf_with_inline(bot, pdf, call.message.chat.id)

>>>>>>> Advance catogry  but un solved
        try:
            bot.edit_message_text(
                "📄 PDF sent.",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
<<<<<<< HEAD
    
=======

>>>>>>> Advance catogry  but un solved
        bot.answer_callback_query(call.id)
        return

    # ---------- Like button ----------
    if data.startswith("like_pdf:"):
        pdf_id = int(data.split(":", 1)[1])
<<<<<<< HEAD
    
        success = database.like_pdf(pdf_id, user_id)
    
        if not success:
            bot.answer_callback_query(call.id, "❤️ Already liked")
            return
    
        pdf = database.get_pdf_by_id(pdf_id)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"❤️ {pdf['likes']}", callback_data=f"like_pdf:{pdf_id}"))
    
=======

        success = database.like_pdf(pdf_id, user_id)

        if not success:
            bot.answer_callback_query(call.id, "❤️ Already liked")
            return

        pdf = database.get_pdf_by_id(pdf_id)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"❤️ {pdf['likes']}", callback_data=f"like_pdf:{pdf_id}"))

>>>>>>> Advance catogry  but un solved
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
<<<<<<< HEAD
    
=======

>>>>>>> Advance catogry  but un solved
        bot.answer_callback_query(call.id, "❤️ Liked!")
        return

    # ---------- Pagination ----------
    if data.startswith("pdf_page:"):
        search_results = pdf_search_results.get(user_id)
        if not search_results:
            bot.answer_callback_query(call.id, "❌ No search context! Start a new search.")
            finalize_user(user_id)
            return

        page = int(data.split(":", 1)[1])
        send_pdf_results(bot, call, search_results, page=page)
        bot.answer_callback_query(call.id)
        return

# ---------------- Menu Router ----------------
def menu_router(bot, message):
    try:
        pdf_search_results.pop(message.from_user.id, None)
        search_selected_tags.pop(message.from_user.id, None)
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