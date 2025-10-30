# CustomModules

[![PyPI version](https://img.shields.io/pypi/v/CustomModules.svg)](https://pypi.org/project/CustomModules/)
[![Python versions](https://img.shields.io/pypi/pyversions/CustomModules.svg)](https://pypi.org/project/CustomModules/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Build Status](https://github.com/Serpensin/CustomModules-Python/actions/workflows/test-build.yml/badge.svg)](https://github.com/Serpensin/CustomModules-Python/actions/workflows/test-build.yml)
[![PyPI downloads](https://img.shields.io/pypi/dm/CustomModules.svg)](https://pypi.org/project/CustomModules/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A collection of custom Python modules for Discord bots and various utilities.

## ✨ What's New in v2.0.2

- **Universal Logger Support**: All modules now support optional logger parameter with hierarchical child logger pattern
- **Improved Security**: Fixed dependency issues and passed all Snyk security scans
- **Code Quality**: Achieved 10/10 pylint score with black formatting and flake8 compliance

## Installation

Install the base package:
```bash
pip install CustomModules
```

Install with specific module dependencies:
```bash
# Install with a specific module's dependencies
pip install CustomModules[statdock]
pip install CustomModules[databasehandler]
pip install CustomModules[loghandler]

# Install multiple modules
pip install CustomModules[statdock,databasehandler,loghandler]

# Install all modules with all dependencies
pip install CustomModules[all]
```

## Available Modules

- **AppTranslation** - Discord Application translation utilities
- **BitmapHandler** - Bitmap manipulation and handling
- **BotDirectory** - Bot directory management
- **DatabaseHandler** - Multi-database async handler (SQLite, MySQL, PostgreSQL, MongoDB)
- **Googletrans** - Google Translate integration
- **InviteTracker** - Discord invite tracking
- **Killswitch** - Dead by Daylight killswitch monitoring
- **Libretrans** - LibreTranslate integration
- **LogHandler** - Advanced logging with colored console output
- **Patchnotes** - Patch notes management for DeadByDaylight
- **PrivateVoice** - Private voice channel management
- **RandomUsernames** - Random username generation
- **StatDock** - Statistics tracking for Discord
- **Steam** - Steam API integration
- **SteamCharts** - Steam Charts data retrieval
- **Twitch** - Twitch API integration

## Usage

Import modules using dot notation:
```python
from CustomModules.bitmap_handler import BitmapHandler
from CustomModules.database_handler import DatabaseHandler
from CustomModules.log_handler import LogManager
from CustomModules.stat_dock import setup as stat_dock_setup
```

### Logger Support (v2.0.2+)

All modules now support optional logger parameter for better debugging and monitoring:

```python
import logging
from CustomModules.bitmap_handler import BitmapHandler
from CustomModules.steam import API as SteamAPI

# Create a parent logger
logger = logging.getLogger('MyApp')

# All modules create child loggers under CustomModules.ModuleName
bitmap = BitmapHandler(['read', 'write'], logger=logger)
# Creates logger: MyApp.CustomModules.BitmapHandler

steam_api = SteamAPI(api_key='your_key', logger=logger)
# Creates logger: MyApp.CustomModules.Steam

# Function-based modules use set_logger()
from CustomModules import killswitch
killswitch.set_logger(logger)
# Creates logger: MyApp.CustomModules.Killswitch
```

## Requirements

- Python 3.10 or higher
- Additional dependencies are installed based on which modules you use (see extras_require)

## License

This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0).

## Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation guide for end users
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Guide for developers and contributors
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/Serpensin/CustomModules-Python/issues) page.
