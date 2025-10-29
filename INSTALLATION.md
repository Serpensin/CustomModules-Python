# Installation Guide

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
pip install CustomModules[StatDock]

# Multiple modules
pip install CustomModules[StatDock,DatabaseHandler,LogHandler]

# All modules
pip install CustomModules[all]
```

### Available Module Extras

You can install any of these extras:

- `AppTranslation` - Application translation utilities
- `BitmapHandler` - Bitmap manipulation (no additional dependencies)
- `BotDirectory` - Bot directory management
- `DatabaseHandler` - Multi-database async handler
- `Googletrans` - Google Translate integration
- `InviteTracker` - Discord invite tracking
- `Killswitch` - Dead by Daylight killswitch monitoring
- `Libretrans` - LibreTranslate integration
- `LogHandler` - Advanced logging with colored console output
- `Patchnotes` - Patch notes management
- `PrivateVoice` - Private voice channel management
- `RandomUsernames` - Random username generation
- `StatDock` - Statistics tracking for Discord
- `Steam` - Steam API integration
- `SteamCharts` - Steam Charts data retrieval
- `Twitch` - Twitch API integration
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

# Create a log manager
log_manager = LogManager(
    log_folder='./logs',
    app_folder_name='MyApp',
    log_level='INFO'
)

# Get a logger
logger = log_manager.get_logger('my_module')

# Use the logger
logger.info('Application started')
logger.error('An error occurred')
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
