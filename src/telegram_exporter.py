"""
Telegram contacts and chats exporter.

This module provides the main orchestrator for exporting Telegram data.
"""

from file_manager import FileManager
from menu_manager import MenuManager
from telegram_client_wrapper import TelegramClientWrapper


class TelegramExporter:
    """
    Main orchestrator for Telegram data export operations.

    Coordinates between menu, file operations, and Telegram client.
    """

    def __init__(self):
        self.file_manager = FileManager()
        self.menu_manager = MenuManager(self.file_manager)
        self.telegram_client = TelegramClientWrapper()

        # Initialize sessions and migrate if needed
        self.menu_manager.initialize_sessions()

    async def export_contacts(self, resume: bool = False):
        """Export Telegram contacts to CSV and JSON files."""
        print("\n📞 Экспорт контактов...")

        contacts = await self.telegram_client.get_contacts()
        total = len(contacts)

        if resume and "contacts" in self.file_manager.progress:
            completed = self.file_manager.progress["contacts"].get("completed", 0)
            print(f"Продолжение с позиции {completed}/{total}")
            contacts = contacts[completed:]
        else:
            completed = 0

        contact_list = []
        for i, contact in enumerate(contacts, completed):
            contact_list.append(contact)

            progress = int((i + 1) / total * 100)
            print(f"\rПрогресс: {i + 1}/{total} ({progress}%)", end="", flush=True)

            if (i + 1) % 10 == 0:
                self.file_manager.save_progress(
                    "contacts", {"completed": i + 1, "total": total, "finished": False}
                )

        print(f"\n✅ Контакты обработаны: {total}")

        self.file_manager.save_contacts_to_files(contact_list)
        self.file_manager.save_progress(
            "contacts", {"completed": total, "total": total, "finished": True}
        )

        return total

    async def export_chats(self, resume: bool = False):
        """Export Telegram chats to CSV and JSON files."""
        print("\n💬 Экспорт чатов...")

        chats = await self.telegram_client.get_chats()
        total = len(chats)

        if resume and "chats" in self.file_manager.progress:
            completed = self.file_manager.progress["chats"].get("completed", 0)
            print(f"Продолжение с позиции {completed}/{total}")
            chats = chats[completed:]
        else:
            completed = 0

        chat_list = []
        for i, chat in enumerate(chats, completed):
            chat_list.append(chat)

            progress = int((i + 1) / total * 100)
            print(f"\rПрогресс: {i + 1}/{total} ({progress}%)", end="", flush=True)

            if (i + 1) % 10 == 0:
                self.file_manager.save_progress(
                    "chats", {"completed": i + 1, "total": total, "finished": False}
                )

        print(f"\n✅ Чаты обработаны: {total}")

        self.file_manager.save_chats_to_files(chat_list)
        self.file_manager.save_progress(
            "chats", {"completed": total, "total": total, "finished": True}
        )

        return total

    async def export_chat_members(self, resume: bool = False):
        """Export all members from all accessible chats and groups."""
        print("\n👥 Экспорт участников чатов...")

        # Get list of all chats
        all_chats = await self.telegram_client.get_all_group_chats()
        total_chats = len(all_chats)

        if total_chats == 0:
            print("⚠️ Не найдено групп или каналов для экспорта")
            return 0

        # Check what was already processed
        processed_chat_ids = []
        completed_chats = 0
        total_members = 0

        if resume and "chat_members" in self.file_manager.progress:
            progress_data = self.file_manager.progress["chat_members"]
            processed_chat_ids = progress_data.get("processed_items", [])
            completed_chats = progress_data.get("completed", 0)
            print(f"Продолжение с позиции {completed_chats}/{total_chats} чатов")
        else:
            # Clear existing files if not resuming
            if not resume:
                import os

                from config import (
                    CHAT_MEMBERS_CSV_TEMPLATE,
                    CHAT_MEMBERS_JSON_TEMPLATE,
                )

                for template in [CHAT_MEMBERS_CSV_TEMPLATE, CHAT_MEMBERS_JSON_TEMPLATE]:
                    file_path = self.file_manager.get_session_file_path(template)
                    if os.path.exists(file_path):
                        os.remove(file_path)

        print(f"📊 Всего чатов для обработки: {total_chats}")

        # Process each chat individually
        for i, chat_info in enumerate(all_chats):
            chat_id = chat_info["chat_id"]

            # Skip if already processed
            if chat_id in processed_chat_ids:
                continue

            try:
                # Get members for this specific chat
                chat_members = await self.telegram_client.get_chat_members_for_chat(
                    chat_info
                )

                if chat_members:
                    # Save immediately (append mode)
                    self.file_manager.save_chat_members_to_files(
                        chat_members,
                        append=(completed_chats > 0 or len(processed_chat_ids) > 0),
                    )
                    total_members += len(chat_members)

                # Mark this chat as processed
                processed_chat_ids.append(chat_id)
                completed_chats += 1

                # Update progress
                progress = int(completed_chats / total_chats * 100)
                print(f"Прогресс чатов: {completed_chats}/{total_chats} ({progress}%)")

                # Save progress every chat
                self.file_manager.save_progress(
                    "chat_members",
                    {
                        "completed": completed_chats,
                        "total": total_chats,
                        "finished": completed_chats >= total_chats,
                        "processed_items": processed_chat_ids,
                    },
                )

            except Exception as e:
                print(f"❌ Ошибка при обработке чата {chat_info['chat_title']}: {e}")
                # Still mark as processed to avoid infinite retries
                processed_chat_ids.append(chat_id)
                completed_chats += 1
                continue

        print(
            f"\n✅ Участники чатов обработаны: {total_members} из {total_chats} чатов"
        )

        # Final progress save
        self.file_manager.save_progress(
            "chat_members",
            {
                "completed": completed_chats,
                "total": total_chats,
                "finished": True,
                "processed_items": processed_chat_ids,
            },
        )

        return total_members

    async def ensure_connection(self):
        """Ensure Telegram connection is established."""
        if not self.menu_manager.current_session:
            print("❌ Сначала необходимо выбрать или создать сессию (пункт 1)")
            return False

        # Set session context for file operations
        self.file_manager.set_session(self.menu_manager.current_session)

        # Get session credentials
        credentials = self.menu_manager.get_current_session_credentials()
        if not credentials:
            print("❌ Не удалось загрузить учетные данные сессии")
            return False

        # Set up client
        session_path = self.menu_manager.get_current_session_path()
        self.telegram_client.set_session_file(session_path)
        self.telegram_client.set_credentials(
            credentials["api_id"], credentials["api_hash"], credentials["phone"]
        )

        if not self.telegram_client.client:
            await self.telegram_client.create_client()
            # Update last used timestamp
            self.menu_manager.session_manager.update_last_used(
                self.menu_manager.current_session
            )

        return True

    async def run(self):
        """Main application loop."""
        try:
            while True:
                choice = self.menu_manager.show_main_menu()

                if choice == "0":
                    print("👋 До свидания!")
                    break

                if choice == "1":
                    # Session management
                    session_selected = self.menu_manager.handle_session_management()
                    if session_selected and self.menu_manager.current_session:
                        print("\n🔄 Проверка подключения к Telegram...")
                        if await self.ensure_connection():
                            print("✅ Подключение успешно установлено!")
                        else:
                            print("❌ Не удалось подключиться")

                elif choice == "2":
                    if not await self.ensure_connection():
                        continue

                    resume = self.menu_manager.ask_resume("контактов")
                    await self.export_contacts(resume=resume)

                elif choice == "3":
                    if not await self.ensure_connection():
                        continue

                    resume = self.menu_manager.ask_resume("чатов")
                    await self.export_chats(resume=resume)

                elif choice == "4":
                    if not await self.ensure_connection():
                        continue

                    resume = self.menu_manager.ask_resume("участников чатов")
                    members_count = await self.export_chat_members(resume=resume)
                    print(
                        f"\n🎉 Экспорт участников завершен! Найдено {members_count} участников"
                    )

                elif choice == "5":
                    if not await self.ensure_connection():
                        continue

                    resume_contacts = self.menu_manager.ask_resume("контактов")
                    resume_chats = self.menu_manager.ask_resume("чатов")
                    resume_members = self.menu_manager.ask_resume("участников чатов")

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
                    matches_count = self.file_manager.cross_reference_nicknames()
                    if matches_count > 0:
                        print(
                            f"\n🎉 Сверка завершена! Найдено {matches_count} совпадений"
                        )
                    else:
                        print("\n😞 Сверка завершена, совпадений не найдено")

                else:
                    print("❌ Неверный выбор, попробуйте снова")

                self.menu_manager.wait_for_continue()

        finally:
            await self.telegram_client.disconnect()
