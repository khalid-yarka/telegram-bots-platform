# bots/ardayda_bot/profile.py

from telebot.types import Message
from bots.ardayda_bot import database, buttons

def show(bot, message: Message):
    """Display user profile information"""
    user_id = message.from_user.id
    
    # Get user data from database
    user = database.get_user(user_id)
    
    if not user:
        bot.send_message(
            message.chat.id,
            "❌ User not found. Please start over with /cancel",
            reply_markup=buttons.main_menu(user_id)
        )
        return
    
    # Get user's PDF upload count
    pdf_count = database.get_user_pdfs_count(user_id)
    
    # Format creation date
    created_at = user.get('created_at')
    if created_at:
        if hasattr(created_at, 'strftime'):
            join_date = created_at.strftime("%Y-%m-%d")
        else:
            join_date = str(created_at).split()[0]  # Take first part if string
    else:
        join_date = "Unknown"
    
    # Build profile message
    name = user.get('name', 'Not set')
    region = user.get('region', 'Not set')
    school = user.get('school', 'Not set')
    user_class = user.get('class', 'Not set')
    
    profile_text = (
        f"👤 *Your Profile*\n\n"
        f"📝 *Name:* {name}\n"
        f"📍 *Region:* {region}\n"
        f"🏫 *School:* {school}\n"
        f"📚 *Class:* {user_class}\n\n"
        f"📊 *Statistics:*\n"
        f"📄 PDFs uploaded: {pdf_count}\n"
        f"📅 Member since: {join_date}"
    )
    
    bot.send_message(
        message.chat.id,
        profile_text,
        reply_markup=buttons.main_menu(user_id),
        parse_mode="Markdown"
    )