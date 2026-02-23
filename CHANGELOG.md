# Changelog

All notable changes to this project will be documented in this file.

## [3.1.2] - 2026-02-23

### Added
- Type stub files (`.pyi`) for all modules to enable type checking with pyright/mypy
  - `app_translation.pyi`, `bitmap_handler.pyi`, `bot_directory.pyi`, `googletrans.pyi`
  - `killswitch.pyi`, `libretrans.pyi`, `log_handler.pyi`, `patchnotes.pyi`
  - `private_voice.pyi`, `random_usernames.pyi`, `stat_dock.pyi`, `steam.pyi`
  - `steam_charts.pyi`, `twitch.pyi`
- `pyrightconfig.json` - Configuration for pyright type checker
- GitHub Actions workflow for type stub validation (`typecheck` job)
- `owns_game()` method to Steam API module

### Changed
- Updated GitHub Actions workflow to simplify test steps
- Updated `pyproject.toml` to include `.pyi` files in package distribution

### Fixed
- Fixed `googletrans.py` import: changed `from google.cloud import translate_v2` to `from google.cloud.translate_v2 import Client`
- Fixed `database_handler.py`: added default empty string for MySQL password parameter
- Fixed `database_handler.py`: added type ignore comment for pool parameters in async backend creation
- Added `.python-version` to `.gitignore`

### Removed
- Removed version info section from README.md (moved to CHANGELOG)
