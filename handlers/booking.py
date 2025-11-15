import re
from datetime import date, datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import BookingStates
from keyboards import get_date_keyboard, get_time_keyboard, get_confirm_keyboard
import db

router = Router()


# ============================================================
# Booking flow — FSM based, пошаговое создание записи
# Шаги: имя -> телефон -> дата (inline) -> время (inline) -> подтверждение
# ============================================================

@router.message(Command("book"))
async def cmd_book(message: Message, state: FSMContext):
    """Начало записи. Переводим в состояние ожидания имени клиента."""
    await state.clear()  # на всякий случай сбрасываем предыдущее состояние
    await message.answer(
        "📝 Начинаем запись на приём!\n\n"
        "Введите имя клиента (или своё имя):"
    )
    await state.set_state(BookingStates.waiting_name)


@router.message(BookingStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Получаем имя, валидируем, переходим к телефону.
    Имя должно быть хотя бы 2 символа и содержать только буквы/пробелы."""
    name = message.text.strip() if message.text else ""

    # базовая валидация — имя не слишком короткое
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введите имя (минимум 2 символа):")
        return

    # проверяем что нет каких-то спец символов (разрешаем буквы, пробелы, дефис)
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', name):
        await message.answer(
            "⚠️ Имя может содержать только буквы, пробелы и дефис.\n"
            "Попробуйте ещё раз:"
        )
        return

    await state.update_data(client_name=name)
    await message.answer(
        f"Отлично, {name}! 👍\n\n"
        "Теперь введите номер телефона для связи\n"
        "(например: +7 999 123-45-67):"
    )
    await state.set_state(BookingStates.waiting_phone)


@router.message(BookingStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    """Получаем телефон. Простая валидация — должны быть цифры и +.
    После этого показываем inline-клавиатуру с датами на 7 дней вперёд."""
    phone = message.text.strip() if message.text else ""

    # убираем всё кроме цифр и + для проверки длины
    digits_only = re.sub(r'[^\d+]', '', phone)
    if len(digits_only) < 7:
        await message.answer(
            "⚠️ Похоже, номер телефона некорректный.\n"
            "Введите номер с кодом страны (минимум 7 цифр):"
        )
        return

    await state.update_data(phone=phone)

    # переходим к выбору даты — показываем inline keyboard
    await message.answer(
        "📅 Выберите дату приёма:",
        reply_markup=get_date_keyboard()
    )
    await state.set_state(BookingStates.waiting_date)


# callback handler для выбора даты
@router.callback_query(BookingStates.waiting_date, F.data.startswith("date:"))
async def process_date_callback(callback: CallbackQuery, state: FSMContext):
    """Пользователь нажал на кнопку с датой.
    Парсим дату из callback_data, проверяем доступные слоты, показываем время."""
    await callback.answer()  # убираем loading на кнопке

    date_str = callback.data.split(":", 1)[1]
    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        await callback.message.answer("Ошибка: некорректная дата. Попробуйте /book заново.")
        await state.clear()
        return

    # check: дата не в прошлом
    if selected_date < date.today():
        await callback.message.answer("⚠️ Эта дата уже прошла! Выберите другую:")
        return

    await state.update_data(date=date_str)

    # получаем занятые слоты для этой даты
    booked = await db.get_booked_slots(selected_date)

    # все слоты заняты?
    all_slots = [f"{h:02d}:00" for h in range(9, 19)]
    available = [s for s in all_slots if s not in booked]

    if not available:
        await callback.message.edit_text(
            "😔 К сожалению, на эту дату все слоты заняты.\n"
            "Выберите другую дату:",
            reply_markup=get_date_keyboard()
        )
        return

    # показываем доступные слоты
    await callback.message.edit_text(
        f"🕐 Выберите время на <b>{selected_date.strftime('%d.%m.%Y')}</b>:",
        reply_markup=get_time_keyboard(booked),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_time)


# callback для выбора времени
@router.callback_query(BookingStates.waiting_time, F.data.startswith("time:"))
async def process_time_callback(callback: CallbackQuery, state: FSMContext):
    """Юзер выбрал слот. Показываем summary и кнопки подтверждения."""
    await callback.answer()

    time_slot = callback.data.split(":", 1)[1]
    await state.update_data(time_slot=time_slot)

    # достаём все данные для подтверждения
    data = await state.get_data()
    client_name = data["client_name"]
    phone = data["phone"]
    selected_date = date.fromisoformat(data["date"])

    # формируем summary — пользователь должен подтвердить
    summary_text = (
        "📋 <b>Проверьте данные записи:</b>\n\n"
        f"👤 Имя: {client_name}\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Дата: {selected_date.strftime('%d.%m.%Y')}\n"
        f"🕐 Время: {time_slot}\n\n"
        "Всё верно?"
    )
    await callback.message.edit_text(
        summary_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.confirm)


# подтверждение записи
@router.callback_query(BookingStates.confirm, F.data == "confirm:yes")
async def process_confirm_yes(callback: CallbackQuery, state: FSMContext):
    """Пользователь подтвердил — сохраняем в базу.
    Проверяем ещё раз что слот не занят (race condition prevention)."""
    await callback.answer()
    data = await state.get_data()

    selected_date = date.fromisoformat(data["date"])
    time_slot = data["time_slot"]

    # double-check: слот ещё свободен? (на случай если кто-то забронил пока юзер думал)
    booked = await db.get_booked_slots(selected_date)
    if time_slot in booked:
        await callback.message.edit_text(
            "😔 К сожалению, этот слот только что заняли.\n"
            "Попробуйте записаться заново: /book"
        )
        await state.clear()
        return

    # сохраняем в базу
    appointment_id = await db.add_appointment(
        user_id=callback.from_user.id,
        client_name=data["client_name"],
        phone=data["phone"],
        date=selected_date,
        time_slot=time_slot,
    )

    await callback.message.edit_text(
        f"✅ Запись #{appointment_id} успешно создана!\n\n"
        f"👤 {data['client_name']}\n"
        f"📅 {selected_date.strftime('%d.%m.%Y')} в {time_slot}\n\n"
        "Я пришлю напоминание за 1 час до приёма 🔔\n"
        "Посмотреть записи: /my_bookings"
    )
    await state.clear()


@router.callback_query(BookingStates.confirm, F.data == "confirm:no")
async def process_confirm_no(callback: CallbackQuery, state: FSMContext):
    """Отмена на этапе подтверждения."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ Запись отменена.\n"
        "Чтобы записаться заново, нажмите /book"
    )


# universal cancel handler — works at any FSM stage
@router.callback_query(F.data == "booking:cancel")
async def process_booking_cancel(callback: CallbackQuery, state: FSMContext):
    """Кнопка отмены на любом шаге FSM."""
    await callback.answer("Запись отменена")
    await state.clear()
    await callback.message.edit_text(
        "❌ Процесс записи отменён.\n"
        "Для новой записи: /book"
    )
