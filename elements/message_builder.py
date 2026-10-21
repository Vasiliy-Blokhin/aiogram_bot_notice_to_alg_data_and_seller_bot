import json
import logging
from html import escape
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
    'reverse': 'Реверсивный (опыт + новости)',
    'rotation': 'Ротация фондов',
}
STATUS_ICONS = {'approved': '🟢', 'used': '✅', 'rejected': '⛔', 'skipped': '⚪', 'expired': '⌛'}
EVOLVE_LIVE_STAGES = 3  # столько лучших этапов движок держит действующими (EVOLVE_LIVE_STAGES движка)
ACTIVE_STATUSES = ('opening', 'open', 'closing')
EXIT_TITLES = {
    'stop': 'стоп', 'take': 'тейк', 'time': 'по времени', 'manual': 'вручную',
    'rebalance': 'ребалансировка', 'market': 'падение рынка', 'review': 'ухудшение динамики',
    'stale': 'мала вероятность роста', 'max_age': 'слишком долго открыта',
}
REVERSE_NOTABLE = ('promote', 'death', 'params', 'mode', 'reflection')


def exit_title(reason: str | None) -> str:
    return EXIT_TITLES.get(reason, reason or '—')


def strategy_title(name: str | None) -> str:
    """ Название стратегии (в т.ч. составной: 'momentum+reverse', 'evolve:12+15')."""
    titles = []
    for part in (name or '').split('+'):
        if part.startswith('evolve:'):
            titles.append(f'Геномный этап #{part[7:]}')
        elif part.isdigit():
            titles.append(f'#{part}')
        else:
            titles.append(STRATEGY_TITLES.get(part, part))
    return ' + '.join(titles)


def atoms_text(atoms_json: str) -> str:
    """ Условия правила реверсивного алгоритма: [[признак, знак, порог], ...] -> текст."""
    return ' и '.join(f'{f} {op} {v:.4g}' for f, op, v in json.loads(atoms_json))


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
            f'   🧩 {strategy_title(row["STRATEGY"])}, доля {row["WEIGHT"] or 0:.1%}\n'
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
            f'🔸 <b>{row["SECID"]}</b>: {row["QUANTITY"]} шт. по {row["ENTRY_PRICE"]:.4g} '
            f'[{strategy_title(row["STRATEGY"])}]\n'
            + (f'   стоп {row["STOP_PRICE"]:.4g} / тейк {row["TAKE_PRICE"]:.4g}, выход {row["EXIT_DATE"]}\n'
               if row['STOP_PRICE'] is not None else '   без стопа и срока (портфель фондов)\n')
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
        f'  👉 Выходы: ' + ', '.join(f'{exit_title(k)} — {v}' for k, v in reasons.items())
    )


