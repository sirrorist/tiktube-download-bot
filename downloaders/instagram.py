"""Instagram downloader."""
import os
from pathlib import Path
from typing import Dict, Any

from config import settings


async def download_instagram_content(url: str) -> Dict[str, Any]:
    """Download Instagram content (photo or video)."""
    try:
        import yt_dlp
        
        output_dir = Path(settings.temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(output_dir / 'instagram_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Determine content type
            ext = Path(filename).suffix.lower()
            content_type = "video" if ext in ['.mp4', '.mov', '.webm'] else "photo"
            
            # Get file size
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            
            return {
                "success": True,
                "file_path": filename,
                "content_type": content_type,
                "file_size": file_size,
                "title": info.get("title", "Instagram Content"),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
