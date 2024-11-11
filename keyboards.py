from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ParamsMyCallback(CallbackData, prefix="params"):
    callback: str
    bar: int

async def params_keyboard(
        user_order_limit: float,
        percent_profit: float,
        autobuy_up_sec: int,
        autobuy_down_percent: float,
        taker: float = 0,
        maker: float = 0.00
):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Размер ордера – {round(user_order_limit, 2)} USDT', callback_data='set_order_limit')
    keyboard.button(text=f'Процент прибыли – {round(percent_profit, 2)} %', callback_data='set_profit_percent')
    keyboard.button(text=f'Автопокупка при росте – {autobuy_up_sec} сек', callback_data='set_autobuy_up')
    
    if isinstance(autobuy_down_percent, float) and autobuy_down_percent != 1000:
        keyboard.button(text=f'Автопокупка при падении – {round(autobuy_down_percent, 2)} %', callback_data='set_autobuy_down')
    if autobuy_down_percent == 1000:
        keyboard.button(text=f'Автопокупка при падении – откл. 🚫', callback_data='set_autobuy_down')
    keyboard.button(text=f'Комиссия биржи M: {round(maker, 2)}% | T: {round(taker, 2) if taker >= 0.02 else round(taker, 5)}%', callback_data='set_user_commission')
    
    
    
    keyboard.button(text='Сбросить настройки', callback_data='reset_settings')
    keyboard.adjust(1)
    
    return keyboard.as_markup()


async def user_autobuy_down_keyboard_off():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Отключить автопадение', callback_data='autobuy_off')
    keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    keyboard.adjust(1)
    return keyboard.as_markup()


async def back_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    return keyboard.as_markup()


async def yes_no_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Да', callback_data='yes_callback')
    keyboard.button(text=f'Нет', callback_data='cancel_to_parametrs')
    return keyboard.as_markup()

# клавиатура для установления комисии в параметрах
async def user_commission_choices():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Mейкер: 0.00% | Tейкер: 0.020% ', callback_data='set_user_commission_3')
    keyboard.button(text=f'Mейкер: 0.00% | Tейкер: 0.016% ', callback_data='set_user_commission_2')
    keyboard.button(text=f'Mейкер: 0.00% | Tейкер: 0.010%', callback_data='set_user_commission_1')
    keyboard.button(text=f'Моя комиссия: ', callback_data='user_check_commission')
    keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    keyboard.adjust(1)
    return keyboard.as_markup()

def commission_to_url():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Установить эти значения 🔺', callback_data='set_user_commission_4')
    keyboard.button(text=f'Подробнее на сайте', url='https://www.mexc.com/fee')
    keyboard.button(text=f'🔙', callback_data='set_user_commission')
    keyboard.adjust(1)
    return keyboard.as_markup()

def admin_keyboard(level: int = 0):
    keyboard = InlineKeyboardBuilder()
    if level == 0:
        keyboard.button(text=f'1.ОБНОВИТЬСЯ', callback_data='refreshing')
        keyboard.button(text=f'Получить последний лог', callback_data='get_logs')
    if level == 1:
        keyboard.button(text=f'1.Обновить', callback_data='refresh')
        keyboard.button(text=f'2.Колбаса', callback_data='restart')
        keyboard.button(text=f'🔙', callback_data='back_to_admin')
    keyboard.adjust(1)
    return keyboard.as_markup()