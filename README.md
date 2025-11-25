# Schedule Bot

Telegram-бот для управления записями на приём. Клиенты могут бронировать свободные слоты, просматривать свои записи и получать напоминания за час до приёма.

## Стек

- Python 3.11
- aiogram 3.x (async Telegram Bot framework)
- PostgreSQL 15 (через asyncpg)
- APScheduler (напоминания за 1 час)
- Docker + Docker Compose

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и список команд |
| `/help` | Подробная справка |
| `/book` | Начать запись на приём (пошаговый FSM) |
| `/my_bookings` | Мои записи + кнопки отмены |
| `/all_bookings` | Все записи (только админ) |
| `/today` | Расписание на сегодня (только админ) |

## Процесс записи

1. Ввод имени клиента
2. Ввод номера телефона
3. Выбор даты (inline-кнопки на 7 дней вперёд)
4. Выбор времени (свободные слоты 09:00-18:00)
5. Подтверждение

## Запуск

### Docker (рекомендуется)

```bash
cp .env.example .env
# отредактируйте .env — укажите BOT_TOKEN и ADMIN_ID
docker-compose up -d --build
```

### Локально

```bash
cp .env.example .env
# отредактируйте .env, установите DB_HOST=localhost

pip install -r requirements.txt

# PostgreSQL должен быть запущен
python bot.py
```

## Переменные окружения

| Переменная | Описание |
|-----------|----------|
| `BOT_TOKEN` | Токен от @BotFather |
| `DB_HOST` | Хост PostgreSQL (`postgres` для Docker) |
| `DB_PORT` | Порт PostgreSQL (по умолчанию `5432`) |
| `DB_NAME` | Имя базы данных |
| `DB_USER` | Пользователь БД |
| `DB_PASS` | Пароль БД |
| `ADMIN_ID` | Telegram ID администратора |

## Структура проекта

```
schedule-bot/
├── bot.py              # точка входа, dispatcher, polling
├── db.py               # asyncpg pool, CRUD операции
├── states.py           # FSM states для aiogram
├── keyboards.py        # inline-клавиатуры
├── scheduler.py        # APScheduler — напоминания
├── handlers/
│   ├── start.py        # /start, /help
│   ├── booking.py      # FSM-based запись на приём
│   ├── schedule.py     # /my_bookings + отмена
│   └── admin.py        # /all_bookings, /today
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```
