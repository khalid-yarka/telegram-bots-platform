from flask import Flask, request, jsonify, render_template, abort
import logging
import os

# Database operations
from master_db.operations import get_bot_by_token, add_log_entry, get_all_bots

# Config
from config import config

# Security utilities
from utils.security import validate_bot_token, verify_telegram_secret

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(config)

# Store active bot instances
active_bots = {}

def load_bot_handlers():
    """Placeholder for dynamic bot loading if needed"""
    pass

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html', title="Telegram Bots Platform")

@app.route('/webhook/<bot_token>', methods=['POST'])
def handle_webhook(bot_token):
    """Handle incoming Telegram webhook updates"""
    try:
        # 1. Validate token format
        if not validate_bot_token(bot_token):
            logger.warning(f"Invalid token format: {bot_token[:10]}...")
            abort(400)

        # 2. Verify Telegram secret header
        verify_telegram_secret(app.config.get("TELEGRAM_WEBHOOK_SECRET"))

        # 3. Get JSON data
        json_data = request.get_json(force=True)
        if not json_data:
            logger.warning(f"No JSON data for token: {bot_token[:10]}...")
            return jsonify({'error': 'No data received'}), 400

        update_id = json_data.get('update_id', 'unknown')

        # 4. Fetch bot info
        bot_info = get_bot_by_token(bot_token)
        if not bot_info:
            logger.warning(f"Bot not found: {bot_token[:10]}...")
            return jsonify({'error': 'Bot not found'}), 404

        if not bot_info.get('is_active'):
            logger.warning(f"Inactive bot attempt: {bot_token[:10]}...")
            return jsonify({'error': 'Bot inactive'}), 403

        # 5. Log the update
        add_log_entry(
            bot_token=bot_token,
            action_type='webhook_received',
            details=f"Update {update_id} received"
        )

        # 6. Dispatch update based on bot type
        bot_type = bot_info.get('bot_type', 'unknown')

        if bot_type == 'master':
            from bots.master_bot.bot import process_master_update
            process_master_update(bot_token, json_data)
        elif bot_type == 'ardayda':
            from bots.ardayda_bot.bot import process_ardayda_update
            process_ardayda_update(bot_token, json_data)
        elif bot_type == 'dhalinyaro':
            from bots.dhalinyaro_bot.bot import process_dhalinyaro_update
            process_dhalinyaro_update(bot_token, json_data)
        else:
            logger.error(f"Unknown bot type: {bot_type}")
            return jsonify({'error': 'Unknown bot type'}), 400

        return jsonify({'status': 'success', 'update_id': update_id}), 200

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-bots-platform',
        'timestamp': 'now'
    })

@app.route('/api/bots', methods=['GET'])
def list_bots_api():
    """API to list all bots (admin only)"""
    try:
        bots = get_all_bots()

        # Hide full tokens for security
        safe_bots = []
        for bot in bots:
            safe_bot = bot.copy()
            if 'bot_token' in safe_bot:
                safe_bot['bot_token'] = f"{safe_bot['bot_token'][:10]}..."
            safe_bots.append(safe_bot)

        return jsonify({
            'success': True,
            'count': len(safe_bots),
            'bots': safe_bots
        })
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Load bot handlers
    load_bot_handlers()

    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
else:
    # For PythonAnywhere WSGI
    load_bot_handlers()