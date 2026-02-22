from bots.ardayda_bot import database, buttons, text
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import traceback

# Dynamic upload sequences based on PDF type


# ================= MEMORY =================
pdf_upload_stage = {}        # user_id -> {file_id, name}
selected_user_tags = {}     # user_id -> {subject, chapter, type}
pdf_search_results = {}     # user_id -> search results
UPLOAD_SEQUENCE = {
    "Book": ["subject", "type"],
    "Assignment": ["subject", "type", "chapter"],
    "Exam": ["subject", "type", "year_or_exam_type"]
}
UPLOAD_STEPS = ["subject", "chapter", "type"]

# ================= HELPERS =================
def finalize_user(user_id):
    pdf_upload_stage.pop(user_id, None)
    selected_user_tags.pop(user_id, None)
    pdf_search_results.pop(user_id, None)
    database.set_status(user_id, "menu:main")


def is_registering(user_id):
    status = database.get_user_status(user_id)
    return bool(status and status.startswith("reg:"))


def is_uploading(user_id):
    status = database.get_user_status(user_id)
    return bool(status and status.startswith("upload:"))


# ================= REGISTRATION =================
def registration(bot, message: Message):
    try:
        user_id = message.from_user.id
        msg = message.text.strip()
        status = database.get_user_status(user_id)

        if not status or ":" not in status:
            database.set_status(user_id, "reg:name")
            bot.send_message(message.chat.id, text.REG_NAME)
            return

        step = status.split(":", 1)[1]

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
                bot.send_message(message.chat.id, "❌ Select region using keyboard.", reply_markup=buttons.region_menu())
                return
            database.update_user(user_id, region=msg)
            database.set_status(user_id, "reg:school")
            bot.send_message(message.chat.id, text.REG_SCHOOL, reply_markup=buttons.school_menu(msg))

        elif step == "school":
            user = database.get_user(user_id)
            if msg not in text.form_four_schools_by_region[user["region"]]:
                bot.send_message(message.chat.id, "❌ Select school using keyboard.", reply_markup=buttons.school_menu(user["region"]))
                return
            database.update_user(user_id, school=msg)
            database.set_status(user_id, "reg:class")
            bot.send_message(message.chat.id, text.REG_CLASS, reply_markup=buttons.class_menu())

        elif step == "class":
            if msg not in ["F1", "F2", "F3", "F4"]:
                bot.send_message(message.chat.id, "❌ Select class using keyboard.", reply_markup=buttons.class_menu())
                return
            database.update_user(user_id, class_=msg)
            database.set_status(user_id, "menu:main")
            bot.send_message(message.chat.id, text.REG_DONE, reply_markup=buttons.main_menu())

    except Exception as e:
        traceback.print_exc()
        bot.send_message(message.chat.id, "⚠️ Registration error. Try again.")


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


# ================= PROFILE =================
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


# ================= UPLOAD FLOW =================

# ================= HELPERS =================
def finalize_user(user_id):
    pdf_upload_stage.pop(user_id, None)
    selected_user_tags.pop(user_id, None)
    database.set_status(user_id, "menu:main")


# ---------------- START UPLOAD ----------------
def start_upload(bot, message: Message):
    user_id = message.from_user.id
    pdf_upload_stage.pop(user_id, None)
    selected_user_tags[user_id] = {"subject": None, "type": None, "chapter": None, "year_or_exam_type": None}
    database.set_status(user_id, "upload:waiting_file")
    bot.send_message(message.chat.id, "📄 Send the PDF file.\n/cancel to stop.")


# ---------------- HANDLE PDF ----------------
def handle_pdf_upload(bot, message: Message):
    user_id = message.from_user.id

    if not message.document or message.document.mime_type != "application/pdf":
        bot.send_message(message.chat.id, "❌ Send a valid PDF file.")
        return

    pdf_upload_stage[user_id] = {
        "file_id": message.document.file_id,
        "name": message.document.file_name
    }

    database.set_status(user_id, "upload:subject")
    send_upload_step(bot, message, "subject", user_id=user_id)


