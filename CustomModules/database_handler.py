"""
Unified database handler module supporting multiple database systems.

Architecture:
- SQLite: Always synchronous (no native async support)
- MySQL/MariaDB/PostgreSQL/MongoDB: User chooses sync or async mode

Usage:
    # SQLite (always synchronous)
    from CustomModules.database_handler import SQLiteDatabaseHandler
    db = SQLiteDatabaseHandler("path/to/db.db")
    result = db.execute("SELECT * FROM users", fetch="all")
    
    # Other databases (async)
    from CustomModules.database_handler import AsyncDatabaseHandler
    db = await AsyncDatabaseHandler.create("mysql://user:pass@host/db")
    result = await db.execute("SELECT * FROM users", fetch="all")
    
    # Other databases (sync - runs async in thread pool)
    from CustomModules.database_handler import SyncDatabaseHandler
    db = SyncDatabaseHandler.create("mysql://user:pass@host/db")
    result = db.execute("SELECT * FROM users", fetch="all")  # No await!
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from urllib.parse import urlparse


# ============================================================================
# Base Classes
# ============================================================================


class _BaseDatabaseBackend(ABC):
    """Abstract base class for database backends"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("DatabaseHandler")
        else:
            self.logger = logging.getLogger("CustomModules.DatabaseHandler")

    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute a database query"""
        pass

    @abstractmethod
    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute a query multiple times with different parameters"""
        pass

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert query to backend-specific format (can be overridden)"""
        return query, params


class _BaseAsyncDatabaseBackend(ABC):
    """Abstract base class for async database backends"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("DatabaseHandler")
        else:
            self.logger = logging.getLogger("CustomModules.DatabaseHandler")

    @abstractmethod
    async def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute a database query"""
        pass

    @abstractmethod
    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute a query multiple times with different parameters"""
        pass

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert query to backend-specific format (can be overridden)"""
        return query, params


# ============================================================================
# SQLite Backend (Synchronous Only)
# ============================================================================


class _SQLiteSyncBackend(_BaseDatabaseBackend):
    """Synchronous SQLite backend - no async support"""

    DB_NOT_CONNECTED_ERROR = "Database connection not established"
    COMMITTED_TRANSACTION_MSG = "Committed transaction"

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(logger)
        self.connection: Optional[Any] = None  # sqlite3.Connection
        self.db_path: Optional[str] = None

    def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish synchronous SQLite connection with optimizations"""
        import sqlite3

        self.db_path = connection_params.get("path")
        if self.db_path is None:
            raise ValueError("SQLite database path is required")

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrent performance
        pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=-64000",
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=268435456",
            "PRAGMA busy_timeout=5000",
        ]

        for pragma in pragmas:
            self.connection.execute(pragma)

        self.logger.debug(f"SQLite connection established: {self.db_path}")

    def close(self) -> None:
        """Close SQLite connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.debug("SQLite connection closed")

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute SQLite query synchronously"""
        query, params = self.convert_query(query, params)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result: Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]] = None
            if fetch == "one":
                row = cursor.fetchone()
                result = dict(row) if row else None
            elif fetch == "all":
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            elif fetch is False:
                result = cursor.rowcount

            if commit:
                self.connection.commit()
                self.logger.debug(self.COMMITTED_TRANSACTION_MSG)

            return result

        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"SQLite query execution error: {e}")
            raise
        finally:
            cursor.close()

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute SQLite query multiple times"""
        query, _ = self.convert_query(query)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        cursor = self.connection.cursor()
        try:
            cursor.executemany(query, params_list)
            rowcount = cursor.rowcount

            if commit:
                self.connection.commit()
                self.logger.debug(
                    f"Committed batch transaction: {rowcount} rows affected"
                )

            return rowcount

        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"SQLite batch query execution error: {e}")
            raise
        finally:
            cursor.close()

    def checkpoint_wal(self) -> None:
        """Run a WAL checkpoint"""
        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        try:
            self.connection.execute("PRAGMA wal_checkpoint(FULL);")
            self.logger.info("WAL checkpoint completed")
        except Exception as e:
            self.logger.error(f"Error running WAL checkpoint: {e}")
            raise


# ============================================================================
# MySQL/MariaDB Backends
# ============================================================================


class _MySQLAsyncBackend(_BaseAsyncDatabaseBackend):
    """Async MySQL/MariaDB backend"""

    _AUTOINCREMENT_PATTERN = re.compile(r"AUTOINCREMENT", re.IGNORECASE)
    _CURRENT_TIMESTAMP_PATTERN = re.compile(
        r"DEFAULT\s+CURRENT_TIMESTAMP", re.IGNORECASE
    )
    DB_POOL_NOT_ESTABLISHED = "Database pool not established"
    COMMITTED_TRANSACTION_MSG = "Committed transaction"

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        pool_minsize: int = 1,
        pool_maxsize: int = 10,
    ):
        super().__init__(logger)
        self.pool: Any = None
        self.pool_minsize = pool_minsize
        self.pool_maxsize = pool_maxsize

    async def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish MySQL connection pool"""
        import aiomysql

        self.pool = await aiomysql.create_pool(
            host=connection_params.get("host", "localhost"),
            port=connection_params.get("port", 3306),
            user=connection_params.get("user"),
            password=connection_params.get("password"),
            db=connection_params.get("database"),
            autocommit=False,
            minsize=self.pool_minsize,
            maxsize=self.pool_maxsize,
        )
        self.logger.debug(
            f"MySQL pool established: {connection_params.get('database')} "
            f"(pool: {self.pool_minsize}-{self.pool_maxsize})"
        )

    async def close(self) -> None:
        """Close MySQL connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            self.logger.debug("MySQL pool closed")

    @lru_cache(maxsize=128)
    def _convert_query_cached(self, query: str) -> str:
        """Cache query conversions"""
        converted = query.replace("?", "%s")
        converted = self._AUTOINCREMENT_PATTERN.sub("AUTO_INCREMENT", converted)
        converted = self._CURRENT_TIMESTAMP_PATTERN.sub(
            "DEFAULT CURRENT_TIMESTAMP", converted
        )
        return converted

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert SQLite query to MySQL format"""
        return self._convert_query_cached(query), params

    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute MySQL query"""
        import aiomysql

        query, params = self.convert_query(query, params)

        if self.pool is None:
            raise RuntimeError(self.DB_POOL_NOT_ESTABLISHED)

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    if params:
                        await cursor.execute(query, params)
                    else:
                        await cursor.execute(query)

                    result: Optional[
                        Union[List[Dict[str, Any]], Dict[str, Any], int]
                    ] = None
                    if fetch == "one":
                        result = await cursor.fetchone()
                    elif fetch == "all":
                        result = await cursor.fetchall()
                    elif fetch is False:
                        result = cursor.rowcount

                    if commit:
                        await conn.commit()
                        self.logger.debug(self.COMMITTED_TRANSACTION_MSG)

                    return result

                except Exception as e:
                    await conn.rollback()
                    self.logger.error(f"MySQL query error: {e}")
                    raise

    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute MySQL query multiple times"""
        query, _ = self.convert_query(query)

        if self.pool is None:
            raise RuntimeError(self.DB_POOL_NOT_ESTABLISHED)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.executemany(query, params_list)
                    rowcount = cursor.rowcount

                    if commit:
                        await conn.commit()
                        self.logger.debug(
                            f"Committed batch: {rowcount} rows affected"
                        )

                    return rowcount

                except Exception as e:
                    await conn.rollback()
                    self.logger.error(f"MySQL batch error: {e}")
                    raise


