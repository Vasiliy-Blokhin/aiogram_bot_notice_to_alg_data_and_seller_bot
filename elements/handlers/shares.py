from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from elements.module import value_validator
from source.settings.settings import SPLIT_SYM
from elements.message_builder import (
    certain_shares,
    shares_score_output_mesage,
    empty_output_message,
    shares_start_message,
    start_input_message,
    end_input_message,
    better_shares_output_mesage
)
from source.sql.main import SQLmain as sql
import source.sql.tables as tables


router = Router()


class SharesFilter(StatesGroup):
    start_value = State()
    end_value = State()


# Клавиатура для вывода акций.
@router.message(Command('акции'))
async def input_start_value(message: types.Message, state: FSMContext):
    """ Вывод сообщения - общей информации."""
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text='📊 Лучшие',
            callback_data='лучшие'
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text='📊 По параметру',
            callback_data='параметр'
        )
    )
    await message.answer('Выберите: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'параметр')
async def param_shares_button(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.reply(text=shares_start_message())
    await state.set_state(SharesFilter.start_value)
    await callback.message.answer(start_input_message())


@router.message(SharesFilter.start_value)
async def input_end_value(message: types.Message, state: FSMContext):
    await state.update_data(start_value=message.text)

    data = await state.get_data()
    if not await value_validator(message, state, data['start_value']):
        return await input_start_value(message, state)

    await state.set_state(SharesFilter.end_value)
    await message.answer(end_input_message())


@router.message(SharesFilter.end_value)
async def output_shares(message: types.Message, state: FSMContext):
    await state.update_data(end_value=message.text)

    data = await state.get_data()
    start_value = int(data['start_value'])

    if not await value_validator(message, state, data['end_value']):
        return await input_start_value(message, state)

    end_value = int(data['end_value'])
    if start_value > end_value:
        start_value, end_value = end_value, start_value
    await state.clear()

    shares = sql.get_all_data(tables.FilterData)

    builder = InlineKeyboardBuilder()
    max_f_score: int | float = 0
    min_f_score: int | float = 0
    counter = 0

    for share in shares:
        filter_score = share.get('FILTER_SCORE')
        if not isinstance(filter_score, int | float):
            continue

        if (
            filter_score >= start_value
            and filter_score <= end_value
            and counter <= 15
        ):
            counter += 1
            builder.add(
                types.InlineKeyboardButton(
                    text=share['SECID'],
                    callback_data='shares' + SPLIT_SYM + share['SECID']
                )
            )
            builder.adjust(4)

        if max_f_score < filter_score:
            max_f_score = filter_score
        if min_f_score > filter_score:
            min_f_score = filter_score

    if counter == 0:
        return await message.answer(
            text=empty_output_message()
        )
    return await message.answer(
        text=shares_score_output_mesage(
            start=start_value,
            end=end_value,
            max_score=max_f_score,
            min_score=min_f_score
        ),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.split(SPLIT_SYM)[0] == 'shares')
async def shares_button(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    share = callback.data.split(SPLIT_SYM)[1]
    await callback.message.answer(text=certain_shares(share))
#--------------------------------------------------------


@router.callback_query(F.data == 'лучшие')
async def better_shares_button(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    shares = sql.get_all_data(tables.CurrentScore)
    builder = InlineKeyboardBuilder()
    counter = 0

    for share in shares:

        counter += 1
        builder.add(
            types.InlineKeyboardButton(
                text=share['SECID'],
                callback_data='better' + SPLIT_SYM + share['SECID']
            )
        )
        builder.adjust(2)

    if counter == 0:
        return await callback.message.answer(
            text=empty_output_message()
        )
    return await callback.message.answer(
        text=better_shares_output_mesage(),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.split(SPLIT_SYM)[0] == 'better')
async def better_shares_result(callback: types.CallbackQuery):
    """ Вывод сообщения информации о возможных рисках."""
    share = callback.data.split(SPLIT_SYM)[1]
    await callback.message.answer(
        f'share - {share}\n'
        f'all data - {callback.data}'
    )
    await callback.message.answer(text=certain_shares(share))
    await callback.message.answer(text='check before')
