"""
CustomModules - A collection of custom Python modules for Discord bots and utilities.

Available modules:
- app_translation: Application translation utilities
- bitmap_handler: Bitmap manipulation and handling
- bot_directory: Bot directory management
- database_handler: Multi-database async handler
- googletrans: Google Translate integration
- invite_tracker: Discord invite tracking
- killswitch: Dead by Daylight killswitch monitoring
- libretrans: LibreTranslate integration
- log_handler: Advanced logging with colored console output
- patchnotes: Patch notes management
- private_voice: Private voice channel management
- random_usernames: Random username generation
- stat_dock: Statistics tracking for Discord
- steam: Steam API integration
- steam_charts: Steam Charts data retrieval
- twitch: Twitch API integration
"""

__version__ = "3.1.1"
__author__ = "Serpensin"
__license__ = "AGPL-3.0"

# Conditional imports based on available dependencies
try:
    from . import bitmap_handler
except ImportError:
    pass

try:
    from . import log_handler
except ImportError:
    pass

try:
    from . import app_translation
except ImportError:
    pass

try:
    from . import bot_directory
except ImportError:
    pass

try:
    from . import database_handler
except ImportError:
    pass

try:
    from . import googletrans
except ImportError:
    pass

try:
    from . import invite_tracker
except ImportError:
    pass

try:
    from . import killswitch
except ImportError:
    pass

try:
    from . import libretrans
except ImportError:
    pass

try:
    from . import patchnotes
except ImportError:
    pass

try:
    from . import private_voice
except ImportError:
    pass

try:
    from . import random_usernames
except ImportError:
    pass

try:
    from . import stat_dock
except ImportError:
    pass

try:
    from . import steam
except ImportError:
    pass

try:
    from . import steam_charts
except ImportError:
    pass

try:
    from . import twitch
except ImportError:
    pass

__all__ = [
    "app_translation",
    "bitmap_handler",
    "bot_directory",
    "database_handler",
    "googletrans",
    "invite_tracker",
    "killswitch",
    "libretrans",
    "log_handler",
    "patchnotes",
    "private_voice",
    "random_usernames",
    "stat_dock",
    "steam",
    "steam_charts",
    "twitch",
]
