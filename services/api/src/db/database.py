import contextlib
import logging
import time

from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from core.config import settings
from core.logging import get_logger
from db.models.job import Job
from db.models.schedule import Schedule
from db.models.target import Target
from db.models.url import URL

logger = get_logger()

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

engine = create_async_engine(
    url=settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.debug("db_connection_opened", pool_size=engine.pool.size(), checked_out=engine.pool.checkedout())

@event.listens_for(engine.sync_engine, "close")
def receive_close(dbapi_conn, connection_record):
    logger.debug("db_connection_closed", pool_size=engine.pool.size(), checked_out=engine.pool.checkedout())

@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    logger.debug("db_connection_checkout", checked_out=engine.pool.checkedout(), overflow=engine.pool.overflow())

@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    logger.debug("db_connection_checkin", checked_out=engine.pool.checkedout())


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info["query_start_time"].pop()
    logger.info(
        "sql_query_executed",
        query=statement[:200] if len(statement) > 200 else statement,
        duration_ms=round(total_time * 1000, 2),
        executemany=executemany,
    )


@contextlib.asynccontextmanager
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    logger.debug("session_creating", pool_checked_out=engine.pool.checkedout())
    async with async_session() as session:
        try:
            logger.debug("session_created", session_id=id(session))
            yield session
        except Exception as e:
            logger.error(
                "database_session_error",
                session_id=id(session),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            await session.rollback()
            raise
        finally:
            logger.debug("session_closing", session_id=id(session), pool_checked_out=engine.pool.checkedout())
            await session.close()
            logger.debug("session_closed", pool_checked_out=engine.pool.checkedout())


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
