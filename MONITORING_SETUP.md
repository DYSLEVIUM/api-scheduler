# Monitoring Setup Guide

## Grafana Credentials

- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `admin`

> **Note**: On first login, Grafana will prompt you to change the password. You can skip this or change it as needed.

## Prometheus

- **URL**: http://localhost:9090
- **No authentication required** (development setup)

## Fluentd UI

- **URL**: http://localhost:8081
- **No authentication required**

## Temporal UI

- **URL**: http://localhost:8080
- **No authentication required**
- **Note**: Temporal UI provides a web interface to view workflows, activities, and Temporal server status

## Available Dashboards

After logging into Grafana, you'll find the following pre-configured dashboards:

### 1. System Overview
- Service health status for all components
- Overall system metrics
- Quick status indicators

### 2. API Scheduler Overview
- Active schedules and jobs
- HTTP request metrics (rate, duration, status codes)
- Schedule execution metrics
- Job duration metrics
- Request/response size tracking

### 3. Temporal Metrics
- Workflow execution metrics
- Active workflows
- Workflow failures
- Activity execution metrics
- Temporal server health

### 4. Fluentd Metrics
- Fluentd status
- Log processing rate
- Buffer queue length
- Buffer total bytes
- Output errors and retries

### 5. PostgreSQL Metrics
- Database connection status (Temporal DB & App DB)
- Active connections
- Database size
- Transaction metrics (commits, rollbacks)
- Tuple operations (inserts, updates, deletes)
- Cache hit ratio
- Deadlocks
- Database size over time

## Accessing Dashboards

1. Open Grafana: http://localhost:3000
2. Login with credentials above
3. Navigate to **Dashboards** in the left sidebar
4. Click **Browse** to see all available dashboards
5. Select any dashboard to view metrics

## Prometheus Targets

Prometheus is configured to scrape metrics from:

- **API Scheduler**: `api:8000/health/metrics` (every 10s)
- **Temporal**: `temporal:7233/metrics` (every 15s)
- **Fluentd**: `fluentd:24231/metrics` (every 15s)
- **PostgreSQL Temporal**: `postgres-exporter-temporal:9187` (every 15s)
- **PostgreSQL App**: `postgres-exporter-app:9187` (every 15s)
- **Prometheus**: `localhost:9090` (self-monitoring)

View targets status at: http://localhost:9090/targets

## Quick Start

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Access Grafana**: http://localhost:3000
   - Login: `admin` / `admin`

3. **View Prometheus**: http://localhost:9090

4. **View Fluentd Logs**: http://localhost:8081

## Metrics Endpoints

### API Scheduler Metrics
Available at: `http://api:8000/health/metrics`

Key metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `active_schedules_total` - Number of active schedules
- `active_jobs_total` - Number of active jobs
- `schedule_executions_total` - Schedule execution counter
- `job_duration_seconds` - Job execution duration histogram

### Temporal Metrics
Available at: `http://temporal:7233/metrics`

### Fluentd Metrics
Available at: `http://fluentd:24231/metrics`

### PostgreSQL Metrics
Available at:
- **Temporal DB**: `http://postgres-exporter-temporal:9187/metrics`
- **App DB**: `http://postgres-exporter-app:9187/metrics`

Key metrics:
- `pg_stat_database_numbackends` - Number of active connections
- `pg_database_size_bytes` - Database size
- `pg_stat_database_xact_commit` - Transaction commits
- `pg_stat_database_xact_rollback` - Transaction rollbacks
- `pg_stat_database_tup_inserted` - Tuples inserted
- `pg_stat_database_tup_updated` - Tuples updated
- `pg_stat_database_tup_deleted` - Tuples deleted
- `pg_stat_database_blks_hit` - Cache hits
- `pg_stat_database_blks_read` - Disk reads
- `pg_stat_database_deadlocks` - Deadlock count

## Troubleshooting

### Dashboards not showing up?
1. Check that dashboards are in `grafana/dashboards/` directory
2. Restart Grafana: `docker-compose restart grafana`
3. Check Grafana logs: `docker-compose logs grafana`

### Prometheus not scraping?
1. Check targets: http://localhost:9090/targets
2. Verify services are running: `docker-compose ps`
3. Check Prometheus config: `prometheus/prometheus.yml`

### Can't access Grafana?
1. Verify Grafana is running: `docker-compose ps grafana`
2. Check port 3000 is not in use
3. View logs: `docker-compose logs grafana`