class _MySQLSyncBackend(_BaseDatabaseBackend):
    """Synchronous MySQL/MariaDB backend using pymysql"""

    _AUTOINCREMENT_PATTERN = re.compile(r"AUTOINCREMENT", re.IGNORECASE)
    _CURRENT_TIMESTAMP_PATTERN = re.compile(
        r"DEFAULT\s+CURRENT_TIMESTAMP", re.IGNORECASE
    )
    DB_NOT_CONNECTED_ERROR = "Database connection not established"
    COMMITTED_TRANSACTION_MSG = "Committed transaction"

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.connection: Optional[Any] = None

    def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish MySQL connection"""
        import pymysql

        self.connection = pymysql.connect(
            host=connection_params.get("host", "localhost"),
            port=connection_params.get("port", 3306),
            user=connection_params.get("user"),
            password=connection_params.get("password"),
            database=connection_params.get("database"),
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.logger.debug(
            f"MySQL connection established: {connection_params.get('database')}"
        )

    def close(self) -> None:
        """Close MySQL connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.debug("MySQL connection closed")

    @lru_cache(maxsize=128)
    def _convert_query_cached(self, query: str) -> str:
        """Cache query conversions"""
        converted = query.replace("?", "%s")
        converted = self._AUTOINCREMENT_PATTERN.sub("AUTO_INCREMENT", converted)
        converted = self._CURRENT_TIMESTAMP_PATTERN.sub(
            "DEFAULT CURRENT_TIMESTAMP", converted
        )
        return converted

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert SQLite query to MySQL format"""
        return self._convert_query_cached(query), params

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute MySQL query"""
        query, params = self.convert_query(query, params)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        with self.connection.cursor() as cursor:
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                result: Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]] = (
                    None
                )
                if fetch == "one":
                    result = cursor.fetchone()
                elif fetch == "all":
                    result = cursor.fetchall()
                elif fetch is False:
                    result = cursor.rowcount

                if commit:
                    self.connection.commit()
                    self.logger.debug(self.COMMITTED_TRANSACTION_MSG)

                return result

            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"MySQL query error: {e}")
                raise

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute MySQL query multiple times"""
        query, _ = self.convert_query(query)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        with self.connection.cursor() as cursor:
            try:
                cursor.executemany(query, params_list)
                rowcount = cursor.rowcount

                if commit:
                    self.connection.commit()
                    self.logger.debug(f"Committed batch: {rowcount} rows affected")

                return rowcount

            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"MySQL batch error: {e}")
                raise


# ============================================================================
# PostgreSQL Backends
# ============================================================================


class _PostgreSQLAsyncBackend(_BaseAsyncDatabaseBackend):
    """Async PostgreSQL backend (supports asyncpg and psycopg)"""

    _AUTOINCREMENT_PATTERN = re.compile(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.IGNORECASE
    )
    _ROWCOUNT_PATTERN = re.compile(r"\d+")
    DB_POOL_NOT_ESTABLISHED = "Database pool not established"
    COMMITTED_TRANSACTION_MSG = "Committed transaction"

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        pool_minsize: int = 1,
        pool_maxsize: int = 10,
    ):
        super().__init__(logger)
        self.pool: Any = None
        self.driver: Optional[str] = None
        self.pool_minsize = pool_minsize
        self.pool_maxsize = pool_maxsize

    async def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish PostgreSQL connection pool"""
        # Try asyncpg first (most common and doesn't need psycopg_pool)
        try:
            import asyncpg  # type: ignore[import-not-found]

            self.driver = "asyncpg"
            self.pool = await asyncpg.create_pool(
                host=connection_params.get("host", "localhost"),
                port=connection_params.get("port", 5432),
                user=connection_params.get("user"),
                password=connection_params.get("password"),
                database=connection_params.get("database"),
                min_size=self.pool_minsize,
                max_size=self.pool_maxsize,
            )
            self.logger.debug(
                f"PostgreSQL (asyncpg) pool: {connection_params.get('database')} "
                f"({self.pool_minsize}-{self.pool_maxsize})"
            )
        except ImportError:
            # Fall back to psycopg if asyncpg not available
            try:
                from psycopg_pool import AsyncConnectionPool

                self.driver = "psycopg"
                conninfo = (
                    f"host={connection_params.get('host', 'localhost')} "
                    f"port={connection_params.get('port', 5432)} "
                    f"user={connection_params.get('user')} "
                    f"password={connection_params.get('password')} "
                    f"dbname={connection_params.get('database')}"
                )
                self.pool = AsyncConnectionPool(
                    conninfo, min_size=self.pool_minsize, max_size=self.pool_maxsize
                )
                await self.pool.wait()
                self.logger.debug(
                    f"PostgreSQL (psycopg) pool: {connection_params.get('database')} "
                    f"({self.pool_minsize}-{self.pool_maxsize})"
                )
            except ImportError as e:
                raise ImportError(
                    "PostgreSQL async support requires either 'asyncpg' or 'psycopg' with 'psycopg_pool'. "
                    "Install with: pip install asyncpg  (recommended) or: pip install psycopg psycopg-pool"
                ) from e

    async def close(self) -> None:
        """Close PostgreSQL pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.logger.debug(f"PostgreSQL ({self.driver}) pool closed")

    def _convert_query_impl(self, query: str) -> str:
        """Convert query to PostgreSQL format"""
        placeholder_count = query.count("?")
        converted = query
        for i in range(1, placeholder_count + 1):
            converted = converted.replace("?", f"${i}", 1)
        converted = self._AUTOINCREMENT_PATTERN.sub("SERIAL PRIMARY KEY", converted)
        return converted

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert SQLite query to PostgreSQL format"""
        return self._convert_query_impl(query), params

    def _normalize_params(
        self, params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]]
    ) -> Optional[Tuple[Any, ...]]:
        """Normalize parameters to tuple"""
        if isinstance(params, dict):
            return tuple(params.values()) if params else None
        elif isinstance(params, list):
            return tuple(params)
        return params

    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute PostgreSQL query"""
        query, params = self.convert_query(query, params)

        if self.driver == "asyncpg":
            return await self._execute_asyncpg(query, params, fetch)
        else:
            return await self._execute_psycopg(query, params, commit, fetch)

    async def _execute_asyncpg(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]],
        fetch: Optional[Union[str, bool]],
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute using asyncpg"""
        params_tuple = self._normalize_params(params)

        if self.pool is None:
            raise RuntimeError(self.DB_POOL_NOT_ESTABLISHED)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    if fetch == "one":
                        result = (
                            await conn.fetchrow(query, *params_tuple)
                            if params_tuple
                            else await conn.fetchrow(query)
                        )
                        return dict(result) if result else None
                    elif fetch == "all":
                        result = (
                            await conn.fetch(query, *params_tuple)
                            if params_tuple
                            else await conn.fetch(query)
                        )
                        return [dict(row) for row in result]
                    elif fetch is False:
                        result = (
                            await conn.execute(query, *params_tuple)
                            if params_tuple
                            else await conn.execute(query)
                        )
                        match = self._ROWCOUNT_PATTERN.search(str(result))
                        return int(match.group()) if match else 0
                    else:
                        if params_tuple:
                            await conn.execute(query, *params_tuple)
                        else:
                            await conn.execute(query)
                        return None
                except Exception as e:
                    self.logger.error(f"PostgreSQL (asyncpg) error: {e}")
                    raise

    async def _execute_psycopg(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]],
        commit: bool,
        fetch: Optional[Union[str, bool]],
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute using psycopg"""
        params_tuple = self._normalize_params(params)

        if self.pool is None:
            raise RuntimeError(self.DB_POOL_NOT_ESTABLISHED)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    if params_tuple:
                        await cursor.execute(query, params_tuple)
                    else:
                        await cursor.execute(query)

                    result: Optional[
                        Union[List[Dict[str, Any]], Dict[str, Any], int]
                    ] = None
                    if fetch == "one":
                        row = await cursor.fetchone()
                        if row:
                            columns = [desc[0] for desc in cursor.description]
                            result = dict(zip(columns, row))
                    elif fetch == "all":
                        rows = await cursor.fetchall()
                        if rows:
                            columns = [desc[0] for desc in cursor.description]
                            result = [dict(zip(columns, row)) for row in rows]
                        else:
                            result = []
                    elif fetch is False:
                        result = cursor.rowcount

                    if commit:
                        await conn.commit()

                    return result

                except Exception as e:
                    await conn.rollback()
                    self.logger.error(f"PostgreSQL (psycopg) error: {e}")
                    raise

    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute PostgreSQL query multiple times"""
        query, _ = self.convert_query(query)

        if self.pool is None:
            raise RuntimeError(self.DB_POOL_NOT_ESTABLISHED)

        if self.driver == "asyncpg":
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    try:
                        await conn.executemany(query, params_list)
                        self.logger.debug(
                            f"Committed batch: {len(params_list)} rows affected"
                        )
                        return len(params_list)
                    except Exception as e:
                        self.logger.error(f"PostgreSQL (asyncpg) batch error: {e}")
                        raise
        else:  # psycopg
            async with self.pool.connection() as conn:
                async with conn.cursor() as cursor:
                    try:
                        await cursor.executemany(query, params_list)
                        rowcount = cursor.rowcount
                        if commit:
                            await conn.commit()
                        self.logger.debug(f"Committed batch: {rowcount} rows affected")
                        return rowcount
                    except Exception as e:
                        await conn.rollback()
                        self.logger.error(f"PostgreSQL (psycopg) batch error: {e}")
                        raise


