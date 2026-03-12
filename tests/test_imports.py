"""Test imports to verify structure."""

from downloaders import (
    download_tiktok,
    download_youtube,
    download_instagram,
    download_twitter,
    detect_platform
)
# Тест 1: Базовые импорты
print("Testing basic imports...")
print("✅ Basic downloaders imported")

# Тест 2: Utils импорты
print("\nTesting utils imports...")
from utils.po_token_cache import POTokenCache
print("✅ POTokenCache imported")

# Тест 3: PO Token manager (внутренний)
print("\nTesting internal imports...")
from downloaders.po_token_manager import POTokenGenerator
print("✅ POTokenGenerator imported")

# Тест 4: Detect platform
print("\nTesting detect_platform...")
test_urls = {
    "https://youtu.be/dQw4w9WgXcQ": "youtube",
    "https://tiktok.com/@user/video/123": "tiktok",
    "https://instagram.com/p/ABC123/": "instagram",
}

for url, expected in test_urls.items():
    detected = detect_platform(url)
    assert detected == expected, f"Failed for {url}: got {detected}, expected {expected}"
    print(f"  ✅ {url} → {detected}")

print("\n🎉 All imports working correctly!")
