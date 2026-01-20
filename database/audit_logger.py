"""
Audit Logger Module
Provides Flask middleware and decorators for logging API requests/responses.
"""

import json
import time
import uuid
import functools
import logging
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager

from flask import request, g

from .config import get_audit_config, AuditConfig
from .connection import execute_insert, get_cursor

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking API requests and external calls.
    """
    
    def __init__(self, config: Optional[AuditConfig] = None):
        self.config = config or get_audit_config()
    
    def _truncate_data(self, data: Any, max_size: int) -> tuple[Any, bool]:
        """
        Truncate data if it exceeds max_size.
        
        Returns:
            Tuple of (truncated_data, was_truncated)
        """
        if data is None:
            return None, False
        
        try:
            json_str = json.dumps(data, default=str)
            if len(json_str) <= max_size:
                return data, False
            
            # Truncate and add marker
            truncated_str = json_str[:max_size - len(self.config.truncation_marker)]
            return truncated_str + self.config.truncation_marker, True
        except (TypeError, ValueError):
            return str(data)[:max_size], True
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive headers from logging."""
        return {
            k: v for k, v in headers.items()
            if k.lower() not in self.config.excluded_headers
        }
    
    def _get_client_ip(self) -> str:
        """Get client IP address, handling proxies."""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr or 'unknown'
    
    def log_request(
        self,
        request_id: str,
        endpoint: str,
        http_method: str,
        request_params: dict,
        request_body: Optional[dict],
        response_status: int,
        response_body: Any,
        execution_time_ms: int,
        status: str = 'SUCCESS',
        error_message: Optional[str] = None,
    ) -> Optional[int]:
        """
        Log an API request to the database.
        
        Returns:
            The inserted log ID, or None if logging is disabled/failed
        """
        if not self.config.enable_request_logging:
            return None
        
        try:
            # Truncate response if needed
            response_data, is_truncated = self._truncate_data(
                response_body, 
                self.config.max_response_body_size
            )
            
            # Truncate request body if needed
            request_data, _ = self._truncate_data(
                request_body,
                self.config.max_request_body_size
            )
            
            # Calculate original response size
            response_size = len(json.dumps(response_body, default=str)) if response_body else 0
            
            query = """
                INSERT INTO api_audit_logs (
                    request_id, api_type, endpoint, http_method, source_ip, user_agent,
                    request_headers, request_params, request_body,
                    response_status_code, response_body, response_size_bytes, is_response_truncated,
                    execution_time_ms, status, error_message
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
            """
            
            params = (
                request_id,
                'INTERNAL',
                endpoint,
                http_method,
                self._get_client_ip(),
                request.headers.get('User-Agent', '')[:255],
                json.dumps(self._sanitize_headers(dict(request.headers))),
                json.dumps(request_params),
                json.dumps(request_data) if request_data else None,
                response_status,
                json.dumps(response_data) if response_data else None,
                response_size,
                is_truncated,
                execution_time_ms,
                status,
                error_message,
            )
            
            log_id = execute_insert(query, params)
            
            # Update performance metrics if enabled
            if self.config.enable_performance_metrics:
                self._update_metrics(endpoint, execution_time_ms, status == 'SUCCESS')
            
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            return None
    
    def log_external_call(
        self,
        audit_log_id: Optional[int],
        service_name: str,
        endpoint_url: str,
        http_method: str = 'GET',
        request_payload: Optional[dict] = None,
        response_payload: Any = None,
        response_status: int = 200,
        execution_time_ms: int = 0,
        status: str = 'SUCCESS',
        error_message: Optional[str] = None,
    ) -> Optional[int]:
        """
        Log an external API call to the database.
        
        Returns:
            The inserted log ID, or None if logging is disabled/failed
        """
        if not self.config.enable_external_call_logging:
            return None
        
        try:
            # Truncate response if needed
            response_data, is_truncated = self._truncate_data(
                response_payload,
                self.config.max_response_body_size
            )
            
            query = """
                INSERT INTO external_api_calls (
                    audit_log_id, service_name, endpoint_url, http_method,
                    request_payload, response_payload, response_status_code, is_response_truncated,
                    execution_time_ms, status, error_message
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
            """
            
            params = (
                audit_log_id,
                service_name,
                endpoint_url[:255],
                http_method,
                json.dumps(request_payload) if request_payload else None,
                json.dumps(response_data) if response_data else None,
                response_status,
                is_truncated,
                execution_time_ms,
                status,
                error_message,
            )
            
            return execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Failed to log external API call: {e}")
            return None
    
    def _update_metrics(self, endpoint: str, execution_time_ms: int, is_success: bool) -> None:
        """Update performance metrics using stored procedure."""
        try:
            with get_cursor() as cursor:
                cursor.callproc('update_performance_metrics', 
                              (endpoint, execution_time_ms, is_success))
        except Exception as e:
            logger.warning(f"Failed to update performance metrics: {e}")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(func: Callable) -> Callable:
    """
    Decorator to automatically log Flask API requests and responses.
    
    Usage:
        @app.route('/api/stock/<symbol>')
        @audit_log
        def get_stock_data(symbol):
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        g.audit_request_id = request_id
        
        start_time = time.time()
        status = 'SUCCESS'
        error_message = None
        response_body = None
        response_status = 200
        
        try:
            # Execute the actual function
            result = func(*args, **kwargs)
            
            # Extract response data
            if hasattr(result, 'get_json'):
                response_body = result.get_json()
                response_status = result.status_code
            elif isinstance(result, tuple):
                response_body = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
                response_status = result[1] if len(result) > 1 else 200
            else:
                response_body = result
            
            if response_status >= 400:
                status = 'ERROR'
            
            return result
            
        except Exception as e:
            status = 'ERROR'
            error_message = str(e)
            response_status = 500
            raise
            
        finally:
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the request
            audit_logger = get_audit_logger()
            audit_logger.log_request(
                request_id=request_id,
                endpoint=request.path,
                http_method=request.method,
                request_params=dict(request.args),
                request_body=request.get_json(silent=True),
                response_status=response_status,
                response_body=response_body,
                execution_time_ms=execution_time_ms,
                status=status,
                error_message=error_message,
            )
    
    return wrapper


@contextmanager
def log_external_call(
    service_name: str,
    endpoint_url: str,
    http_method: str = 'GET',
    request_payload: Optional[dict] = None,
):
    """
    Context manager for logging external API calls.
    
    Usage:
        with log_external_call('yahoo_finance', 'ticker.history') as ctx:
            result = ticker.history(period=period)
            ctx['response'] = result  # Optional: set response data
    """
    audit_logger = get_audit_logger()
    
    # Get parent request ID if available
    audit_log_id = getattr(g, 'audit_log_id', None) if hasattr(g, 'audit_log_id') else None
    
    context = {
        'response': None,
        'status_code': 200,
        'error': None,
    }
    
    start_time = time.time()
    status = 'SUCCESS'
    
    try:
        yield context
    except Exception as e:
        status = 'ERROR'
        context['error'] = str(e)
        context['status_code'] = 500
        raise
    finally:
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        audit_logger.log_external_call(
            audit_log_id=audit_log_id,
            service_name=service_name,
            endpoint_url=endpoint_url,
            http_method=http_method,
            request_payload=request_payload,
            response_payload=context.get('response'),
            response_status=context.get('status_code', 200),
            execution_time_ms=execution_time_ms,
            status=status,
            error_message=context.get('error'),
        )