class _PostgreSQLSyncBackend(_BaseDatabaseBackend):
    """Synchronous PostgreSQL backend using psycopg (version 3)"""

    _AUTOINCREMENT_PATTERN = re.compile(
        r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.IGNORECASE
    )
    DB_NOT_CONNECTED_ERROR = "Database connection not established"
    COMMITTED_TRANSACTION_MSG = "Committed transaction"

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.connection: Optional[Any] = None

    def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish PostgreSQL connection"""
        import psycopg

        conninfo = (
            f"host={connection_params.get('host', 'localhost')} "
            f"port={connection_params.get('port', 5432)} "
            f"user={connection_params.get('user')} "
            f"password={connection_params.get('password')} "
            f"dbname={connection_params.get('database')}"
        )
        self.connection = psycopg.connect(conninfo)
        self.logger.debug(
            f"PostgreSQL connection established: {connection_params.get('database')}"
        )

    def close(self) -> None:
        """Close PostgreSQL connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.debug("PostgreSQL connection closed")

    def _convert_query_impl(self, query: str) -> str:
        """Convert query to PostgreSQL format - psycopg 3 uses %s placeholders"""
        # psycopg 3 uses %s style placeholders like MySQL, not $1 style
        converted = query.replace("?", "%s")
        converted = self._AUTOINCREMENT_PATTERN.sub("SERIAL PRIMARY KEY", converted)
        return converted

    def convert_query(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Tuple[str, Any]:
        """Convert SQLite query to PostgreSQL format"""
        return self._convert_query_impl(query), params

    def _normalize_params(
        self, params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]]
    ) -> Optional[Tuple[Any, ...]]:
        """Normalize parameters to tuple"""
        if isinstance(params, dict):
            return tuple(params.values()) if params else None
        elif isinstance(params, list):
            return tuple(params)
        return params

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute PostgreSQL query"""
        query, params = self.convert_query(query, params)
        params_tuple = self._normalize_params(params)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        with self.connection.cursor() as cursor:
            try:
                # Debug logging
                self.logger.debug(f"PostgreSQL Query: {query[:100]}...")
                self.logger.debug(f"PostgreSQL Params: {params_tuple}")
                
                if params_tuple:
                    cursor.execute(query, params_tuple)
                else:
                    cursor.execute(query)

                result: Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]] = (
                    None
                )
                if fetch == "one":
                    row = cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        result = dict(zip(columns, row))
                elif fetch == "all":
                    rows = cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        result = [dict(zip(columns, row)) for row in rows]
                    else:
                        result = []
                elif fetch is False:
                    result = cursor.rowcount

                if commit:
                    self.connection.commit()
                    self.logger.debug(self.COMMITTED_TRANSACTION_MSG)

                return result

            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"PostgreSQL query error: {e}")
                raise

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute PostgreSQL query multiple times"""
        query, _ = self.convert_query(query)

        if self.connection is None:
            raise RuntimeError(self.DB_NOT_CONNECTED_ERROR)

        with self.connection.cursor() as cursor:
            try:
                cursor.executemany(query, params_list)
                rowcount = cursor.rowcount

                if commit:
                    self.connection.commit()
                    self.logger.debug(f"Committed batch: {rowcount} rows affected")

                return rowcount

            except Exception as e:
                self.connection.rollback()
                self.logger.error(f"PostgreSQL batch error: {e}")
                raise


