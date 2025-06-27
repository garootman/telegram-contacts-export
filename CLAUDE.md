# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a refactored Python application that exports Telegram contacts and chat data to CSV/JSON formats. It provides a modular command-line interface with multi-session support, progress tracking, and cross-referencing capabilities.

## Common Commands

### Running the Application
```bash
python main.py
```

### Development Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Testing
```bash
pytest                    # All tests
pytest -m "not integration"  # Fast unit tests only
pytest -n auto          # Parallel execution for speed
```

### Code Quality
```bash
ruff check .          # Linting
ruff format .         # Auto-formatting
ruff check . --fix    # Auto-fix issues
```

Note: Ruff handles both linting and formatting. Auto-formatting occurs on file save in VS Code.

## Architecture

### Modular Structure

The application is refactored into separate modules:

**`src/telegram_exporter.py`** - Main orchestrator class
**`src/session_manager.py`** - Multi-session management  
**`src/file_manager.py`** - File operations with session isolation
**`src/menu_manager.py`** - User interface and menu handling
**`src/telegram_client_wrapper.py`** - Telegram API wrapper
**`src/config.py`** - Configuration constants and templates
**`main.py`** - Application entry point

### Key Features

**Multi-Session Support:**
- Sessions stored in `sessions/` directory
- Each session has isolated exports in `exports/{session}/`
- Session metadata with credentials and usage tracking
- Legacy session migration from old `anon.session` format

**File Organization:**
- Session-specific output files using templates
- Progress tracking per session: `export_progress_{session}.json`
- Exported data: `telegram_contacts_{session}.csv/json`
- Cross-references: `telegram_nicknames_matches_{session}.csv/json`

**Export Process:**
- Granular chat member exports (per-chat processing)
- Resume capability for interrupted exports
- Dual format output (CSV + JSON)
- Progress saving every 10 items or per chat

### Session Management
1. User selects or creates session at startup
2. API credentials stored per session in `sessions/{session}_info.json`
3. Telegram session files in `sessions/{session}.session`
4. All exports isolated by session in `exports/{session}/`

## Development Notes

### Dependencies
- **Telethon**: Modern Telegram client library (>= 1.40.0)
- **pytest**: Testing framework with async support
- **pytest-xdist**: Parallel test execution (optional)
- **Python 3.7+**: Minimum version requirement

### Code Style
- Russian language interface and comments
- Modular architecture with separation of concerns
- Async/await pattern for Telegram operations
- Context managers for resource management
- Type hints where appropriate
- Auto-formatting with Ruff on save

### Testing
- Minimal test suite focused on core functionality
- Unit tests for SessionManager and FileManager
- Integration tests marked with `@pytest.mark.integration`
- Temporary directories with proper cleanup
- Mock objects for external dependencies

### Security Considerations
- Session files isolated per user account
- No hardcoded credentials
- All sensitive files in `.gitignore`
- API credentials stored locally only

## Common Issues

### Session Management
- Legacy `anon.session` files automatically migrated
- Multiple sessions supported for different accounts
- Session selection at startup
- Isolated exports prevent data mixing

### Performance
- Tests run without parallel execution by default
- Use `pytest -n auto` for parallel execution if needed
- Granular chat processing prevents timeouts
- Progress saved frequently for resumption

### File Organization
- All exports isolated by session name
- Template-based file naming for consistency
- Automatic directory creation
- Cross-referencing respects session isolation