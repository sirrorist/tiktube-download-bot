"""Download handlers."""
import re
from aiogram import Router, F, Dispatcher
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime

from database import get_db, User, Download
from downloaders import (
    download_tiktok,
    download_youtube,
    download_instagram,
    download_twitter,
    detect_platform
)
from config import settings

router = Router()

# URL patterns
URL_PATTERNS = {
    "tiktok": r"(?:https?://)?(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)",
    "youtube": r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)",
    "instagram": r"(?:https?://)?(?:www\.)?instagram\.com",
    "twitter": r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)",
    "reddit": r"(?:https?://)?(?:www\.)?reddit\.com",
    "pinterest": r"(?:https?://)?(?:www\.)?pinterest\.com",
}


def register_download_handlers(dp: Dispatcher) -> None:
    """Register download handlers."""
    dp.include_router(router)


@router.message(Command("download"))
@router.callback_query(F.data == "download_menu")
async def download_menu(message_or_query):
    """Show download menu."""
    text = (
        "📥 <b>Скачать контент</b>\n\n"
        "Отправьте ссылку на контент, который хотите скачать.\n\n"
        "<b>Поддерживаемые платформы:</b>\n"
        "• TikTok\n"
        "• YouTube\n"
        "• Instagram\n"
        "• X.com (Twitter)\n"
        "• Reddit\n"
        "• Pinterest"
    )
    
    if hasattr(message_or_query, "message"):
        await message_or_query.message.edit_text(text)
        await message_or_query.answer()
    else:
        await message_or_query.answer(text)


@router.message(F.text)
async def handle_url(message: Message, user: User = None, rate_limited: bool = False):
    """Handle URL message."""
    if not user:
        return  # User not found, skip
    
    if rate_limited:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="⭐ Получить Premium", callback_data="premium")
        await message.answer(
            "❌ Достигнут лимит скачиваний на сегодня.\n\n"
            "⭐ Получите Premium для безлимитного доступа!",
            reply_markup=keyboard.as_markup()
        )
        return
    
    text = message.text.strip()
    
    # Check if it's a URL
    if not any(re.search(pattern, text, re.IGNORECASE) for pattern in URL_PATTERNS.values()):
        return  # Not a URL, ignore
    
    # Detect platform
    platform = detect_platform(text)
    if not platform:
        await message.answer("❌ Не удалось определить платформу. Проверьте ссылку.")
        return
    
    # Send processing message
    processing_msg = await message.answer("⏳ Обрабатываю запрос...")
    
    try:
        # Download content based on platform
        result = None
        if platform == "tiktok":
            result = await download_tiktok(text)
        elif platform == "youtube":
            result = await download_youtube(text)
        elif platform == "instagram":
            result = await download_instagram(text)
        elif platform == "twitter":
            result = await download_twitter(text)
        # Add other platforms as needed
        
        if not result or not result.get("success"):
            await processing_msg.edit_text(
                f"❌ Ошибка при скачивании: {result.get('error', 'Неизвестная ошибка')}"
            )
            logger.info("Download failed for user {user.id} from {platform}: {result.get('error')}")
            return
        
        # Send file
        file_path = result["file_path"]
        file_size_mb = result.get("file_size", 0) / (1024 * 1024)
        
        if file_size_mb > settings.max_file_size_mb:
            await processing_msg.edit_text(
                f"❌ Файл слишком большой ({file_size_mb:.1f} MB). "
                f"Максимальный размер: {settings.max_file_size_mb} MB"
            )
            return
        
        file = FSInputFile(file_path)
        caption = (
            f"✅ <b>Контент скачан!</b>\n\n"
            f"Платформа: {platform.upper()}\n"
            f"Размер: {file_size_mb:.1f} MB"
        )
        
        if result["content_type"] == "video":
            await message.answer_video(file, caption=caption)
        elif result["content_type"] == "photo":
            await message.answer_photo(file, caption=caption)
        else:
            await message.answer_document(file, caption=caption)
        
        await processing_msg.delete()
        
        # Update user stats
        async for session in get_db():
            # Refresh user to get current values
            await session.refresh(user, ['downloads_today', 'total_downloads'])
            
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    downloads_today=user.downloads_today + 1,
                    total_downloads=user.total_downloads + 1
                )
            )
            
            # Save download history
            download = Download(
                user_id=user.id,
                platform=platform,
                url=text,
                content_type=result["content_type"],
                file_size=result.get("file_size"),
                status="completed"
            )
            session.add(download)
            await session.commit()
            break
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")
        # Log error
        import logging
        logging.error(f"Download error: {e}", exc_info=True)