# ============================================================================
# MongoDB Backends  
# ============================================================================


class _MongoDBAsyncBackend(_BaseAsyncDatabaseBackend):
    """Async MongoDB backend"""

    _WHERE_PATTERN = re.compile(r"WHERE\s+(.+)$", re.IGNORECASE)
    _WHERE_WITH_LIMIT_PATTERN = re.compile(
        r"WHERE\s+(.+?)(?:ORDER BY|LIMIT)", re.IGNORECASE
    )
    _COLLECTION_PATTERN = re.compile(r"(?:FROM|INTO|UPDATE)\s+(\w+)", re.IGNORECASE)
    _COLUMNS_PATTERN = re.compile(r"\(([^)]+)\)\s*VALUES\s*\(", re.IGNORECASE)
    _SET_PATTERN = re.compile(r"SET\s+(.+?)\s+WHERE", re.IGNORECASE)
    _COLUMN_EQUALS_PATTERN = re.compile(r"(\w+)\s*=")
    _LIMIT_ONE_PATTERN = re.compile(r"LIMIT\s+1", re.IGNORECASE)
    _AND_PATTERN = re.compile(r"\s+AND\s+", re.IGNORECASE)

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.client: Any = None
        self.db: Any = None
        self.database_name: Optional[str] = None

    async def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish MongoDB connection"""
        from motor.motor_asyncio import AsyncIOMotorClient

        self.database_name = connection_params.get("database")
        
        # Build connection string with authSource=admin for authentication
        connection_string = (
            f"mongodb://{connection_params.get('user')}:{connection_params.get('password')}@"
            f"{connection_params.get('host', 'localhost')}:{connection_params.get('port', 27017)}/"
            f"{self.database_name}?authSource=admin"
        )

        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[self.database_name]
        
        # Verify connection
        try:
            await self.client.admin.command("ping")
            self.logger.debug(f"MongoDB connection established: {self.database_name}")
        except Exception as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            raise

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.logger.debug("MongoDB connection closed")

    def _parse_sql_to_mongo(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Convert SQL-like query to MongoDB operation"""
        query = query.strip()
        query_upper = query.upper()

        collection_match = self._COLLECTION_PATTERN.search(query)
        collection_name = collection_match.group(1) if collection_match else None

        operation: Dict[str, Any] = {
            "collection": collection_name,
            "operation": None,
            "filter": {},
            "data": {},
            "projection": None,
        }

        if query_upper.startswith("SELECT"):
            operation["operation"] = "find"
            where_match = self._WHERE_WITH_LIMIT_PATTERN.search(query)
            if not where_match:
                where_match = self._WHERE_PATTERN.search(query)
            if where_match and params and isinstance(params, (tuple, list)):
                where_clause = where_match.group(1).strip()
                operation["filter"] = self._parse_where_clause(where_clause, params)
            if self._LIMIT_ONE_PATTERN.search(query):
                operation["limit"] = 1

        elif query_upper.startswith("INSERT"):
            operation["operation"] = "insert"
            columns_match = self._COLUMNS_PATTERN.search(query)
            if columns_match and params:
                columns = [col.strip() for col in columns_match.group(1).split(",")]
                if isinstance(params, dict):
                    operation["data"] = params
                else:
                    operation["data"] = dict(zip(columns, params))

        elif query_upper.startswith("UPDATE"):
            operation["operation"] = "update"
            set_match = self._SET_PATTERN.search(query)
            if set_match and params and isinstance(params, (tuple, list)):
                set_clause = set_match.group(1)
                set_parts = [s.strip() for s in set_clause.split(",")]
                param_idx = 0
                for part in set_parts:
                    col_match = self._COLUMN_EQUALS_PATTERN.match(part)
                    if col_match and param_idx < len(params):
                        operation["data"][col_match.group(1)] = params[param_idx]
                        param_idx += 1
                where_match = self._WHERE_PATTERN.search(query)
                if where_match:
                    where_clause = where_match.group(1).strip()
                    remaining_params = params[param_idx:] if params else []
                    operation["filter"] = self._parse_where_clause(
                        where_clause, remaining_params
                    )

        elif query_upper.startswith("DELETE"):
            operation["operation"] = "delete"
            where_match = self._WHERE_PATTERN.search(query)
            if where_match and params and isinstance(params, (tuple, list)):
                where_clause = where_match.group(1).strip()
                operation["filter"] = self._parse_where_clause(where_clause, params)

        elif query_upper.startswith("CREATE TABLE"):
            operation["operation"] = "create_collection"

        return operation

    def _parse_where_clause(
        self, where_clause: str, params: Union[Tuple[Any, ...], List[Any]]
    ) -> Dict[str, Any]:
        """Parse SQL WHERE clause to MongoDB filter"""
        filter_dict: Dict[str, Any] = {}

        if "=" in where_clause and "?" in where_clause:
            parts = where_clause.split("=")
            if len(parts) == 2:
                column = parts[0].strip()
                if len(params) > 0:
                    filter_dict[column] = params[0]
        elif "AND" in where_clause.upper():
            conditions = self._AND_PATTERN.split(where_clause)
            param_idx = 0
            for condition in conditions:
                if "=" in condition:
                    column = condition.split("=")[0].strip()
                    if param_idx < len(params):
                        filter_dict[column] = params[param_idx]
                        param_idx += 1

        return filter_dict

    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute MongoDB operation"""
        try:
            operation = self._parse_sql_to_mongo(query, params)

            if not operation["collection"]:
                if "CREATE TABLE" in query.upper():
                    return None
                raise ValueError(f"Could not parse collection name from query: {query}")

            collection = self.db[operation["collection"]]

            if operation["operation"] == "find":
                cursor = collection.find(operation["filter"])
                if fetch == "one" or operation.get("limit") == 1:
                    result = await cursor.to_list(length=1)
                    return result[0] if result else None
                elif fetch == "all":
                    return await cursor.to_list(length=None)
                return None

            elif operation["operation"] == "insert":
                result = await collection.insert_one(operation["data"])
                return result.inserted_id if fetch is False else None

            elif operation["operation"] == "update":
                result = await collection.update_many(
                    operation["filter"], {"$set": operation["data"]}
                )
                return result.modified_count if fetch is False else None

            elif operation["operation"] == "delete":
                result = await collection.delete_many(operation["filter"])
                return result.deleted_count if fetch is False else None

            elif operation["operation"] == "create_collection":
                return None

            return None

        except Exception as e:
            self.logger.error(f"MongoDB operation error: {e}")
            raise

    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute MongoDB operation multiple times"""
        try:
            operation = self._parse_sql_to_mongo(
                query, params_list[0] if params_list else None
            )
            collection = self.db[operation["collection"]]

            if operation["operation"] == "insert":
                documents = []
                for params in params_list:
                    op = self._parse_sql_to_mongo(query, params)
                    documents.append(op["data"])
                result = await collection.insert_many(documents)
                return len(result.inserted_ids)

            return 0

        except Exception as e:
            self.logger.error(f"MongoDB batch operation error: {e}")
            raise


