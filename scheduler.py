import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import db

logger = logging.getLogger(__name__)

# scheduler instance — создаётся один раз при старте
scheduler = AsyncIOScheduler()


def setup_scheduler(bot: Bot):
    """Настраиваем джобы для напоминаний.
    Проверяем каждые 5 минут, нет ли записей в ближайший час."""

    async def check_reminders():
        """Job: ищем записи до которых осталось меньше часа,
        отправляем reminder пользователю."""
        try:
            upcoming = await db.get_upcoming_appointments(minutes_ahead=60)
            for apt in upcoming:
                try:
                    text = (
                        f"🔔 <b>Напоминание!</b>\n\n"
                        f"Через ~1 час у вас запись:\n"
                        f"👤 {apt['client_name']}\n"
                        f"📅 {apt['date'].strftime('%d.%m.%Y')} в {apt['time_slot']}\n\n"
                        f"Не забудьте!"
                    )
                    await bot.send_message(
                        chat_id=apt["user_id"],
                        text=text,
                        parse_mode="HTML"
                    )
                    await db.mark_reminder_sent(apt["id"])
                    logger.info(f"Reminder sent for appointment #{apt['id']} to user {apt['user_id']}")
                except Exception as e:
                    # если не удалось отправить (юзер заблокировал бота и т.д.)
                    logger.warning(f"Failed to send reminder for #{apt['id']}: {e}")
        except Exception as e:
            logger.error(f"Error in check_reminders job: {e}")

    # запускаем проверку каждые 5 минут
    scheduler.add_job(check_reminders, "interval", minutes=5, id="reminders_check")
    scheduler.start()
    logger.info("Scheduler started — checking reminders every 5 minutes")
