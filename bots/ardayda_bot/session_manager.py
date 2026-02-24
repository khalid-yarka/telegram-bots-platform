# bots/ardayda_bot/session_manager.py

# Dictionary to track each user's ongoing operation and temporary data
user_sessions = {}

def start_session(user_id, operation):
    """
    Start a session for a user.
    operation: 'upload' | 'search'
    """
    user_sessions[user_id] = {
        "status": operation,
        "pdf_temp": None,
        "subject": None,
        "tags": [],
        "page": 1
    }

def update_session(user_id, key, value):
    """Update a key in the user's session"""
    if user_id in user_sessions:
        user_sessions[user_id][key] = value

def get_session(user_id):
    """Get the session dict for a user"""
    return user_sessions.get(user_id, None)

def end_session(user_id):
    """Clear the user's session"""
    if user_id in user_sessions:
        del user_sessions[user_id]

def has_active_session(user_id):
    """Check if user is currently in an operation"""
    return user_id in user_sessions and user_sessions[user_id]["status"] in ("upload", "search")