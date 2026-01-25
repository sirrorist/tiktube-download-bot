import os
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Автоматически мокает settings для всех тестов."""
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    
    # Мокаем config.settings целиком
    with patch('config.settings') as mock_settings:
        mock_settings.max_file_size_mb = 100
        yield mock_settings

@pytest.fixture
def mock_db():
    """Мокает database."""
    with patch('database.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_session]
        yield mock_session
