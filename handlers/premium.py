"""Premium handlers."""
from aiogram import Router, F, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def register_premium_handlers(dp: Dispatcher) -> None:
    """Register premium handlers."""
    dp.include_router(router)


@router.message(Command("premium"))
@router.callback_query(F.data == "premium")
async def show_premium(message_or_query, user=None):
    """Show premium information."""
    is_premium = user.is_premium if user and hasattr(user, 'is_premium') else False
    
    if is_premium:
        text = (
            "⭐ <b>Вы уже Premium пользователь!</b>\n\n"
            "Спасибо за поддержку! Вы имеете:\n"
            "✅ Безлимитные скачивания\n"
            "✅ Приоритетная обработка\n"
            "✅ Поддержка всех платформ\n"
            "✅ Без рекламы"
        )
        keyboard = None
    else:
        text = (
            "⭐ <b>Premium подписка</b>\n\n"
            "<b>Преимущества:</b>\n"
            "✅ Безлимитные скачивания (вместо 7/день)\n"
            "✅ Приоритетная обработка запросов\n"
            "✅ Доступ ко всем платформам\n"
            "✅ Без рекламы\n"
            "✅ Поддержка больших файлов\n\n"
            "<b>Цены:</b>\n"
            "💰 Месяц: 199 ₽\n"
            "💰 Год: 1299 ₽ (экономия 40%)\n\n"
            "💳 Оплата через Telegram Payments"
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💰 Месяц - 199 ₽", callback_data="premium_month")
        keyboard.button(text="💰 Год - 1299 ₽", callback_data="premium_year")
        keyboard.button(text="❌ Отмена", callback_data="cancel")
        keyboard.adjust(1)
    
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


@router.callback_query(F.data.startswith("premium_"))
async def handle_premium_payment(callback: CallbackQuery):
    """Handle premium payment."""
    period = callback.data.split("_")[1]  # month or year
    
    # Here would integration with Telegram Payments
    # For now, just shows a message
    await callback.answer(
        "💳 Интеграция с платежами в разработке. "
        "Свяжитесь с администратором для активации Premium.",
        show_alert=True
    )


@router.callback_query(F.data == "cancel")
async def cancel_premium(callback: CallbackQuery):
    """Cancel premium selection."""
    await callback.answer("Отменено")
    await callback.message.delete()
