"""
Database Configuration Module
Contains all database connection settings and audit logging configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables directly


@dataclass
class DatabaseConfig:
    """MySQL database connection configuration."""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '3306'))
    user: str = os.getenv('DB_USER', 'root')
    password: str = os.getenv('DB_PASSWORD', '')
    database: str = os.getenv('DB_NAME', 'stock_analysis_audit')
    charset: str = 'utf8mb4'
    
    # Connection pool settings
    pool_name: str = 'audit_pool'
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '5'))
    pool_reset_session: bool = True


@dataclass
class AuditConfig:
    """Audit logging configuration with configurable thresholds."""
    
    # Response/Request body truncation thresholds (in bytes)
    max_response_body_size: int = int(os.getenv('AUDIT_MAX_RESPONSE_SIZE', str(10 * 1024)))  # 10KB default
    max_request_body_size: int = int(os.getenv('AUDIT_MAX_REQUEST_SIZE', str(10 * 1024)))   # 10KB default
    
    # Data retention (in days)
    retention_days: int = int(os.getenv('AUDIT_RETENTION_DAYS', '30'))
    
    # Feature toggles
    enable_performance_metrics: bool = os.getenv('AUDIT_ENABLE_METRICS', 'true').lower() == 'true'
    enable_request_logging: bool = os.getenv('AUDIT_ENABLE_REQUEST_LOG', 'true').lower() == 'true'
    enable_external_call_logging: bool = os.getenv('AUDIT_ENABLE_EXTERNAL_LOG', 'true').lower() == 'true'
    
    # Headers to exclude from logging (sensitive data)
    excluded_headers: tuple = (
        'authorization',
        'cookie',
        'x-api-key',
        'x-auth-token',
    )
    
    # Truncation marker
    truncation_marker: str = '... [TRUNCATED]'


# Global configuration instances
db_config = DatabaseConfig()
audit_config = AuditConfig()


def get_db_config() -> DatabaseConfig:
    """Get database configuration instance."""
    return db_config


def get_audit_config() -> AuditConfig:
    """Get audit configuration instance."""
    return audit_config
