import pytest
import os
from unittest.mock import MagicMock, AsyncGenerator, patch
from unittest.mock import patch as autopatch

# Автоматическое мокамирование для ВСЕХ тестов
@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Мокает все зависимости для тестов."""
    
    monkeypatch.setattr("sqlalchemy.dialects.postgresql.psycopg2", MagicMock())

    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")

    mock_settings = MagicMock()
    mock_settings.max_file_size_mb = 100
    monkeypatch.setattr("config.settings", mock_settings)

    with autopatch("database.User") as mock_user, \
         autopatch("database.Download") as mock_download, \
         autopatch("database.get_db") as mock_get_db:
        
        # Мокаем get_db как async generator
        async def mock_db_generator():
            mock_session = MagicMock()
            yield mock_session
            mock_session.commit.return_value = None
            mock_session.rollback.return_value = None
        mock_get_db.return_value = AsyncGenerator(mock_db_generator())
        mock_user.id = 123
        
        yield {
            "mock_user": mock_user,
            "mock_session": mock_session,
            "mock_get_db": mock_get_db
        }

@pytest.fixture
def mock_message():
    """Mock сообщение."""
    from aiogram.types import Message
    mock = MagicMock(spec=Message)
    mock.text = "https://www.tiktok.com/@aliushkaa1/video/7593764380861385991"
    return mock
