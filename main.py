""" Основной исполняемый файл (запуск бота). """
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from source.settings.settings import TOKEN, handler
from elements.handlers import (
    reply_markup,
    inline_markup,
    shares
)


logger = logging.getLogger(name=__name__)  # Запуск логга проекта.
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


async def main() -> None:
    """ Выполнение основной части работы бота."""
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_routers(
        reply_markup.router,
        inline_markup.router,
        shares.router
    )
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
