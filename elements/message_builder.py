import json
import logging
from datetime import date, datetime

from source.settings.settings import handler, TRADING_MODE
from source.sql.main import SQLmain as sql

logger = logging.getLogger(name=__name__)  # Запуск логга проекта.
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

STRATEGY_TITLES = {
    'model': 'Модель',
    'mean_reversion': 'Откат RSI(2)',
    'momentum': 'Импульс 5 дн.',
    'breakout': 'Пробой максимума',
    'trend_pullback': 'Откат в тренде',
    'squeeze': 'Сжатие волатильности',
    'capitulation': 'Отскок после паники',
}
STATUS_ICONS = {'approved': '🟢', 'used': '✅', 'rejected': '⛔', 'skipped': '⚪', 'expired': '⌛'}


def signals_message():
    """ Сигналы по последнему закрытию."""
    rows = sql.query(
        'SELECT * FROM signals WHERE "SIGNAL_DATE" = (SELECT MAX("SIGNAL_DATE") FROM signals) '
        'ORDER BY "EXPECTED_RETURN" DESC'
    )
    if not rows:
        return empty_message()
    message = f'📈 Сигналы по закрытию {rows[0]["SIGNAL_DATE"]}:\n\n'
    for row in rows:
        message += (
            f'{STATUS_ICONS.get(row["STATUS"], "🔸")} <b>{row["SECID"]}</b> {row["SHORTNAME"] or ""}\n'
            f'   вероятность {row["PROBABILITY"]:.0%}, ожидание {row["EXPECTED_RETURN"]:+.2%}\n'
            f'   стоп {row["STOP_PRICE"]:.4g} / тейк {row["TAKE_PRICE"]:.4g}, '
            f'удержание {row["HOLD_DAYS"]} дн.\n'
        )
        if row['AI_DECISION'] not in (None, 'n/a'):
            message += f'   🤖 ИИ: {row["AI_DECISION"]} ({row["AI_CONFIDENCE"]}%) {row["AI_REASON"] or ""}\n'
        message += '\n'
    return message


def portfolio_message():
    """ Открытые позиции и счёт исполнителя."""
    positions = sql.query(
        'SELECT * FROM positions WHERE "MODE" = :mode AND "STATUS" <> :closed AND "STATUS" <> :cancelled',
        {'mode': TRADING_MODE, 'closed': 'closed', 'cancelled': 'cancelled'},
    )
    account = sql.query('SELECT * FROM paper_account LIMIT 1') if TRADING_MODE == 'paper' else []
    message = f'💼 Портфель ({TRADING_MODE}):\n\n'
    if account:
        message += f'Свободные средства: {account[0]["CASH"]:,.0f} ₽ (старт {account[0]["START_CASH"]:,.0f} ₽)\n\n'
    if not positions:
        return message + 'Открытых позиций нет.'
    for row in positions:
        message += (
            f'🔸 <b>{row["SECID"]}</b>: {row["QUANTITY"]} шт. по {row["ENTRY_PRICE"]:.4g}\n'
            f'   стоп {row["STOP_PRICE"]:.4g} / тейк {row["TAKE_PRICE"]:.4g}, выход {row["EXIT_DATE"]}\n'
        )
    return message


def trades_statistic_message():
    """ Фактические (paper/live) результаты закрытых сделок."""
    rows = sql.query(
        'SELECT "PNL", "PNL_PCT", "EXIT_REASON" FROM positions '
        'WHERE "MODE" = :mode AND "STATUS" = :closed',
        {'mode': TRADING_MODE, 'closed': 'closed'},
    )
    if not rows:
        return '📊 Закрытых сделок пока нет.'
    wins = [row for row in rows if row['PNL'] > 0]
    total = sum(row['PNL'] for row in rows)
    average = sum(row['PNL_PCT'] for row in rows) / len(rows)
    reasons = {}
    for row in rows:
        reasons[row['EXIT_REASON']] = reasons.get(row['EXIT_REASON'], 0) + 1
    return (
        f'📊 Сделки исполнителя ({TRADING_MODE}):\n\n'
        f'  👉 Сделок: {len(rows)}, прибыльных {len(wins) / len(rows):.0%}\n'
        f'  👉 Средняя сделка: {average:+.2%}\n'
        f'  👉 Итог: {total:+,.0f} ₽\n'
        f'  👉 Выходы: ' + ', '.join(f'{k} — {v}' for k, v in reasons.items())
    )


