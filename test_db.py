from master_db.connection import test_connection
from master_db.operations import add_bot, get_all_bots

if __name__ == "__main__":
    print("Testing database connection...")

    if test_connection():
        print("✅ Database connection successful!")

        # Test get all bots
        bots = get_all_bots()
        print(f"📊 Found {len(bots)} bots in system")

        for bot in bots:
            print(f"  - {bot['bot_name']} ({bot['bot_type']})")
    else:
        print("❌ Database connection failed!")