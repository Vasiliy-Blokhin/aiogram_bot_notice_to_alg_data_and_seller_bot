""" Кнопки «⚙️ Запуск» (задачи движка через очередь task_requests) и «🧭 Режим» рынка."""
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from elements.regime_messages import regime_message, blind_message, tasks_message
from source.sql.main import SQLmain as sql

router = Router()
TASK_BUTTONS = [
    ('evolve', '🧬 Поиск генов (1 ч)'),
    ('evolve_regimes', '🧬 Поиск по режимам (1 ч)'),
    ('blind', '🕶 Слепой тест 1 мес.–5 лет'),
    ('blind_fast', '🕶 Слепой тест быстро (без генов)'),
    ('pools', '📦 Пересобрать пулы режимов'),
    ('backtest', '🧪 Бэктест'),
    ('update', '🔄 Обновить данные')
]
TITLES = dict(TASK_BUTTONS)

def enqueue(kind: str, chat_id: int) -> str:
    """Добавляем задачу в очередь."""
    active = sql.query(
        "SELECT id, STATUS FROM task_requests WHERE KIND = :k AND STATUS IN ('new', 'running') ORDER BY id DESC LIMIT 1",
        {'k': kind}
    )
    if active:
        status = active[0]['STATUS']
        task_id = active[0]['id']
        if status == 'running':
            return f'⏳ Уже идёт (#{task_id}).'
        else:
            return f'⏳ Уже в очереди (#{task_id}).'
    try:
        sql.execute(
            "INSERT INTO task_requests (CREATED_AT, KIND, CHAT_ID, STATUS) VALUES (datetime('now', 'localtime'), :k, :c, 'new')",
            {'k': kind, 'c': chat_id}
        )
    except Exception:
        return '⚠️ Движок ещё не обновлён: нет очереди задач.'
    return f'✅ {TITLES[kind]}: принято. О запуске и результате напишу в бот отчётов.'

@router.message(Command('запуск'))
async def launch(message: types.Message):
    """Отправляем клавиатуру с задачами."""
    builder = InlineKeyboardBuilder()
    for kind, text in TASK_BUTTONS:
        builder.button(text=text, callback_data=f'task:{kind}')
    builder.button(text='📋 Очередь', callback_data='task_list')
    builder.adjust(1)
    await message.answer('Что запустить?', reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith('task:'))
async def task_callback(callback: types.CallbackQuery):
    """Обрабатываем выбор задачи."""
    kind = callback.data.split(':', 1)[1]
    if kind not in TITLES:
        await callback.answer('Неизвестная задача', show_alert=True)
        return
    await callback.message.answer(enqueue(kind, callback.message.chat.id))
    await callback.answer()

@router.callback_query(F.data == 'task_list')
async def task_list(callback: types.CallbackQuery):
    """Показываем список задач."""
    await callback.message.answer(tasks_message())
    await callback.answer()

@router.message(Command('режим'))
async def regime(message: types.Message):
    """Клавиатура режима."""
    builder = InlineKeyboardBuilder()
    builder.button(text='🕶 Итоги слепого теста', callback_data='blind_result')
    await message.answer(regime_message(), reply_markup=builder.as_markup())

@router.callback_query(F.data == 'blind_result')
async def blind_result(callback: types.CallbackQuery):
    """Показываем результаты слепого теста."""
    await callback.message.answer(blind_message())
    await callback.answer()
