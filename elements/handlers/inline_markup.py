from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from elements.message_builder import (
    risk_message,
    info_message,
    trades_statistic_message,
    backtest_message,
)

router = Router()


# Информационная клавиатура.
@router.message(Command('информация'))
async def info_keyboard(message: types.Message):
    """ Вывод сообщения - общей информации."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='⚠️ Риски', callback_data='риски'))
    builder.row(types.InlineKeyboardButton(text='📊 Информация', callback_data='информация'))
    await message.answer('Выберите: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'риски')
async def risk_button(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    await callback.message.answer(text=risk_message())
    await callback.answer()


@router.callback_query(F.data == 'информация')
async def info_button(callback: types.CallbackQuery):
    """ Вывод сообщения общей информации."""
    await callback.message.answer(text=info_message())
    await callback.answer()
#--------------------------------------------------------


# Клавиатура для отображения статистики
@router.message(Command('статистика'))
async def statistic_keyboard(message: types.Message):
    """ Выбор вида статистики."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='💼 Сделки исполнителя', callback_data='stat_trades'))
    builder.row(types.InlineKeyboardButton(text='🧪 Бэктест', callback_data='stat_backtest'))
    await message.answer('Укажите значение: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'stat_trades')
async def trades_statistic_callback(callback: types.CallbackQuery):
    """ Фактические результаты сделок."""
    await callback.message.answer(text=trades_statistic_message())
    await callback.answer()


@router.callback_query(F.data == 'stat_backtest')
async def backtest_callback(callback: types.CallbackQuery):
    """ Результаты бэктеста."""
    await callback.message.answer(text=backtest_message())
    await callback.answer()
#--------------------------------------------------------
