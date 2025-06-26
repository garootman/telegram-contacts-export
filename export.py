#!/usr/bin/env python3
"""
Telegram contacts and chats exporter.

This module provides functionality to export Telegram contacts and chats to CSV and JSON formats.
It also supports cross-referencing with a nicknames file to find specific users.
"""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from getpass import getpass

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    ChatAdminRequiredError,
    ChannelPrivateError,
)
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, Channel, Chat

SESSION_FILE = "anon.session"
PROGRESS_FILE = "export_progress.json"
CREDENTIALS_FILE = "credentials.json"
NICKNAMES_FILE = "nicknames.txt"


class TelegramExporter:
    """
    Main class for exporting Telegram contacts and chats.

    Handles authentication, data export to CSV/JSON formats,
    and cross-referencing with nicknames file.
    """

    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.client = None
        self.progress = self.load_progress()
        self.credentials = self.load_credentials()

    def load_progress(self) -> dict:
        """Load export progress from file."""
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def load_credentials(self) -> dict:
        """Load saved credentials from file."""
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_credentials(self):
        """Save API credentials to file."""
        credentials = {
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "phone": self.phone,
        }
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(credentials, f, ensure_ascii=False, indent=2)
        print(f"💾 Учетные данные сохранены в {CREDENTIALS_FILE}")

    def save_progress(self, export_type: str, data: dict):
        """Save export progress to file."""
        self.progress[export_type] = {
            "timestamp": datetime.now().isoformat(),
            "completed": data.get("completed", 0),
            "total": data.get("total", 0),
            "finished": data.get("finished", False),
        }
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def setup_credentials(self):
        """Set up Telegram API credentials interactively."""
        print("\n🔧 Настройка учетных данных Telegram API")
        print("Получите api_id и api_hash на https://my.telegram.org")
        print("=" * 50)

        # Показать текущие учетные данные если есть
        if self.credentials:
            print("\n📋 Текущие учетные данные:")
            print(f"API ID: {self.credentials.get('api_id', 'не задан')}")
            print(
                f"API Hash: {'*' * 10 if self.credentials.get('api_hash') else 'не задан'}"
            )
            print(f"Телефон: {self.credentials.get('phone', 'не задан')}")

            if input("\nИспользовать существующие учетные данные? (y/n): ").lower() in [
                "y",
                "yes",
                "да",
                "д",
            ]:
                self.api_id = self.credentials["api_id"]
                self.api_hash = self.credentials["api_hash"]
                self.phone = self.credentials["phone"]
                return True

        print("\n📝 Введите новые учетные данные:")
        self.api_id = input("API ID: ").strip()
        self.api_hash = input("API Hash: ").strip()
        self.phone = input(
            "Номер телефона (с кодом страны, например +79991234567): "
        ).strip()

        if not all([self.api_id, self.api_hash, self.phone]):
            print("❌ Ошибка: все поля должны быть заполнены!")
            return False

        # Сохранить учетные данные
        save_choice = input(
            "\n💾 Сохранить учетные данные для будущих запусков? (y/n): "
        ).lower()
        if save_choice in ["y", "yes", "да", "д"]:
            self.save_credentials()

        return True

    def load_saved_credentials(self):
        """Load previously saved credentials."""
        if self.credentials:
            self.api_id = self.credentials.get("api_id")
            self.api_hash = self.credentials.get("api_hash")
            self.phone = self.credentials.get("phone")
            return True
        return False

    async def create_client(self):
        """Create and authenticate Telegram client."""
        if os.path.exists(SESSION_FILE):
            print(f"Найден файл сессии {SESSION_FILE}, используем существующую сессию")

        self.client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)

        try:
            await self.client.start(phone=self.phone)
        except SessionPasswordNeededError:
            password = getpass("Введите пароль двухфакторной аутентификации: ")
            await self.client.start(phone=self.phone, password=password)

        print("Успешно подключен к Telegram!")

    async def export_contacts(self, resume: bool = False):
        """Export Telegram contacts to CSV and JSON files."""
        print("\n📞 Экспорт контактов...")

        contacts_result = await self.client(GetContactsRequest(hash=0))
        contacts = contacts_result.users
        total = len(contacts)

        if resume and "contacts" in self.progress:
            completed = self.progress["contacts"].get("completed", 0)
            print(f"Продолжение с позиции {completed}/{total}")
        else:
            completed = 0

        contact_list = []

        for i, contact in enumerate(contacts[completed:], completed):
            contact_info = {
                "id": contact.id,
                "first_name": contact.first_name or "",
                "last_name": contact.last_name or "",
                "username": contact.username or "",
                "phone": contact.phone or "",
                "is_bot": contact.bot,
                "is_contact": True,
            }
            contact_list.append(contact_info)

            # Обновление прогресса
            progress = int((i + 1) / total * 100)
            print(f"\rПрогресс: {i + 1}/{total} ({progress}%)", end="", flush=True)

            # Сохранение промежуточного прогресса каждые 10 контактов
            if (i + 1) % 10 == 0:
                self.save_progress(
                    "contacts", {"completed": i + 1, "total": total, "finished": False}
                )

        print(f"\n✅ Контакты обработаны: {total}")

        # Экспорт в CSV
        contacts_csv = "telegram_contacts.csv"
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
            writer.writerows(contact_list)

        # Экспорт в JSON (для совместимости)
        with open("telegram_contacts.json", "w", encoding="utf-8") as f:
            json.dump(contact_list, f, ensure_ascii=False, indent=2)

        self.save_progress(
            "contacts", {"completed": total, "total": total, "finished": True}
        )

        print(f"📁 Контакты сохранены в {contacts_csv} и telegram_contacts.json")
        return total

    async def export_chats(self, resume: bool = False):
        """Export Telegram chats to CSV and JSON files."""
        print("\n💬 Экспорт чатов...")

        dialogs = await self.client.get_dialogs()
        user_dialogs = [d for d in dialogs if d.is_user]
        total = len(user_dialogs)

        if resume and "chats" in self.progress:
            completed = self.progress["chats"].get("completed", 0)
            print(f"Продолжение с позиции {completed}/{total}")
        else:
            completed = 0

        dialog_list = []

        for i, dialog in enumerate(user_dialogs[completed:], completed):
            entity = dialog.entity
            dialog_info = {
                "id": entity.id,
                "first_name": getattr(entity, "first_name", "") or "",
                "last_name": getattr(entity, "last_name", "") or "",
                "username": getattr(entity, "username", "") or "",
                "phone": getattr(entity, "phone", "") or "",
                "is_contact": getattr(entity, "contact", False),
                "last_message_date": dialog.date.isoformat() if dialog.date else "",
                "unread_count": dialog.unread_count,
            }
            dialog_list.append(dialog_info)

            # Обновление прогресса
            progress = int((i + 1) / total * 100)
            print(f"\rПрогресс: {i + 1}/{total} ({progress}%)", end="", flush=True)

            # Сохранение промежуточного прогресса каждые 10 чатов
            if (i + 1) % 10 == 0:
                self.save_progress(
                    "chats", {"completed": i + 1, "total": total, "finished": False}
                )

        print(f"\n✅ Чаты обработаны: {total}")

        # Экспорт в CSV
        chats_csv = "telegram_chats.csv"
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
            writer.writerows(dialog_list)

        # Экспорт в JSON (для совместимости)
        with open("telegram_dialogs.json", "w", encoding="utf-8") as f:
            json.dump(dialog_list, f, ensure_ascii=False, indent=2)

        self.save_progress(
            "chats", {"completed": total, "total": total, "finished": True}
        )

        print(f"📁 Чаты сохранены в {chats_csv} и telegram_dialogs.json")
        return total

    async def export_chat_members(self, resume: bool = False):
        """Export all members from all accessible chats and groups."""
        print("\n👥 Экспорт участников чатов...")

        dialogs = await self.client.get_dialogs()
        group_dialogs = [d for d in dialogs if d.is_group or d.is_channel]
        total_chats = len(group_dialogs)

        if resume and "chat_members" in self.progress:
            completed_chats = self.progress["chat_members"].get("completed", 0)
            print(f"Продолжение с позиции {completed_chats}/{total_chats}")
        else:
            completed_chats = 0

        all_members = []
        processed_chats = 0

        for i, dialog in enumerate(group_dialogs[completed_chats:], completed_chats):
            try:
                entity = dialog.entity
                chat_title = dialog.title or "Без названия"
                chat_id = entity.id
                chat_type = "channel" if dialog.is_channel else "group"

                print(f"\n🔍 Обрабатываем {chat_type}: {chat_title}")

                if isinstance(entity, (Channel, Chat)):
                    # Получаем участников чата
                    try:
                        if dialog.is_channel:
                            # For channels, we need to use GetParticipantsRequest
                            participants = await self.client(
                                GetParticipantsRequest(
                                    entity,
                                    ChannelParticipantsSearch(""),
                                    offset=0,
                                    limit=10000,
                                    hash=0,
                                )
                            )
                            members = participants.users
                        else:
                            # For regular groups, use get_participants
                            members = await self.client.get_participants(entity)

                        for member in members:
                            if hasattr(member, "id"):  # Ensure it's a user
                                member_info = {
                                    "chat_id": chat_id,
                                    "chat_title": chat_title,
                                    "chat_type": chat_type,
                                    "user_id": member.id,
                                    "first_name": getattr(member, "first_name", "")
                                    or "",
                                    "last_name": getattr(member, "last_name", "") or "",
                                    "username": getattr(member, "username", "") or "",
                                    "phone": getattr(member, "phone", "") or "",
                                    "is_bot": getattr(member, "bot", False),
                                    "is_premium": getattr(member, "premium", False),
                                    "is_verified": getattr(member, "verified", False),
                                }
                                all_members.append(member_info)

                        print(f"✅ Найдено {len(members)} участников")

                    except (ChatAdminRequiredError, ChannelPrivateError) as e:
                        print(f"⚠️ Нет доступа к участникам: {e}")
                    except Exception as e:
                        print(f"❌ Ошибка при получении участников: {e}")

                processed_chats += 1
                progress = int(processed_chats / total_chats * 100)
                print(f"Прогресс чатов: {processed_chats}/{total_chats} ({progress}%)")

                # Сохранение промежуточного прогресса каждые 5 чатов
                if processed_chats % 5 == 0:
                    self.save_progress(
                        "chat_members",
                        {
                            "completed": processed_chats,
                            "total": total_chats,
                            "finished": False,
                        },
                    )

            except Exception as e:
                print(f"❌ Ошибка при обработке чата {dialog.title}: {e}")
                processed_chats += 1
                continue

        print(
            f"\n✅ Участники чатов обработаны: {len(all_members)} из {total_chats} чатов"
        )

        if all_members:
            # Экспорт в CSV
            members_csv = "telegram_chat_members.csv"
            with open(members_csv, "w", newline="", encoding="utf-8") as csvfile:
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
                writer.writeheader()
                writer.writerows(all_members)

            # Экспорт в JSON
            with open("telegram_chat_members.json", "w", encoding="utf-8") as f:
                json.dump(all_members, f, ensure_ascii=False, indent=2)

            print(
                f"📁 Участники чатов сохранены в {members_csv} и telegram_chat_members.json"
            )

        self.save_progress(
            "chat_members",
            {"completed": total_chats, "total": total_chats, "finished": True},
        )

        return len(all_members)

    def load_nicknames_list(self):
        """Load list of nicknames from nicknames.txt file."""
        if not os.path.exists(NICKNAMES_FILE):
            print(f"❌ Файл {NICKNAMES_FILE} не найден!")
            return set()

        try:
            with open(NICKNAMES_FILE, "r", encoding="utf-8") as f:
                nicknames_set = {line.strip().lower() for line in f if line.strip()}
            print(f"📋 Загружено {len(nicknames_set)} ников из {NICKNAMES_FILE}")
            return nicknames_set
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {NICKNAMES_FILE}: {e}")
            return set()

    def cross_reference_nicknames_offline(self):
        """Cross-reference contacts and chats with nicknames file."""
        """Сверяет контакты и чаты с файлом nicknames.txt"""
        print("\n🔍 Сверка с файлом nicknames.txt...")

        # Загружаем список ников
        nicknames_set = self.load_nicknames_list()
        if not nicknames_set:
            return

        matched_contacts = []

        # Сверяем контакты из файла
        print("📞 Сверка контактов...")
        try:
            if os.path.exists("telegram_contacts.json"):
                with open("telegram_contacts.json", "r", encoding="utf-8") as f:
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
                        matched_contacts.append(contact_info)
                        print(f"✅ Найден контакт: @{username}")
            else:
                print("⚠️ Файл telegram_contacts.json не найден, пропускаем сверку контактов")

        except Exception as e:
            print(f"❌ Ошибка при сверке контактов: {e}")

        # Сверяем чаты из файла
        print("💬 Сверка чатов...")
        try:
            if os.path.exists("telegram_dialogs.json"):
                with open("telegram_dialogs.json", "r", encoding="utf-8") as f:
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
                        matched_contacts.append(dialog_info)
                        print(f"✅ Найден чат: @{username}")
            else:
                print("⚠️ Файл telegram_dialogs.json не найден, пропускаем сверку чатов")

        except Exception as e:
            print(f"❌ Ошибка при сверке чатов: {e}")

        # Сверяем участников чатов из файла
        print("👥 Сверка участников чатов...")
        try:
            if os.path.exists("telegram_chat_members.json"):
                with open("telegram_chat_members.json", "r", encoding="utf-8") as f:
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
                        matched_contacts.append(member_info)
                        print(f"✅ Найден участник в {member.get('chat_title', '')}: @{username}")
            else:
                print("⚠️ Файл telegram_chat_members.json не найден, пропускаем сверку участников чатов")

        except Exception as e:
            print(f"❌ Ошибка при сверке участников чатов: {e}")

        # Сохраняем результаты
        if matched_contacts:
            print(f"\n🎯 Найдено совпадений: {len(matched_contacts)}")

            # Экспорт в CSV
            matched_csv = "telegram_nicknames_matches.csv"
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
                    # Добавляем недостающие поля для разных источников
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

            # Экспорт в JSON
            with open("telegram_nicknames_matches.json", "w", encoding="utf-8") as f:
                json.dump(matched_contacts, f, ensure_ascii=False, indent=2)

            print(
                f"📁 Совпадения сохранены в {matched_csv} и telegram_nicknames_matches.json"
            )

            # Статистика
            contacts_count = sum(
                1 for c in matched_contacts if c["source"] == "contacts"
            )
            chats_count = sum(1 for c in matched_contacts if c["source"] == "chats")
            chat_members_count = sum(
                1 for c in matched_contacts if c["source"] == "chat_members"
            )
            print("📊 Статистика:")
            print(f"  📞 Контакты: {contacts_count}")
            print(f"  💬 Чаты: {chats_count}")
            print(f"  👥 Участники чатов: {chat_members_count}")
            print(f"  🎯 Всего: {len(matched_contacts)}")
        else:
            print("❌ Совпадений не найдено")

        return len(matched_contacts) if matched_contacts else 0

    def show_menu(self):
        """Display interactive menu and get user choice."""
        print("\n" + "=" * 50)
        print("🚀 Telegram Data Exporter")
        print("=" * 50)

        # Показать статус подключения
        session_status = (
            "✅ Активна" if os.path.exists(SESSION_FILE) else "❌ Не создана"
        )
        credentials_status = "✅ Сохранены" if self.credentials else "❌ Не настроены"

        print("\n🔐 Статус:")
        print(f"  Сессия: {session_status}")
        print(f"  Учетные данные: {credentials_status}")

        # Показать информацию о предыдущих экспортах
        if self.progress:
            print("\n📊 Информация о предыдущих экспортах:")
            for export_type, data in self.progress.items():
                timestamp = datetime.fromisoformat(data["timestamp"]).strftime(
                    "%d.%m.%Y %H:%M"
                )
                status = "✅ Завершен" if data.get("finished") else "⏸️ Прерван"
                completed = data.get("completed", 0)
                total = data.get("total", 0)
                progress_percent = int(completed / total * 100) if total > 0 else 0

                print(
                    f"  {export_type.capitalize()}: {status} {timestamp} "
                    f"({completed}/{total}, {progress_percent}%)"
                )

        print("\n📋 Выберите действие:")
        print("1. Настройка и подключение к Telegram")
        print("2. Экспорт контактов")
        print("3. Экспорт чатов")
        print("4. Экспорт участников чатов")
        print("5. Экспорт всего (контакты + чаты + участники)")
        print("6. Сверка с файлом nicknames.txt")
        print("0. Выход")

        return input("\nВведите номер действия: ").strip()

    async def ensure_connection(self):
        """Ensure Telegram connection is established."""
        if not all([self.api_id, self.api_hash, self.phone]):
            if not self.load_saved_credentials():
                print(
                    "❌ Сначала необходимо настроить подключение к Telegram (пункт 1)"
                )
                return False

        if not self.client:
            await self.create_client()

        return True

    async def run(self):
        """Main application loop."""
        try:
            while True:
                choice = self.show_menu()

                if choice == "0":
                    print("👋 До свидания!")
                    break

                if choice == "1":
                    # Настройка и подключение
                    if self.setup_credentials():
                        print("\n🔄 Создание сессии Telegram...")
                        await self.create_client()
                        print("✅ Подключение успешно настроено!")
                    else:
                        print("❌ Не удалось настроить подключение")

                elif choice == "2":
                    # Экспорт контактов
                    if not await self.ensure_connection():
                        continue

                    resume = False
                    if "contacts" in self.progress and not self.progress[
                        "contacts"
                    ].get("finished", False):
                        resume_choice = input(
                            "Найден незавершенный экспорт контактов. Продолжить? (y/n): "
                        ).lower()
                        resume = resume_choice in ["y", "yes", "да", "д"]

                    await self.export_contacts(resume=resume)

                elif choice == "3":
                    # Экспорт чатов
                    if not await self.ensure_connection():
                        continue

                    resume = False
                    if "chats" in self.progress and not self.progress["chats"].get(
                        "finished", False
                    ):
                        resume_choice = input(
                            "Найден незавершенный экспорт чатов. Продолжить? (y/n): "
                        ).lower()
                        resume = resume_choice in ["y", "yes", "да", "д"]

                    await self.export_chats(resume=resume)

                elif choice == "4":
                    # Экспорт участников чатов
                    if not await self.ensure_connection():
                        continue

                    resume = False
                    if "chat_members" in self.progress and not self.progress[
                        "chat_members"
                    ].get("finished", False):
                        resume_choice = input(
                            "Найден незавершенный экспорт участников чатов. Продолжить? (y/n): "
                        ).lower()
                        resume = resume_choice in ["y", "yes", "да", "д"]

                    members_count = await self.export_chat_members(resume=resume)
                    print(
                        f"\n🎉 Экспорт участников завершен! Найдено {members_count} участников"
                    )

                elif choice == "5":
                    # Экспорт всего
                    if not await self.ensure_connection():
                        continue

                    resume_contacts = False
                    resume_chats = False
                    resume_members = False

                    if "contacts" in self.progress and not self.progress[
                        "contacts"
                    ].get("finished", False):
                        resume_choice = input(
                            "Найден незавершенный экспорт контактов. Продолжить? (y/n): "
                        ).lower()
                        resume_contacts = resume_choice in ["y", "yes", "да", "д"]

                    if "chats" in self.progress and not self.progress["chats"].get(
                        "finished", False
                    ):
                        resume_choice = input(
                            "Найден незавершенный экспорт чатов. Продолжить? (y/n): "
                        ).lower()
                        resume_chats = resume_choice in ["y", "yes", "да", "д"]

                    if "chat_members" in self.progress and not self.progress[
                        "chat_members"
                    ].get("finished", False):
                        resume_choice = input(
                            "Найден незавершенный экспорт участников чатов. Продолжить? (y/n): "
                        ).lower()
                        resume_members = resume_choice in ["y", "yes", "да", "д"]

                    contacts_count = await self.export_contacts(resume=resume_contacts)
                    chats_count = await self.export_chats(resume=resume_chats)
                    members_count = await self.export_chat_members(
                        resume=resume_members
                    )

                    print("\n🎉 Полный экспорт завершен!")
                    print(f"📞 Контактов: {contacts_count}")
                    print(f"💬 Чатов: {chats_count}")
                    print(f"👥 Участников чатов: {members_count}")

                elif choice == "6":
                    # Сверка с файлом nicknames.txt
                    matches_count = self.cross_reference_nicknames_offline()
                    if matches_count > 0:
                        print(
                            f"\n🎉 Сверка завершена! Найдено {matches_count} совпадений"
                        )
                    else:
                        print("\n😞 Сверка завершена, совпадений не найдено")

                else:
                    print("❌ Неверный выбор, попробуйте снова")

                input("\nНажмите Enter для продолжения...")

        finally:
            if self.client:
                await self.client.disconnect()


def main():
    """Main entry point."""
    if sys.version_info < (3, 7):
        print("Требуется Python 3.7 или выше")
        sys.exit(1)

    try:
        exporter = TelegramExporter()
        asyncio.run(exporter.run())
    except KeyboardInterrupt:
        print("\n\n⏹️ Экспорт прерван пользователем")
        print("💾 Прогресс сохранен, можно продолжить позже")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
