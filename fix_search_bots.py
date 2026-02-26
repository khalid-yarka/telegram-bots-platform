#!/usr/bin/env python3
import os

# Read operations.py
ops_path = 'master_db/operations.py'
with open(ops_path, 'r') as f:
    content = f.read()

# Check if function exists
if 'def search_bots' not in content:
    print("Adding search_bots function...")

    # Find where to add it (before the last return or at end)
    lines = content.split('\n')

    # Add before the last function or at end
    new_content = content + """

def search_bots(search_term):
    \"\"\"Search bots by name, username, or token\"\"\"
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = \"\"\"
            SELECT * FROM system_bots
            WHERE (bot_name LIKE %s OR bot_username LIKE %s OR bot_token LIKE %s)
            AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 10
            \"\"\"
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
        finally:
            cursor.close()
"""

    with open(ops_path, 'w') as f:
        f.write(new_content)

    print("✅ search_bots function added!")
else:
    print("✅ search_bots function already exists")