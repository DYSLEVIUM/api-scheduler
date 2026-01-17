import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import db.database
from main import create_app


def setup_test_env():
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("DEV", "1")
    os.environ.setdefault("DEBUG", "0")


setup_test_env()

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
def override_database(monkeypatch):
    test_database_url = "sqlite+aiosqlite:///:memory:"
    test_engine = create_async_engine(
        test_database_url, echo=False, pool_pre_ping=False)

    monkeypatch.setattr(db.database, "engine", test_engine)

    async def create_test_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(create_test_tables())

    yield

    async def cleanup():
        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
        except Exception:
            pass
        finally:
            await test_engine.dispose()
            await asyncio.sleep(0)

    asyncio.run(cleanup())


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def target_data():
    return {
        "name": "Test Target",
        "url": "https://api.example.com/v1/test",
        "method": "GET",
        "headers": {},
        "body": None,
    }


@pytest.fixture
def target_id(client, target_data):
    response = client.post("/targets", json=target_data)
    return response.json()["data"]["id"]


@pytest.fixture
def schedule_data(target_id):
    return {
        "target_id": target_id,
        "interval_seconds": 60,
    }


@pytest.fixture
def schedule_id(client, schedule_data):
    response = client.post("/schedules", json=schedule_data)
    return response.json()["data"]["id"]