class _MongoDBSyncBackend(_BaseDatabaseBackend):
    """Synchronous MongoDB backend using pymongo"""

    _WHERE_PATTERN = re.compile(r"WHERE\s+(.+)$", re.IGNORECASE)
    _WHERE_WITH_LIMIT_PATTERN = re.compile(
        r"WHERE\s+(.+?)(?:ORDER BY|LIMIT)", re.IGNORECASE
    )
    _COLLECTION_PATTERN = re.compile(r"(?:FROM|INTO|UPDATE)\s+(\w+)", re.IGNORECASE)
    _COLUMNS_PATTERN = re.compile(r"\(([^)]+)\)\s*VALUES\s*\(", re.IGNORECASE)
    _SET_PATTERN = re.compile(r"SET\s+(.+?)\s+WHERE", re.IGNORECASE)
    _COLUMN_EQUALS_PATTERN = re.compile(r"(\w+)\s*=")
    _LIMIT_ONE_PATTERN = re.compile(r"LIMIT\s+1", re.IGNORECASE)
    _AND_PATTERN = re.compile(r"\s+AND\s+", re.IGNORECASE)

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.client: Any = None
        self.db: Any = None
        self.database_name: Optional[str] = None

    def connect(self, connection_params: Dict[str, Any]) -> None:
        """Establish MongoDB connection"""
        from pymongo import MongoClient

        self.database_name = connection_params.get("database")
        
        # Build connection string with authSource=admin for authentication
        connection_string = (
            f"mongodb://{connection_params.get('user')}:{connection_params.get('password')}@"
            f"{connection_params.get('host', 'localhost')}:{connection_params.get('port', 27017)}/"
            f"{self.database_name}?authSource=admin"
        )

        self.client = MongoClient(connection_string)
        self.db = self.client[self.database_name]
        
        # Verify connection
        try:
            self.client.admin.command("ping")
            self.logger.debug(f"MongoDB connection established: {self.database_name}")
        except Exception as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            raise

    def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.logger.debug("MongoDB connection closed")

    def _parse_sql_to_mongo(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Convert SQL-like query to MongoDB operation"""
        # Same implementation as async version
        query = query.strip()
        query_upper = query.upper()

        collection_match = self._COLLECTION_PATTERN.search(query)
        collection_name = collection_match.group(1) if collection_match else None

        operation: Dict[str, Any] = {
            "collection": collection_name,
            "operation": None,
            "filter": {},
            "data": {},
            "projection": None,
        }

        if query_upper.startswith("SELECT"):
            operation["operation"] = "find"
            where_match = self._WHERE_WITH_LIMIT_PATTERN.search(query)
            if not where_match:
                where_match = self._WHERE_PATTERN.search(query)
            if where_match and params and isinstance(params, (tuple, list)):
                where_clause = where_match.group(1).strip()
                operation["filter"] = self._parse_where_clause(where_clause, params)
            if self._LIMIT_ONE_PATTERN.search(query):
                operation["limit"] = 1

        elif query_upper.startswith("INSERT"):
            operation["operation"] = "insert"
            columns_match = self._COLUMNS_PATTERN.search(query)
            if columns_match and params:
                columns = [col.strip() for col in columns_match.group(1).split(",")]
                if isinstance(params, dict):
                    operation["data"] = params
                else:
                    operation["data"] = dict(zip(columns, params))

        elif query_upper.startswith("UPDATE"):
            operation["operation"] = "update"
            set_match = self._SET_PATTERN.search(query)
            if set_match and params and isinstance(params, (tuple, list)):
                set_clause = set_match.group(1)
                set_parts = [s.strip() for s in set_clause.split(",")]
                param_idx = 0
                for part in set_parts:
                    col_match = self._COLUMN_EQUALS_PATTERN.match(part)
                    if col_match and param_idx < len(params):
                        operation["data"][col_match.group(1)] = params[param_idx]
                        param_idx += 1
                where_match = self._WHERE_PATTERN.search(query)
                if where_match:
                    where_clause = where_match.group(1).strip()
                    remaining_params = params[param_idx:] if params else []
                    operation["filter"] = self._parse_where_clause(
                        where_clause, remaining_params
                    )

        elif query_upper.startswith("DELETE"):
            operation["operation"] = "delete"
            where_match = self._WHERE_PATTERN.search(query)
            if where_match and params and isinstance(params, (tuple, list)):
                where_clause = where_match.group(1).strip()
                operation["filter"] = self._parse_where_clause(where_clause, params)

        elif query_upper.startswith("CREATE TABLE"):
            operation["operation"] = "create_collection"

        return operation

    def _parse_where_clause(
        self, where_clause: str, params: Union[Tuple[Any, ...], List[Any]]
    ) -> Dict[str, Any]:
        """Parse SQL WHERE clause to MongoDB filter"""
        filter_dict: Dict[str, Any] = {}

        if "=" in where_clause and "?" in where_clause:
            parts = where_clause.split("=")
            if len(parts) == 2:
                column = parts[0].strip()
                if len(params) > 0:
                    filter_dict[column] = params[0]
        elif "AND" in where_clause.upper():
            conditions = self._AND_PATTERN.split(where_clause)
            param_idx = 0
            for condition in conditions:
                if "=" in condition:
                    column = condition.split("=")[0].strip()
                    if param_idx < len(params):
                        filter_dict[column] = params[param_idx]
                        param_idx += 1

        return filter_dict

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute MongoDB operation"""
        try:
            operation = self._parse_sql_to_mongo(query, params)

            if not operation["collection"]:
                if "CREATE TABLE" in query.upper():
                    return None
                raise ValueError(f"Could not parse collection name from query: {query}")

            collection = self.db[operation["collection"]]

            if operation["operation"] == "find":
                cursor = collection.find(operation["filter"])
                if fetch == "one" or operation.get("limit") == 1:
                    result = list(cursor.limit(1))
                    return result[0] if result else None
                elif fetch == "all":
                    return list(cursor)
                return None

            elif operation["operation"] == "insert":
                result = collection.insert_one(operation["data"])
                return result.inserted_id if fetch is False else None

            elif operation["operation"] == "update":
                result = collection.update_many(
                    operation["filter"], {"$set": operation["data"]}
                )
                return result.modified_count if fetch is False else None

            elif operation["operation"] == "delete":
                result = collection.delete_many(operation["filter"])
                return result.deleted_count if fetch is False else None

            elif operation["operation"] == "create_collection":
                return None

            return None

        except Exception as e:
            self.logger.error(f"MongoDB operation error: {e}")
            raise

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute MongoDB operation multiple times"""
        try:
            operation = self._parse_sql_to_mongo(
                query, params_list[0] if params_list else None
            )
            collection = self.db[operation["collection"]]

            if operation["operation"] == "insert":
                documents = []
                for params in params_list:
                    op = self._parse_sql_to_mongo(query, params)
                    documents.append(op["data"])
                result = collection.insert_many(documents)
                return len(result.inserted_ids)

            return 0

        except Exception as e:
            self.logger.error(f"MongoDB batch operation error: {e}")
            raise


# ============================================================================
# High-Level Handlers
# ============================================================================


class SQLiteDatabaseHandler:
    """
    SQLite database handler - always synchronous.
    
    Usage:
        db = SQLiteDatabaseHandler("path/to/db.db")
        result = db.execute("SELECT * FROM users", fetch="all")
        db.close()
    """

    def __init__(self, db_path: str, logger: Optional[logging.Logger] = None):
        """Initialize SQLite handler"""
        self.backend = _SQLiteSyncBackend(logger)
        self.backend.connect({"path": db_path})
        self.logger = logger or logging.getLogger(__name__)

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute a database query"""
        return self.backend.execute(query, params, commit, fetch)

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute a query multiple times"""
        return self.backend.execute_many(query, params_list, commit)

    def checkpoint_wal(self) -> None:
        """Run a WAL checkpoint"""
        self.backend.checkpoint_wal()

    def close(self) -> None:
        """Close database connection"""
        self.backend.close()

    def __enter__(self) -> "SQLiteDatabaseHandler":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()


class AsyncDatabaseHandler:
    """
    Async database handler for MySQL/MariaDB/PostgreSQL/MongoDB.
    
    Usage:
        db = await AsyncDatabaseHandler.create("mysql://user:pass@host/db")
        result = await db.execute("SELECT * FROM users", fetch="all")
        await db.close()
    """

    BACKENDS: Dict[str, Type[_BaseAsyncDatabaseBackend]] = {
        "mysql": _MySQLAsyncBackend,
        "mariadb": _MySQLAsyncBackend,
        "postgresql": _PostgreSQLAsyncBackend,
        "mongodb": _MongoDBAsyncBackend,
    }

    def __init__(
        self, backend: _BaseAsyncDatabaseBackend, logger: Optional[logging.Logger] = None
    ):
        """Initialize async handler"""
        self.backend = backend
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    async def create(
        cls,
        connection_string: str,
        logger: Optional[logging.Logger] = None,
        pool_minsize: int = 1,
        pool_maxsize: int = 10,
    ) -> "AsyncDatabaseHandler":
        """Create and initialize async database handler"""
        parsed = urlparse(connection_string)
        db_type = parsed.scheme.lower()

        if db_type == "sqlite":
            raise ValueError(
                "SQLite doesn't support async. Use SQLiteDatabaseHandler instead."
            )

        if db_type not in cls.BACKENDS:
            raise ValueError(
                f"Unsupported database: {db_type}. "
                f"Supported: {', '.join(cls.BACKENDS.keys())}"
            )

        backend_class = cls.BACKENDS[db_type]

        if db_type in ("mysql", "mariadb", "postgresql"):
            backend = backend_class(
                logger, pool_minsize=pool_minsize, pool_maxsize=pool_maxsize
            )
        else:
            backend = backend_class(logger)

        if db_type in ("mysql", "mariadb"):
            default_port = 3306
        elif db_type == "postgresql":
            default_port = 5432
        else:  # mongodb
            default_port = 27017

        connection_params = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or default_port,
            "user": parsed.username or "",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/"),
        }

        await backend.connect(connection_params)
        return cls(backend, logger)

    async def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute a database query"""
        return await self.backend.execute(query, params, commit, fetch)

    async def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute a query multiple times"""
        return await self.backend.execute_many(query, params_list, commit)

    async def close(self) -> None:
        """Close database connection"""
        await self.backend.close()

    async def __aenter__(self) -> "AsyncDatabaseHandler":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()


class SyncDatabaseHandler:
    """
    Synchronous database handler for MySQL/MariaDB/PostgreSQL/MongoDB.
    Runs operations in thread pool for compatibility.
    
    Usage:
        db = SyncDatabaseHandler.create("mysql://user:pass@host/db")
        result = db.execute("SELECT * FROM users", fetch="all")
        db.close()
    """

    BACKENDS: Dict[str, Type[_BaseDatabaseBackend]] = {
        "mysql": _MySQLSyncBackend,
        "mariadb": _MySQLSyncBackend,
        "postgresql": _PostgreSQLSyncBackend,
        "mongodb": _MongoDBSyncBackend,
    }

    def __init__(
        self, backend: _BaseDatabaseBackend, logger: Optional[logging.Logger] = None
    ):
        """Initialize sync handler"""
        self.backend = backend
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def create(
        cls,
        connection_string: str,
        logger: Optional[logging.Logger] = None,
    ) -> "SyncDatabaseHandler":
        """Create and initialize sync database handler"""
        parsed = urlparse(connection_string)
        db_type = parsed.scheme.lower()

        if db_type == "sqlite":
            raise ValueError(
                "SQLite doesn't need this handler. Use SQLiteDatabaseHandler instead."
            )

        if db_type not in cls.BACKENDS:
            raise ValueError(
                f"Unsupported database: {db_type}. "
                f"Supported: {', '.join(cls.BACKENDS.keys())}"
            )

        backend_class = cls.BACKENDS[db_type]
        backend = backend_class(logger)

        if db_type in ("mysql", "mariadb"):
            default_port = 3306
        elif db_type == "postgresql":
            default_port = 5432
        else:  # mongodb
            default_port = 27017

        connection_params = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or default_port,
            "user": parsed.username or "",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/"),
        }

        backend.connect(connection_params)
        return cls(backend, logger)

    def execute(
        self,
        query: str,
        params: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None,
        commit: bool = False,
        fetch: Optional[Union[str, bool]] = None,
    ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any], int]]:
        """Execute a database query"""
        return self.backend.execute(query, params, commit, fetch)

    def execute_many(
        self,
        query: str,
        params_list: List[Union[Tuple[Any, ...], Dict[str, Any]]],
        commit: bool = True,
    ) -> int:
        """Execute a query multiple times"""
        return self.backend.execute_many(query, params_list, commit)

    def close(self) -> None:
        """Close database connection"""
        self.backend.close()

    def __enter__(self) -> "SyncDatabaseHandler":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()

