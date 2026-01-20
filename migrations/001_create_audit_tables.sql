-- ============================================================================
-- MySQL Audit Log Database Migration Script
-- Version: 001
-- Description: Create audit log tables for API request/response tracking
-- ============================================================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS stock_analysis_audit
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE stock_analysis_audit;

-- ============================================================================
-- Table 1: api_audit_logs (Main Audit Table)
-- Logs all incoming requests to internal Flask endpoints
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL UNIQUE COMMENT 'UUID for request tracing',
    
    -- Request metadata
    api_type ENUM('INTERNAL', 'EXTERNAL') NOT NULL DEFAULT 'INTERNAL',
    endpoint VARCHAR(100) NOT NULL COMMENT 'e.g., /api/stock/TSLA',
    http_method VARCHAR(10) NOT NULL COMMENT 'GET, POST, etc.',
    source_ip VARCHAR(50) COMMENT 'Client IP address',
    user_agent VARCHAR(255) COMMENT 'Browser/client info',
    
    -- Request data (will be truncated if over threshold)
    request_headers JSON COMMENT 'Sanitized headers',
    request_params JSON COMMENT 'Query parameters',
    request_body JSON COMMENT 'POST body (truncated if large)',
    
    -- Response data (will be truncated if over threshold)
    response_status_code INT COMMENT 'HTTP status code',
    response_body JSON COMMENT 'Response payload (truncated if large)',
    response_size_bytes BIGINT COMMENT 'Original response size before truncation',
    is_response_truncated BOOLEAN DEFAULT FALSE COMMENT 'True if response was truncated',
    
    -- Performance
    execution_time_ms INT COMMENT 'Total processing time in milliseconds',
    
    -- Status
    status ENUM('SUCCESS', 'ERROR', 'TIMEOUT') NOT NULL DEFAULT 'SUCCESS',
    error_message TEXT COMMENT 'Error details if failed',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    INDEX idx_endpoint (endpoint),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status),
    INDEX idx_api_type (api_type),
    INDEX idx_request_id (request_id),
    INDEX idx_response_status (response_status_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 2: external_api_calls (External API Tracking)
-- Logs all outgoing calls to external services (Yahoo Finance)
-- ============================================================================
CREATE TABLE IF NOT EXISTS external_api_calls (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    audit_log_id BIGINT COMMENT 'Link to parent internal request',
    
    -- External service info
    service_name VARCHAR(100) NOT NULL COMMENT 'e.g., yahoo_finance',
    endpoint_url VARCHAR(255) NOT NULL COMMENT 'Full URL or endpoint',
    http_method VARCHAR(10) DEFAULT 'GET',
    
    -- Request/Response (truncated if large)
    request_payload JSON COMMENT 'What was sent',
    response_payload JSON COMMENT 'What was received (truncated if large)',
    response_status_code INT,
    is_response_truncated BOOLEAN DEFAULT FALSE,
    
    -- Performance
    execution_time_ms INT,
    
    -- Status
    status ENUM('SUCCESS', 'ERROR', 'TIMEOUT') NOT NULL DEFAULT 'SUCCESS',
    error_message TEXT,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    CONSTRAINT fk_audit_log FOREIGN KEY (audit_log_id) 
        REFERENCES api_audit_logs(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_service_name (service_name),
    INDEX idx_audit_log_id (audit_log_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 3: api_performance_metrics (Daily Aggregates)
-- Stores pre-aggregated performance metrics for dashboards
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    metric_date DATE NOT NULL,
    
    -- Counters
    total_requests INT DEFAULT 0,
    successful_requests INT DEFAULT 0,
    failed_requests INT DEFAULT 0,
    
    -- Response times (in milliseconds)
    avg_response_time_ms DECIMAL(10,2),
    min_response_time_ms INT,
    max_response_time_ms INT,
    p95_response_time_ms DECIMAL(10,2),
    p99_response_time_ms DECIMAL(10,2),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Unique constraint for daily aggregation
    UNIQUE KEY uk_endpoint_date (endpoint, metric_date),
    INDEX idx_metric_date (metric_date),
    INDEX idx_endpoint (endpoint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Scheduled Event: Cleanup old audit logs (30-day retention)
-- Note: Requires event_scheduler to be enabled in MySQL
-- Run: SET GLOBAL event_scheduler = ON;
-- ============================================================================
DELIMITER //

CREATE EVENT IF NOT EXISTS cleanup_old_audit_logs
ON SCHEDULE EVERY 1 DAY
STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 2 HOUR)
COMMENT 'Cleanup audit logs older than 30 days'
DO
BEGIN
    -- Delete external API calls first (foreign key constraint)
    DELETE FROM external_api_calls 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Delete main audit logs
    DELETE FROM api_audit_logs 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Delete old performance metrics
    DELETE FROM api_performance_metrics 
    WHERE metric_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY);
END //

DELIMITER ;

-- ============================================================================
-- Stored Procedure: Update daily performance metrics
-- Called after each API request to update aggregates
-- ============================================================================
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS update_performance_metrics(
    IN p_endpoint VARCHAR(100),
    IN p_execution_time_ms INT,
    IN p_is_success BOOLEAN
)
BEGIN
    INSERT INTO api_performance_metrics (endpoint, metric_date, total_requests, 
                                         successful_requests, failed_requests,
                                         avg_response_time_ms, min_response_time_ms, max_response_time_ms)
    VALUES (p_endpoint, CURDATE(), 1,
            IF(p_is_success, 1, 0),
            IF(p_is_success, 0, 1),
            p_execution_time_ms, p_execution_time_ms, p_execution_time_ms)
    ON DUPLICATE KEY UPDATE
        total_requests = total_requests + 1,
        successful_requests = successful_requests + IF(p_is_success, 1, 0),
        failed_requests = failed_requests + IF(p_is_success, 0, 1),
        avg_response_time_ms = ((avg_response_time_ms * (total_requests - 1)) + p_execution_time_ms) / total_requests,
        min_response_time_ms = LEAST(min_response_time_ms, p_execution_time_ms),
        max_response_time_ms = GREATEST(max_response_time_ms, p_execution_time_ms),
        updated_at = NOW();
END //

DELIMITER ;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Show created tables
SHOW TABLES;

-- Describe table structures
DESCRIBE api_audit_logs;
DESCRIBE external_api_calls;
DESCRIBE api_performance_metrics;

-- Check scheduled events
SHOW EVENTS;
