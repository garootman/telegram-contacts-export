"""Основные тесты для Telegram exporter."""

import tempfile
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from file_manager import FileManager
from session_manager import SessionManager
from telegram_exporter import TelegramExporter


@contextmanager
def temp_directory():
    """Временная директория с автоочисткой."""
    import shutil

    test_dir = tempfile.mkdtemp()
    try:
        yield test_dir
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def session_manager():
    """SessionManager с временной директорией."""
    with temp_directory() as test_dir:
        manager = SessionManager()
        manager.sessions_dir = f"{test_dir}/sessions"
        manager.ensure_sessions_dir()
        yield manager


@pytest.fixture
def file_manager():
    """FileManager с временной директорией."""
    with temp_directory() as test_dir:
        manager = FileManager()
        manager.exports_dir = f"{test_dir}/exports"
        manager.ensure_exports_dir()
        yield manager


def test_session_manager_basic(session_manager):
    """Тест базовой функциональности SessionManager."""
    # Создание имени сессии
    phone = "+79991234567"
    session_name = session_manager.create_session_name(phone)
    assert session_name == "session_79991234567"

    # Сохранение и загрузка сессии
    api_id = "12345"
    api_hash = "test_hash"
    session_manager.save_session_info(session_name, api_id, api_hash, phone)

    info = session_manager.get_session_info(session_name)
    assert info["api_id"] == api_id
    assert info["api_hash"] == api_hash
    assert info["phone"] == phone

    # Получение credentials
    creds = session_manager.get_session_credentials(session_name)
    assert creds["api_id"] == api_id


def test_file_manager_basic(file_manager):
    """Тест базовой функциональности FileManager."""
    # Установка сессии
    session_name = "test_session"
    file_manager.set_session(session_name)
    assert file_manager.current_session == session_name

    # Сохранение контактов
    contacts = [{"id": 123, "first_name": "Test", "username": "test"}]
    result = file_manager.save_contacts_to_files(contacts)
    assert result == 1

    # Прогресс
    progress_data = {"completed": 50, "total": 100, "finished": False}
    file_manager.save_progress("test_export", progress_data)

    loaded_progress = file_manager.load_progress()
    assert "test_export" in loaded_progress
    assert loaded_progress["test_export"]["completed"] == 50


@pytest.mark.integration
def test_exporter_initialization():
    """Тест инициализации основного экспортера."""
    with temp_directory() as test_dir:
        exporter = TelegramExporter()
        exporter.file_manager.exports_dir = f"{test_dir}/exports"
        exporter.menu_manager.session_manager.sessions_dir = f"{test_dir}/sessions"

        # Проверка компонентов
        assert exporter.file_manager is not None
        assert exporter.menu_manager is not None
        assert exporter.telegram_client is not None


@pytest.mark.integration
async def test_export_workflow():
    """Тест workflow экспорта."""
    from unittest.mock import AsyncMock

    with temp_directory() as test_dir:
        exporter = TelegramExporter()
        exporter.file_manager.exports_dir = f"{test_dir}/exports"
        exporter.file_manager.set_session("test_session")

        # Мок данных
        mock_contacts = [{"id": 123, "first_name": "Test", "username": "test"}]
        exporter.telegram_client.get_contacts = AsyncMock(return_value=mock_contacts)

        # Экспорт
        result = await exporter.export_contacts()
        assert result == 1
