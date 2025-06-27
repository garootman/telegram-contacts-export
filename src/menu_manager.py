"""Menu management for Telegram exporter."""

from datetime import datetime
from typing import Dict, Optional

from session_manager import SessionManager


class MenuManager:
    """Handles menu display and user interaction."""

    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.session_manager = SessionManager()
        self.current_session = None

    def show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        print("\n" + "=" * 50)
        print("🚀 Telegram Data Exporter")
        print("=" * 50)

        # Show current session status
        if self.current_session:
            session_info = self.session_manager.get_session_info(self.current_session)
            phone = session_info.get("phone", "Unknown")
            print(f"\n📱 Текущая сессия: {self.current_session} ({phone})")
        else:
            print("\n❌ Сессия не выбрана")

        self._show_progress_info()

        print("\n📋 Выберите действие:")
        if not self.current_session:
            print("1. Управление сессиями")
            print("0. Выход")
        else:
            print("1. Управление сессиями")
            print("2. Экспорт контактов")
            print("3. Экспорт чатов")
            print("4. Экспорт участников чатов")
            print("5. Экспорт всего (контакты + чаты + участники)")
            print("6. Сверка с файлом nicknames.txt")
            print("0. Выход")

        return input("\nВведите номер действия: ").strip()

    def show_session_menu(self) -> str:
        """Display session management menu."""
        print("\n" + "=" * 50)
        print("📱 Управление сессиями")
        print("=" * 50)

        sessions = self.session_manager.list_sessions()

        if sessions:
            print("\n📋 Доступные сессии:")
            for i, session in enumerate(sessions, 1):
                status = "🟢" if session["name"] == self.current_session else "⚪"
                last_used = session.get("last_used", "Never")
                if last_used != "Never" and last_used != "Unknown":
                    try:
                        dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
                        last_used = dt.strftime("%d.%m.%Y %H:%M")
                    except (ValueError, TypeError):
                        pass

                print(
                    f"  {i}. {status} {session['name']} ({session['phone']}) - {last_used}"
                )
        else:
            print("\n❌ Сессии не найдены")

        print("\n📋 Действия:")
        if sessions:
            print("1-N. Выбрать сессию (номер из списка)")
        print("N. Создать новую сессию")
        if sessions:
            print("D. Удалить сессию")
        print("0. Назад в главное меню")

        return input("\nВведите действие: ").strip().lower()

    def _show_progress_info(self):
        """Show information about previous exports."""
        progress = self.file_manager.progress
        if progress:
            print("\n📊 Информация о предыдущих экспортах:")
            for export_type, data in progress.items():
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

    def ask_resume(self, export_type: str) -> bool:
        """Ask user if they want to resume incomplete export."""
        progress = self.file_manager.progress
        if export_type in progress and not progress[export_type].get("finished", False):
            resume_choice = input(
                f"Найден незавершенный экспорт {export_type}. Продолжить? (y/n): "
            ).lower()
            return resume_choice in ["y", "yes", "да", "д"]
        return False

    def wait_for_continue(self):
        """Wait for user to press Enter to continue."""
        input("\nНажмите Enter для продолжения...")

    def handle_session_management(self) -> bool:
        """Handle session management menu. Returns True if session was selected."""
        while True:
            choice = self.show_session_menu()

            if choice == "0":
                return self.current_session is not None

            elif choice == "n":
                # Create new session
                session_name = self.create_new_session()
                if session_name:
                    self.current_session = session_name
                    return True

            elif choice == "d":
                # Delete session
                self.delete_session_interactive()

            else:
                # Try to select session by number
                try:
                    sessions = self.session_manager.list_sessions()
                    session_num = int(choice) - 1

                    if 0 <= session_num < len(sessions):
                        self.current_session = sessions[session_num]["name"]
                        self.session_manager.update_last_used(self.current_session)
                        print(f"✅ Выбрана сессия: {self.current_session}")
                        return True
                    else:
                        print("❌ Неверный номер сессии")

                except ValueError:
                    print("❌ Неверный ввод")

    def create_new_session(self) -> Optional[str]:
        """Create a new session interactively."""
        print("\n🔧 Создание новой сессии")
        print("Получите api_id и api_hash на https://my.telegram.org")
        print("=" * 50)

        print("\n📝 Введите учетные данные:")
        api_id = input("API ID: ").strip()
        api_hash = input("API Hash: ").strip()
        phone = input(
            "Номер телефона (с кодом страны, например +79991234567): "
        ).strip()

        if not all([api_id, api_hash, phone]):
            print("❌ Ошибка: все поля должны быть заполнены!")
            return None

        # Generate session name
        session_name = self.session_manager.create_session_name(phone)

        # Check if session already exists
        if self.session_manager.session_exists(session_name):
            print(f"⚠️ Сессия для номера {phone} уже существует!")
            overwrite = input("Перезаписать? (y/n): ").lower()
            if overwrite not in ["y", "yes", "да", "д"]:
                return None

            # Delete existing session
            self.session_manager.delete_session(session_name)

        # Save session info
        self.session_manager.save_session_info(session_name, api_id, api_hash, phone)

        print(f"✅ Сессия '{session_name}' создана")
        return session_name

    def delete_session_interactive(self):
        """Delete session interactively."""
        sessions = self.session_manager.list_sessions()
        if not sessions:
            print("❌ Нет сессий для удаления")
            return

        print("\n🗑️ Удаление сессии")
        print("Выберите сессию для удаления:")

        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['name']} ({session['phone']})")

        try:
            choice = input("\nНомер сессии для удаления (0 - отмена): ").strip()
            if choice == "0":
                return

            session_num = int(choice) - 1
            if 0 <= session_num < len(sessions):
                session_to_delete = sessions[session_num]["name"]

                confirm = input(
                    f"Удалить сессию '{session_to_delete}'? (y/n): "
                ).lower()
                if confirm in ["y", "yes", "да", "д"]:
                    if self.session_manager.delete_session(session_to_delete):
                        print(f"✅ Сессия '{session_to_delete}' удалена")

                        # Clear current session if it was deleted
                        if self.current_session == session_to_delete:
                            self.current_session = None
                    else:
                        print("❌ Ошибка при удалении сессии")
            else:
                print("❌ Неверный номер сессии")

        except ValueError:
            print("❌ Неверный ввод")

    def get_current_session_path(self) -> Optional[str]:
        """Get path to current session file."""
        if self.current_session:
            return self.session_manager.get_session_path(self.current_session)
        return None

    def get_current_session_credentials(self) -> Optional[Dict]:
        """Get credentials for current session."""
        if self.current_session:
            return self.session_manager.get_session_credentials(self.current_session)
        return None

    def initialize_sessions(self):
        """Initialize session management, migrate old sessions if needed."""
        migrated_session = self.session_manager.migrate_old_session()
        if migrated_session:
            self.current_session = migrated_session
        else:
            # Try to auto-select the most recently used session
            sessions = self.session_manager.list_sessions()
            if sessions:
                self.current_session = sessions[0][
                    "name"
                ]  # Already sorted by last_used
