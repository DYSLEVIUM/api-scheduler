import asyncio
from core.logging import get_logger

logger = get_logger()


async def monitor_db_pool(engine, interval_seconds: int = 60):
    logger.info("db_pool_monitor_started", interval_seconds=interval_seconds)
    
    while True:
        try:
            pool = engine.pool
            
            pool_status = {
                "size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "max_overflow": pool._max_overflow,
                "pool_size": pool._pool.maxsize if hasattr(pool._pool, 'maxsize') else pool._pool_size,
            }
            
            logger.info(
                "db_pool_status",
                **pool_status
            )
            
            if pool.checkedout() >= pool.size() * 0.8:
                logger.warning(
                    "db_pool_high_utilization",
                    checked_out=pool.checkedout(),
                    pool_size=pool.size(),
                    utilization_percent=round((pool.checkedout() / pool.size()) * 100, 2)
                )
            
        except Exception as e:
            logger.error(
                "db_pool_monitor_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
        
        await asyncio.sleep(interval_seconds)


def get_pool_stats(engine) -> dict:
    try:
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool._max_overflow,
            "pool_size": pool._pool.maxsize if hasattr(pool._pool, 'maxsize') else pool._pool_size,
            "utilization_percent": round((pool.checkedout() / pool.size()) * 100, 2) if pool.size() > 0 else 0
        }
    except Exception as e:
        logger.error("get_pool_stats_error", error=str(e), error_type=type(e).__name__)
        return {"error": str(e)}
