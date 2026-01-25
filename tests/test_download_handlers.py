import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

# Настройка pytest для импорта
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.download import (
    URL_PATTERNS, 
    handle_url, 
    download_menu
)
from downloaders import detect_platform
from database import User, Download
from config.settings import settings


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


@pytest.mark.asyncio
async def test_download_menu_message():
    """Тест меню для Message."""
    mock_message = AsyncMock(spec=Message)
    
    await download_menu(mock_message)
    
    mock_message.answer.assert_called_once()
    assert "📥 <b>Скачать контент</b>" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_download_menu_callback():
    """Тест меню для CallbackQuery."""
    mock_query = AsyncMock()
    mock_query.message = AsyncMock()
    
    await download_menu(mock_query)
    
    mock_query.message.edit_text.assert_called_once()
    mock_query.answer.assert_called_once()


@pytest.mark.asyncio
@patch('handlers.download.get_db')
@patch('downloaders.download_tiktok')
@patch('downloaders.detect_platform')
async def test_handle_url_tiktok_success(
    mock_detect, mock_tiktok, mock_get_db, mock_message, mock_user
):
    """Тест успешного скачивания TikTok."""
    # Моки
    mock_detect.return_value = "tiktok"
    mock_tiktok.return_value = {
        "success": True,
        "file_path": "/tmp/test.mp4",
        "content_type": "video",
        "file_size": 1024 * 1024  # 1MB
    }
    
    mock_session = AsyncMock(spec=AsyncSession)
    mock_get_db.return_value.__aiter__ = AsyncMock(return_value=[mock_session])
    
    # Тест
    await handle_url(mock_message, user=mock_user)
    
    # Проверки
    mock_detect.assert_called_once()
    mock_tiktok.assert_called_once()
    mock_message.answer_video.assert_called_once()
    mock_session.execute.assert_called()


@pytest.mark.asyncio
@patch('downloaders.detect_platform')
async def test_handle_url_not_url(mock_detect, mock_message, mock_user):
    """Тест обработки не-URL."""
    mock_message.text = "привет"
    
    await handle_url(mock_message, user=mock_user)
    
    mock_message.answer.assert_not_called()
    mock_detect.assert_not_called()


@pytest.mark.asyncio
@patch('downloaders.download_tiktok')
@patch('downloaders.detect_platform')
async def test_handle_url_download_error(
    mock_detect, mock_tiktok, mock_message, mock_user
):
    """Тест ошибки скачивания."""
    mock_detect.return_value = "tiktok"
    mock_tiktok.return_value = {"success": False, "error": "Video not found"}
    
    processing_msg = AsyncMock()
    mock_message.answer.return_value = processing_msg
    
    await handle_url(mock_message, user=mock_user)
    
    processing_msg.edit_text.assert_called_once()
    assert "Video not found" in processing_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
@patch('downloaders.download_tiktok')
@patch('downloaders.detect_platform')
async def test_handle_url_file_too_big(
    mock_detect, mock_tiktok, mock_message, mock_user
):
    """Тест слишком большого файла."""
    mock_detect.return_value = "tiktok"
    mock_tiktok.return_value = {
        "success": True,
        "file_path": "/tmp/huge.mp4",
        "content_type": "video",
        "file_size": 30 * 1024 * 1024  # 30MB
    }
    
    processing_msg = AsyncMock()
    mock_message.answer.return_value = processing_msg
    
    # Патчим settings.max_file_size_mb
    with patch('handlers.download.settings.max_file_size_mb', 20):
        await handle_url(mock_message, user=mock_user)
    
    assert "Файл слишком большой" in processing_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
@patch('downloaders.detect_platform')
async def test_handle_url_unknown_platform(mock_detect, mock_message, mock_user):
    """Тест неизвестной платформы."""
    mock_message.text = "https://example.com"
    mock_detect.return_value = None
    
    await handle_url(mock_message, user=mock_user)
    
    mock_message.answer.assert_called_once_with(
        "❌ Не удалось определить платформу. Проверьте ссылку."
    )
