from aiogram import types, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from elements.message_builder import (
    weights_message,
    trading_info_message,
    start_message,
    better_shares_info_message
)


router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Стартовый набор команд (сообщений).
    """
    builder = ReplyKeyboardBuilder()
    builder.row(  # Вывод информации о весах.
        types.KeyboardButton(text='/информация',)
    )
    builder.add(  # Вывод информации о весах.
        types.KeyboardButton(text='/веса',)
    )
    builder.row(  # Вывод информации о статистике.
        types.KeyboardButton(text='/статистика')
    )
    builder.add(  # Вывод информации о статусе торговли.
        types.KeyboardButton(text='/статус')
    )
    builder.row(  # Вывод информации о статусе торговли.
        types.KeyboardButton(text='/акции')
    )
    builder.add(  # Вывод информации о статусе торговли.
        types.KeyboardButton(text='/выборка')
    )
    await message.answer(  # Сообщение старт.
        start_message(message.from_user.first_name),
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@router.message(F.text.lower() == '/веса')
async def weights_button(message: types.Message):
    """ Вывод сообщения - общей информации."""
    await message.reply(weights_message())


@router.message(F.text.lower() == '/статус')
async def trading_info_button(message: types.Message):
    """ Вывод сообщения - общей информации."""
    await message.reply(trading_info_message())


@router.message(F.text.lower() == '/выборка')
async def better_share_button(message: types.Message):
    """ Вывод сообщения - общей информации."""
    await message.reply(better_shares_info_message())
