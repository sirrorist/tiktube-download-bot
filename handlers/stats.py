"""Statistics handlers."""
from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from sqlalchemy import select, func

from database import get_db, User, Download

router = Router()


def register_stats_handlers(dp: Dispatcher) -> None:
    """Register stats handlers."""
    dp.include_router(router)


@router.message(Command("stats"))
@router.callback_query(F.data == "stats")
async def show_stats(message_or_query, user: User = None):
    """Show user statistics."""
    if not user:
        text = "❌ Не удалось загрузить данные пользователя."
        if hasattr(message_or_query, "message"):
            await message_or_query.message.edit_text(text)
            await message_or_query.answer()
        else:
            await message_or_query.answer(text)
        return
    async for session in get_db():
        # Get download statistics
        result = await session.execute(
            select(
                func.count(Download.id).label("total"),
                func.sum(Download.file_size).label("total_size")
            ).where(Download.user_id == user.id)
        )
        stats = result.first()
        
        # Get platform breakdown
        platform_stats = await session.execute(
            select(
                Download.platform,
                func.count(Download.id).label("count")
            )
            .where(Download.user_id == user.id)
            .group_by(Download.platform)
        )
        platforms = platform_stats.all()
        break
    
    total_downloads = stats.total or 0
    total_size_gb = (stats.total_size or 0) / (1024 * 1024 * 1024)
    
    platform_text = "\n".join([
        f"• {platform}: {count} скачиваний"
        for platform, count in platforms
    ]) if platforms else "Нет скачиваний"
    
    limit = "∞" if user.is_premium else f"{user.downloads_today}/{7}"
    
    text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"👤 Пользователь: {user.first_name or 'Неизвестно'}\n"
        f"⭐ Статус: {'Premium' if user.is_premium else 'Бесплатный'}\n\n"
        f"📥 <b>Скачивания:</b>\n"
        f"• Всего: {total_downloads}\n"
        f"• Сегодня: {limit}\n"
        f"• Общий объем: {total_size_gb:.2f} GB\n\n"
        f"📈 <b>По платформам:</b>\n{platform_text}"
    )
    
    keyboard = None
    if not user.is_premium:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="⭐ Получить Premium", callback_data="premium")
    
    if hasattr(message_or_query, "message"):
        await message_or_query.message.edit_text(
            text,
            reply_markup=keyboard.as_markup() if keyboard else None
        )
        await message_or_query.answer()
    else:
        await message_or_query.answer(
            text,
            reply_markup=keyboard.as_markup() if keyboard else None
        )
