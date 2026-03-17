#!/usr/bin/env python3
"""Test imports to verify structure."""

from downloaders import (
    download_tiktok,
    download_youtube,
    download_instagram,
    download_twitter,
    detect_platform,
)

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
