# Docker Compose Setup Guide

This setup includes:
- **PostgreSQL** (for Temporal and Application databases)
- **Temporal** (workflow orchestration)
- **Temporal UI** (web interface)
- **Fluentd** (log aggregation)
- **Prometheus** (metrics collection)
- **Grafana** (metrics visualization)
- **API Application** (FastAPI service)

## Prerequisites

- Podman (or Docker) installed
- Podman Compose (or Docker Compose) installed

## Quick Start

### Using Podman Compose

```bash
# Start all services
podman-compose up -d

# Or with newer Podman versions
podman compose up -d

# View logs
podman-compose logs -f

# Stop all services
podman-compose down

# Stop and remove volumes
podman-compose down -v
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Service Endpoints

Once all services are running, you can access:

- **API Application**: http://localhost:8000
- **Temporal UI**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **PostgreSQL (Temporal)**: localhost:5432
- **PostgreSQL (Application)**: localhost:5433

## Environment Variables

The API service uses the following environment variables (configured in docker-compose.yml):

- `DATABASE_URL`: PostgreSQL connection string for the application
- `TEMPORAL_HOST`: Temporal server address
- `TEMPORAL_NAMESPACE`: Temporal namespace (default: "default")
- `TEMPORAL_TASK_QUEUE`: Temporal task queue name
- `FLUENTD_HOST`: Fluentd server address
- `FLUENTD_PORT`: Fluentd port (default: 24224)
- `ENABLE_FLUENTD`: Enable/disable Fluentd logging
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Database Credentials

### Temporal Database
- User: `temporal`
- Password: `temporal`
- Database: `temporal`
- Port: `5432`

### Application Database
- User: `api_scheduler`
- Password: `api_scheduler`
- Database: `api_scheduler`
- Port: `5433` (host), `5432` (container)

## Monitoring

### Prometheus
- Scrapes metrics from the API application at `/health/metrics`
- Scrapes Temporal metrics
- Access at http://localhost:9090

### Grafana
- Pre-configured with Prometheus as data source
- Default credentials: `admin` / `admin`
- Access at http://localhost:3000

## Logging

Fluentd is configured to:
- Receive logs via forward protocol on port 24224
- Output logs to stdout (can be extended to write to files or other destinations)

## Troubleshooting

### Check service status
```bash
podman-compose ps
```

### View logs for a specific service
```bash
podman-compose logs api
podman-compose logs temporal
```

### Restart a specific service
```bash
podman-compose restart api
```

### Rebuild services after code changes
```bash
podman-compose build api
podman-compose up -d api
```

## Notes

- All services are connected via a Docker bridge network (`api-scheduler-network`)
- Data persistence is handled via named volumes
- Health checks are configured for critical services to ensure proper startup order
- The setup is optimized for development; adjust for production use
