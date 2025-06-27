"""Telegram client wrapper for handling Telegram API operations."""

import os
from getpass import getpass
from typing import Dict, List

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    ChatAdminRequiredError,
    SessionPasswordNeededError,
)
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import Channel, ChannelParticipantsSearch, Chat


class TelegramClientWrapper:
    """Wraps Telegram client operations."""

    def __init__(self):
        self.client = None
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.session_file = None

    def set_credentials(self, api_id: str, api_hash: str, phone: str):
        """Set API credentials."""
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone

    def set_session_file(self, session_file: str):
        """Set session file path."""
        self.session_file = session_file

    async def create_client(self):
        """Create and authenticate Telegram client."""
        if not self.session_file:
            raise ValueError("Session file not set")

        if os.path.exists(self.session_file):
            print("Найден файл сессии, используем существующую сессию")

        self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)

        try:
            await self.client.start(phone=self.phone)
        except SessionPasswordNeededError:
            password = getpass("Введите пароль двухфакторной аутентификации: ")
            await self.client.start(phone=self.phone, password=password)

        print("Успешно подключен к Telegram!")

    async def get_contacts(self) -> List[Dict]:
        """Get all Telegram contacts."""
        contacts_result = await self.client(GetContactsRequest(hash=0))
        contacts = contacts_result.users

        contact_list = []
        for contact in contacts:
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

        return contact_list

    async def get_chats(self) -> List[Dict]:
        """Get all user chats/dialogs."""
        dialogs = await self.client.get_dialogs()
        user_dialogs = [d for d in dialogs if d.is_user]

        dialog_list = []
        for dialog in user_dialogs:
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

        return dialog_list

    async def get_all_group_chats(self) -> List[Dict]:
        """Get list of all group chats and channels."""
        dialogs = await self.client.get_dialogs()
        group_dialogs = [d for d in dialogs if d.is_group or d.is_channel]

        chat_list = []
        for dialog in group_dialogs:
            entity = dialog.entity
            chat_info = {
                "chat_id": entity.id,
                "chat_title": dialog.title or "Без названия",
                "chat_type": "channel" if dialog.is_channel else "group",
                "is_channel": dialog.is_channel,
                "entity": entity,
                "dialog": dialog,
            }
            chat_list.append(chat_info)

        return chat_list

    async def get_chat_members_for_chat(self, chat_info: Dict) -> List[Dict]:
        """Get members from a specific chat."""
        chat_id = chat_info["chat_id"]
        chat_title = chat_info["chat_title"]
        chat_type = chat_info["chat_type"]
        entity = chat_info["entity"]
        dialog = chat_info["dialog"]

        print(f"\n🔍 Обрабатываем {chat_type}: {chat_title}")

        members_list = []

        if isinstance(entity, (Channel, Chat)):
            try:
                if dialog.is_channel:
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
                    members = await self.client.get_participants(entity)

                for member in members:
                    if hasattr(member, "id"):
                        member_info = {
                            "chat_id": chat_id,
                            "chat_title": chat_title,
                            "chat_type": chat_type,
                            "user_id": member.id,
                            "first_name": getattr(member, "first_name", "") or "",
                            "last_name": getattr(member, "last_name", "") or "",
                            "username": getattr(member, "username", "") or "",
                            "phone": getattr(member, "phone", "") or "",
                            "is_bot": getattr(member, "bot", False),
                            "is_premium": getattr(member, "premium", False),
                            "is_verified": getattr(member, "verified", False),
                        }
                        members_list.append(member_info)

                print(f"✅ Найдено {len(members)} участников")

            except (ChatAdminRequiredError, ChannelPrivateError) as e:
                print(f"⚠️ Нет доступа к участникам: {e}")
            except Exception as e:
                print(f"❌ Ошибка при получении участников: {e}")

        return members_list

    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
