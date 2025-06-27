#!/usr/bin/env python3
"""
Main entry point for Telegram contacts and chats exporter.

This script provides a command-line interface for exporting Telegram data
to CSV and JSON formats with cross-referencing capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegram_exporter import TelegramExporter


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
