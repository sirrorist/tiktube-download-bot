"""YouTube downloader with automatic PO Token management."""
import os
from pathlib import Path

from loguru import logger

from config import settings
from utils.po_token_cache import POTokenCache
from downloaders.po_token_manager import POTokenGenerator


# Инициализация менеджера токенов (глобально)
_po_token_cache = POTokenCache(cache_file="storage/po_token_cache.json")


def _get_po_token(client: str = "android") -> str:
    """
    Получить актуальный PO Token с автообновлением.

    Args:
        client: Тип клиента (android, ios)

    Returns:
        PO Token (может быть пустым)
    """
    # Пытаемся получить из кэша
    token = _po_token_cache.get_token(client)

    if token:
        return token

    # Токен истёк или отсутствует - генерируем новый
    logger.info(f"PO Token for {client} not found or expired, generating new...")

    new_token = POTokenGenerator.generate_from_ytdlp(client)

    if new_token:
        # Сохраняем в кэш на 3 дня
        _po_token_cache.set_token(client, new_token, ttl_days=3)
        return new_token
    else:
        # Fallback - работаем без токена
        logger.warning(
            f"Failed to generate PO Token for {client}, using fallback"
        )
        return POTokenGenerator.generate_fallback()


async def download_youtube_video(url: str) -> dict[str, any]:
    """Download YouTube video or audio with automatic PO Token."""
    try:
        import yt_dlp

        output_dir = Path(settings.temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Автоматически получаем актуальный PO Token
        po_token_android = _get_po_token("android")

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

        # Добавляем PO Token если есть
        if po_token_android:
            info_opts["extractor_args"]["youtube"]["po_token"] = [
                f"android.gvs+{po_token_android}"
            ]

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {
                    "success": False,
                    "error": "Не удалось получить информацию о видео",
                }

            # Проверка: Прямая трансляция запрещена
            is_live = info.get("is_live", False)
            was_live = info.get("was_live", False)
            live_status = info.get("live_status")

            if is_live or live_status == "is_live":
                return {
                    "success": False,
                    "error": "❌ Прямые трансляции не поддерживаются.",
                }
            
            if live_status == "post_live":
                return {
                    "success": False,
                    "error": "⏳ Трансляция только что закончилась.\n\n"
                             "Подождите 5-10 минут, пока YouTube обработает видео.",
                }

            # Доп проверка: Доступность форматов
            formats = info.get("formats", [])
            if not formats or len(formats) == 0:
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

            # Определение: Музыка или видео?
            is_music = _is_music_content(info)

            # Формируем параметры скачивания в зависимости от типа контента
            if is_music:
                # Для музыки
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
                # Для видео
                ydl_opts = {
                    # Используем комбинированные форматы или fallback на best
                    "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/best",
                    "outtmpl": str(output_dir / "youtube_video_%(id)s.%(ext)s"),
                    "merge_output_format": "mp4",
                }
                content_type = "video"

            # Общие параметры
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
                    "max_filesize": 50 * 1024 * 1024,
                    "nocheckcertificate": True,
                    "prefer_free_formats": True,
                    "geo_bypass": True,
                }
            )

            # Добавляем PO Token если есть
            if po_token_android:
                ydl_opts["extractor_args"]["youtube"]["po_token"] = [
                    f"android.gvs+{po_token_android}"
                ]
                logger.debug(f"Using PO Token for download: {po_token_android[:30]}...")

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
            # Возможно токен истёк - очищаем кэш
            _po_token_cache.clear_token("android")
            return {
                "success": False,
                "error": "⚠️ YouTube временно ограничил доступ. Попробуйте:\n"
                "1. Подождать 1-2 минуты\n"
                "2. Использовать другую ссылку\n"
                "3. Скопировать ссылку заново",
            }
        elif "Video unavailable" in error_msg:
            return {"success": False, "error": "❌ Видео недоступно или удалено"}
        elif "Private video" in error_msg:
            return {"success": False, "error": "❌ Это приватное видео"}
        elif "Sign in to confirm your age" in error_msg:
            return {
                "success": False,
                "error": "❌ Видео с возрастным ограничением. Скачивание недоступно.",
            }
        else:
            return {"success": False, "error": f"⚠️ Ошибка YouTube: {error_msg[:200]}"}
    except AttributeError:
        return {
            "success": False,
            "error": "⚠️ Ошибка обработки данных видео. Попробуйте другую ссылку.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"⚠️ Неизвестная ошибка: {str(e)[:200]}",
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
    if categories and "Music" in categories:
        return True

    # Проверка 2: Жанр
    genre = info.get("genre")
    if genre:
        genre_lower = str(genre).lower()
        if any(
            music_genre in genre_lower
            for music_genre in ["music", "song", "audio", "soundtrack", "ost"]
        ):
            return True

    # Проверка 3: Название содержит музыкальные слова
    title = info.get("title")
    if title:
        title_lower = str(title).lower()
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
        if any(keyword in title_lower for keyword in music_keywords):
            return True

    # Проверка 4: Канал музыкальный
    uploader = info.get("uploader")
    channel_id = info.get("channel_id")
    
    if uploader:
        uploader_lower = str(uploader).lower()
        music_channels = ["vevo", "official", " - topic", "records", "music"]
        
        if any(marker in uploader_lower for marker in music_channels):
            return True
        
        # YouTube Music обычно добавляет " - Topic" к названиям каналов
        if channel_id and "topic" in uploader_lower:
            return True

    # Проверка 5: Длительность (песни обычно < 10 минут)
    duration = info.get("duration", 0)
    if duration and 0 < duration < 600:  # Меньше 10 минут и больше 0
        # Дополнительная проверка: если короткое И есть музыкальные теги
        tags = info.get("tags", [])
        if tags:
            music_tags = ["music", "song", "audio", "official"]

            if any(str(tag).lower() in music_tags for tag in tags if tag):
                return True

    # По умолчанию - видео
    return False
