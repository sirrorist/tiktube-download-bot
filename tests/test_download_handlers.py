import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from aiogram.types import Message
# from sqlalchemy import update

import sys
with patch('sqlalchemy.dialects.postgresql.psycopg2') as mock_psycopg2:
    sys.modules['sqlalchemy.dialects.postgresql.psycopg2'] = mock_psycopg2

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.download import (
    URL_PATTERNS 
    # handle_url, 
    # download_menu
)
# from downloaders import detect_platform
from database import User

@pytest.fixture(autouse=True)
def mock_database():
    """Автоматически мокать database при запуске тестов."""
    with patch('database.engine', new=Mock()):
        with patch('database.get_db', new=lambda: Mock()):
            yield

@pytest.fixture
def mock_message():
    """Фикстура для mock-сообщения."""
    mock = AsyncMock(spec=Message)
    mock.text = "https://www.tiktok.com/@aliushkaa1/video/7593764380861385991"
    return mock

@pytest.fixture
def mock_user():
    """Фикстура для mock-пользователя."""
    user = MagicMock(spec=User)
    user.id = 123
    user.downloads_today = 0
    user.total_downloads = 10
    return user

@pytest.mark.asyncio
async def test_url_patterns():
    """Тест паттернов URL."""
    tiktok_url = "https://vt.tiktok.com/ZSaD796vL/"
    youtube_url = "https://youtu.be/dQw4w9WgXcQ"
    
    assert re.search(URL_PATTERNS["tiktok"], tiktok_url, re.IGNORECASE)
    assert re.search(URL_PATTERNS["youtube"], youtube_url, re.IGNORECASE)
