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

CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    url_id UUID NOT NULL REFERENCES urls(id),
    method httpmethods NOT NULL,
    headers JSONB,
    body JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_targets_name ON targets(name);

CREATE TABLE IF NOT EXISTS interval_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interval_seconds INTEGER NOT NULL,
    target_id UUID NOT NULL REFERENCES targets(id),
    paused BOOLEAN NOT NULL DEFAULT FALSE,
    temporal_workflow_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interval_schedules_target_id ON interval_schedules(target_id);

CREATE TABLE IF NOT EXISTS window_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interval_seconds INTEGER NOT NULL,
    target_id UUID NOT NULL REFERENCES targets(id),
    duration_seconds INTEGER NOT NULL,
    paused BOOLEAN NOT NULL DEFAULT FALSE,
    temporal_workflow_id VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_window_schedules_target_id ON window_schedules(target_id);

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
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_schedule_id ON jobs(schedule_id);
