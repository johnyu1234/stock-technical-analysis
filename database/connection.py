"""
Database Connection Module
Manages MySQL connection pool for audit logging.
"""

import mysql.connector
from mysql.connector import pooling, Error
from typing import Optional, Any
from contextlib import contextmanager
import logging

from .config import get_db_config, DatabaseConfig

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[pooling.MySQLConnectionPool] = None


def init_connection_pool(config: Optional[DatabaseConfig] = None) -> pooling.MySQLConnectionPool:
    """
    Initialize the MySQL connection pool.
    
    Args:
        config: Optional database configuration. Uses default if not provided.
        
    Returns:
        MySQLConnectionPool instance
    """
    global _connection_pool
    
    if _connection_pool is not None:
        return _connection_pool
    
    if config is None:
        config = get_db_config()
    
    try:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name=config.pool_name,
            pool_size=config.pool_size,
            pool_reset_session=config.pool_reset_session,
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset=config.charset,
            autocommit=True,
        )
        logger.info(f"Database connection pool '{config.pool_name}' initialized with {config.pool_size} connections")
        return _connection_pool
    except Error as e:
        logger.error(f"Failed to create connection pool: {e}")
        raise


def get_connection_pool() -> Optional[pooling.MySQLConnectionPool]:
    """Get the current connection pool or initialize if needed."""
    global _connection_pool
    if _connection_pool is None:
        return init_connection_pool()
    return _connection_pool


@contextmanager
def get_connection():
    """
    Context manager to get a database connection from the pool.
    
    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM api_audit_logs")
    """
    pool = get_connection_pool()
    connection = None
    
    try:
        connection = pool.get_connection()
        yield connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


@contextmanager
def get_cursor(dictionary: bool = True):
    """
    Context manager to get a database cursor.
    
    Args:
        dictionary: If True, returns results as dictionaries
        
    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM api_audit_logs WHERE id = %s", (1,))
            result = cursor.fetchone()
    """
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            connection.commit()
        except Error as e:
            connection.rollback()
            logger.error(f"Database operation error: {e}")
            raise
        finally:
            cursor.close()


def execute_query(query: str, params: tuple = None, fetch: bool = True) -> Any:
    """
    Execute a SQL query with optional parameters.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters
        fetch: If True, fetch and return results
        
    Returns:
        Query results if fetch=True, otherwise None
    """
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        return None


def execute_insert(query: str, params: tuple = None) -> int:
    """
    Execute an INSERT query and return the last inserted ID.
    
    Args:
        query: INSERT SQL query
        params: Optional tuple of parameters
        
    Returns:
        Last inserted row ID
    """
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.lastrowid


def close_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool is not None:
        # Note: mysql-connector-python doesn't have explicit pool close
        # Connections are closed when they go out of scope
        _connection_pool = None
        logger.info("Database connection pool closed")


def health_check() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result is not None
    except Error as e:
        logger.error(f"Database health check failed: {e}")
        return False
