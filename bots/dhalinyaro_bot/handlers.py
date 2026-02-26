import logging
from telebot import types

logger = logging.getLogger(__name__)

def setup_dhalinyaro_handlers(bot):
    """Setup callback handlers for Dhalinyaro bot"""

    @bot.callback_query_handler(func=lambda call: True)
    def handle_dhalinyaro_callback(call):
        """Handle Dhalinyaro bot callback queries"""
        try:
            data = call.data

            if data.startswith('event_'):
                event_id = data.split('_')[1]
                bot.answer_callback_query(call.id, "Loading event details...")
                handle_event_details(bot, call, event_id)

            elif data.startswith('join_group_'):
                group_id = data.split('_')[2]
                bot.answer_callback_query(call.id, "Joining group...")
                handle_join_group(bot, call, group_id)

            elif data == 'organize_event':
                bot.answer_callback_query(call.id, "Event organization")
                handle_organize_event(bot, call)

            else:
                bot.answer_callback_query(call.id, "Action processed")

        except Exception as e:
            logger.error(f"Dhalinyaro callback error: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Error processing request")

def handle_event_details(bot, call, event_id):
    """Handle event details selection"""
    from bots.dhalinyaro_bot.database import get_upcoming_events

    events = get_upcoming_events()
    event = next((e for e in events if str(e['id']) == event_id), None)

    if event:
        response = f"🎯 {event.get('event_name', 'Event')}\n\n"
        response += f"Type: {event.get('event_type', 'N/A')}\n"
        response += f"Date: {event.get('event_date', 'TBD')}\n"
        response += f"Location: {event.get('location', 'Online')}\n\n"
        response += f"Description: {event.get('description', 'No description')}\n\n"
        response += "React with 👍 to show interest!"
    else:
        response = "Event not found."

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, response)

def handle_join_group(bot, call, group_id):
    """Handle join group button"""
    from bots.dhalinyaro_bot.database import get_dhalinyaro_groups

    groups = get_dhalinyaro_groups()
    group = next((g for g in groups if str(g['id']) == group_id), None)

    if group:
        response = f"✅ Joined: {group.get('group_name', 'Group')}\n\n"
        response += f"Welcome to the {group.get('group_type', '')} group!\n"
        response += "You'll receive updates and can participate in group activities."
    else:
        response = "Group not found."

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, response)

def handle_organize_event(bot, call):
    """Handle organize event button"""
    response = "🤝 Organize Your Event\n\n"
    response += "To organize an event:\n"
    response += "1. Message the admin\n"
    response += "2. Provide event details\n"
    response += "3. Choose date & location\n"
    response += "4. We'll help promote it!\n\n"
    response += "Contact @admin_username to start."

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, response)

def create_events_keyboard():
    """Create inline keyboard for events"""
    from bots.dhalinyaro_bot.database import get_upcoming_events

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    events = get_upcoming_events()

    for event in events[:5]:  # Show first 5 events
        button = types.InlineKeyboardButton(
            text=f"📅 {event.get('event_name', 'Event')}",
            callback_data=f"event_{event['id']}"
        )
        keyboard.add(button)

    organize_btn = types.InlineKeyboardButton(
        "🤝 Organize Event",
        callback_data="organize_event"
    )
    keyboard.add(organize_btn)

    return keyboard

def create_groups_keyboard():
    """Create inline keyboard for groups"""
    from bots.dhalinyaro_bot.database import get_dhalinyaro_groups

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    groups = get_dhalinyaro_groups()

    for group in groups[:5]:  # Show first 5 groups
        button = types.InlineKeyboardButton(
            text=f"👥 {group.get('group_name', 'Group')}",
            callback_data=f"join_group_{group['id']}"
        )
        keyboard.add(button)

    return keyboard