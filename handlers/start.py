"""Start command handlers."""
from aiogram import Router, F, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def register_start_handlers(dp: Dispatcher) -> None:
    """Register start handlers."""
    dp.include_router(router)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📥 Скачать контент", callback_data="download_menu")
    keyboard.button(text="📊 Статистика", callback_data="stats")
    keyboard.button(text="⭐ Premium", callback_data="premium")
    keyboard.button(text="ℹ️ Помощь", callback_data="help")
    keyboard.adjust(2)
    
    text = (
        "👋 <b>Добро пожаловать в Content Downloader Bot!</b>\n\n"
        "Я помогу вам скачать:\n"
        "• 🎥 Видео из TikTok, YouTube, Instagram\n"
        "• 📸 Фото из Instagram, Pinterest\n"
        "• 📝 Тексты из X.com, Reddit\n\n"
        "Просто отправьте мне ссылку на контент!\n\n"
        "💡 <i>Бесплатно: 7 скачиваний в день (сейчас - безлимит)</i>\n"
        "⭐ <i>Premium: безлимит</i>"
    )
    
    await message.answer(text, reply_markup=keyboard.as_markup())


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(message_or_query):
    """Handle /help command."""
    text = (
        "📖 <b>Как использовать бота:</b>\n\n"
        "1️⃣ Отправьте ссылку на контент (TikTok, YouTube, Instagram, X.com и т.д.)\n"
        "2️⃣ Бот автоматически определит платформу\n"
        "3️⃣ Выберите формат (видео/фото/текст)\n"
        "4️⃣ Получите файл!\n\n"
        "<b>Поддерживаемые платформы:</b>\n"
        "• TikTok\n"
        "• YouTube\n"
        "• Instagram\n"
        "• X.com (Twitter)\n"
        "• Reddit\n"
        "• Pinterest\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/stats - Ваша статистика\n"
        "/premium - Информация о Premium\n"
        "/help - Эта справка"
    )
    
    if hasattr(message_or_query, "message"):
        await message_or_query.message.edit_text(text)
        await message_or_query.answer()
    else:
        await message_or_query.answer(text)


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command."""
    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "Версия: 1.0.0\n"
        "Разработчик: @sir_yessir\n\n"
        "Этот бот создан для удобного скачивания контента "
        "из популярных социальных сетей.\n\n"
        "Используются современные технологии:\n"
        "• Python 3.11\n"
        "• aiogram 3.4.1\n"
        "• yt-dlp\n"
        "• FastAPI\n"
    )
    await message.answer(text)
