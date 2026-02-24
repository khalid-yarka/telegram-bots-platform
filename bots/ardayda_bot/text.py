# bots/ardayda_bot/text.py

# ---------- REGISTRATION ----------

REG_NAME = (
    "👋 Welcome!\n\n"
    "Please enter your *full name* to complete registration."
)

REG_SUCCESS = (
    "✅ Registration completed successfully.\n\n"
    "You can now upload and search PDFs using the menu below."
)

REG_IN_PROGRESS_BLOCK = (
    "⚠️ Registration is still in progress.\n"
    "Please complete it before using other features."
)


# ---------- GENERAL ----------

HOME_WELCOME = (
    "🏠 *Main Menu*\n\n"
    "Choose what you want to do:"
)

CANCELLED = (
    "❌ Operation cancelled.\n\n"
    "You are back at the main menu."
)

SESSION_EXPIRED = (
    "⚠️ This session has expired.\n"
    "Please start again from the main menu."
)

CONFLICT_UPLOAD = (
    "⚠️ You are currently uploading a PDF.\n"
    "Finish it or tap ❌ Cancel before doing something else."
)

CONFLICT_SEARCH = (
    "⚠️ You are currently searching.\n"
    "Finish it or tap ❌ Cancel before starting a new action."
)

UNKNOWN_INPUT = (
    "ℹ️ Please use the buttons provided.\n"
    "If you are stuck, tap ❌ Cancel."
)


# ---------- UPLOAD FLOW ----------

UPLOAD_START = (
    "📤 *Upload PDF*\n\n"
    "Please send your PDF file."
)

UPLOAD_INVALID_FILE = (
    "❌ Invalid file.\n"
    "Please send a valid *PDF document*."
)

UPLOAD_ALREADY_EXISTS = (
    "⚠️ This PDF already exists in the system.\n"
    "Upload cancelled."
)

UPLOAD_SUBJECT = (
    "📝 *Choose Subject*\n\n"
    "Select the subject for this PDF:"
)

UPLOAD_TAGS = (
    "🏷️ *Select Tags*\n\n"
    "You can select multiple tags.\n"
    "Tap ⬆️ Upload PDF when done."
)

UPLOAD_SUCCESS = (
    "🎉 *Upload Completed!*\n\n"
    "Your PDF has been successfully uploaded."
)

UPLOAD_FAILED = (
    "❌ Upload failed due to an internal error.\n"
    "Please try again later."
)


# ---------- SEARCH FLOW ----------

SEARCH_START = (
    "🔍 *Search PDFs*\n\n"
    "Select one or more tags to search:"
)

SEARCH_NO_RESULTS = (
    "😕 No PDFs found for the selected tags."
)

SEARCH_RESULTS = (
    "📚 *Search Results*\n\n"
    "Tap a result to receive the PDF."
)


# ---------- PROFILE ----------

PROFILE_HEADER = (
    "👤 *Your Profile*\n\n"
)

PROFILE_STATS = (
    "📄 PDFs uploaded: {count}\n"
    "📅 Member since: {date}"
)

PROFILE_NO_UPLOADS = (
    "📭 You haven't uploaded any PDFs yet."
)