import os

class Config:
    """
    Telegram Bots Platform Configuration
    NO .env file needed - All values hardcoded here
    """

    # ============ SUPER ADMIN ============
    # Your Telegram ID - Get it from @userinfobot on Telegram
    # Example: Send /id to @userinfobot, it replies "Your ID: 123456789"
    SUPER_ADMINS = [
        2094426161,  # ← REPLACE WITH YOUR ACTUAL TELEGRAM ID
    ]

    # ============ PYTHONANYWHERE MYSQL DATABASE ============
    # Get these from PythonAnywhere → Databases tab
    DB_CONFIG = {
        'host': 'Zabots1.mysql.pythonanywhere-services.com',  # ← Replace YOUR_USERNAME
        'user': 'Zabots1',        # ← Your PythonAnywhere username
        'password': 'users_db_pass',  # ← Password from Databases tab
        'database': 'Zabots1$telegram_bots',  # ← Must match your database name
        'port': 3306,
        'charset': 'utf8mb4',
        'autocommit': False
    }

    # ============ WEBHOOK SETTINGS ============
    # Your PythonAnywhere domain
    WEBHOOK_URL_BASE = 'https://Zabots1.pythonanywhere.com'  # ← Replace

    # ============ FLASK SETTINGS ============
    SECRET_KEY = 'telegram-bots-platform-secret-key-2024-change-this'
    DEBUG = False  # Set to True only for local testing

    # ============ APPLICATION SETTINGS ============
    MAX_BOTS_PER_USER = 10
    LOG_RETENTION_DAYS = 30
    TELEGRAM_API_URL = 'https://api.telegram.org/bot'

    # ============ PATHS ============
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

    # ============ BOT SPECIFIC SETTINGS ============
    # Master bot settings
    MASTER_BOT_TOKEN = None  # Will be set when bot is registered

    # Ardayda bot default settings
    ARDAYDA_SETTINGS = {
        'welcome_message': 'Welcome to Ardayda Bot! 📚',
        'max_posts_per_day': 5,
        'default_language': 'so',
    }

    # Dhalinyaro bot default settings
    DHALINYARO_SETTINGS = {
        'welcome_message': 'Welcome to Dhalinyaro Bot! 🎉',
        'min_age': 16,
        'max_group_members': 100,
    }

config = Config()

# ============ CONFIGURATION VERIFICATION ============
def verify_config():
    """Verify that configuration is properly set"""
    print("\n" + "="*50)
    print("CONFIGURATION VERIFICATION")
    print("="*50)

    # Check super admin
    if config.SUPER_ADMINS[0] == 123456789:
        print("❌ ERROR: You must set your Telegram ID in SUPER_ADMINS")
        print("  Get your ID from @userinfobot on Telegram")
        return False
    else:
        print(f"✅ Super Admin ID: {config.SUPER_ADMINS[0]}")

    # Check database config
    if 'YOUR_USERNAME' in config.DB_CONFIG['host']:
        print("❌ ERROR: You must set your PythonAnywhere username in DB_CONFIG")
        return False
    else:
        print(f"✅ Database: {config.DB_CONFIG['database']}")

    # Check webhook URL
    if 'YOUR_USERNAME' in config.WEBHOOK_URL_BASE:
        print("❌ ERROR: You must set your PythonAnywhere domain in WEBHOOK_URL_BASE")
        return False
    else:
        print(f"✅ Webhook URL: {config.WEBHOOK_URL_BASE}")

    print("="*50)
    print("✅ Configuration verified successfully!")
    print("="*50 + "\n")
    return True

# ============ DATABASE TEST ============
def test_database_connection():
    """Test MySQL database connection"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**config.DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and result[0] == 1:
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database test failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Go to PythonAnywhere → Databases tab")
        print("2. Check your MySQL password")
        print("3. Verify database name matches: username$telegram_bots")
        print("4. Make sure you ran the SQL script to create tables")
        return False

# ============ EXAMPLE CONFIG FOR USER 'ahmed123' ============
"""
Example for user 'ahmed123' with Telegram ID 987654321:

class Config:
    SUPER_ADMINS = [987654321]

    DB_CONFIG = {
        'host': 'ahmed123.mysql.pythonanywhere-services.com',
        'user': 'ahmed123',
        'password': 'MySecurePass123',
        'database': 'ahmed123$telegram_bots',
        'port': 3306,
        'charset': 'utf8mb4',
        'autocommit': False
    }

    WEBHOOK_URL_BASE = 'https://ahmed123.pythonanywhere.com'

    # ... rest stays the same
"""

# Run verification when this file is executed directly
if __name__ == '__main__':
    print("🔧 Telegram Bots Platform Configuration")
    print("-" * 40)

    if verify_config():
        test_database_connection()

    print("\n📝 NEXT STEPS:")
    print("1. Replace ALL 'YOUR_USERNAME' with your actual PythonAnywhere username")
    print("2. Replace 123456789 with your actual Telegram ID")
    print("3. Set your MySQL password from PythonAnywhere Databases tab")
    print("4. Save this file and restart your web app")