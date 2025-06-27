"""Configuration constants for Telegram exporter."""

# Legacy files (for migration)
LEGACY_SESSION_FILE = "anon.session"
LEGACY_CREDENTIALS_FILE = "credentials.json"

# Current directories
SESSIONS_DIR = "sessions"
EXPORTS_DIR = "exports"

# Global files (not session-specific)
NICKNAMES_FILE = "nicknames.txt"

# File templates (will be formatted with session name)
PROGRESS_FILE_TEMPLATE = "export_progress_{session}.json"
CONTACTS_CSV_TEMPLATE = "telegram_contacts_{session}.csv"
CONTACTS_JSON_TEMPLATE = "telegram_contacts_{session}.json"
CHATS_CSV_TEMPLATE = "telegram_chats_{session}.csv"
DIALOGS_JSON_TEMPLATE = "telegram_dialogs_{session}.json"
CHAT_MEMBERS_CSV_TEMPLATE = "telegram_chat_members_{session}.csv"
CHAT_MEMBERS_JSON_TEMPLATE = "telegram_chat_members_{session}.json"
NICKNAMES_MATCHES_CSV_TEMPLATE = "telegram_nicknames_matches_{session}.csv"
NICKNAMES_MATCHES_JSON_TEMPLATE = "telegram_nicknames_matches_{session}.json"
