""" Основной исполняемый файл (запуск бота). """
import asyncio
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from source.settings.settings import TOKEN, ALLOWED_USERS, REPORT_TIME, TIMEZONE, handler
from source.sql.main import SQLmain as sql
from elements.message_builder import daily_report_message
from elements.handlers import (
    reply_markup,
    inline_markup,
)


logger = logging.getLogger(name=__name__)  # Запуск логга проекта.
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


async def daily_report(bot: Bot) -> None:
    """ Раз в будний день после REPORT_TIME рассылает итоги дня подписчикам (/start)."""
    while True:
        try:
            now = datetime.now(ZoneInfo(TIMEZONE))
            today = now.date().isoformat()
            if (
                now.weekday() < 5
                and now.hour + now.minute / 100 >= REPORT_TIME
                and sql.get_state('last_report') != today
            ):
                text = daily_report_message(now.date())
                for chat_id in sql.subscribers():
                    try:
                        await bot.send_message(chat_id, text)
                    except Exception as error:
                        logger.error(f'Отчёт в {chat_id}: {error}')
                sql.set_state('last_report', today)
                logger.info('Дневной отчёт отправлен')
        except Exception as error:
            logger.exception(error)
        await asyncio.sleep(60)


async def main() -> None:
    """ Выполнение основной части работы бота."""
    if not TOKEN:
        raise SystemExit('Задайте BOT_TOKEN в .env')
    sql.create_bot_tables()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    if ALLOWED_USERS:
        for router in (reply_markup.router, inline_markup.router):
            router.message.filter(F.from_user.id.in_(ALLOWED_USERS))
            router.callback_query.filter(F.from_user.id.in_(ALLOWED_USERS))
    dp.include_routers(
        reply_markup.router,
        inline_markup.router,
    )
    asyncio.create_task(daily_report(bot))
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
