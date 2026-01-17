from contextlib import contextmanager
from unittest.mock import patch

from sqlalchemy.ext.asyncio import AsyncSession


@contextmanager
def mock_session(session: AsyncSession, *module_paths: str):
    patches = [
        patch(f"{path}.get_session") for path in module_paths
    ]
    for mock_patch in patches:
        mock = mock_patch.__enter__()
        mock.return_value.__aenter__.return_value = session
        mock.return_value.__aexit__.return_value = None
    try:
        yield
    finally:
        for mock_patch in patches:
            mock_patch.__exit__(None, None, None)
