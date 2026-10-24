import json
from source.sql.main import SQLmain as sql   # sql.query(text, params=None) -> list[dict]

REGIMES = {
    'crisis': ('🔴', 'Кризис'),
    'bear': ('🟠', 'Спад'),
    'neutral': ('⚪', 'Нейтральный'),
    'bull': ('🟢', 'Рост'),
    'boom': ('💚', 'Сильный рост')
}
PERIODS = {
    '1m': '1 мес.',
    '6m': 'полгода',
    '1y': '1 год',
    '2y': '2 года',
    '3y': '3 года',
    '4y': '4 года',
    '5y': '5 лет'
}
TASK_TITLES = {
    'evolve': 'Поиск генов',
    'evolve_regimes': 'Поиск по режимам',
    'blind': 'Слепой тест',
    'blind_fast': 'Слепой тест быстро',
    'pools': 'Пулы режимов',
    'regime': 'Режим рынка',
    'backtest': 'Бэктест',
    'update': 'Обновление данных'
}
STATUS = {
    'new': '⏳ в очереди',
    'running': '▶️ идёт',
    'done': '✅ готово',
    'failed': '❌ ошибка'
}


def safe(query, params=None) -> list[dict]:
    try:
        return sql.query(query, params)
    except Exception:
        return []


def label(name: str) -> str:
    if ':' in name:
        parts = name.split(':')
        if len(parts) == 2:
            return parts[1]
        if len(parts) == 3:
            return f'гены #{parts[2]}'
    return name


def regime_message() -> str:
    row = safe('SELECT * FROM market_regime ORDER BY "DATE" DESC LIMIT 1')
    if not row:
        return 'Режим рынка ещё не определён.'
    row = row[0]
    emoji, title = REGIMES.get(row['REGIME'], ('', row['REGIME']))
    comp = json.loads(row['COMPONENTS'] or '{}')
    lines = [
        f'{emoji} <b>Режим рынка: {title}</b> (на {row["DATE"]})'
    ]
    if 'drawdown' in comp:
        lines.append(f'IMOEX от годового максимума: {comp["drawdown"]:+.0%}')
    if 'r63' in comp:
        lines.append(f'За 3 месяца: {comp["r63"]:+.0%}')
    if 'breadth' in comp:
        lines.append(f'Акций в росте: {comp["breadth"]:.0%}')
    lines.append('')
    lines.append('<b>Стратегии для режимов:</b>')
    pools = safe('SELECT REGIME, STRATEGY, AVG_TRADE FROM regime_pools WHERE ACTIVE ORDER BY REGIME, RANK')
    for key in REGIMES:
        emoji, title = REGIMES[key]
        members = [label(p['STRATEGY']) for p in pools if p['REGIME'] == key]
        line = f'{emoji} {title}: ' + (', '.join(members) if members else 'только фонды')
        if key == row['REGIME']:
            line += ' ← сейчас'
        lines.append(line)
    return '\n'.join(lines)


def blind_message() -> str:
    key_row = safe('SELECT RUN_KEY FROM blind_runs ORDER BY id DESC LIMIT 1')
    if not key_row:
        return 'Слепой тест ещё не запускался. Кнопка: /запуск → Слепой тест.'
    key = key_row[0]['RUN_KEY']
    rows = safe('SELECT * FROM blind_runs WHERE RUN_KEY = :k ORDER BY id', {'k': key})
    if not rows:
        return 'Слепой тест ещё не запускался.'
    header = f'🕶 <b>Слепой тест</b> ({rows[0]["CREATED_AT"]} — первые 16 символов). Счёт 50 тыс. ₽ с комиссиями.'
    lines = [header, 'Период: итог | просадка | акции | фонд денег']
    for r in rows:
        period = PERIODS.get(r["PERIOD"], r["PERIOD"])
        total = f'{r["TOTAL_RETURN"]:+.1%}' if r["TOTAL_RETURN"] is not None else '—'
        drawdown = f'{r["MAX_DRAWDOWN"]:.1%}' if r["MAX_DRAWDOWN"] is not None else '—'
        bench = f'{r["BENCH_RETURN"]:+.1%}' if r["BENCH_RETURN"] is not None else '—'
        cash = f'{r["CASH_RETURN"]:+.1%}' if r["CASH_RETURN"] is not None else '—'
        lines.append(f'{period}: {total} | {drawdown} | {bench} | {cash}')
    note = rows[-1].get('NOTE', '')
    if note:
        part = note.split('{')[0].strip('; ')
        if part:
            lines.append(f'Решение: {part}')
    return '\n'.join(lines)


def tasks_message() -> str:
    rows = safe('SELECT * FROM task_requests ORDER BY id DESC LIMIT 8')
    if not rows:
        return 'Задач пока не было.'
    lines = ['📋 <b>Последние задачи</b>']
    for r in rows:
        kind = TASK_TITLES.get(r["KIND"], r["KIND"])
        status = STATUS.get(r["STATUS"], r["STATUS"])
        time = str(r["CREATED_AT"])[5:16]
        lines.append(f'#{r["id"]} {kind} — {status} ({time})')
    return '\n'.join(lines)
