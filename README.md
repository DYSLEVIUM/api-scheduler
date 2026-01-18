# API Scheduler

A distributed API scheduling system built with FastAPI, Temporal, and PostgreSQL.

## Quick Start

```bash
# Start all services
podman compose up --build

# Check monitoring health
./scripts/check-monitoring.sh
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **Web UI** | http://localhost:3001 | - |
| **Grafana** | http://localhost:3002 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Temporal UI** | http://localhost:8080 | - |
| **API Docs** | http://localhost:8000/docs | - |

## Monitoring & Logs

**Complete Observability Stack**: Logs, metrics, and system monitoring in one place.

### 📊 What's Monitored

#### Application & Service Metrics
- ✅ HTTP requests, latency, status codes
- ✅ Database connections, queries, performance
- ✅ All CRUD operations with timing
- ✅ Errors, warnings, and stack traces

#### System & Container Metrics
- ✅ CPU usage per container and host
- ✅ Memory usage and limits
- ✅ Network I/O (RX/TX bytes/sec)
- ✅ Disk I/O (read/write bytes/sec)
- ✅ Filesystem usage

#### Logs
- ✅ Structured application logs
- ✅ Database query logs
- ✅ HTTP request/response logs
- ✅ Container logs

### 📚 Documentation
- **[QUICK_LOGGING_REFERENCE.md](./QUICK_LOGGING_REFERENCE.md)** - Log queries quick reference ⚡
- **[SYSTEM_METRICS_ADDED.md](./SYSTEM_METRICS_ADDED.md)** - System metrics guide ⚡
- **[COMPREHENSIVE_LOGGING.md](./COMPREHENSIVE_LOGGING.md)** - Complete logging guide
- **[MONITORING_LOGS.md](./MONITORING_LOGS.md)** - Monitoring architecture

### 🎯 Quick Access
```bash
# View dashboards in Grafana
open http://localhost:3000

# Check monitoring health
./scripts/check-monitoring.sh

# Test logging
./test-comprehensive-logging.sh
```

### 📈 Grafana Dashboards
- **API Overview**: Application metrics (requests, latency)
- **PostgreSQL**: Database performance
- **System Metrics**: CPU, memory, I/O for all services ⭐ NEW
- **Logs**: Real-time structured logs

## Development

### Database Migrations

```bash
# Check current version
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic current

# Create migration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic revision --autogenerate -m "Description"

# Apply migrations
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic upgrade head

# Rollback one migration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic downgrade -1

# View history
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic history
```

### Running Tests

```bash
cd services/api
uv run pytest
```

## Architecture

- **API**: FastAPI application
- **Worker**: Temporal workflow engine
- **Database**: PostgreSQL (app + temporal)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Loki + Promtail
- **Frontend**: React + Vite

## Troubleshooting

```bash
# View all service status
podman compose ps

# Restart specific service
podman compose restart api

# View logs
podman compose logs -f api

# Rebuild and restart
podman compose up --build -d

# Check monitoring stack
./scripts/check-monitoring.sh
```