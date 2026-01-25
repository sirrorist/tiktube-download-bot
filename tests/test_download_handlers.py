import pytest
from unittest.mock import patch, AsyncMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.download import URL_PATTERNS, download_menu

@pytest.mark.asyncio
async def test_url_patterns():
    """Тест паттернов URL."""
    assert "tiktok" in URL_PATTERNS
    assert URL_PATTERNS["tiktok"]

@pytest.mark.asyncio
async def test_download_menu_message(mock_message):
    """Тест меню для Message."""
    await download_menu(mock_message)
    mock_message.answer.assert_called_once()
