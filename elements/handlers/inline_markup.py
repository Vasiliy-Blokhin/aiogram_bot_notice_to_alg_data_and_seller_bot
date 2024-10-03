from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from elements.message_builder import (
    risk_message,
    info_message,
    last_statistic_message,
    all_statistic_message,
)

router = Router()


# Информационная клавиатура.
@router.message(Command('информация'))
async def info_keyboard(message: types.Message):
    """ Вывод сообщения - общей информации."""
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text='⚠️ риски',
            callback_data='риски'
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text='📊 Информация',
            callback_data='информация'
        )
    )
    await message.answer('Выберите: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'риски')
async def risk_button(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    await callback.message.answer(text=risk_message())


@router.callback_query(F.data == 'информация')
async def info_button(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    await callback.message.answer(text=info_message())
#--------------------------------------------------------

# Клавиатура для отображения статистики
@router.message(Command('статистика'))
async def statistic_keyboard(message: types.Message):
    """ Вывод сообщения - общей информации."""
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text='📝 Последняя итерация (лучшие)',
            callback_data='last_stat_max'
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text='📝 За все время (лучшие)',
            callback_data='all_stat_max'
        )
    )
    await message.answer('Укажите значение: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'last_stat_max')
async def last_statistic_max_callback(callback: types.CallbackQuery):
    """ Вывод сообщения псоледней статистики."""
    await callback.message.answer(text=last_statistic_message())


@router.callback_query(F.data == 'all_stat_max')
async def all_statistic__max_callback(callback: types.CallbackQuery):
    """ Вывод сообщения статистики за все время."""
    await callback.message.answer(text=all_statistic_message())
#--------------------------------------------------------
