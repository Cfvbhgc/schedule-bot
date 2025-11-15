from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик /start — приветствие и список команд."""
    await message.answer(
        "👋 Привет! Я бот для записи на приём.\n\n"
        "Доступные команды:\n"
        "/book — записаться на приём\n"
        "/my_bookings — мои записи\n"
        "/help — помощь\n\n"
        "Выберите нужную команду или нажмите /book чтобы начать."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    # help message with all available commands
    text = (
        "📋 <b>Список команд:</b>\n\n"
        "/book — создать новую запись\n"
        "/my_bookings — посмотреть свои записи и отменить\n"
        "/help — эта справка\n\n"
        "При записи вы пошагово укажете:\n"
        "1. Имя клиента\n"
        "2. Телефон для связи\n"
        "3. Удобную дату\n"
        "4. Время приёма\n\n"
        "За 1 час до приёма бот пришлёт напоминание 🔔"
    )
    await message.answer(text, parse_mode="HTML")
