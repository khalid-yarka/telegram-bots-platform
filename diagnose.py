#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

from master_db.operations import get_all_bots, get_recent_logs
from master_db.connection import test_connection
from utils.webhook_manager import check_webhook, set_webhook
from config import config

print("🔍 MASTER BOT DIAGNOSIS\n")

# 1. Database
print("1. Database Connection:")
db_ok = test_connection()
print(f"   {'✅ Connected' if db_ok else '❌ Failed'}")

# 2. Bots in DB
print("\n2. Bots in Database:")
bots = get_all_bots()
if not bots:
    print("   ❌ No bots found!")
else:
    for b in bots:
        print(f"   - {b['bot_name']} ({b['bot_type']})")
        if b['bot_type'] == 'master':
            master = b

# 3. Webhook
if 'master' in locals():
    print(f"\n3. Master Bot Webhook:")
    result = check_webhook(master['bot_token'])
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   URL: {result.get('url', 'Not set')}")

    if result.get('status') != 'active':
        print(f"   ⚠️ Setting webhook...")
        success = set_webhook(master['bot_token'], 'master')
        print(f"   {'✅ Webhook set' if success else '❌ Failed'}")

# 4. Logs
print("\n4. Recent Activity:")
logs = get_recent_logs(limit=5)
if logs:
    for l in logs:
        print(f"   {l['timestamp']} - {l['action_type']}")
else:
    print("   No recent activity")

print("\n📋 SUMMARY:")
if not bots:
    print("❌ No bots in database. Add Master Bot first.")
elif 'master' not in [b['bot_type'] for b in bots]:
    print("❌ Master bot not in database.")
else:
    print("✅ Master bot exists in database.")
    print("✅ Webhook should be active.")
    print("\n💡 Next: Open Telegram, find your bot, send /start")