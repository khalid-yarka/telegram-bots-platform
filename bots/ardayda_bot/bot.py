import telebot
from telebot.types import Message, Update
from bots.ardayda_bot import database, handlers, buttons

selected_user_tags = {}
pdf_upload_stage = {}

class PDFBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token,threaded=False)

        @self.bot.message_handler(content_types=["text","document"])
        def router(message: Message):
            user_id = message.from_user.id
            status = database.get_user_status(user_id)

            # --- registration ---
            if not database.get_user(user_id):
                database.add_user(user_id)
                database.set_status(user_id,"reg:name")
                self.bot.send_message(message.chat.id,"Enter your full name:")
                return

            if handlers.is_registering(user_id):
                if message.content_type!="text":
                    self.bot.send_message(message.chat.id,"❌ Use keyboard to continue registration.")
                else:
                    handlers.registration(self.bot,message)
                return

            # --- upload PDF ---
            if status and status.startswith("upload:"):
                if status=="upload:waiting_file" and message.content_type=="document":
                    file_name = message.document.file_name
                    file_id = message.document.file_id
                    pdf_upload_stage[user_id] = {"file_name":file_name,"file_id":file_id}
                    database.set_status(user_id,"upload:select_tags")
                    self.bot.send_message(message.chat.id,"Select tags for PDF:",reply_markup=buttons.search_tags_menu())
                elif status=="upload:select_tags":
                    self.bot.send_message(message.chat.id,"Select tags using inline buttons above.")
                return

            # --- menu ---
            if status and status.startswith("menu:"):
                handlers.menu_router(self.bot,message)

        # --- inline buttons ---
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_inline(call):
            user_id = call.from_user.id
            data = call.data

            # --- search tags ---
            if data.startswith("tag:"):
                tag = data.split(":",1)[1]
                tags = selected_user_tags.get(user_id,[])
                if tag in tags: tags.remove(tag)
                else: tags.append(tag)
                selected_user_tags[user_id]=tags
                self.bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=buttons.search_tags_menu(tags))
                return

            elif data=="find_pdfs":
                tags = selected_user_tags.get(user_id,[])
                pdfs = database.get_pdfs_by_tags(tags)
                if not pdfs:
                    self.bot.send_message(call.message.chat.id,"❌ No PDFs found.")
                else:
                    for p in pdfs:
                        text_msg=f"{p['name']} (⬇️ {p['downloads']} | ❤️ {p['likes']})"
                        self.bot.send_document(call.message.chat.id,p['file_id'],caption=text_msg,reply_markup=buttons.pdf_like_menu(p['id']))
                        database.increment_download(p['id'])
                selected_user_tags[user_id]=[]

            elif data=="cancel_search":
                self.bot.send_message(call.message.chat.id,"Search cancelled.")
                selected_user_tags[user_id]=[]

            # --- like PDF ---
            elif data.startswith("like:"):
                pdf_id = int(data.split(":",1)[1])
                database.like_pdf(pdf_id)
                self.bot.answer_callback_query(call.id,"❤️ Liked!")
                self.bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=buttons.pdf_like_menu(pdf_id))

            # --- upload PDF tags selection ---
            elif data=="tag_upload":
                tags = selected_user_tags.get(user_id,[])
                if not pdf_upload_stage.get(user_id): return
                pdf = pdf_upload_stage[user_id]
                pdf_id = database.add_pdf(pdf['file_name'],pdf['file_id'],user_id)
                database.assign_tags_to_pdf(pdf_id,tags)
                self.bot.send_message(call.message.chat.id,f"✅ PDF uploaded with tags: {', '.join(tags)}",reply_markup=buttons.main_menu())
                database.set_status(user_id,"menu:main")
                pdf_upload_stage.pop(user_id,None)
                selected_user_tags[user_id]=[]

    def process_update(self,update_json):
        update = Update.de_json(update_json)
        self.bot.process_new_updates([update])
        return True

# Run bot
if __name__=="__main__":
    TOKEN="7119823898:AAFNTiyEMvk5I6rdrarBP0uEOwniSyxF9u4"
    pdf_bot = PDFBot(TOKEN)
    pdf_bot.bot.infinity_polling()