"""YouTube downloader."""
import os
from pathlib import Path

from config import settings


async def download_youtube_video(url: str) -> dict[str, any]:
    """Download YouTube video or audio."""
    try:
        import yt_dlp

        output_dir = Path(settings.temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Сначала получаем информацию о видео БЕЗ скачивания
        info_opts = {
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        }

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {
                    "success": False,
                    "error": "Не удалось получить информацию о видео",
                }

            # ПРОВЕРКА: Прямая трансляция запрещена
            is_live = info.get("is_live", False)
            if is_live:
                return {
                    "success": False,
                    "error": "❌ Прямые трансляции не поддерживаются. Дождитесь окончания и попробуйте снова.",
                }

            # Проверка длительности (лимит 30 минут)
            duration = info.get("duration", 0)
            if duration > 1800:  # 30 минут
                return {
                    "success": False,
                    "error": f"Видео слишком длинное ({duration // 60} мин). Максимум: 30 минут",
                }

            # Музыка или видео?
            is_music = _is_music_content(info)

            # Формируем параметры скачивания в зависимости от типа контента
            if is_music:
                # Для музыки
                ydl_opts = {
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "outtmpl": str(output_dir / "youtube_audio_%(id)s.%(ext)s"),
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                    "writethumbnail": True,  # Скачиваем обложку
                    "postprocessor_args": [
                        "-metadata",
                        f"title={info.get('title', 'Unknown')}",
                        "-metadata",
                        f"artist={info.get('uploader', 'Unknown')}",
                    ],
                }
                content_type = "audio"
            else:
                # Для видео
                ydl_opts = {
                    "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
                    "outtmpl": str(output_dir / "youtube_video_%(id)s.%(ext)s"),
                    "merge_output_format": "mp4",
                }
                content_type = "video"

            # Общие параметры для обоих типов
            ydl_opts.update(
                {
                    "quiet": False,
                    "no_warnings": False,
                    "ignoreerrors": False,
                    # User-Agent для обхода блокировок YouTube
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-us,en;q=0.5",
                        "Sec-Fetch-Mode": "navigate",
                    },
                    # Повторные попытки
                    "retries": 10,
                    "fragment_retries": 10,
                    "skip_unavailable_fragments": True,
                    # Лимит размера для Telegram (50MB)
                    "max_filesize": 50 * 1024 * 1024,
                    # Использовать aria2c если доступен (опционально)
                    # 'external_downloader': 'aria2c',
                    # 'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M'],
                }
            )

            # Скачиваем контент
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                info_downloaded = ydl_download.extract_info(url, download=True)
                filename = ydl_download.prepare_filename(info_downloaded)

                # Для аудио: после обработки расширение меняется на .mp3
                if is_music:
                    # Ищем файл с расширением .mp3
                    base_name = os.path.splitext(filename)[0]
                    mp3_file = f"{base_name}.mp3"
                    if os.path.exists(mp3_file):
                        filename = mp3_file

                # Проверяем что файл существует и не пустой
                if not os.path.exists(filename):
                    return {"success": False, "error": "Файл не был скачан"}

                file_size = os.path.getsize(filename)
                if file_size == 0:
                    return {"success": False, "error": "Скачанный файл пустой"}

                # Формируем название
                title = info.get("title", "YouTube Content")
                if is_music:
                    uploader = info.get("uploader", "Unknown Artist")
                    title = f"title} - {uploader}"
                else:
                    title = f"🎥 {title}"

                return {
                    "success": True,
                    "file_path": filename,
                    "content_type": content_type,
                    "file_size": file_size,
                    "title": title,
                }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "HTTP Error 403" in error_msg:
            return {
                "success": False,
                "error": "YouTube заблокировал доступ. Попробуйте позже или используйте другую ссылку.",
            }
        elif "Video unavailable" in error_msg:
            return {"success": False, "error": "Видео недоступно или удалено"}
        elif "Requested format is not available" in error_msg:
            return {
                "success": False,
                "error": "Запрашиваемый формат недоступен. Попробуйте другое видео.",
            }
        else:
            return {"success": False, "error": f"Ошибка загрузки: {error_msg}"}
    except Exception as e:
        return {"success": False, "error": f"Неизвестная ошибка: {str(e)}"}


def _is_music_content(info: dict) -> bool:
    """
    Определяет, является ли контент музыкой.
    
    Проверяет:
    - Категорию видео (Music)
    - Наличие в названии музыкальных слов
    - Канал является музыкальным (Official, VEVO, Topic)
    - Короткая длительность (< 10 минут обычно музыка)
    """
    # Проверка 1: Категория YouTube
    categories = info.get("categories", [])
    if "Music" in categories:
        return True

    # Проверка 2: Жанр
    genre = info.get("genre", "").lower()
    if genre and any(
        music_genre in genre
        for music_genre in ["music", "song", "audio", "soundtrack", "ost"]
    ):
        return True

    # Проверка 3: Название содержит музыкальные слова
    title = info.get("title", "").lower()
    music_keywords = [
        "official music video",
        "official video",
        "official audio",
        "lyrics",
        "lyric video",
        "(audio)",
        "[audio]",
        "full album",
        "ost",
        "soundtrack",
        "original sound",
    ]
    if any(keyword in title for keyword in music_keywords):
        return True

    # Проверка 4: Канал музыкальный
    uploader = info.get("uploader", "").lower()
    channel_id = info.get("channel_id", "")
    music_channels = ["vevo", "official", " - topic", "records", "music"]

    if any(marker in uploader for marker in music_channels):
        return True

    # YouTube Music обычно добавляет " - Topic" к названиям каналов
    if channel_id and "topic" in uploader:
        return True

    # Проверка 5: Длительность (песни обычно < 10 минут)
    duration = info.get("duration", 0)
    if duration > 0 and duration < 600:  # Меньше 10 минут
        # Дополнительная проверка: если короткое И есть музыкальные теги
        tags = info.get("tags", [])
        music_tags = ["music", "song", "audio", "official"]
        if any(tag.lower() in music_tags for tag in tags):
            return True

    # По умолчанию - видео
    return False
