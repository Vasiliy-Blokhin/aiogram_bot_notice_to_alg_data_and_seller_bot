from aiogram import types, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from source.sql.main import SQLmain as sql
from elements.message_builder import (
    start_message,
    signals_message,
    portfolio_message,
    services_message,
    daily_report_message,
    strategies_message,
)


router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Стартовый набор команд (сообщений) + подписка на отчёты и уведомления о сделках.
    """
    sql.add_subscriber(message.chat.id, message.from_user.full_name)
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text='/сигналы'))
    builder.add(types.KeyboardButton(text='/портфель'))
    builder.row(types.KeyboardButton(text='/статистика'))
    builder.add(types.KeyboardButton(text='/статус'))
    builder.row(types.KeyboardButton(text='/отчёт'))
    builder.add(types.KeyboardButton(text='/стратегии'))
    builder.row(types.KeyboardButton(text='/режим'))
    builder.add(types.KeyboardButton(text='/запуск'))
    builder.row(types.KeyboardButton(text='/алгоритмы'))
    builder.add(types.KeyboardButton(text='/информация'))
    await message.answer(  # Сообщение старт.
        start_message(message.from_user.first_name),
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@router.message(F.text.lower() == '/сигналы')
async def signals_button(message: types.Message):
    """ Сигналы по последнему закрытию."""
    await message.reply(signals_message())


@router.message(F.text.lower() == '/портфель')
async def portfolio_button(message: types.Message):
    """ Позиции исполнителя."""
    await message.reply(portfolio_message())


@router.message(F.text.lower() == '/статус')
async def services_button(message: types.Message):
    """ Состояние сервисов."""
    await message.reply(services_message())


@router.message(F.text.lower().in_({'/отчёт', '/отчет'}))
async def report_button(message: types.Message):
    """ Итоги сегодняшнего дня (то же, что приходит автоматически в REPORT_TIME)."""
    await message.reply(daily_report_message())


@router.message(F.text.lower() == '/стратегии')
async def strategies_button(message: types.Message):
    """ Статистика стратегий и распределение капитала."""
    await message.reply(strategies_message())
