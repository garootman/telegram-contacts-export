"""File management operations for Telegram exporter."""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Set

from config import (
    CHAT_MEMBERS_CSV_TEMPLATE,
    CHAT_MEMBERS_JSON_TEMPLATE,
    CHATS_CSV_TEMPLATE,
    CONTACTS_CSV_TEMPLATE,
    CONTACTS_JSON_TEMPLATE,
    DIALOGS_JSON_TEMPLATE,
    EXPORTS_DIR,
    LEGACY_CREDENTIALS_FILE,
    NICKNAMES_FILE,
    NICKNAMES_MATCHES_CSV_TEMPLATE,
    NICKNAMES_MATCHES_JSON_TEMPLATE,
    PROGRESS_FILE_TEMPLATE,
)


class FileManager:
    """Handles file I/O operations for the Telegram exporter."""

    def __init__(self):
        self.current_session = None
        self.exports_dir = EXPORTS_DIR
        self.ensure_exports_dir()

    def set_session(self, session_name: str):
        """Set current session for file operations."""
        self.current_session = session_name
        self.ensure_session_dir()

    def ensure_exports_dir(self):
        """Ensure exports directory exists."""
        if not os.path.exists(self.exports_dir):
            os.makedirs(self.exports_dir)

    def ensure_session_dir(self):
        """Ensure session-specific directory exists."""
        if self.current_session:
            session_dir = self.get_session_dir()
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)

    def get_session_dir(self) -> str:
        """Get session-specific directory path."""
        if not self.current_session:
            raise ValueError("No session set")
        return os.path.join(self.exports_dir, self.current_session)

    def get_session_file_path(self, template: str) -> str:
        """Get full path for a session-specific file."""
        if not self.current_session:
            raise ValueError("No session set")
        filename = template.format(session=self.current_session)
        return os.path.join(self.get_session_dir(), filename)

    @property
    def progress(self) -> Dict:
        """Get progress data for current session."""
        return self.load_progress()

    def load_progress(self) -> Dict:
        """Load export progress from session-specific file."""
        if not self.current_session:
            return {}

        progress_file = self.get_session_file_path(PROGRESS_FILE_TEMPLATE)
        if os.path.exists(progress_file):
            with open(progress_file, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_progress(self, export_type: str, data: Dict):
        """Save export progress to session-specific file."""
        if not self.current_session:
            raise ValueError("No session set")

        # Load current progress
        current_progress = self.load_progress()

        # Update with new data
        current_progress[export_type] = {
            "timestamp": datetime.now().isoformat(),
            "completed": data.get("completed", 0),
            "total": data.get("total", 0),
            "finished": data.get("finished", False),
            "processed_items": data.get("processed_items", []),
        }

        # Save to session-specific file
        progress_file = self.get_session_file_path(PROGRESS_FILE_TEMPLATE)
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(current_progress, f, ensure_ascii=False, indent=2)

    def load_credentials(self) -> Dict:
        """Load saved credentials from legacy file (for backward compatibility)."""
        if os.path.exists(LEGACY_CREDENTIALS_FILE):
            with open(LEGACY_CREDENTIALS_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_credentials(self, api_id: str, api_hash: str, phone: str):
        """Save API credentials to legacy file (deprecated - use sessions instead)."""
        credentials = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone": phone,
        }
        with open(LEGACY_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(credentials, f, ensure_ascii=False, indent=2)
        print(f"💾 Учетные данные сохранены в {LEGACY_CREDENTIALS_FILE}")

    def save_contacts_to_files(self, contacts: List[Dict]) -> int:
        """Save contacts to session-specific CSV and JSON files."""
        if not self.current_session:
            raise ValueError("No session set")

        contacts_csv = self.get_session_file_path(CONTACTS_CSV_TEMPLATE)
        contacts_json = self.get_session_file_path(CONTACTS_JSON_TEMPLATE)

        with open(contacts_csv, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "id",
                "first_name",
                "last_name",
                "username",
                "phone",
                "is_bot",
                "is_contact",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(contacts)

        with open(contacts_json, "w", encoding="utf-8") as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)

        print(
            f"📁 Контакты сохранены в {os.path.basename(contacts_csv)} и {os.path.basename(contacts_json)}"
        )
        return len(contacts)

    def save_chats_to_files(self, chats: List[Dict]) -> int:
        """Save chats to session-specific CSV and JSON files."""
        if not self.current_session:
            raise ValueError("No session set")

        chats_csv = self.get_session_file_path(CHATS_CSV_TEMPLATE)
        dialogs_json = self.get_session_file_path(DIALOGS_JSON_TEMPLATE)

        with open(chats_csv, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "id",
                "first_name",
                "last_name",
                "username",
                "phone",
                "is_contact",
                "last_message_date",
                "unread_count",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(chats)

        with open(dialogs_json, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)

        print(
            f"📁 Чаты сохранены в {os.path.basename(chats_csv)} и {os.path.basename(dialogs_json)}"
        )
        return len(chats)

    def save_chat_members_to_files(
        self, members: List[Dict], append: bool = False
    ) -> int:
        """Save chat members to session-specific CSV and JSON files."""
        if not members:
            return 0

        if not self.current_session:
            raise ValueError("No session set")

        members_csv = self.get_session_file_path(CHAT_MEMBERS_CSV_TEMPLATE)
        members_json = self.get_session_file_path(CHAT_MEMBERS_JSON_TEMPLATE)

        # For CSV, we need to handle append mode carefully
        mode = "a" if append and os.path.exists(members_csv) else "w"
        write_header = not (append and os.path.exists(members_csv))

        with open(members_csv, mode, newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "chat_id",
                "chat_title",
                "chat_type",
                "user_id",
                "first_name",
                "last_name",
                "username",
                "phone",
                "is_bot",
                "is_premium",
                "is_verified",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(members)

        # For JSON, load existing data and append
        existing_members = []
        if append and os.path.exists(members_json):
            try:
                with open(members_json, encoding="utf-8") as f:
                    existing_members = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_members = []

        all_members = existing_members + members if append else members

        with open(members_json, "w", encoding="utf-8") as f:
            json.dump(all_members, f, ensure_ascii=False, indent=2)

        csv_name = os.path.basename(members_csv)
        json_name = os.path.basename(members_json)

        if not append:
            print(f"📁 Участники чатов сохранены в {csv_name} и {json_name}")
        else:
            print(f"📁 Добавлено {len(members)} участников в {csv_name} и {json_name}")
        return len(members)

    def load_nicknames_list(self) -> Set[str]:
        """Load list of nicknames from nicknames.txt file."""
        if not os.path.exists(NICKNAMES_FILE):
            print(f"❌ Файл {NICKNAMES_FILE} не найден!")
            return set()

        try:
            with open(NICKNAMES_FILE, encoding="utf-8") as f:
                nicknames_set = {line.strip().lower() for line in f if line.strip()}
            print(f"📋 Загружено {len(nicknames_set)} ников из {NICKNAMES_FILE}")
            return nicknames_set
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {NICKNAMES_FILE}: {e}")
            return set()

    def cross_reference_nicknames(self) -> int:
        """Cross-reference contacts and chats with nicknames file."""
        print("\n🔍 Сверка с файлом nicknames.txt...")

        nicknames_set = self.load_nicknames_list()
        if not nicknames_set:
            return 0

        matched_contacts = []

        # Check contacts
        matched_contacts.extend(self._check_contacts(nicknames_set))
        # Check chats
        matched_contacts.extend(self._check_chats(nicknames_set))
        # Check chat members
        matched_contacts.extend(self._check_chat_members(nicknames_set))

        if matched_contacts:
            self._save_matches(matched_contacts)
            self._print_statistics(matched_contacts)
        else:
            print("❌ Совпадений не найдено")

        return len(matched_contacts)

    def _check_contacts(self, nicknames_set: Set[str]) -> List[Dict]:
        """Check contacts for nickname matches."""
        print("📞 Сверка контактов...")
        matched = []

        try:
            contacts_json = self.get_session_file_path(CONTACTS_JSON_TEMPLATE)
            if os.path.exists(contacts_json):
                with open(contacts_json, encoding="utf-8") as f:
                    contacts = json.load(f)

                for contact in contacts:
                    username = contact.get("username", "")
                    if username and username.lower() in nicknames_set:
                        contact_info = {
                            "source": "contacts",
                            "found_in_chat": "Контакты",
                            "chat_id": "",
                            "id": contact.get("id", ""),
                            "first_name": contact.get("first_name", ""),
                            "last_name": contact.get("last_name", ""),
                            "username": username,
                            "phone": contact.get("phone", ""),
                            "is_bot": contact.get("is_bot", False),
                            "matched_nick": username.lower(),
                        }
                        matched.append(contact_info)
                        print(f"✅ Найден контакт: @{username}")
            else:
                print(
                    f"⚠️ Файл {os.path.basename(contacts_json)} не найден, пропускаем сверку контактов"
                )
        except Exception as e:
            print(f"❌ Ошибка при сверке контактов: {e}")

        return matched

    def _check_chats(self, nicknames_set: Set[str]) -> List[Dict]:
        """Check chats for nickname matches."""
        print("💬 Сверка чатов...")
        matched = []

        try:
            dialogs_json = self.get_session_file_path(DIALOGS_JSON_TEMPLATE)
            if os.path.exists(dialogs_json):
                with open(dialogs_json, encoding="utf-8") as f:
                    dialogs = json.load(f)

                for dialog in dialogs:
                    username = dialog.get("username", "")
                    if username and username.lower() in nicknames_set:
                        dialog_info = {
                            "source": "chats",
                            "found_in_chat": "Личные сообщения",
                            "chat_id": dialog.get("id", ""),
                            "id": dialog.get("id", ""),
                            "first_name": dialog.get("first_name", ""),
                            "last_name": dialog.get("last_name", ""),
                            "username": username,
                            "phone": dialog.get("phone", ""),
                            "is_contact": dialog.get("is_contact", False),
                            "last_message_date": dialog.get("last_message_date", ""),
                            "unread_count": dialog.get("unread_count", 0),
                            "matched_nick": username.lower(),
                        }
                        matched.append(dialog_info)
                        print(f"✅ Найден чат: @{username}")
            else:
                print(
                    f"⚠️ Файл {os.path.basename(dialogs_json)} не найден, пропускаем сверку чатов"
                )
        except Exception as e:
            print(f"❌ Ошибка при сверке чатов: {e}")

        return matched

    def _check_chat_members(self, nicknames_set: Set[str]) -> List[Dict]:
        """Check chat members for nickname matches."""
        print("👥 Сверка участников чатов...")
        matched = []

        try:
            members_json = self.get_session_file_path(CHAT_MEMBERS_JSON_TEMPLATE)
            if os.path.exists(members_json):
                with open(members_json, encoding="utf-8") as f:
                    chat_members = json.load(f)

                for member in chat_members:
                    username = member.get("username", "")
                    if username and username.lower() in nicknames_set:
                        member_info = {
                            "source": "chat_members",
                            "found_in_chat": f"{member.get('chat_title', '')} ({member.get('chat_type', '')})",
                            "chat_id": member.get("chat_id", ""),
                            "id": member.get("user_id", ""),
                            "first_name": member.get("first_name", ""),
                            "last_name": member.get("last_name", ""),
                            "username": username,
                            "phone": member.get("phone", ""),
                            "is_bot": member.get("is_bot", False),
                            "is_premium": member.get("is_premium", False),
                            "is_verified": member.get("is_verified", False),
                            "matched_nick": username.lower(),
                        }
                        matched.append(member_info)
                        print(
                            f"✅ Найден участник в {member.get('chat_title', '')}: @{username}"
                        )
            else:
                print(
                    f"⚠️ Файл {os.path.basename(members_json)} не найден, пропускаем сверку участников чатов"
                )
        except Exception as e:
            print(f"❌ Ошибка при сверке участников чатов: {e}")

        return matched

    def _save_matches(self, matched_contacts: List[Dict]):
        """Save matched contacts to session-specific files."""
        print(f"\n🎯 Найдено совпадений: {len(matched_contacts)}")

        matched_csv = self.get_session_file_path(NICKNAMES_MATCHES_CSV_TEMPLATE)
        matched_json = self.get_session_file_path(NICKNAMES_MATCHES_JSON_TEMPLATE)

        with open(matched_csv, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "source",
                "found_in_chat",
                "chat_id",
                "id",
                "first_name",
                "last_name",
                "username",
                "phone",
                "is_bot",
                "is_contact",
                "is_premium",
                "is_verified",
                "last_message_date",
                "unread_count",
                "matched_nick",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for contact in matched_contacts:
                # Add missing fields for different sources
                if contact["source"] == "contacts":
                    contact.update(
                        {
                            "last_message_date": "",
                            "unread_count": 0,
                            "is_premium": False,
                            "is_verified": False,
                            "is_contact": True,
                        }
                    )
                elif contact["source"] == "chats":
                    contact.update({"is_premium": False, "is_verified": False})
                elif contact["source"] == "chat_members":
                    contact.update(
                        {
                            "is_contact": False,
                            "last_message_date": "",
                            "unread_count": 0,
                        }
                    )
                writer.writerow(contact)

        with open(matched_json, "w", encoding="utf-8") as f:
            json.dump(matched_contacts, f, ensure_ascii=False, indent=2)

        print(
            f"📁 Совпадения сохранены в {os.path.basename(matched_csv)} и {os.path.basename(matched_json)}"
        )

    def _print_statistics(self, matched_contacts: List[Dict]):
        """Print statistics about matches."""
        contacts_count = sum(1 for c in matched_contacts if c["source"] == "contacts")
        chats_count = sum(1 for c in matched_contacts if c["source"] == "chats")
        chat_members_count = sum(
            1 for c in matched_contacts if c["source"] == "chat_members"
        )

        print("📊 Статистика:")
        print(f"  📞 Контакты: {contacts_count}")
        print(f"  💬 Чаты: {chats_count}")
        print(f"  👥 Участники чатов: {chat_members_count}")
        print(f"  🎯 Всего: {len(matched_contacts)}")
