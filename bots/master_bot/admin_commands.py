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
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminCommands:
    """Super admin commands - Only for you!"""

    def __init__(self, bot_instance, bot_token):
        self.bot = bot_instance
        self.bot_token = bot_token

    def register_admin_handlers(self):
        """Register admin-only command handlers"""

        # Admin panel
        @self.bot.message_handler(commands=['admin', 'super'])
        def handle_admin(message):
            self.show_admin_panel(message)

        # System stats
        @self.bot.message_handler(commands=['admin_stats', 'stats'])
        def handle_admin_stats(message):
            self.show_system_stats(message)

        # List all users
        @self.bot.message_handler(commands=['admin_users'])
        def handle_admin_users(message):
            self.list_all_users(message)

        # System logs
        @self.bot.message_handler(commands=['admin_logs'])
        def handle_admin_logs(message):
            self.show_system_logs(message)

        # Cleanup old data
        @self.bot.message_handler(commands=['admin_cleanup'])
        def handle_admin_cleanup(message):
            self.cleanup_system(message)

    def show_admin_panel(self, message):
        """Show admin panel with all commands"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Super admin access required.")
            return

        response = "👑 SUPER ADMIN CONTROL PANEL\n\n"
        response += "📊 Statistics:\n"
        response += "/admin_stats - System statistics\n\n"

        response += "👥 User Management:\n"
        response += "/admin_users - List all users\n\n"

        response += "🤖 Bot Management:\n"
        response += "/admin_logs - View all system logs\n\n"

        response += "⚙️ System Tools:\n"
        response += "/admin_cleanup - Clean old data\n\n"

        response += "⚠️ These commands affect the entire system!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'admin_command', user_id, '/admin_panel')

    def show_system_stats(self, message):
        """Show detailed system statistics"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Super admin access required.")
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

        response = "📊 SYSTEM STATISTICS\n\n"
        response += f"✅ Database: {'Connected' if db_connected else 'Disconnected'}\n"
        response += f"📅 Time: {get_current_time()}\n\n"

        response += "🤖 BOT STATISTICS:\n"
        response += f"Total bots: {total_bots}\n"
        response += f"Active bots: {active_bots}\n"
        response += "By type:\n"
        for bot_type, count in bot_types.items():
            response += f"  • {bot_type}: {count}\n"
        response += "\n"

        response += "🌐 WEBHOOK STATUS:\n"
        response += f"✅ Active: {webhook_status.get('active', 0)}\n"
        response += f"❌ Failed: {webhook_status.get('failed', 0)}\n"
        response += f"⏳ Pending: {webhook_status.get('pending', 0)}\n\n"

        response += "📝 RECENT ACTIVITY (Last 500 logs):\n"
        for log_type, count in list(log_by_type.items())[:5]:  # Show top 5
            response += f"  • {log_type}: {count}\n"

        if len(log_by_type) > 5:
            response += f"  • ... and {len(log_by_type) - 5} more types\n"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'admin_command', user_id, '/admin_stats')

    def list_all_users(self, message):
        """List all users in the system"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Super admin access required.")
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
            response = "👥 No users found in the system."
        else:
            response = f"👥 SYSTEM USERS ({total_users}):\n\n"

            # Show first 20 users
            user_list = list(user_ids)
            for i, uid in enumerate(user_list[:20], 1):
                # Get last activity for this user
                user_logs = [log for log in logs if log.get('user_id') == uid]
                last_seen = user_logs[0].get('timestamp') if user_logs else 'Never'
                last_action = user_logs[0].get('action_type') if user_logs else 'No activity'

                response += f"{i}. User ID: {uid}\n"
                response += f"   Last seen: {last_seen}\n"
                response += f"   Last action: {last_action}\n\n"

            if total_users > 20:
                response += f"... and {total_users - 20} more users"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'admin_command', user_id, '/admin_users')

    def show_system_logs(self, message):
        """Show detailed system logs"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Super admin access required.")
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
            response = "📭 No logs found."
        else:
            response = f"📋 SYSTEM LOGS (Last {len(logs)}):\n\n"

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

                response += f"🕒 {time_part} | 🤖 {bot_token}... | 👤 {user_id_log}\n"
                response += f"   📝 {action}"
                if details:
                    response += f" | {details}"
                response += "\n\n"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'admin_command', user_id, '/admin_logs')

    def cleanup_system(self, message):
        """Clean up old system data"""
        user_id = message.from_user.id

        if not is_super_admin(user_id):
            self.bot.reply_to(message, "❌ Super admin access required.")
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

        response = f"🧹 SYSTEM CLEANUP COMPLETE\n\n"
        response += f"Deleted old logs: {deleted_logs} entries\n"
        response += f"Log retention: {retention_days} days\n\n"
        response += "✅ System cleaned successfully!"

        self.bot.reply_to(message, response)
        add_log_entry(self.bot_token, 'admin_command', user_id, '/admin_cleanup')