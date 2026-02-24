# bots/ardayda_bot/handlers.py

from bots.ardayda_bot import (
    database,
    buttons,
    text,
    upload_flow,
    search_flow,
    profile
)
from bots.ardayda_bot.session_manager import (
    start_session,
    end_session,
    get_session,
    has_active_session
)

# ---------- REGISTRATION HELPERS (UNCHANGED LOGIC) ----------

def is_registering(user_id):
    status = database.get_user_status(user_id)
    return status and status.startswith("reg:")


def finalize_user(user_id):
    database.set_status(user_id, "menu:home")


def registration(bot, message):
    user_id = message.from_user.id

    database.set_user_name(user_id, message.text.strip())
    database.set_status(user_id, "menu:home")

    bot.send_message(
        message.chat.id,
        text.REG_SUCCESS,
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )


# ---------- MENU ROUTER ----------

def menu_router(bot, message):
    user_id = message.from_user.id
    msg = message.text.strip()

    # Block actions during active session
    if has_active_session(user_id):
        session = get_session(user_id)
        if session["status"] == "upload":
            bot.send_message(message.chat.id, text.CONFLICT_UPLOAD)
        elif session["status"] == "search":
            bot.send_message(message.chat.id, text.CONFLICT_SEARCH)
        return

    if msg == "📤 Upload":
        start_session(user_id, "upload")
        upload_flow.start(bot, message)

    elif msg == "🔍 Search":
        start_session(user_id, "search")
        search_flow.start(bot, message)

    elif msg == "👤 Profile":
        profile.show(bot, message)

    else:
        bot.send_message(message.chat.id, text.UNKNOWN_INPUT)


# ---------- CANCEL HANDLER ----------

def cancel_operation(bot, message):
    user_id = message.from_user.id

    if is_registering(user_id):
        bot.send_message(
            message.chat.id,
            "❌ Registration cannot be cancelled.\nPlease complete it first."
        )
        return

    end_session(user_id)
    finalize_user(user_id)

    bot.send_message(
        message.chat.id,
        text.CANCELLED,
        reply_markup=buttons.main_menu(),
        parse_mode="Markdown"
    )


# ---------- CALLBACK ROUTER ----------

def handle_callback(bot, call):
    user_id = call.from_user.id
    data = call.data

    session = get_session(user_id)

    if not session:
        bot.answer_callback_query(call.id, text.SESSION_EXPIRED)
        return

    # ---- UPLOAD FLOW ----
    if session["status"] == "upload" and data.startswith("upload_"):
        upload_flow.handle_callback(bot, call)
        return

    # ---- SEARCH FLOW ----
    if session["status"] == "search" and data.startswith("search_"):
        search_flow.handle_callback(bot, call)
        return

    # ---- PAGINATION / PDF ACTIONS ----
    if data.startswith(("pdf_page:", "pdf_send:")):
        search_flow.handle_pdf_action(bot, call)
        return

    # ---- STALE BUTTON ----
    bot.answer_callback_query(call.id, "❌ This action is no longer available.")