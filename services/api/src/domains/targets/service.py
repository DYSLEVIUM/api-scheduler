from uuid import UUID

from core.logging import get_logger
from models.target import Target

from .repository import TargetRepository

logger = get_logger()


class TargetService:
    repository = TargetRepository()

    async def get_target_by_id(self, target_id: UUID):
        logger.debug("service_get_target_by_id", target_id=str(target_id))
        try:
            db_target, url = await self.repository.get_target_by_id(target_id)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            logger.error("service_get_target_by_id_error", target_id=str(target_id), error=str(e))
            raise Exception(str(e))

    async def create_target(self, target: Target):
        logger.info("service_create_target", url=target.url, method=target.method)
        try:
            db_target, url = await self.repository.create_target(target)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            logger.error("service_create_target_error", error=str(e))
            raise Exception(str(e))

    async def get_all_targets(self):
        logger.debug("service_get_all_targets")
        try:
            db_targets = await self.repository.get_all_targets()
            return [
                db_target.to_pydantic_model(url.get_url_string())
                for db_target, url in db_targets
            ]
        except Exception as e:
            logger.error("service_get_all_targets_error", error=str(e))
            raise Exception(str(e))

    async def update_target(self, target_id: UUID, target: Target):
        logger.info("service_update_target", target_id=str(target_id), url=target.url)
        try:
            db_target, url = await self.repository.update_target(target_id, target)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            logger.error("service_update_target_error", target_id=str(target_id), error=str(e))
            raise Exception(str(e))

    async def delete_target(self, target_id: UUID):
        logger.info("service_delete_target", target_id=str(target_id))
        try:
            db_target, url = await self.repository.delete_target(target_id)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            logger.error("service_delete_target_error", target_id=str(target_id), error=str(e))
            raise Exception(str(e))