# ---------------- SEND INLINE ----------------
def send_upload_step(bot, message, step, *, edit=False, user_id=None):
    user_id = user_id or message.from_user.id
    kb = InlineKeyboardMarkup(row_width=3)

    # Determine category and label
    category = step
    label = step.replace("_", " ").title()
    if step == "chapter_or_year":  # fallback not really used
        pdf_type = selected_user_tags[user_id]["type"]
        if pdf_type == "Assignment":
            category = "chapter"
            label = "Chapter"
        elif pdf_type == "Exam":
            category = "year_or_exam_type"
            label = "Year / Exam Type"

    # Add buttons for each tag
    for tag in database.get_tags_by_category(category):
        selected = "✓" if selected_user_tags[user_id].get(category) == tag["name"] else "×"
        kb.add(
            InlineKeyboardButton(
                f"{selected} {tag['name']}",
                callback_data=f"upload_{category}:{tag['name']}"
            )
        )

    kb.add(InlineKeyboardButton("⬅️ Cancel", callback_data="upload_cancel"))

    if edit:
        bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup=kb)
    else:
        bot.send_message(message.chat.id, f"Select {label}:", reply_markup=kb)


# ---------------- CALLBACK HANDLER ----------------
def handle_upload_callback(bot, call: CallbackQuery):
    try:
        user_id = call.from_user.id
        data = call.data

        if data == "upload_cancel":
            finalize_user(user_id)
            bot.edit_message_text(
                "❌ Upload cancelled.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=buttons.main_menu()
            )
            return

        if ":" not in data:
            bot.answer_callback_query(call.id, "❌ Invalid selection.")
            return

        step, value = data.split(":", 1)
        step = step.replace("upload_", "")
        selected_user_tags[user_id][step] = value

        # Determine next step dynamically
        pdf_type = selected_user_tags[user_id].get("type")
        sequence = UPLOAD_SEQUENCE.get(pdf_type, ["subject", "type", "chapter_or_year"])
        try:
            idx = sequence.index(step)
            next_step = sequence[idx + 1]
        except (ValueError, IndexError):
            next_step = None

        if next_step:
            database.set_status(user_id, f"upload:{next_step}")
            send_upload_step(bot, call.message, next_step, edit=True, user_id=user_id)
        else:
            finalize_pdf_upload(bot, call, user_id)

        bot.answer_callback_query(call.id)

    except Exception:
        traceback.print_exc()
        bot.send_message(call.message.chat.id, "⚠️ Upload error.")


# ---------------- FINALIZE UPLOAD ----------------
def finalize_pdf_upload(bot, call, user_id):
    info = pdf_upload_stage.get(user_id)
    tags = selected_user_tags.get(user_id)

    if not info or not tags:
        bot.answer_callback_query(call.id, "❌ Upload failed.")
        return

    pdf_id = database.add_pdf(info["name"], info["file_id"], user_id)

    # Assign selected tags
    if tags.get("subject"):
        database.assign_tag_to_pdf(pdf_id, tags["subject"], "subject")
    if tags.get("type"):
        database.assign_tag_to_pdf(pdf_id, tags["type"], "type")
    if tags.get("chapter") and tags["type"] == "Assignment":
        database.assign_tag_to_pdf(pdf_id, tags["chapter"], "chapter")
    if tags.get("year_or_exam_type") and tags["type"] == "Exam":
        database.assign_tag_to_pdf(pdf_id, tags["year_or_exam_type"], "year_or_exam_type")

    finalize_user(user_id)

    bot.edit_message_text(
        "✅ PDF uploaded successfully.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=buttons.main_menu()
    )

# ================= MENU ROUTER =================
def menu_router(bot, message):
    if message.text == buttons.Main.PROFILE:
        show_profile(bot, message)
    elif message.text == buttons.Main.UPLOAD:
        start_upload(bot, message)
    else:
        bot.send_message(message.chat.id, "📋 Main menu", reply_markup=buttons.main_menu())