import os
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import db

router = Router()

# ID админа из переменных окружения
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


def is_admin(user_id: int) -> bool:
    """Проверка что пользователь — администратор."""
    return user_id == ADMIN_ID


@router.message(Command("all_bookings"))
async def cmd_all_bookings(message: Message):
    """Показать все активные записи. Только для админа."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    appointments = await db.get_all_active_appointments()

    if not appointments:
        await message.answer("📭 Нет активных записей.")
        return

    lines = ["📋 <b>Все активные записи:</b>\n"]
    for apt in appointments:
        lines.append(
            f"#{apt['id']} | {apt['date'].strftime('%d.%m.%Y')} {apt['time_slot']} | "
            f"{apt['client_name']} | тел: {apt['phone']} | uid: {apt['user_id']}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("today"))
async def cmd_today(message: Message):
    """Показать расписание на сегодня. Admin only."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    today = date.today()
    appointments = await db.get_all_appointments_for_date(today)

    if not appointments:
        await message.answer(f"📭 На сегодня ({today.strftime('%d.%m.%Y')}) записей нет.")
        return

    lines = [f"📅 <b>Расписание на {today.strftime('%d.%m.%Y')}:</b>\n"]
    for apt in appointments:
        status_icon = "✅" if apt["status"] == "active" else "❌"
        lines.append(
            f"{status_icon} {apt['time_slot']} — {apt['client_name']} "
            f"(тел: {apt['phone']})"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
