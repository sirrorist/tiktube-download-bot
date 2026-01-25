"""Downloaders package."""
import re
from typing import Optional, Dict, Any

from .tiktok import download_tiktok_video
from .youtube import download_youtube_video
from .instagram import download_instagram_content
from .twitter import download_twitter_content

URL_PATTERNS = {
    "tiktok": r"(?:https?://)?(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)",
    "youtube": r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)",
    "instagram": r"(?:https?://)?(?:www\.)?instagram\.com",
    "twitter": r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)",
    "reddit": r"(?:https?://)?(?:www\.)?reddit\.com",
    "pinterest": r"(?:https?://)?(?:www\.)?pinterest\.com",
}


def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL."""
    url_lower = url.lower()
    for platform, pattern in URL_PATTERNS.items():
        if re.search(pattern, url_lower):
            return platform
    return None


async def download_tiktok(url: str) -> Dict[str, Any]:
    """Download TikTok content."""
    return await download_tiktok_video(url)


async def download_youtube(url: str) -> Dict[str, Any]:
    """Download YouTube content."""
    return await download_youtube_video(url)


async def download_instagram(url: str) -> Dict[str, Any]:
    """Download Instagram content."""
    return await download_instagram_content(url)


async def download_twitter(url: str) -> Dict[str, Any]:
    """Download Twitter/X content."""
    return await download_twitter_content(url)
