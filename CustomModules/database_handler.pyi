"""Type stubs for DatabaseHandler module."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

class BaseDatabaseBackend(ABC):
    """Abstract base class for database backends"""
    logger: logging.Logger
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    
    @abstractmethod
    async def connect(self, connection_params: Dict[str, Any]) -> None: ...
    
    @abstractmethod
    async def close(self) -> None: ...
    
    @abstractmethod
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    
    @abstractmethod
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...
    
    @abstractmethod
    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]: ...

class SQLiteBackend(BaseDatabaseBackend):
    """SQLite database backend"""
    connection: Optional[Any]
    db_path: Optional[str]
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    async def connect(self, connection_params: Dict[str, Any]) -> None: ...
    async def close(self) -> None: ...
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...
    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]: ...

class MySQLBackend(BaseDatabaseBackend):
    """MySQL database backend"""
    pool: Optional[Any]
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    async def connect(self, connection_params: Dict[str, Any]) -> None: ...
    async def close(self) -> None: ...
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...
    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]: ...

class PostgreSQLBackend(BaseDatabaseBackend):
    """PostgreSQL database backend"""
    pool: Optional[Any]
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    async def connect(self, connection_params: Dict[str, Any]) -> None: ...
    async def close(self) -> None: ...
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...
    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]: ...

class MongoDBBackend(BaseDatabaseBackend):
    """MongoDB database backend"""
    client: Optional[Any]
    db: Optional[Any]
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None: ...
    async def connect(self, connection_params: Dict[str, Any]) -> None: ...
    async def close(self) -> None: ...
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...
    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]: ...

class AsyncDatabaseHandler:
    """Async database handler supporting multiple backends"""
    backend: Optional[BaseDatabaseBackend]
    logger: logging.Logger
    
    def __init__(
        self,
        db_uri: str,
        logger: Optional[logging.Logger] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ) -> None: ...
    
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...

class SyncDatabaseHandler:
    """Synchronous database handler supporting multiple backends"""
    backend: Optional[BaseDatabaseBackend]
    logger: logging.Logger
    
    def __init__(
        self,
        db_uri: str,
        logger: Optional[logging.Logger] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ) -> None: ...
    
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]: ...
    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int: ...

__all__ = [
    'BaseDatabaseBackend',
    'SQLiteBackend',
    'MySQLBackend',
    'PostgreSQLBackend',
    'MongoDBBackend',
    'AsyncDatabaseHandler',
    'SyncDatabaseHandler'
]
