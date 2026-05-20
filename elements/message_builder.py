import logging

from elements.module import all_statistic_info, weights_in_list
from source.settings.settings import (
    PARAMS_ALL,
    STATUS_DOWN,
    STATUS_MEDIUM,
    STATUS_UP,
    BORDERS_SCORE,
    handler
)
from source.sql.main import SQLmain as sql
import source.sql.tables as tables

logger = logging.getLogger(name=__name__)  # Запуск логга проекта.
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Интерактивные сообщения.
def trading_info_message():
    """ Сообщение с выводом статуса торговли."""
    message = (
        '📊 Текущий статус торговли: \n\n👉 '
    )
    status = sql.get_all_data(tables.PrepareData)[0]['TRADINGSESSION']
    match status:
        case "1": 
            status = 'торги идут'
        case "2":
            status = 'торги приостановлены'

    return message + status + '.'


def better_shares_info_message():
    '''data = ALL_JC.read_file(file=FILE_SHARES_TO_BUY)
    message = ''
    if data == []:
        return empty_message
    for share in data:
        message += share.get('symbol') + ', '
    return message
    '''
    return 'wait seller bot'
#--------------------------------------------------------


def weights_message():
    """ Сообщение с выводом весов."""
    if weights_in_list() == []:
        return empty_message()

    message = '📊 Текущий коэффициент весов:\n\n'
    for weight in weights_in_list():
        message += f'👉 {weight};\n'

    return message
#--------------------------------------------------------


def last_statistic_message():
    statistic = sql.get_all_data(tables.AllStatistic)
    if statistic == []:
        return empty_message()

    last_positive = statistic[-1]['statistic_prcnt']
    last_neutral = statistic[-1]['neutral_prcnt']
    try:
        last_profit = 100 * statistic[-1][
            'potential_profitability'
        ] / statistic[-1]['count_price_after']
    except ZeroDivisionError:
        last_profit = 0.0

    message = (
        '📊 Статистическая вероятность за последнюю итерацию:\n\n'
        f'  👉 Процент роста цены: {(last_positive):.2f} %\n'
        f'  👉 Процент совпадения цены: {(last_neutral):.2f} %\n'
        '  👉 Процент падения цены: '
        f'{(100 - last_positive - last_neutral):.2f} %\n'
        f'  👉 Процент прибыли: {last_profit:.2f} %\n\n'
    )

    return message


def all_statistic_message():
    data = sql.get_all_data(tables.AllStatistic)
    all_statistic = all_statistic_info(
        data=data
    )

    message = (
        '📊 Средняя статистическая вероятность за все время:\n'
        f'(Количество итераций: {len(data)})\n\n'
        f'  👉 Процент роста цены: {all_statistic[0]:.2f} %\n'
        f'  👉 Процент совпадения цены: {all_statistic[2]:.2f} %\n'
        '  👉 Процент падения цены: '
        f'{(100 - all_statistic[2] - all_statistic[2]):.2f} %\n'
        f'  👉 Процент прибыли: {all_statistic[1]:.2f} %\n\n'
    )

    return message
#--------------------------------------------------------


def shares_score_output_mesage(start, end, max_score, min_score):
    return (
        '📝 Параметры запроса:\n\n'
        f'   👉 Параметр поиска: {PARAMS_ALL["FILTER_SCORE"]};\n'
        f'   👉 Границы диапозона: {min_score:.2f} - {max_score:.2f};\n'
        f'   👉 Выбранный диапозон поиска: {start} - {end};\n'
    )


def shares_start_message():
    return (
        '📈 Что нужно для работы:\n\n'
        '   👉 После того как высветятся сообщение о вводе стартового значения '
        '-> необходимо ввести целое число*;\n'
        '   👉 После того как высветятся сообщение о вводе конечного значения '
        '-> необходимо ввести целое число*;\n'
        '   👉 После того как высветятся список результатов -> необходимо '
        'нажать на нужную котировку акций;\n\n'
        '   * Целое число - комбинация цифр, без дополнительных знаков и букв.'
        '\n\n'
    )


def start_input_message():
    return (
        '📝 Введите стартовое значение:'
    )


def end_input_message():
    return (
        '📝 Введите конечное значение:'
    )


def better_shares_output_mesage():
    return '📈 Для получения результата нужно только нажать на кнопку.'
#--------------------------------------------------------


def shares_mess(key, value):
    """ Шаблон карточки акции."""
    sym = '☑️' if key == 'SECID' else '🔸'
    if key == 'STATUS_FILTER' and value == STATUS_UP:
        sym = '\n🟢'
    elif key == 'STATUS_FILTER' and value == STATUS_DOWN:
        sym = '\n🔴'
    elif key == 'STATUS_FILTER' and value == STATUS_MEDIUM:
        sym = '\n🟡'
    if isinstance(value, float):
        message = f"{sym} {PARAMS_ALL.get(key)}: {value:.2f}.\n"
    else:
        message = f"{sym} {PARAMS_ALL.get(key)}: {value}.\n"
    if key == 'SECID':
        message += '\n'

    return message


def certain_shares(code):
    """ Сообщение с определенной акцией."""
    message = ''
    sort_data = []
    for data in sql.get_all_data(tables.FilterData):
        if data['SECID'] in sort_data:
            continue
        sort_data.append(data['SECID'])
        logger.info(sort_data)

        if (
            data['SECID'] == code
            and data['FILTER_SCORE'] > BORDERS_SCORE
        ):


            for key, value in data.items():
                if key in PARAMS_ALL.keys():
                    message += shares_mess(key, value)
            break
    return message
#--------------------------------------------------------


# Системные сообщения.
def empty_message():
    return '📝 Извините, но файл пустой.'


def empty_output_message():
    return '📝 Извините, но нет результата на ваш запрос.'


def error_message():
    """ Информация об ошибке."""
    return (
        '❗️ Читай внимательнее инструкцию "/информация".'
    )


# Информационные сообщения
def start_message(name):
    """ Стартовое сообщение."""
    hello_message = (
        f'👋Приветсвую, {name}!\n\n '
    )
    disclaimer_message = (
        '💰📈 Бот предоставляет прогнозы по акциям с анализом роста/падения.\n\n'
        'Перед работой обязательно ознакомтесь с дополнительной информации '
        '"/информация"❗️\n\n'
    )
    return hello_message + disclaimer_message


def info_message():
    """ Сообщение общей информации."""
    message = (
        '📊 Информация о боте финансовой аналитики\n\n'
        '💸 Наш бот использует данные с Мосбиржи, анализирует их с '
        'помощью алгоритмов '
        'технического анализа и предоставляет прогнозы по акциям '
        '(рост или падение), чтобы помочь вам увеличить свой капитал.'
        '\n\n'
        '⚠️ Обратите внимание, что мы не несем ответственности за '
        'последствия ваших '
        'решений. Помните о возможных рисках, связанных с самой '
        'природой экономики. Ознакомтесь с рисками подробнее'
        '\n\n'
        '✍️ Автор (разработчик): @Vasilianin\n'
        '🤝 Если у вас есть какие-либо вопросы или предложения, '
        'пожалуйста, свяжитесь со мной.'
            )
    return message


def risk_message():
    """ Сообщение о возможных рисках."""
    message = (
        '📊 Возможные риски (учтите их при работе).\n\n'
        '⚠️ Информация может потерять актуальность из-за задережек данных, '
        'отправляемых Мосбиржей. Поэтому внимательно следите за временными '
        'показателями.\n⚠️ Любой алгоритм не может дать 100% гарантии на '
        'результат (но к этому стремлюсь, поэтому он усовершенствуется).'
    )
    return message
