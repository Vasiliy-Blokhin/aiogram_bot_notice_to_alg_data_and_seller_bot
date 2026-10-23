# aiogram_bot_notice_to_alg_data_and_seller_bot

Telegram-бот (aiogram 3) для просмотра данных `iss_filter_algorithm` и `ALOR_TICKETS_BOT`
из общей БД `../data/trading.db`.

Команды: `/сигналы`, `/портфель`, `/статистика` (сделки исполнителя, бэктест),
`/статус` (живы ли сервисы), `/отчёт`, `/стратегии` (статистика 7 стратегий за
день/неделю/месяц и текущие доли капитала), `/алгоритмы` (геномный и реверсивный),
`/поиск` (часовая итерация геномного поиска: запрос в `evolve_requests`, его берёт демон
`iss_evolve`; сводки этапов — в бот отчётов), `/информация`.

Этот бот — только кнопки. Отчёты и логи (ежедневный отчёт в будни после `REPORT_TIME`,
по умолчанию 19:00 МСК; сигналы, сделки, ошибки движка и исполнителя) идут через отдельного
бота `TLG_REPORT_TOKEN` (тот же токен — в `.env` движка и исполнителя). `/start` здесь
подписывает чат; в боте отчётов тоже нужно один раз нажать `/start`, либо задать
`TLG_REPORT_CHAT_ID`.
Ограничьте доступ своим Telegram id через `ALLOWED_USERS`.

```bash
../.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, TLG_REPORT_TOKEN, ALLOWED_USERS
../.venv/Scripts/python main.py
```
