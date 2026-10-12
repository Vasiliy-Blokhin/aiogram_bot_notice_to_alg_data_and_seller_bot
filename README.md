# aiogram_bot_notice_to_alg_data_and_seller_bot

Telegram-бот (aiogram 3) для просмотра данных `iss_filter_algorithm` и `ALOR_TICKETS_BOT`
из общей БД `../data/trading.db`.

Команды: `/сигналы`, `/портфель`, `/статистика` (сделки исполнителя, бэктест),
`/статус` (живы ли сервисы), `/отчёт`, `/информация`.

`/start` подписывает чат на ежедневный отчёт (будни, `REPORT_TIME`, по умолчанию 19:00 МСК —
после основной сессии) и на уведомления исполнителя о покупках/продажах.
Ограничьте доступ своим Telegram id через `ALLOWED_USERS`.

```bash
../.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, ALLOWED_USERS
../.venv/Scripts/python main.py
```
