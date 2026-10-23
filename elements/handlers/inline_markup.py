from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from elements.message_builder import (
    risk_message,
    info_message,
    trades_statistic_message,
    backtest_message,
    evolve_message,
    reverse_message,
)
from source.sql.main import SQLmain as sql

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


# Клавиатура геномного и реверсивного алгоритмов.
@router.message(Command('алгоритмы'))
async def algorithms_keyboard(message: types.Message):
    """ Выбор алгоритма."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='🧬 Геномный', callback_data='algo_evolve'))
    builder.row(types.InlineKeyboardButton(text='🔄 Реверсивный', callback_data='algo_reverse'))
    builder.row(types.InlineKeyboardButton(text='🔍 Запустить поиск (1 ч)', callback_data='algo_evolve_search'))
    await message.answer('Выберите алгоритм: ', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'algo_evolve')
async def algo_evolve_callback(callback: types.CallbackQuery):
    """ Этапы, сигналы и сделки геномного алгоритма."""
    await callback.message.answer(text=evolve_message())
    await callback.answer()


@router.callback_query(F.data == 'algo_reverse')
async def algo_reverse_callback(callback: types.CallbackQuery):
    """ Режим, правила, журнал и сделки реверсивного алгоритма."""
    await callback.message.answer(text=reverse_message())
    await callback.answer()
#--------------------------------------------------------


# Часовая итерация геномного поиска по запросу: запрос в БД, его берёт демон iss_evolve.
SEARCH_MINUTES = 60


def request_search(chat_id: int) -> str:
    """ Поставить запрос на часовой поиск геномного алгоритма; текст ответа."""
    active = sql.query(
        "SELECT id, STATUS FROM evolve_requests WHERE STATUS IN ('new', 'running') ORDER BY id DESC LIMIT 1"
    )
    if active:
        status = active[0]['STATUS']
        return (f'🧬 Поиск уже {"идёт" if status == "running" else "в очереди"} '
                f'(запрос #{active[0]["id"]}). Сводки придут в бот отчётов.')
    try:
        sql.execute(
            "INSERT INTO evolve_requests (CREATED_AT, MINUTES, SOURCE, CHAT_ID, STATUS) "
            "VALUES (datetime('now', 'localtime'), :minutes, 'telegram', :chat_id, 'new')",
            {'minutes': SEARCH_MINUTES, 'chat_id': chat_id},
        )
    except Exception:
        return '⚠️ Движок ещё не обновлён: нет таблицы запросов поиска.'
    return (f'🧬 Запрос принят: поиск на {SEARCH_MINUTES} мин. начнётся в течение минуты '
            '(три этапа: новые гены, смешанный, доработка). Сводки этапов придут в бот отчётов.')


@router.message(Command('поиск'))
async def evolve_search_command(message: types.Message):
    """ Запуск часовой итерации геномного поиска."""
    await message.answer(request_search(message.chat.id))


@router.callback_query(F.data == 'algo_evolve_search')
async def evolve_search_button(callback: types.CallbackQuery):
    """ Кнопка «Запустить поиск» в клавиатуре алгоритмов."""
    await callback.message.answer(request_search(callback.message.chat.id))
    await callback.answer()
