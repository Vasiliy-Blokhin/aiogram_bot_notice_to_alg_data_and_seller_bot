""" Общая БД: чтение данных сервисов + собственные таблицы бота (подписчики, состояние)."""
import sqlalchemy as sa

from source.settings.settings import DB_URL


main_engine = sa.create_engine(DB_URL, echo=False)


class SQLmain:

    @staticmethod
    def query(command: str, params: dict | None = None) -> list[dict]:
        try:
            with main_engine.connect() as connection:
                return [dict(row) for row in connection.execute(sa.text(command), params or {}).mappings()]
        except sa.exc.OperationalError:
            # Таблицы ещё не созданы (сервисы не запускались).
            return []

    @staticmethod
    def execute(command: str, params: dict | None = None):
        with main_engine.begin() as connection:
            connection.execute(sa.text(command), params or {})

    @classmethod
    def create_bot_tables(cls):
        cls.execute(
            'CREATE TABLE IF NOT EXISTS tg_subscribers '
            '(CHAT_ID INTEGER PRIMARY KEY, NAME TEXT, CREATED_AT TEXT)'
        )
        cls.execute('CREATE TABLE IF NOT EXISTS bot_state (KEY TEXT PRIMARY KEY, VALUE TEXT)')

    @classmethod
    def add_subscriber(cls, chat_id: int, name: str):
        cls.execute(
            "INSERT OR IGNORE INTO tg_subscribers VALUES (:chat_id, :name, datetime('now', 'localtime'))",
            {'chat_id': chat_id, 'name': name},
        )

    @classmethod
    def subscribers(cls) -> list[int]:
        return [row['CHAT_ID'] for row in cls.query('SELECT CHAT_ID FROM tg_subscribers')]

    @classmethod
    def get_state(cls, key: str) -> str | None:
        rows = cls.query('SELECT VALUE FROM bot_state WHERE KEY = :key', {'key': key})
        return rows[0]['VALUE'] if rows else None

    @classmethod
    def set_state(cls, key: str, value: str):
        cls.execute(
            'INSERT INTO bot_state VALUES (:key, :value) '
            'ON CONFLICT(KEY) DO UPDATE SET VALUE = excluded.VALUE',
            {'key': key, 'value': value},
        )
