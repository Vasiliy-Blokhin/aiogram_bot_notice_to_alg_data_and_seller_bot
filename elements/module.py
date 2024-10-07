from source.sql.main import SQLmain as sql
import source.sql.tables as tables


def all_statistic_info(data):
    all_success = 0
    all_profit = 0
    for el in data:
        try:
            all_success += el['statistic_prcnt']
            all_profit += 100 * el[
                'potential_profitability'
            ] / el['count_price_after']
        except ZeroDivisionError:
            if len(data) == 0:
                return [0, 0]
            else:
                continue
    return [all_success / len(data), all_profit / len(data)]


def weights_in_list():
    data = sql.get_all_data(tables.Weights)[0]
    result = []

    for key, value in data.items():
        result.append(f'{key}: {value:.3f}')

    return result


async def value_validator(message, state, value):
    try:
        if not isinstance(int(value), int):
            await message.answer(
                'Вы ввели неверные данные. \n'
                'Ознакомтесь с правилами еще раз'
            )
            await state.clear()
            return False
    except Exception:
        await message.answer(
                'Вы ввели неверные данные. \n'
                'Ознакомтесь с правилами еще раз'
            )
        await state.clear()
        return False
    return True
