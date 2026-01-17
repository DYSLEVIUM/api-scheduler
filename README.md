```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic init src/db/migrations

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic downgrade base

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic revision --autogenerate -m "Initial migration"

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic stamp base
```

# Check current migration version
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic current

# Create a new migration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic revision --autogenerate -m "Description"

# Apply migrations
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic upgrade head

# Rollback one migration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic downgrade -1

# View migration history
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic history

# Upgrade
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic upgrade head

# Downgrade
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/api_scheduler uv run alembic downgrade base