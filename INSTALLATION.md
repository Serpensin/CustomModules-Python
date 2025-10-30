# Installation Guide

## What's New in v2.0.2

- **Universal Logger Support**: All 16 modules now support optional logger parameter
- **Logger Hierarchy**: Child loggers follow pattern `parent.getChild('CustomModules').getChild('ModuleName')`
- **Improved Code Quality**: 10/10 pylint score, black formatted, flake8 compliant
- **Security**: Fixed dependencies, passed Snyk security scans

## For End Users

### Basic Installation

Install the base package without any dependencies:

```bash
pip install CustomModules
```

### Installing Specific Modules

Install with dependencies for specific modules you plan to use:

```bash
# Single module
pip install CustomModules[statdock]

# Multiple modules
pip install CustomModules[statdock,databasehandler,loghandler]

# All modules
pip install CustomModules[all]
```

### Available Module Extras

You can install any of these extras (use lowercase):

- `apptranslation` - Application translation utilities
- `bitmaphandler` - Bitmap manipulation (no additional dependencies)
- `botdirectory` - Bot directory management
- `databasehandler` - Multi-database async handler
- `googletrans` - Google Translate integration
- `invitetracker` - Discord invite tracking
- `killswitch` - Dead by Daylight killswitch monitoring
- `libretrans` - LibreTranslate integration
- `loghandler` - Advanced logging with colored console output
- `patchnotes` - Patch notes management
- `privatevoice` - Private voice channel management
- `randomusernames` - Random username generation
- `statdock` - Statistics tracking for Discord
- `steam` - Steam API integration
- `steamcharts` - Steam Charts data retrieval
- `twitch` - Twitch API integration
- `all` - Install all dependencies for all modules

## Usage Examples

### Using BitmapHandler

```python
from CustomModules.bitmap_handler import BitmapHandler

# Create a bitmap handler
keys = ['read', 'write', 'execute', 'delete']
handler = BitmapHandler(keys)

# Get a bitkey
bitkey = handler.get_bitkey('read', 'write')

# Check if a key is in the bitkey
has_read = handler.check_key_in_bitkey('read', bitkey)
```

### Using LogHandler

```python
from CustomModules.log_handler import LogManager
import logging

# Create a parent logger
parent_logger = logging.getLogger('MyApp')

# Create a log manager with parent logger
log_manager = LogManager(
    log_folder='./logs',
    app_folder_name='MyApp',
    log_level='INFO',
    logger=parent_logger  # Optional: enables meta-logging
)

# Get a logger
logger = log_manager.get_logger('my_module')

# Use the logger
logger.info('Application started')
logger.error('An error occurred')
```

### Using Logger Support (v2.0.2+)

All modules now support optional logger parameter:

```python
import logging
from CustomModules.bitmap_handler import BitmapHandler
from CustomModules.steam import API as SteamAPI

# Create a parent logger
logger = logging.getLogger('MyApp')

# Class-based modules: pass logger to __init__
bitmap = BitmapHandler(['read', 'write'], logger=logger)
steam_api = SteamAPI(api_key='your_key', logger=logger)

# Function-based modules: use set_logger()
from CustomModules import killswitch, random_usernames
killswitch.set_logger(logger)
random_usernames.set_logger(logger)

# Setup function modules: pass logger to setup()
from CustomModules.stat_dock import setup as stat_dock_setup
stat_dock_setup(client, tree, connection, logger=logger)
```

### Using DatabaseHandler

```python
from CustomModules.database_handler import DatabaseHandler

# Create a database handler
db = DatabaseHandler(
    db_type='sqlite',
    connection_string='sqlite:///mydb.sqlite'
)

# Initialize the database
await db.initialize()

# Execute a query
result = await db.execute(
    'SELECT * FROM users WHERE id = ?',
    params=(1,),
    fetch='one'
)

# Close the connection
await db.close()
```

### Using StatDock

```python
from CustomModules.stat_dock import StatDock
import discord

# Create a StatDock instance
statdock = StatDock(
    bot=bot,  # Your discord.py bot instance
    db_path='./stats.db',
    timezone='UTC'
)

# Setup in your bot's on_ready event
await statdock.setup(guild_id=123456789)
```

## Requirements

- Python 3.10 or higher
- Additional requirements depend on which modules you use

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade CustomModules

# Or with extras
pip install --upgrade CustomModules[all]
```

## Uninstalling

```bash
pip uninstall CustomModules
```

## Troubleshooting

### Import Error: No module named 'CustomModules.xxx'

Make sure you installed the module's dependencies:

```bash
pip install CustomModules[xxx]
```

### Import Error: No module named 'discord'

Some modules require discord.py. Install with:

```bash
pip install CustomModules[StatDock]
# or
pip install discord.py
```

### Import Error: No module named 'aiosqlite'

Database modules require database drivers. Install with:

```bash
pip install CustomModules[DatabaseHandler]
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/Serpensin/CustomModules-Python/issues)
- **Documentation**: [README.md](https://github.com/Serpensin/CustomModules-Python/blob/master/README.md)
- **Source Code**: [GitHub](https://github.com/Serpensin/CustomModules-Python)

## License

This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0).
See the LICENSE.txt file for details.