def backtest_message():
    """ Последний бэктест по каждой стратегии."""
    rows = sql.query(
        'SELECT * FROM backtest_runs WHERE id IN '
        '(SELECT MAX(id) FROM backtest_runs GROUP BY "STRATEGY") ORDER BY "SHARPE" DESC'
    )
    if not rows:
        return '📊 Бэктест ещё не запускался.'
    message = f'🧪 Бэктест {rows[0]["PERIOD_START"]} — {rows[0]["PERIOD_END"]}:\n\n'
    for row in rows:
        message += (
            f'<b>{row["STRATEGY"]}</b>: сделок {row["TRADES"]}, прибыльных {row["WIN_RATE"]:.0%}, '
            f'средняя {row["AVG_TRADE"]:+.2%}, итог {row["TOTAL_RETURN"]:+.1%}, '
            f'просадка {row["MAX_DRAWDOWN"]:.1%}, Sharpe {row["SHARPE"]:.2f}\n\n'
        )
    return message


def services_message():
    """ Когда сервисы последний раз подавали признаки жизни."""
    rows = sql.query('SELECT * FROM activity')
    if not rows:
        return '⚙️ Сервисы ещё не запускались.'
    message = '⚙️ Состояние сервисов:\n\n'
    for row in rows:
        last = datetime.fromisoformat(str(row['LAST_TIME']))
        minutes = (datetime.now() - last).total_seconds() / 60
        icon = '🟢' if minutes < 10 else '🔴'
        message += f'{icon} {row["SERVICE"]}: {minutes:.0f} мин. назад\n'
    return message


def allocation_text():
    """ Текущее распределение капитала по стратегиям."""
    rows = sql.query('SELECT * FROM strategy_selection ORDER BY "DATE" DESC LIMIT 1')
    if not rows:
        return '🧭 Распределение по стратегиям ещё не рассчитано.\n'
    allocation = json.loads(rows[0].get('ALLOCATION') or '{}')
    if not allocation:
        return f'🧭 Торговля приостановлена: {rows[0]["REASON"]}\n'
    return '🧭 Доли капитала: ' + ', '.join(
        f'{STRATEGY_TITLES.get(name, name)} {share:.0%}' for name, share in allocation.items()
    ) + '\n'


def strategies_message():
    """ Теневая статистика стратегий за день/неделю/месяц и текущее распределение."""
    rows = sql.query(
        'SELECT * FROM strategy_stats WHERE "DATE" = (SELECT MAX("DATE") FROM strategy_stats)'
    )
    if not rows:
        return '📊 Статистика стратегий ещё не рассчитана.'
    table = {}
    for row in rows:
        table.setdefault(row['STRATEGY'], {})[row['PERIOD']] = row
    order = sorted(table, key=lambda name: -table[name]['week']['RETURN'])
    message = (
        f'📊 <b>Стратегии</b> (теневая торговля, по {rows[0]["DATE"]})\n'
        'результат в % капитала (число сделок): день / неделя / месяц\n\n'
    )
    for name in order:
        periods = table[name]
        message += f'<b>{STRATEGY_TITLES.get(name, name)}</b>\n   ' + ' / '.join(
            f'{periods[p]["RETURN"]:+.2%} ({periods[p]["TRADES"]})' for p in ('day', 'week', 'month')
        ) + '\n'
    return message + '\n' + allocation_text()


