from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Генерация клавиатуры с датами на ближайшие 7 дней
def get_date_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = date.today()
    for i in range(7):
        d = today + timedelta(days=i)
        # показываем дату как "Пн 15.01"
        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        label = f"{weekday_names[d.weekday()]} {d.strftime('%d.%m')}"
        builder.button(
            text=label,
            callback_data=f"date:{d.isoformat()}"
        )
    builder.adjust(2)  # по 2 кнопки в ряд
    # cancel button
    builder.row(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="booking:cancel"
    ))
    return builder.as_markup()


def get_time_keyboard(booked_slots: list[str]) -> InlineKeyboardMarkup:
    """Генерим кнопки со слотами 09:00 - 18:00.
    booked_slots — already taken, показываем как недоступные."""
    builder = InlineKeyboardBuilder()
    for hour in range(9, 19):
        slot = f"{hour:02d}:00"
        if slot in booked_slots:
            # слот занят — показываем зачёркнутым но не кликабельным?
            # в телеге нельзя disable кнопку, поэтому просто не добавляем
            continue
        builder.button(
            text=slot,
            callback_data=f"time:{slot}"
        )
    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="booking:cancel"
    ))
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm:yes")
    builder.button(text="❌ Отменить", callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()


def get_cancel_keyboard(appointments: list) -> InlineKeyboardMarkup:
    """Кнопки для отмены каждой записи пользователя."""
    builder = InlineKeyboardBuilder()
    for apt in appointments:
        label = f"❌ {apt['date'].strftime('%d.%m')} {apt['time_slot']} — {apt['client_name']}"
        builder.button(
            text=label,
            callback_data=f"cancel:{apt['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()
