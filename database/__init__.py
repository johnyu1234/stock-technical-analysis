"""
Database Package
Provides MySQL audit logging functionality for the Stock Analysis application.
"""

from .config import get_db_config, get_audit_config, DatabaseConfig, AuditConfig
from .connection import (
    init_connection_pool,
    get_connection,
    get_cursor,
    execute_query,
    execute_insert,
    close_pool,
    health_check,
)
from .audit_logger import (
    audit_log,
    log_external_call,
    AuditLogger,
)

__all__ = [
    # Config
    'get_db_config',
    'get_audit_config',
    'DatabaseConfig',
    'AuditConfig',
    # Connection
    'init_connection_pool',
    'get_connection',
    'get_cursor',
    'execute_query',
    'execute_insert',
    'close_pool',
    'health_check',
    # Audit
    'audit_log',
    'log_external_call',
    'AuditLogger',
]
