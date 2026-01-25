"""Twitter/X downloader."""
import os
from pathlib import Path
from typing import Dict, Any

from config import settings


async def download_twitter_content(url: str) -> Dict[str, Any]:
    """Download Twitter/X content."""
    try:
        import yt_dlp
        
        output_dir = Path(settings.temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(output_dir / 'twitter_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Determine content type
            ext = Path(filename).suffix.lower()
            if ext in ['.mp4', '.mov', '.webm']:
                content_type = "video"
            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                content_type = "photo"
            else:
                content_type = "text"
            
            # Get file size
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            
            return {
                "success": True,
                "file_path": filename,
                "content_type": content_type,
                "file_size": file_size,
                "title": info.get("title", "Twitter Content"),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
