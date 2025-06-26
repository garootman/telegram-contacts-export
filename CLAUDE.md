# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that exports Telegram contacts and chat data to CSV/JSON formats. It provides a command-line interface for authentication, data export, and cross-referencing with custom nickname lists.

## Common Commands

### Running the Application
```bash
python export.py
```

### Development Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Code Quality
```bash
ruff check .          # Linting (preferred over pylint)
ruff format .         # Code formatting
```

Note: The project uses Ruff for linting and formatting. Previous attempts with pylint were abandoned in favor of Ruff.

## Architecture

### Core Components

**`export.py`** - Single main file containing:
- `TelegramExporter` class: Main application logic
- Async/await pattern using Telethon library
- Interactive CLI menu system with Russian interface
- Session management and progress tracking
- Data export functionality (CSV/JSON)
- Cross-referencing system for nickname matching

### Key Files and Data Flow

**Configuration Files:**
- `credentials.json` - API credentials storage
- `anon.session` - Telegram session persistence
- `export_progress.json` - Export resume capability
- `nicknames.txt` - User-defined nicknames for cross-referencing

**Output Files:**
- `telegram_contacts.csv/json` - Exported contacts
- `telegram_chats.csv` - Chat metadata
- `telegram_dialogs.json` - Dialog information
- `telegram_nicknames_matches.csv/json` - Cross-reference results

### Authentication Flow
1. User provides API credentials (api_id, api_hash from my.telegram.org)
2. Phone number verification
3. Two-factor authentication if enabled
4. Session saved to `anon.session` for reuse

### Export Process
- Batch processing with progress tracking
- Resume capability for interrupted exports
- Dual format output (CSV for spreadsheets, JSON for programmatic use)
- Unicode support for international usernames

## Development Notes

### Dependencies
- **Telethon**: Modern Telegram client library (>= 1.40.0)
- **Python 3.7+**: Minimum version requirement
- Standard library only (asyncio, csv, json, datetime)

### Code Style
- Russian language interface and comments
- Async/await pattern throughout
- Progress indicators and user feedback
- Error handling with user-friendly messages
- Modular class-based design

### Security Considerations
- All sensitive files properly gitignored
- No hardcoded credentials
- Session files excluded from version control
- API credentials stored locally only

### Data Formats
The application exports structured data with consistent field names:
- **Contacts**: id, first_name, last_name, username, phone, etc.
- **Chats**: dialog metadata including unread counts, pinned status
- **Cross-references**: matches between exported data and nickname lists

### Resume Functionality
The application can resume interrupted exports by:
- Saving progress in `export_progress.json`
- Tracking completion status per export type
- Offering resume options on restart

## Common Issues

### Authentication
- Ensure API credentials are obtained from my.telegram.org
- Handle 2FA prompts interactively
- Session files persist authentication state

### Export Process
- Large contact lists may take time to process
- Progress is saved automatically for resumption
- Multiple output formats generated simultaneously

### Cross-referencing
- Nicknames file should contain one username per line
- No @ symbols needed in nicknames.txt
- Matches are case-insensitive