# CustomModules

A collection of custom Python modules for Discord bots and various utilities.

## Installation

Install the base package:
```bash
pip install CustomModules
```

Install with specific module dependencies:
```bash
# Install with a specific module's dependencies
pip install CustomModules[StatDock]
pip install CustomModules[DatabaseHandler]
pip install CustomModules[LogHandler]

# Install multiple modules
pip install CustomModules[StatDock,DatabaseHandler,LogHandler]

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
from CustomModules.stat_dock import StatDock
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
