import os


def setup_test_env():
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("DEV", "1")
    os.environ.setdefault("DEBUG", "0")
