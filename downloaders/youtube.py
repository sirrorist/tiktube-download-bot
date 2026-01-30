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

        # Получаем информацию о видео
        info_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            # Используем android client для обхода блокировок
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "android_embedded", "ios"],
                    "skip": ["hls"],  # Пропускаем проблемные форматы
                }
            },
            "http_headers": {
                "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {
                    "success": False,
                    "error": "Не удалось получить информацию о видео",
                }

            # Проверка: Прямая трансляция запрещена
            is_live = info.get("is_live", False)
            was_live = info.get("was_live", False)  # Проверка закончившейся трансляции
            live_status = info.get("live_status")  # Статус: is_live, was_live, not_live, post_live
            
            if is_live or live_status == "is_live":
                return {
                    "success": False,
                    "error": "❌ Прямые трансляции не поддерживаются.",
                }
            
            # Проверка на post_live (только что закончившаяся трансляция)
            if live_status == "post_live":
                return {
                    "success": False,
                    "error": "⏳ Трансляция только что закончилась.\n\n"
                             "Подождите 5-10 минут, пока YouTube обработает видео.",
                }

            # Доп проверка: Доступность форматов
            formats = info.get("formats", [])
            if not formats or len(formats) == 0:
                # Может это всё ещё live/upcoming
                if was_live or info.get("is_upcoming"):
                    return {
                        "success": False,
                        "error": "❌ Видео пока недоступно для скачивания.\n\n"
                                 "Возможные причины:\n"
                                 "• Трансляция ещё не началась\n"
                                 "• Трансляция только что закончилась (подождите 5-10 мин)\n"
                                 "• Видео обрабатывается YouTube",
                    }
                else:
                    return {
                        "success": False,
                        "error": "❌ Форматы видео недоступны.\n\n"
                                 "Видео может быть:\n"
                                 "• Приватным\n"
                                 "• Удалённым\n"
                                 "• С ограничениями региона",
                    }

            # Проверка длительности (лимит 20 минут)
            duration = info.get("duration", 0)
            if duration > 1200:  # 20 минут
                return {
                    "success": False,
                    "error": f"Видео слишком длинное ({duration // 60} мин). Максимум: 20 минут",
                }

            # ОПРЕДЕЛЕНИЕ: Музыка или видео?
            is_music = _is_music_content(info)

            # Формируем параметры скачивания в зависимости от типа контента
            if is_music:
                # Для музыки: только аудио в хорошем качестве
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": str(output_dir / "youtube_audio_%(id)s.%(ext)s"),
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                    # Не скачиваем thumbnail - часто вызывает 403
                    "writethumbnail": False,
                    "embedthumbnail": False,
                }
                content_type = "audio"
            else:
                # Для видео: видео + аудио
                ydl_opts = {
                    # Используем комбинированные форматы или fallback на best
                    "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/best",
                    "outtmpl": str(output_dir / "youtube_video_%(id)s.%(ext)s"),
                    "merge_output_format": "mp4",
                }
                content_type = "video"

            # Общие параметры для обоих типов (КРИТИЧЕСКИ ВАЖНО!)
            ydl_opts.update(
                {
                    "quiet": False,
                    "no_warnings": False,
                    "ignoreerrors": False,
                    # Используем Android client для обхода блокировок
                    "extractor_args": {
                        "youtube": {
                            "player_client": [
                                "android",
                                "android_embedded",
                                "ios",
                            ],  # Приоритет клиентов
                            "skip": ["hls", "dash"],  # Пропускаем проблемные форматы
                        }
                    },
                    # User-Agent Android YouTube app
                    "http_headers": {
                        "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate",
                    },
                    # Повторные попытки
                    "retries": 10,
                    "fragment_retries": 10,
                    "skip_unavailable_fragments": True,
                    # Лимит размера для Telegram (50MB)
                    "max_filesize": 50 * 1024 * 1024,
                    # Не проверять сертификаты (иногда помогает)
                    "nocheckcertificate": True,
                    # Предпочитать свободные форматы
                    "prefer_free_formats": True,
                    # Geo bypass
                    "geo_bypass": True,
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

                # Формируем красивое название
                title = info.get("title", "YouTube Content")
                if is_music:
                    uploader = info.get("uploader", "Unknown Artist")
                    title = f"🎵 {title} - {uploader}"
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
        
        # Специфичная обработка ошибки "No video formats found"
        if "No video formats found" in error_msg or "no formats found" in error_msg.lower():
            return {
                "success": False,
                "error": "❌ Видео недоступно для скачивания.\n\n"
                         "Возможные причины:\n"
                         "• Это прямая трансляция (дождитесь окончания)\n"
                         "• Трансляция только что закончилась (подождите 5-10 мин)\n"
                         "• Приватное видео или удалено\n"
                         "• Ограничения по региону",
            }
        
        if "HTTP Error 403" in error_msg or "Forbidden" in error_msg:
            return {
                "success": False,
                "error": "⚠️ YouTube временно ограничил доступ. Попробуйте:\n"
                "1. Подождать 1-2 минуты\n"
                "2. Использовать другую ссылку\n"
                "3. Скопировать ссылку заново",
            }
        elif "Video unavailable" in error_msg:
            return {"success": False, "error": "❌ Видео недоступно или удалено"}
        elif "Requested format is not available" in error_msg:
            return {
                "success": False,
                "error": "❌ Запрашиваемый формат недоступен. Попробуйте другое видео.",
            }
        elif "Private video" in error_msg:
            return {"success": False, "error": "❌ Это приватное видео"}
        elif "Sign in to confirm your age" in error_msg:
            return {
                "success": False,
                "error": "❌ Видео с возрастным ограничением. Скачивание недоступно.",
            }
        else:
            return {"success": False, "error": f"⚠️ Ошибка YouTube: {error_msg[:100]}"}
    except Exception as e:
        return {
            "success": False,
            "error": f"⚠️ Неизвестная ошибка: {str(e)[:100]}",
        }


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
        "music video",
        "mv",
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
        if tags and any(tag.lower() in music_tags for tag in tags):
            return True

    # По умолчанию - видео
    return False
