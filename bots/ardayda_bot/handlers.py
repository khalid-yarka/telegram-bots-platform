import logging
from telebot import types

logger = logging.getLogger(__name__)

def setup_ardayda_handlers(bot):
    """Setup callback handlers for Ardayda bot"""

    @bot.callback_query_handler(func=lambda call: True)
    def handle_ardayda_callback(call):
        """Handle Ardayda bot callback queries"""
        try:
            data = call.data

            if data.startswith('course_'):
                course_id = data.split('_')[1]
                bot.answer_callback_query(call.id, "Loading course materials...")
                handle_course_materials(bot, call, course_id)

            elif data == 'more_courses':
                bot.answer_callback_query(call.id, "Loading more courses...")
                handle_more_courses(bot, call)

            else:
                bot.answer_callback_query(call.id, "Action processed")

        except Exception as e:
            logger.error(f"Ardayda callback error: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Error processing request")

def handle_course_materials(bot, call, course_id):
    """Handle course materials selection"""
    from bots.ardayda_bot.database import get_ardayda_courses

    courses = get_ardayda_courses()
    course = next((c for c in courses if str(c['id']) == course_id), None)

    if course:
        response = f"📘 {course.get('course_name', 'Course')}\n\n"
        response += f"Code: {course.get('course_code', 'N/A')}\n"
        response += f"Description: {course.get('description', 'No description')}\n\n"
        response += "Materials available:\n"
        response += "• Lecture Notes\n"
        response += "• Past Papers\n"
        response += "• Video Tutorials\n"
        response += "• Reference Books"
    else:
        response = "Course not found."

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, response)

def handle_more_courses(bot, call):
    """Handle more courses button"""
    from bots.ardayda_bot.database import get_ardayda_courses

    courses = get_ardayda_courses()

    response = "🎓 All Available Courses:\n\n"
    for course in courses:
        response += f"• {course.get('course_name')} ({course.get('course_code')})\n"

    try:
        bot.edit_message_text(
            response,
            call.message.chat.id,
            call.message.message_id
        )
    except:
        bot.send_message(call.message.chat.id, response)

def create_courses_keyboard():
    """Create inline keyboard for courses"""
    from bots.ardayda_bot.database import get_ardayda_courses

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    courses = get_ardayda_courses()

    for course in courses[:6]:  # Show first 6 courses
        button = types.InlineKeyboardButton(
            text=course.get('course_name', 'Course'),
            callback_data=f"course_{course['id']}"
        )
        keyboard.add(button)

    # Add more button if there are more courses
    if len(courses) > 6:
        more_btn = types.InlineKeyboardButton("More Courses 📚", callback_data="more_courses")
        keyboard.add(more_btn)

    return keyboard