import telebot
from telebot.types import Message
from bots.ardayda_bot import database, buttons

selected_user_tags = {}
pdf_upload_stage = {}

TOKEN = "7119823898:AAFNTiyEMvk5I6rdrarBP0uEOwniSyxF9u4"
bot = telebot.TeleBot(TOKEN, threaded=False)

# ----------------- Message handler -----------------
@bot.message_handler(content_types=["text","document"])
def router(message: Message):
    try:
        user_id = message.from_user.id
        status = database.get_user_status(user_id)

        # registration
        if not database.get_user(user_id):
            database.add_user(user_id)
            database.set_status(user_id, "reg:name")
            bot.send_message(message.chat.id, "Enter full name:")
            return

        # upload PDF
        if status and status.startswith("upload:"):
            if status=="upload:waiting_file" and message.content_type=="document":
                pdf_upload_stage[user_id] = {"file_id": message.document.file_id, "name": message.document.file_name}
                database.set_status(user_id,"upload:select_tags")
                selected_user_tags[user_id] = []
                bot.send_message(message.chat.id,"Select tags for this PDF:", reply_markup=buttons.tag_inline_menu([]))
                return
            else:
                bot.send_message(message.chat.id,"Send a PDF file to upload.")
                return

        # menu
        if status and (status.startswith("menu:") or status.startswith("reg:")):
            if message.content_type=="text":
                menu_router(message)
            else:
                bot.send_message(message.chat.id,"❌ Please use the keyboard.")
            return

    except Exception as e:
        print("Router error:",e)
        bot.send_message(message.chat.id,f"⚠️ Error: {e}")

# ----------------- Menu handler -----------------
def menu_router(message):
    user_id = message.from_user.id
    text_msg = message.text
    if text_msg == buttons.PROFILE:
        show_profile(message)
    elif text_msg == buttons.SEARCH:
        selected_user_tags[user_id]=[]
        bot.send_message(message.chat.id,"Select tags to search:", reply_markup=buttons.tag_inline_menu([]))
    elif text_msg == buttons.UPLOAD:
        database.set_status(user_id,"upload:waiting_file")
        bot.send_message(message.chat.id,"Send me the PDF file to upload:")
    else:
        bot.send_message(message.chat.id,"📋 Main menu", reply_markup=buttons.main_menu())

def show_profile(message):
    user = database.get_user(message.from_user.id)
    profile = f"👤 *My Profile*\n\n📛 Name: {user['name']}\n🌍 Region: {user['region']}\n🏫 School: {user['school']}\n🎓 Class: {user['class_']}"
    bot.send_message(message.chat.id,profile,parse_mode="Markdown",reply_markup=buttons.main_menu())

# ----------------- Inline handler -----------------
@bot.callback_query_handler(func=lambda call: True)
def inline_router(call):
    try:
        user_id = call.from_user.id
        data = call.data

        # toggle tag
        if data.startswith("tag:"):
            tag = data.split(":",1)[1]
            tags = selected_user_tags.get(user_id,[])
            if tag in tags: tags.remove(tag)
            else: tags.append(tag)
            selected_user_tags[user_id]=tags
            bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=buttons.tag_inline_menu(tags))
            return

        if data=="tag_done":
            status = database.get_user_status(user_id)
            tags = selected_user_tags.get(user_id,[])
            if status=="upload:select_tags" and pdf_upload_stage.get(user_id):
                pdf = pdf_upload_stage.pop(user_id)
                pdf_id = database.add_pdf(pdf["name"],pdf["file_id"],user_id)
                database.assign_tags_to_pdf(pdf_id,tags)
                database.set_status(user_id,"menu:main")
                selected_user_tags[user_id]=[]
                bot.send_message(call.message.chat.id,f"✅ PDF uploaded with tags: {', '.join(tags)}", reply_markup=buttons.main_menu())
            else:
                # search
                pdfs = database.get_pdfs_by_tags(tags)
                if not pdfs: bot.send_message(call.message.chat.id,"❌ No PDFs found.")
                else:
                    for p in pdfs:
                        text_msg = f"{p['name']} (⬇️ {p['downloads']} | ❤️ {p['likes']})"
                        bot.send_document(call.message.chat.id,p['file_id'],caption=text_msg,reply_markup=buttons.pdf_like_menu(p['id']))
                        database.increment_download(p['id'])
                selected_user_tags[user_id]=[]
            return

        if data=="cancel":
            bot.send_message(call.message.chat.id,"Cancelled.",reply_markup=buttons.main_menu())
            selected_user_tags[user_id]=[]
            database.set_status(user_id,"menu:main")
            return

        if data.startswith("like:"):
            pdf_id = int(data.split(":",1)[1])
            database.like_pdf(pdf_id)
            bot.answer_callback_query(call.id,"❤️ Liked!")
            bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=buttons.pdf_like_menu(pdf_id))

    except Exception as e:
        print("Inline handler error:", e)
        bot.answer_callback_query(call.id,f"⚠️ Error: {e}")

# ----------------- Run bot -----------------
if __name__=="__main__":
    bot.infinity_polling()