import logging
from uuid import UUID

from db.database import get_session
from db.models.target import Target as TargetModel
from db.models.url import URL as URLModel
from domains.schedules.repository import ScheduleRepository
from domains.urls.repository import URLRepository
from models.target import Target as TargetPydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

logger = logging.getLogger(__name__)


class TargetRepository:
    url_repository = URLRepository()
    schedule_repository = ScheduleRepository()

    async def get_target_by_id(self, target_id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()
                if not row:
                    raise Exception(f"Target with id {target_id} not found")
                return row
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    raise
                raise Exception(str(e))

    async def create_target(self, target: TargetPydantic):
        async with get_session() as session:
            try:
                parsed_url = target.get_url_parse_result()
                db_url = URLModel(**parsed_url._asdict())
                logger.debug(f"Creating URL: {db_url.model_dump()}")
                session.add(db_url)
                await session.flush()
                logger.debug(f"URL flushed with id: {db_url.id}")

                db_target = target.to_db_model()
                db_target.url_id = db_url.id
                logger.debug(
                    f"Creating target: {db_target.model_dump(exclude={'id', 'created_at', 'updated_at'})}")

                if db_target.headers is None:
                    logger.warning("headers is None, setting to empty dict")
                    db_target.headers = {}

                session.add(db_target)
                await session.commit()
                logger.debug("Target committed successfully")
                await session.refresh(db_target)
                await session.refresh(db_url)

                return db_target, db_url
            except SQLAlchemyError as e:
                logger.error(
                    f"SQLAlchemy error in create_target: {type(e).__name__}: {str(e)}", exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error(
                    f"Error in create_target: {type(e).__name__}: {str(e)}", exc_info=True)
                raise Exception(str(e))

    async def get_all_targets(self) -> list:
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel).join(
                        URLModel, TargetModel.url_id == URLModel.id
                    )
                )
                return result.all()
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    async def update_target(self, target_id: UUID, target: TargetPydantic):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()
                if not row:
                    raise Exception(f"Target with id {target_id} not found")

                existing_target, existing_url = row
                old_url_id = existing_target.url_id

                parsed_url = target.get_url_parse_result()
                db_url = URLModel(**parsed_url._asdict())
                session.add(db_url)
                await session.flush()

                db_target = target.to_db_model()
                for key, value in db_target.model_dump(exclude={"id", "url_id", "created_at", "updated_at"}).items():
                    setattr(existing_target, key, value)

                existing_target.url_id = db_url.id

                session.add(existing_target)
                await session.commit()
                await session.refresh(existing_target)
                await session.refresh(db_url)

                if old_url_id:
                    old_url = await session.get(URLModel, old_url_id)
                    if old_url:
                        await session.delete(old_url)
                        await session.commit()

                return existing_target, db_url
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    raise
                raise Exception(str(e))

    async def delete_target(self, target_id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(TargetModel, URLModel)
                    .where(TargetModel.id == target_id)
                    .join(URLModel, TargetModel.url_id == URLModel.id)
                )
                row = result.first()
                if not row:
                    raise Exception(f"Target with id {target_id} not found")

                target, url = row
                url_id = target.url_id

                await self.schedule_repository.delete_schedules_by_target_id(target_id)

                await session.delete(target)
                await session.commit()

                if url_id:
                    await self.url_repository.delete_url(url_id)

                return target, url
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    raise
                raise Exception(str(e))
