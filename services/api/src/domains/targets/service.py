from uuid import UUID

from models.target import Target

from .repository import TargetRepository


class TargetService:
    repository = TargetRepository()

    async def get_target_by_id(self, target_id: UUID):
        try:
            db_target, url = await self.repository.get_target_by_id(target_id)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            raise Exception(str(e))

    async def create_target(self, target: Target):
        try:
            db_target, url = await self.repository.create_target(target)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            raise Exception(str(e))

    async def get_all_targets(self):
        try:
            db_targets = await self.repository.get_all_targets()
            return [
                db_target.to_pydantic_model(url.get_url_string())
                for db_target, url in db_targets
            ]
        except Exception as e:
            raise Exception(str(e))

    async def update_target(self, target_id: UUID, target: Target):
        try:
            db_target, url = await self.repository.update_target(target_id, target)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            raise Exception(str(e))

    async def delete_target(self, target_id: UUID):
        try:
            db_target, url = await self.repository.delete_target(target_id)
            return db_target.to_pydantic_model(url.get_url_string())
        except Exception as e:
            raise Exception(str(e))