def backtest_message():
    """ Последний бэктест по каждой стратегии."""
    rows = sql.query(
        'SELECT * FROM backtest_runs WHERE id IN '
        '(SELECT MAX(id) FROM backtest_runs GROUP BY "STRATEGY") ORDER BY "SHARPE" DESC'
    )
    if not rows:
        return '📊 Бэктест ещё не запускался.'
    # Этапы геномного меняются: показываем только прогнанные в последнем бэктесте.
    last_end = max(str(row['PERIOD_END']) for row in rows)
    rows = [row for row in rows
            if not row['STRATEGY'].startswith('evolve:') or str(row['PERIOD_END']) == last_end]
    message = f'🧪 Бэктест {rows[0]["PERIOD_START"]} — {rows[0]["PERIOD_END"]}:\n\n'
    for row in rows:
        note = ' (без архива новостей)' if row['STRATEGY'] == 'reverse' else ''
        message += (
            f'<b>{strategy_title(row["STRATEGY"])}</b>{note}: сделок {row["TRADES"]}, прибыльных {row["WIN_RATE"]:.0%}, '
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


def pool_rows() -> list[dict]:
    """ Пул стратегий последнего дня, по убыванию приоритета."""
    return sql.query(
        'SELECT * FROM strategy_pool WHERE "DATE" = (SELECT MAX("DATE") FROM strategy_pool) '
        'ORDER BY "PRIORITY" DESC'
    )


def pool_text() -> str:
    """ Состав пула и приоритеты: бэктест и исполненные сделки."""
    rows = pool_rows()
    if not rows:
        return '⭐ Пул стратегий ещё не рассчитан.\n'
    message = (f'⭐ <b>Пул стратегий</b> ({rows[0]["DATE"]}): приоритет '
               '(средняя сделка бэктеста; исполненных сделок)\n')
    for row in rows:
        backtest = (f'{row["BT_AVG"]:+.2%}, {row["BT_TRADES"]} сд.' if row['BT_AVG'] is not None
                    else 'нет бэктеста')
        real = (f'; исполнено {row["REAL_TRADES"]}, ср. {row["REAL_AVG"]:+.2%}' if row['REAL_TRADES']
                else '')
        message += f'   ×{row["PRIORITY"]:.2f} {strategy_title(row["STRATEGY"])} ({backtest}{real})\n'
    return message


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
    return message + '\n' + allocation_text() + '\n' + pool_text()


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
            f'   {row["SECID"]} ({exit_title(row["EXIT_REASON"])}): {row["PNL"]:+,.0f} ₽ ({row["PNL_PCT"]:+.2%})\n'
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
    message += algorithms_brief()
    top = pool_rows()[:3]
    if top:
        message += '⭐ Приоритет: ' + ', '.join(
            f'{strategy_title(row["STRATEGY"])} ×{row["PRIORITY"]:.2f}' for row in top) + '\n'
    message += '🔭 Сигналы: ' + (', '.join(approved) if approved else 'нет')
    return message


def algo_positions_text(pattern: str) -> str:
    """ Сделки исполнителя по стратегиям, подходящим под LIKE-шаблон."""
    rows = sql.query(
        'SELECT "STATUS", "PNL" FROM positions WHERE "MODE" = :mode AND "STRATEGY" LIKE :pattern',
        {'mode': TRADING_MODE, 'pattern': pattern},
    )
    if not rows:
        return f'💼 Позиций исполнителя ({TRADING_MODE}) ещё не было.\n'
    active = sum(1 for row in rows if row['STATUS'] in ACTIVE_STATUSES)
    closed = [row for row in rows if row['STATUS'] == 'closed']
    message = f'💼 Позиции ({TRADING_MODE}): открыто {active}, закрыто {len(closed)}'
    if closed:
        wins = sum(1 for row in closed if row['PNL'] > 0)
        total = sum(row['PNL'] for row in closed)
        message += f', прибыльных {wins / len(closed):.0%}, итог {total:+,.0f} ₽'
    return message + '\n'


def last_signals(pattern: str) -> list[dict]:
    """ Сигналы последнего дня по стратегиям, подходящим под LIKE-шаблон."""
    return sql.query(
        'SELECT "SECID", "STRATEGY", "STATUS", "WEIGHT" FROM signals '
        'WHERE "SIGNAL_DATE" = (SELECT MAX("SIGNAL_DATE") FROM signals) AND "STRATEGY" LIKE :pattern',
        {'pattern': pattern},
    )


def reverse_state() -> dict:
    """ Состояние жизненного цикла реверсивного алгоритма."""
    rows = sql.query(
        'SELECT "PARAMS" FROM algo_params WHERE "KIND" = :kind AND "ACTIVE" ORDER BY id DESC LIMIT 1',
        {'kind': 'reverse_state'},
    )
    return json.loads(rows[0]['PARAMS']) if rows else {}


def percent(value) -> str:
    return f'{value:+.1%}' if value is not None else '—'


def evolve_message():
    """ Геномный (абстрактный) алгоритм: этапы, поиск, сигналы и сделки."""
    stages = sql.query('SELECT * FROM evolve_stages WHERE "ACTIVE" ORDER BY "SCORE" DESC LIMIT :n',
                       {'n': EVOLVE_LIVE_STAGES})
    if not stages:
        return '🧬 Геномный алгоритм ещё не нашёл ни одного этапа.'
    runs = sql.query('SELECT COUNT(*) AS n, MAX("CREATED_AT") AS last FROM evolve_runs')
    total = runs[0]['n'] if runs else 0
    last = str(runs[0]['last'] or '—')[:16] if runs else '—'
    message = (
        '🧬 <b>Геномный (абстрактный) алгоритм</b>\n'
        'Случайный поиск геномов по воскресеньям; этап фиксируется при CAGR ≥ 5% '
        'и на периоде поиска, и на отложенном последнем году.\n\n'
        f'Проверено геномов: {total}, последний поиск: {last}\n'
        f'Действующие этапы — только топ-{EVOLVE_LIVE_STAGES}: {len(stages)} '
        '(▶️, исполнитель берёт их только в paper)\n\n'
    )
    for stage in stages:
        genome = json.loads(stage['GENOME'])
        exit_gene, size = genome['exit'][0], genome['size'][0]
        message += (
            f'▶️ <b>#{stage["id"]}</b>: '
            f'поиск {percent(stage["CAGR"])} (DD {stage["MAX_DRAWDOWN"]:.1%}, сделок {stage["TRADES"]}), '
            f'отложенная {percent(stage["HOLD_CAGR"])}\n'
            f'   выход: удержание {exit_gene["hold"]} дн., стоп {exit_gene["stop"]:g} / '
            f'тейк {exit_gene["take"]:g} ATR{", на открытии" if exit_gene.get("at_open") else ""}; '
            f'до {size["top"]} бумаг\n'
        )
    signals = last_signals('evolve:%')
    message += '\n🔭 Сигналы последнего дня: ' + (
        ', '.join(f'{row["SECID"]} ({strategy_title(row["STRATEGY"])}, {row["WEIGHT"]:.1%})'
                  for row in signals)
        or 'нет (фильтры этапов не пропустили бумаги)'
    )
    return message + '\n' + algo_positions_text('evolve:%')


def reverse_message():
    """ Реверсивный алгоритм: режим, правила, выбор, журнал и сделки."""
    state = reverse_state()
    counts = {row['STATUS']: row['n'] for row in sql.query(
        'SELECT "STATUS", COUNT(*) AS n FROM reverse_rules GROUP BY "STATUS"')}
    if not state and not counts:
        return '🔄 Реверсивный алгоритм ещё не запускался.'
    news = state.get('news_weight')
    news_text = f'{news:+.4f}' if isinstance(news, (int, float)) else '—'
    mode = ('🟢 торгует' if state.get('trading')
            else '🌑 в тени (своя история за 63 дн. пока не в плюсе — сделки виртуальные)')
    message = (
        '🔄 <b>Реверсивный алгоритм</b> (опыт + новости)\n'
        'Правила выводятся из исходов прошлых сделок и торгуют только после подтверждения '
        'вне выборки; новости оценивает qwen36, ночью gpt-oss-20b разбирает итоги.\n\n'
        f'Режим: {mode}\n'
        f'Правила: живых {counts.get("live", 0)}, кандидатов {counts.get("candidate", 0)}, '
        f'умерших {counts.get("dead", 0)}; строгость {state.get("level", "—")}, '
        f'вес новостей {news_text}\n'
        f'Прожит день: {state.get("last_day", "—")}\n'
    )
    rules = sql.query(
        'SELECT "ATOMS", "OOS_N", "OOS_MEAN" FROM reverse_rules '
        'WHERE "STATUS" = :status ORDER BY "POST" DESC LIMIT 5',
        {'status': 'live'},
    )
    if rules:
        message += '\n📐 Живые правила:\n' + ''.join(
            f'   • {escape(atoms_text(row["ATOMS"]))} — вне выборки {row["OOS_N"] or 0} дн., '
            f'средняя {row["OOS_MEAN"] or 0:+.2%}\n' for row in rules)
    picks = sql.query(
        'SELECT "DATE", "SECID", "REAL" FROM reverse_picks '
        'WHERE "DATE" = (SELECT MAX("DATE") FROM reverse_picks)'
    )
    if picks:
        message += f'\n🎯 Выбор по закрытию {picks[0]["DATE"]}: ' + ', '.join(
            row['SECID'] + ('' if row['REAL'] else ' (тень)') for row in picks) + '\n'
    kinds = ', '.join(f"'{kind}'" for kind in REVERSE_NOTABLE)
    journal = sql.query(
        f'SELECT "DATE", "KIND", "TEXT" FROM reverse_journal '
        f'WHERE "KIND" IN ({kinds}) ORDER BY id DESC LIMIT 5'
    )
    if journal:
        message += '\n📓 Журнал:\n' + ''.join(
            f'   {row["DATE"]} {row["KIND"]}: {escape(row["TEXT"][:200])}\n' for row in journal)
    return message + '\n' + algo_positions_text('%reverse%')


def algorithms_brief() -> str:
    """ Строки о геномном и реверсивном алгоритмах для дневного отчёта."""
    stages = sql.query('SELECT COUNT(*) AS n FROM evolve_stages WHERE "ACTIVE"')
    count = min(stages[0]['n'], EVOLVE_LIVE_STAGES) if stages else 0
    evolve = [row['SECID'] for row in last_signals('evolve:%')]
    reverse = [row['SECID'] for row in last_signals('%reverse%')]
    mode = 'торгует' if reverse_state().get('trading') else 'в тени'
    return (
        f'🧬 Геномный: этапов {count} (топ-{EVOLVE_LIVE_STAGES}), сигналы: {", ".join(evolve) or "нет"}\n'
        f'🔄 Реверсивный: {mode}, сигналы: {", ".join(reverse) or "нет"}\n'
    )


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
        '🧬 Геномный алгоритм сам ищет комбинации фильтров, оценок и правил выхода '
        '(случайная эволюция геномов) и торгует лучшими найденными этапами.\n\n'
        '🔄 Реверсивный алгоритм выводит правила из исходов прошлых сделок, учитывает '
        'новости и сам себя корректирует; торгует, только когда его история в плюсе.\n\n'
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
