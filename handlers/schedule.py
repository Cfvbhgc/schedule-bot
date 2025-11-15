from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import db
from keyboards import get_cancel_keyboard

router = Router()


@router.message(Command("my_bookings"))
async def cmd_my_bookings(message: Message):
    """Показать все активные записи пользователя.
    Каждая запись — с кнопкой отмены (inline)."""
    appointments = await db.get_user_appointments(message.from_user.id)

    if not appointments:
        await message.answer(
            "📭 У вас пока нет активных записей.\n"
            "Чтобы записаться: /book"
        )
        return

    # формируем текстовый список
    text_lines = ["📋 <b>Ваши записи:</b>\n"]
    for apt in appointments:
        text_lines.append(
            f"• <b>{apt['date'].strftime('%d.%m.%Y')}</b> в {apt['time_slot']} — "
            f"{apt['client_name']} (тел: {apt['phone']})"
        )

    text_lines.append("\nНажмите кнопку чтобы отменить запись:")

    await message.answer(
        "\n".join(text_lines),
        reply_markup=get_cancel_keyboard(appointments),
        parse_mode="HTML"
    )


# обработчик отмены конкретной записи
@router.callback_query(F.data.startswith("cancel:"))
async def process_cancel_appointment(callback: CallbackQuery):
    """Отменить запись по ID из callback data."""
    await callback.answer()

    try:
        appointment_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.answer("Ошибка: некорректный ID записи.")
        return

    # пытаемся отменить (проверяем что запись принадлежит этому юзеру)
    success = await db.cancel_appointment(appointment_id, callback.from_user.id)

    if success:
        await callback.message.edit_text(
            f"✅ Запись #{appointment_id} отменена.\n\n"
            "Посмотреть оставшиеся: /my_bookings\n"
            "Создать новую: /book"
        )
    else:
        await callback.message.edit_text(
            "⚠️ Не удалось отменить запись. "
            "Возможно, она уже была отменена ранее."
        )
