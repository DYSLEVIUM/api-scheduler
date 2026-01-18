import asyncio
from uuid import UUID

from core.logging import get_logger
from db.database import get_session
from db.models.target import Target as TargetModel
from db.models.url import URL as URLModel
from domains.schedules.repository import ScheduleRepository
from models.target import Target as TargetPydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

logger = get_logger()


class TargetRepository:
    schedule_repository = ScheduleRepository()

    async def get_target_by_id(self, target_id: UUID):
        logger.info("get_target_by_id_started", target_id=str(target_id))
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()
                if not row:
                    logger.warning("target_not_found",
                                   target_id=str(target_id))
                    raise Exception(f"Target with id {target_id} not found")
                logger.info("get_target_by_id_success",
                            target_id=str(target_id))
                return row
            except SQLAlchemyError as e:
                logger.error(
                    "get_target_by_id_db_error",
                    target_id=str(target_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error(
                        "get_target_by_id_error",
                        target_id=str(target_id),
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                raise

    async def create_target(self, target: TargetPydantic):
        logger.info("create_target_started",
                    url=target.url, method=target.method)
        async with get_session() as session:
            try:
                parsed_url = target.get_url_parse_result()
                db_url = URLModel(**parsed_url._asdict())
                logger.debug("creating_url", scheme=db_url.scheme,
                             netloc=db_url.netloc, path=db_url.path)
                session.add(db_url)
                await session.flush()
                logger.debug("url_created", url_id=str(db_url.id))

                db_target = target.to_db_model()
                db_target.url_id = db_url.id

                if db_target.headers is None:
                    logger.warning("target_headers_none",
                                   setting_empty_dict=True)
                    db_target.headers = {}

                session.add(db_target)
                await session.commit()
                await session.refresh(db_target)
                await session.refresh(db_url)

                logger.info("create_target_success", target_id=str(
                    db_target.id), url_id=str(db_url.id))
                return db_target, db_url
            except SQLAlchemyError as e:
                logger.error(
                    "create_target_db_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error(
                    "create_target_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(str(e))

    async def get_all_targets(self) -> list:
        logger.info("get_all_targets_started")
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel).join(
                        URLModel, TargetModel.url_id == URLModel.id
                    )
                )
                targets = result.all()
                logger.info("get_all_targets_success", count=len(targets))
                return targets
            except SQLAlchemyError as e:
                logger.error(
                    "get_all_targets_db_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error(
                    "get_all_targets_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(str(e))

    async def update_target(self, target_id: UUID, target: TargetPydantic):
        logger.info("update_target_started",
                    target_id=str(target_id), url=target.url)
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()
                if not row:
                    logger.warning("update_target_not_found",
                                   target_id=str(target_id))
                    raise Exception(f"Target with id {target_id} not found")

                existing_target, existing_url = row

                parsed_url = target.get_url_parse_result()
                db_url = URLModel(**parsed_url._asdict())
                session.add(db_url)
                await session.flush()
                logger.debug("update_target_new_url_created",
                             url_id=str(db_url.id))

                db_target = target.to_db_model()
                for key, value in db_target.model_dump(exclude={"id", "url_id", "created_at", "updated_at"}).items():
                    setattr(existing_target, key, value)

                existing_target.url_id = db_url.id

                session.add(existing_target)
                await session.commit()
                await session.refresh(existing_target)
                await session.refresh(db_url)

                logger.info("update_target_success", target_id=str(target_id))
                return existing_target, db_url
            except SQLAlchemyError as e:
                logger.error(
                    "update_target_db_error",
                    target_id=str(target_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error(
                        "update_target_error",
                        target_id=str(target_id),
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                raise

    async def delete_target(self, target_id: UUID):
        logger.info("delete_target_started", target_id=str(target_id))
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()

                if not row:
                    logger.warning("delete_target_not_found",
                                   target_id=str(target_id))
                    raise Exception(f"Target with id {target_id} not found")

                target, url = row

                await self.schedule_repository.delete_schedules_by_target_id(target_id)

                logger.debug("deleting_target_record",
                             target_id=str(target_id))
                await session.delete(target)
                await session.commit()

                logger.info("delete_target_success", target_id=str(target_id))
                return target, url
            except SQLAlchemyError as e:
                logger.error(
                    "delete_target_db_error",
                    target_id=str(target_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error(
                        "delete_target_error",
                        target_id=str(target_id),
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                raise