def daily_report_message(day: date | None = None):
    """ Итоги торгового дня: сделки, результат, капитал, сигналы на завтра."""
    day = day or date.today()
    params = {'mode': TRADING_MODE, 'start': f'{day} 00:00:00', 'end': f'{day} 23:59:59'}
    opened = sql.query(
        'SELECT * FROM positions WHERE "MODE" = :mode AND "ENTRY_TIME" BETWEEN :start AND :end',
        params,
    )
    closed = sql.query(
        'SELECT * FROM positions WHERE "MODE" = :mode AND "STATUS" = :closed '
        'AND "EXIT_TIME" BETWEEN :start AND :end',
        {**params, 'closed': 'closed'},
    )
    all_closed = sql.query(
        'SELECT "PNL" FROM positions WHERE "MODE" = :mode AND "STATUS" = :closed',
        {'mode': TRADING_MODE, 'closed': 'closed'},
    )
    open_positions = sql.query(
        'SELECT * FROM positions WHERE "MODE" = :mode AND "STATUS" = :open',
        {'mode': TRADING_MODE, 'open': 'open'},
    )
    account = sql.query('SELECT * FROM paper_account LIMIT 1') if TRADING_MODE == 'paper' else []

    message = f'📅 <b>Итоги дня {day:%d.%m.%Y}</b> ({TRADING_MODE})\n\n'
    if opened:
        message += '🟢 Куплено:\n' + ''.join(
            f'   {row["SECID"]}: {row["QUANTITY"]} шт. по {row["ENTRY_PRICE"]:.4g}\n' for row in opened
        )
    if closed:
        message += '🔴 Продано:\n' + ''.join(
            f'   {row["SECID"]} ({row["EXIT_REASON"]}): {row["PNL"]:+,.0f} ₽ ({row["PNL_PCT"]:+.2%})\n'
            for row in closed
        )
        message += f'   Результат дня: {sum(row["PNL"] for row in closed):+,.0f} ₽\n'
    if not opened and not closed:
        message += 'Сделок сегодня не было.\n'

    invested = sum(row['QUANTITY'] * row['ENTRY_PRICE'] for row in open_positions)
    message += f'\n💼 Открыто позиций: {len(open_positions)} на {invested:,.0f} ₽\n'
    if account:
        cash, start_cash = account[0]['CASH'], account[0]['START_CASH']
        equity = cash + invested
        message += (
            f'💰 Капитал (позиции по цене входа): {equity:,.0f} ₽, свободно {cash:,.0f} ₽\n'
            f'📈 С начала: {equity - start_cash:+,.0f} ₽ ({equity / start_cash - 1:+.2%})\n'
        )
    if all_closed:
        wins = sum(1 for row in all_closed if row['PNL'] > 0)
        message += (
            f'📊 Всего сделок: {len(all_closed)}, прибыльных {wins / len(all_closed):.0%}, '
            f'итог {sum(row["PNL"] for row in all_closed):+,.0f} ₽\n'
        )
    signals = sql.query(
        'SELECT "SECID", "STATUS" FROM signals '
        'WHERE "SIGNAL_DATE" = (SELECT MAX("SIGNAL_DATE") FROM signals)'
    )
    approved = [row['SECID'] for row in signals if row['STATUS'] == 'approved']
    message += '\n' + allocation_text()
    message += '🔭 Сигналы: ' + (', '.join(approved) if approved else 'нет')
    return message


# Системные сообщения.
def empty_message():
    return '📝 Сигналов пока нет.'


def start_message(name):
    """ Стартовое сообщение."""
    return (
        f'👋 Приветствую, {name}!\n\n'
        '💰📈 Бот показывает сигналы алгоритма на 1–2 дня по акциям Мосбиржи, '
        'портфель исполнителя и статистику.\n\n'
        'Перед работой ознакомьтесь с информацией "/информация" ❗️'
    )


def info_message():
    """ Сообщение общей информации."""
    return (
        '📊 Как это работает\n\n'
        '💸 Каждое утро движок загружает дневные свечи Мосбиржи, модель (логистическая '
        'регрессия, переобучается на скользящем окне) оценивает вероятность прибыли '
        'сделки на 1–2 дня, локальный ИИ проверяет кандидатов на явные риски '
        '(отсечки дивидендов, негатив в новостях).\n\n'
        '⚠️ Это не инвестиционная рекомендация. Мы не несём ответственности за '
        'последствия ваших решений.\n\n'
        '✍️ Автор (разработчик): @Vasilianin'
    )


def risk_message():
    """ Сообщение о возможных рисках."""
    return (
        '📊 Возможные риски (учтите их при работе).\n\n'
        '⚠️ Данные ISS публичные и идут с задержкой 15 минут.\n'
        '⚠️ Результаты бэктеста не гарантируют будущей доходности.\n'
        '⚠️ Стоп-лосс исполняется по рыночной цене и при гэпе может сработать хуже уровня.'
    )
