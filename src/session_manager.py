"""Session management for Telegram exporter."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class SessionManager:
    """Manages Telegram sessions and their metadata."""

    def __init__(self):
        self.sessions_dir = "sessions"
        self.ensure_sessions_dir()

    def ensure_sessions_dir(self):
        """Ensure sessions directory exists."""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def get_session_path(self, session_name: str) -> str:
        """Get full path to session file."""
        return os.path.join(self.sessions_dir, f"{session_name}.session")

    def get_session_info_path(self, session_name: str) -> str:
        """Get path to session info file."""
        return os.path.join(self.sessions_dir, f"{session_name}_info.json")

    def list_sessions(self) -> List[Dict]:
        """List all available sessions with their metadata."""
        sessions = []

        if not os.path.exists(self.sessions_dir):
            return sessions

        for file in os.listdir(self.sessions_dir):
            if file.endswith(".session"):
                session_name = file[:-8]  # Remove .session extension
                session_info = self.get_session_info(session_name)

                sessions.append(
                    {
                        "name": session_name,
                        "phone": session_info.get("phone", "Unknown"),
                        "api_id": session_info.get("api_id", "Unknown"),
                        "created": session_info.get("created", "Unknown"),
                        "last_used": session_info.get("last_used", "Never"),
                        "exists": True,
                    }
                )

        return sorted(sessions, key=lambda x: x.get("last_used", ""), reverse=True)

    def get_session_info(self, session_name: str) -> Dict:
        """Get session metadata."""
        info_path = self.get_session_info_path(session_name)

        if os.path.exists(info_path):
            try:
                with open(info_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        return {}

    def save_session_info(
        self, session_name: str, api_id: str, api_hash: str, phone: str
    ):
        """Save session metadata."""
        info = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone": phone,
            "created": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
        }

        info_path = self.get_session_info_path(session_name)
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

    def update_last_used(self, session_name: str):
        """Update last used timestamp for session."""
        info = self.get_session_info(session_name)
        info["last_used"] = datetime.now().isoformat()

        info_path = self.get_session_info_path(session_name)
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

    def session_exists(self, session_name: str) -> bool:
        """Check if session exists."""
        return os.path.exists(self.get_session_path(session_name))

    def delete_session(self, session_name: str) -> bool:
        """Delete session and its metadata."""
        try:
            session_path = self.get_session_path(session_name)
            info_path = self.get_session_info_path(session_name)

            if os.path.exists(session_path):
                os.remove(session_path)

            if os.path.exists(info_path):
                os.remove(info_path)

            return True
        except Exception as e:
            print(f"❌ Ошибка при удалении сессии: {e}")
            return False

    def get_session_credentials(self, session_name: str) -> Optional[Dict]:
        """Get credentials for session."""
        info = self.get_session_info(session_name)
        if info and all(key in info for key in ["api_id", "api_hash", "phone"]):
            return {
                "api_id": info["api_id"],
                "api_hash": info["api_hash"],
                "phone": info["phone"],
            }
        return None

    def create_session_name(self, phone: str) -> str:
        """Generate session name from phone number."""
        # Remove + and other non-alphanumeric characters
        clean_phone = "".join(c for c in phone if c.isalnum())
        return f"session_{clean_phone}"

    def migrate_old_session(self):
        """Migrate old anon.session to new sessions structure."""
        from config import LEGACY_CREDENTIALS_FILE, LEGACY_SESSION_FILE

        old_session = LEGACY_SESSION_FILE
        old_credentials = LEGACY_CREDENTIALS_FILE

        if os.path.exists(old_session):
            print("🔄 Обнаружена старая сессия, мигрируем в новую структуру...")

            # Load old credentials if available
            credentials = {}
            if os.path.exists(old_credentials):
                try:
                    with open(old_credentials, encoding="utf-8") as f:
                        credentials = json.load(f)
                except Exception:
                    pass

            # Create new session name
            phone = credentials.get("phone", "unknown")
            session_name = self.create_session_name(phone)

            # Move session file
            new_session_path = self.get_session_path(session_name)
            os.rename(old_session, new_session_path)

            # Save session info
            if credentials:
                self.save_session_info(
                    session_name,
                    credentials.get("api_id", ""),
                    credentials.get("api_hash", ""),
                    credentials.get("phone", ""),
                )

            print(f"✅ Сессия мигрирована как '{session_name}'")
            return session_name

        return None
