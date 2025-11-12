import os
import asyncpg
from typing import Optional

# глобальный пул соединений
pool: Optional[asyncpg.Pool] = None


async def create_pool():
    """Создаём connection pool к PostgreSQL."""
    global pool
    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "schedule_bot"),
        user=os.getenv("DB_USER", "bot_user"),
        password=os.getenv("DB_PASS", "bot_password"),
        min_size=2,
        max_size=10,
    )
    return pool


async def close_pool():
    global pool
    if pool:
        await pool.close()


async def init_db():
    """Create tables if not exist. Вызывается при старте бота."""
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                client_name VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                date DATE NOT NULL,
                time_slot VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(20) DEFAULT 'active',
                reminder_sent BOOLEAN DEFAULT FALSE
            );
        """)
        # индекс для быстрого поиска по user_id
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_user_id
            ON appointments(user_id);
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_date
            ON appointments(date);
        """)


# --- CRUD operations ---

async def add_appointment(user_id: int, client_name: str, phone: str,
                          date, time_slot: str) -> int:
    """Добавить запись. Returns appointment id."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO appointments (user_id, client_name, phone, date, time_slot)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_id, client_name, phone, date, time_slot,
        )
        return row["id"]


async def get_user_appointments(user_id: int):
    """Получить все активные записи пользователя."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, client_name, date, time_slot, phone, status
            FROM appointments
            WHERE user_id = $1 AND status = 'active'
            ORDER BY date, time_slot
            """,
            user_id,
        )
        return rows


async def cancel_appointment(appointment_id: int, user_id: int) -> bool:
    """Отменить запись. Возвращает True если запись найдена и отменена."""
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE appointments SET status = 'cancelled'
            WHERE id = $1 AND user_id = $2 AND status = 'active'
            """,
            appointment_id, user_id,
        )
        # result like 'UPDATE 1'
        return result.split()[-1] != "0"


async def get_all_appointments_for_date(date):
    """Admin: все записи на определённую дату."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, client_name, phone, time_slot, status
            FROM appointments
            WHERE date = $1
            ORDER BY time_slot
            """,
            date,
        )
        return rows


async def get_all_active_appointments():
    """Все активные записи (для админа)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, client_name, phone, date, time_slot
            FROM appointments
            WHERE status = 'active'
            ORDER BY date, time_slot
            """,
        )
        return rows


async def get_booked_slots(date) -> list[str]:
    """Какие слоты уже заняты на дату — чтобы не показывать их."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT time_slot FROM appointments
            WHERE date = $1 AND status = 'active'
            """,
            date,
        )
        return [r["time_slot"] for r in rows]


async def get_upcoming_appointments(minutes_ahead: int = 60):
    """Записи, до которых осталось <= minutes_ahead минут.
    Нужно для напоминаний (scheduler)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, client_name, date, time_slot
            FROM appointments
            WHERE status = 'active'
              AND reminder_sent = FALSE
              AND (date + time_slot::time) <= (NOW() + INTERVAL '1 minute' * $1)
              AND (date + time_slot::time) > NOW()
            """,
            minutes_ahead,
        )
        return rows


async def mark_reminder_sent(appointment_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE appointments SET reminder_sent = TRUE WHERE id = $1",
            appointment_id,
        )
