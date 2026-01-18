-- ============================================================================
-- API Scheduler Database Schema
-- ============================================================================
-- This file contains the complete database schema including:
-- - Enum types for HTTP methods and job statuses
-- - Tables for URLs, targets, schedules, jobs, and attempts
-- - Indexes for query optimization
-- - CASCADE constraints for automatic cleanup
-- ============================================================================

-- ============================================================================
-- 1. ENUM TYPES
-- ============================================================================

-- HTTP Methods
DO $$ BEGIN
    CREATE TYPE httpmethods AS ENUM (
        'GET',
        'POST',
        'PUT',
        'DELETE',
        'PATCH',
        'OPTIONS',
        'HEAD'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Job Status Types
DO $$ BEGIN
    CREATE TYPE jobstatus AS ENUM (
        'success',
        'timeout',
        'dns_error',
        'connection_error',
        'http_4xx',
        'http_5xx',
        'error'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 2. TABLES
-- ============================================================================

-- URLs Table
-- Stores parsed URL components for targets
CREATE TABLE IF NOT EXISTS urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme VARCHAR NOT NULL DEFAULT 'https',
    netloc VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    params VARCHAR,
    query VARCHAR,
    fragment VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_urls_netloc ON urls(netloc);

-- Targets Table
-- Stores HTTP request configurations
-- CASCADE: When URL deleted, target is deleted
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    url_id UUID NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    method httpmethods NOT NULL,
    headers JSONB,
    body JSONB,
    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    retry_count INTEGER NOT NULL DEFAULT 0,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 1,
    follow_redirects BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_targets_name ON targets(name);

-- Interval Schedules Table
-- Schedules that run at fixed intervals
-- CASCADE: When target deleted, interval schedules are deleted
CREATE TABLE IF NOT EXISTS interval_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    interval_seconds INTEGER NOT NULL,
    target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    paused BOOLEAN NOT NULL DEFAULT FALSE,
    temporal_workflow_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interval_schedules_target_id ON interval_schedules(target_id);

-- Window Schedules Table
-- Schedules that run for a specific duration
-- CASCADE: When target deleted, window schedules are deleted
CREATE TABLE IF NOT EXISTS window_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    interval_seconds INTEGER NOT NULL,
    target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    duration_seconds INTEGER NOT NULL,
    paused BOOLEAN NOT NULL DEFAULT FALSE,
    temporal_workflow_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_window_schedules_target_id ON window_schedules(target_id);

-- Jobs Table
-- Records of HTTP request executions
-- Note: schedule_id references either interval_schedules OR window_schedules
-- Deletion is handled at application level
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL,
    run_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    status jobstatus NOT NULL,
    status_code INTEGER,
    latency_ms DOUBLE PRECISION,
    response_size_bytes INTEGER,
    request_headers JSONB,
    request_body JSONB,
    response_headers JSONB,
    response_body JSONB,
    error_message VARCHAR,
    redirected BOOLEAN NOT NULL DEFAULT FALSE,
    redirect_count INTEGER NOT NULL DEFAULT 0,
    redirect_history JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_schedule_id ON jobs(schedule_id);

-- Attempts Table
-- Records of retry attempts for jobs
-- CASCADE: When job deleted, attempts are deleted
CREATE TABLE IF NOT EXISTS attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    status jobstatus NOT NULL,
    status_code INTEGER,
    latency_ms DOUBLE PRECISION,
    response_size_bytes INTEGER,
    response_headers JSONB,
    response_body JSONB,
    error_message VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attempts_job_id ON attempts(job_id);

-- ============================================================================
-- CASCADE DELETION HIERARCHY
-- ============================================================================
-- URL (deleted) → Target (CASCADE)
--                   ↓
--                 Schedules (CASCADE)
--                   ↓
--                 Jobs (application-level)
--                   ↓
--                 Attempts (CASCADE)
-- ============================================================================
