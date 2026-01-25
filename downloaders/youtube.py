"""YouTube downloader."""
import os
from pathlib import Path
from typing import Dict, Any

from config import settings


async def download_youtube_video(url: str) -> Dict[str, Any]:
    """Download YouTube video."""
    try:
        import yt_dlp
        
        output_dir = Path(settings.temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = {
            'format': 'best[height<=720]',  # Limit to 720p for Telegram
            'outtmpl': str(output_dir / 'youtube_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Get file size
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            
            return {
                "success": True,
                "file_path": filename,
                "content_type": "video",
                "file_size": file_size,
                "title": info.get("title", "YouTube Video"),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
