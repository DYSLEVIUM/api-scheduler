import pytest
from uuid import uuid4
from urllib.parse import urlparse

from domains.targets.repository import TargetRepository
from enums.http_methods import HTTPMethods
from models.target import Target as TargetPydantic
from tests.helpers.db_helpers import (
    create_test_target,
    create_test_url,
)
from tests.helpers.mocks import mock_session


@pytest.mark.asyncio
async def test_create_target(test_db):
    with mock_session(
        test_db, "domains.targets.repository", "domains.urls.repository"
    ):
        repo = TargetRepository()
        url_model = await create_test_url(test_db)

        target = TargetPydantic(
            name="Test Target",
            url=urlparse("https://api.example.com/v1/test"),
            method="GET",
            headers={"Authorization": "Bearer token"},
            body=None,
        )

        db_target, url = await repo.create_target(target)
        assert db_target.name == "Test Target"
        assert db_target.method.value == "GET"


@pytest.mark.asyncio
async def test_get_target_by_id(test_db):
    with mock_session(test_db, "domains.targets.repository"):
        repo = TargetRepository()
        url_model = await create_test_url(test_db)
        target_model = await create_test_target(
            test_db,
            url_model.id,
            headers={"Authorization": "Bearer token"},
        )

        db_target, url = await repo.get_target_by_id(target_model.id)
        assert db_target.id == target_model.id
        assert db_target.name == "Test Target"


@pytest.mark.asyncio
async def test_get_target_by_id_not_found(test_db):
    with mock_session(test_db, "domains.targets.repository"):
        repo = TargetRepository()
        fake_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await repo.get_target_by_id(fake_id)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_all_targets(test_db):
    with mock_session(test_db, "domains.targets.repository"):
        repo = TargetRepository()
        url_model = await create_test_url(test_db)
        await create_test_target(test_db, url_model.id, name="Target 1")
        await create_test_target(
            test_db, url_model.id, name="Target 2", method=HTTPMethods.POST
        )

        targets = await repo.get_all_targets()
        assert len(targets) == 2
