import logging
from telebot import types

from utils.permissions import is_super_admin
from master_db.operations import (
    get_all_bots, get_recent_logs, get_bot_users,
    add_log_entry, get_setting, set_setting,
    get_webhook_status, get_bot_by_token,
    delete_bot, add_permission, check_permission
)
from utils.webhook_manager import set_webhook, delete_webhook, check_webhook
from utils.helpers import get_current_time, truncate_text

from datetime import datetime

logger = logging.getLogger(__name__)

class AdminCommands:
    """Super admin commands - Only for super admins!"""

    def __init__(self, bot_instance, bot_token):
        self.bot = bot_instance
        self.bot_token = bot_token

    def register_admin_handlers(self):
        """Register admin-only command handlers"""

        @self.bot.message_handler(commands=['admin', 'super'])
        def handle_admin(message):
            self.show_admin_panel(message)

        @self.bot.message_handler(commands=['admin_stats', 'stats'])
        def handle_admin_stats(message):
            self.show_system_stats(message)

        @self.bot.message_handler(commands=['admin_users'])
        def handle_admin_users(message):
            self.list_all_users(message)

        @self.bot.message_handler(commands=['admin_logs'])
        def handle_admin_logs(message):
            self.show_system_logs(message)

        @self.bot.message_handler(commands=['admin_cleanup'])
        def handle_admin_cleanup(message):
            self.cleanup_system(message)

    # ==================== ADMIN PANEL ====================

    def show_admin_panel(self, message):
        """Show admin panel with all commands"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_super_admin(user_id):
            self.bot.send_message(chat_id, "❌ Super admin access required.")
            return

        text = (
            "👑 **SUPER ADMIN CONTROL PANEL**\n\n"
            "📊 **Statistics:**\n"
            "/admin_stats - System statistics\n\n"
            "👥 **User Management:**\n"
            "/admin_users - List all users\n\n"
            "🤖 **Bot Management:**\n"
            "/admin_logs - View all system logs\n\n"
            "⚙️ **System Tools:**\n"
            "/admin_cleanup - Clean old data\n\n"
            "⚠️ These commands affect the entire system!"
        )

        # Create inline keyboard for quick access
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            types.InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            types.InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
            types.InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup")
        )
        markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu"))

        self.bot.send_message(
            chat_id, 
            text, 
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        add_log_entry(self.bot_token, 'admin_panel', user_id)

    # ==================== SYSTEM STATISTICS ====================

    def show_system_stats(self, message):
        """Show detailed system statistics"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_super_admin(user_id):
            self.bot.send_message(chat_id, "❌ Super admin access required.")
            return

        from master_db.connection import test_connection

        # Get data
        bots = get_all_bots()
        recent_logs = get_recent_logs(limit=500)
        db_connected = test_connection()

        # Calculate statistics
        total_bots = len(bots)
        active_bots = sum(1 for b in bots if b.get('is_active', False))

        bot_types = {}
        for bot in bots:
            bot_type = bot.get('bot_type', 'unknown')
            bot_types[bot_type] = bot_types.get(bot_type, 0) + 1

        # Log statistics
        log_by_type = {}
        for log in recent_logs:
            log_type = log.get('action_type', 'unknown')
            log_by_type[log_type] = log_by_type.get(log_type, 0) + 1

        # Webhook status
        webhook_status = {'active': 0, 'failed': 0, 'pending': 0}
        for bot in bots:
            status = get_webhook_status(bot['bot_token'])
            if status:
                webhook_status[status.get('status', 'pending')] = webhook_status.get(status.get('status', 'pending'), 0) + 1

        text = (
            f"📊 **SYSTEM STATISTICS**\n\n"
            f"✅ Database: {'Connected' if db_connected else 'Disconnected'}\n"
            f"📅 Time: {get_current_time()}\n\n"
            f"🤖 **BOT STATISTICS:**\n"
            f"Total bots: {total_bots}\n"
            f"Active bots: {active_bots}\n"
            f"Inactive bots: {total_bots - active_bots}\n"
        )
        
        text += "By type:\n"
        for bot_type, count in bot_types.items():
            text += f"  • {bot_type}: {count}\n"
        
        text += f"\n🌐 **WEBHOOK STATUS:**\n"
        text += f"✅ Active: {webhook_status.get('active', 0)}\n"
        text += f"❌ Failed: {webhook_status.get('failed', 0)}\n"
        text += f"⏳ Pending: {webhook_status.get('pending', 0)}\n\n"

        text += f"📝 **RECENT ACTIVITY** (Last 500 logs):\n"
        for log_type, count in list(log_by_type.items())[:5]:
            text += f"  • {log_type}: {count}\n"

        if len(log_by_type) > 5:
            text += f"  • ... and {len(log_by_type) - 5} more types\n"

        # Add refresh button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats"))

        self.bot.send_message(
            chat_id, 
            text, 
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        add_log_entry(self.bot_token, 'admin_stats', user_id)

    # ==================== LIST ALL USERS ====================

    def list_all_users(self, message):
        """List all users in the system"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_super_admin(user_id):
            self.bot.send_message(chat_id, "❌ Super admin access required.")
            return

        # Get all unique users from system logs
        logs = get_recent_logs(limit=1000)

        # Extract unique user IDs
        user_ids = set()
        for log in logs:
            if log.get('user_id'):
                user_ids.add(log['user_id'])

        # Get bot owners
        bots = get_all_bots()
        for bot in bots:
            if bot.get('owner_id'):
                user_ids.add(bot['owner_id'])

        total_users = len(user_ids)

        if total_users == 0:
            text = "👥 No users found in the system."
        else:
            text = f"👥 **SYSTEM USERS** ({total_users}):\n\n"

            # Show first 20 users
            user_list = list(user_ids)
            for i, uid in enumerate(user_list[:20], 1):
                # Get last activity for this user
                user_logs = [log for log in logs if log.get('user_id') == uid]
                last_seen = user_logs[0].get('timestamp') if user_logs else 'Never'
                last_action = user_logs[0].get('action_type') if user_logs else 'No activity'

                text += f"{i}. User ID: `{uid}`\n"
                text += f"   Last seen: {last_seen}\n"
                text += f"   Last action: {last_action}\n\n"

            if total_users > 20:
                text += f"... and {total_users - 20} more users"

        self.bot.send_message(chat_id, text, parse_mode='Markdown')
        add_log_entry(self.bot_token, 'admin_users', user_id)

    # ==================== SYSTEM LOGS ====================

    def show_system_logs(self, message):
        """Show detailed system logs"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_super_admin(user_id):
            self.bot.send_message(chat_id, "❌ Super admin access required.")
            return

        # Parse command: /admin_logs <limit>
        parts = message.text.split()
        limit = 20

        if len(parts) > 1:
            try:
                limit = min(int(parts[1]), 50)  # Max 50 logs
            except:
                pass

        # Get logs
        logs = get_recent_logs(limit=limit)

        if not logs:
            text = "📭 No logs found."
        else:
            text = f"📋 **SYSTEM LOGS** (Last {len(logs)}):\n\n"

            for log in logs:
                timestamp = log.get('timestamp', 'N/A')
                bot_token = log.get('bot_token', 'N/A')[:10]
                user_id_log = log.get('user_id', 'System')
                action = log.get('action_type', 'unknown')
                details = truncate_text(log.get('details', ''), 30)

                # Format time
                if ' ' in str(timestamp):
                    time_part = str(timestamp).split(' ')[1][:8]
                else:
                    time_part = str(timestamp)[11:19] if len(str(timestamp)) > 19 else str(timestamp)

                text += f"🕒 {time_part} | 🤖 {bot_token}... | 👤 {user_id_log}\n"
                text += f"   📝 {action}"
                if details:
                    text += f" | {details}"
                text += "\n\n"

        self.bot.send_message(chat_id, text, parse_mode='Markdown')
        add_log_entry(self.bot_token, 'admin_logs', user_id)

    # ==================== CLEANUP SYSTEM ====================

    def cleanup_system(self, message):
        """Clean up old system data"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_super_admin(user_id):
            self.bot.send_message(chat_id, "❌ Super admin access required.")
            return

        # Get setting for log retention
        retention_days = int(get_setting('system', 'log_retention_days', 30))

        # Import connection for direct SQL
        from master_db.connection import get_db_connection

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete old logs
            cursor.execute("""
                DELETE FROM system_logs
                WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (retention_days,))
            deleted_logs = cursor.rowcount

            conn.commit()

        text = (
            f"🧹 **SYSTEM CLEANUP COMPLETE**\n\n"
            f"Deleted old logs: {deleted_logs} entries\n"
            f"Log retention: {retention_days} days\n\n"
            f"✅ System cleaned successfully!"
        )

        self.bot.send_message(chat_id, text, parse_mode='Markdown')
        add_log_entry(self.bot_token, 'admin_cleanup', user_id)
        
    # ==================== ADMIN CALLBACK HANDLERS ====================

    def register_admin_callbacks(self):
        """Register admin callback handlers"""
        
        @self.bot.bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
        def handle_admin_stats_callback(call):
            self.show_system_stats(call.message)
        
        @self.bot.bot.callback_query_handler(func=lambda call: call.data == "admin_users")
        def handle_admin_users_callback(call):
            self.list_all_users(call.message)
        
        @self.bot.bot.callback_query_handler(func=lambda call: call.data == "admin_logs")
        def handle_admin_logs_callback(call):
            self.show_system_logs(call.message)
        
        @self.bot.bot.callback_query_handler(func=lambda call: call.data == "admin_cleanup")
        def handle_admin_cleanup_callback(call):
            self.cleanup_system(call.message)