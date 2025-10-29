"""DatabaseHandler module - Multi-database async handler."""
import sys
import os

# Add parent directory to path to allow importing from sibling directories
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from DatabaseHandler.DatabaseHandler import (
    BaseDatabaseBackend,
    SQLiteBackend,
    MySQLBackend,
    PostgreSQLBackend,
    MongoDBBackend,
    AsyncDatabaseHandler,
    SyncDatabaseHandler
)

__all__ = [
    'BaseDatabaseBackend',
    'SQLiteBackend',
    'MySQLBackend',
    'PostgreSQLBackend',
    'MongoDBBackend',
    'AsyncDatabaseHandler',
    'SyncDatabaseHandler'
]
