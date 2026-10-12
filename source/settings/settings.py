from os import getenv
from pathlib import Path
import logging
import sys

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

# Описание хандлера для логгера.
handler = logging.StreamHandler(sys.stdout)
formater = logging.Formatter(
    '%(name)s, %(funcName)s, %(asctime)s, %(levelname)s - %(message)s.'
)
handler.setFormatter(formater)

TOKEN = getenv('BOT_TOKEN') or ''
# Telegram id пользователей с доступом (через запятую). Пусто — доступ у всех.
ALLOWED_USERS = {
    int(user) for user in (getenv('ALLOWED_USERS') or '').split(',') if user.strip()
}

# Общая БД движка сигналов и исполнителя.
DATA_DIR = Path(getenv('DATA_DIR') or BASE_DIR.parent / 'data')
DB_URL = getenv('DB_URL') or f'sqlite:///{(DATA_DIR / "trading.db").as_posix()}'

TRADING_MODE = (getenv('TRADING_MODE') or 'paper').lower()

# Ежедневный отчёт по итогам основной сессии (МСК, часы.минуты), только будни.
REPORT_TIME = float(getenv('REPORT_TIME') or 19.00)
TIMEZONE = 'Europe/Moscow'
