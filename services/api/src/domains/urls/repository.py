from uuid import UUID

from db.database import get_session
from db.models.url import URL as URLModel
from sqlmodel import delete, select


class URLRepository:

    async def create_url(self, url: URLModel):
        async with get_session() as session:
            try:
                session.add(url)
                await session.commit()
                await session.refresh(url)
                return url
            except Exception as e:
                raise Exception(f"Error creating url: {str(e)}")

    async def get_url(self, id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(URLModel).where(URLModel.id == id)
                )
                return result.scalars().first()
            except Exception as e:
                raise Exception(f"Error getting url: {str(e)}")

    async def delete_url(self, url_id: UUID):
        async with get_session() as session:
            try:
                await session.execute(
                    delete(URLModel).where(URLModel.id == url_id)
                )
                await session.commit()
            except Exception as e:
                raise Exception(f"Error deleting url: {str(e)}")
