from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import PAIR_TABLE_MAP
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data
from trading.sesison_manager_start_stop import user_start_stop
from utils.additional_methods import safe_format, format_symbol_for_keyboards


class ParamsMyCallback(CallbackData, prefix="params"):
    callback: str
    bar: int


class ParamsMyCallbackSymbol(CallbackData, prefix="params_choice"):
    level: int
    action: str


class UserSymbolsConfig(CallbackData, prefix="symbols"):
    level: int
    action: str


class StartTrade(CallbackData, prefix="start_stop"):
    level: int
    action: str


class PairCallback(CallbackData, prefix="pair"):
    pair: str


async def params_choice_symbol():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=f"BTC/USDC",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_BTCUSDC").pack()
    )
    keyboard.button(
        text=f"KAS/USDT",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_KASUSDT").pack()
    )
    keyboard.button(
        text=f"SUI/USDT",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_SUIUSDT").pack()
    )
    keyboard.button(
        text=f"TAO/USDT",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_TAOUSDT").pack()
    )
    keyboard.button(
        text=f"PYTH/USDT",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_PYTHUSDT").pack()
    )
    keyboard.button(
        text=f"DOT/USDT",
        callback_data=ParamsMyCallbackSymbol(level=1, action="symbol_DOTUSDT").pack()
    )
    
    keyboard.button(
        text=f"Все пары",
        callback_data=ParamsMyCallbackSymbol(level=1, action="all_pairs").pack()
    )
    keyboard.adjust(1)
    return keyboard.as_markup()


async def params_keyboard(
        user_id,
        symbol,
        for_everything: bool = False
):
    keyboard = InlineKeyboardBuilder()
    symbol_str = format_symbol_for_keyboards(symbol)
    if not for_everything:
        user_order_limit = await get_user_symbol_data(user_id, symbol, "order_limit_by")
        percent_profit = await get_user_symbol_data(user_id, symbol, "percent_profit")
        autobuy_down_percent = await get_user_symbol_data(user_id, symbol, "auto_buy_down_perc")
        user_trade_limit = await get_user_symbol_data(user_id, symbol, "trade_limit")
        keyboard.button(text=f'Размер ордера – {safe_format(user_order_limit, 1)} USDT',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_order_limit_{symbol}").pack())
        keyboard.button(text=f'Процент прибыли – {safe_format(percent_profit, 2)} %',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_profit_percent_{symbol}").pack())
        if isinstance(autobuy_down_percent, float) and autobuy_down_percent != 1000:
            keyboard.button(text=f'Процент при падении – {safe_format(autobuy_down_percent, 2)} %',
                            callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_autobuy_down_{symbol}").pack())
        if autobuy_down_percent == 1000:
            keyboard.button(text=f'Процент при падении – откл. 🚫',
                            callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_autobuy_down_{symbol}").pack())
        keyboard.button(
            text=f'Лимит на покупку {symbol_str} {"♾️" if user_trade_limit == 1000000 else user_trade_limit}',
            callback_data=ParamsMyCallbackSymbol(level=1, action=f"limit_of_trading_{symbol}").pack())
        
        keyboard.button(text='Установить по умолчанию',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"reset_settings_{symbol}").pack())
        keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    else:
        symbol = "everything"
        keyboard.button(text=f'Размер ордера USDT',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_order_limit_{symbol}").pack())
        keyboard.button(text=f'Процент прибыли  %',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_profit_percent_{symbol}").pack())
        keyboard.button(text=f'Процент при падении %',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"set_autobuy_down_{symbol}").pack())
        keyboard.button(text=f'Лимит на покупку монеты',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"limit_of_trading_{symbol}").pack())
        keyboard.button(text='Установить по умолчанию',
                        callback_data=ParamsMyCallbackSymbol(level=1, action=f"reset_settings_{symbol}").pack())
        keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    
    keyboard.adjust(1)
    
    return keyboard.as_markup()


async def user_autobuy_down_keyboard_off():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Отключить автопадение', callback_data='autobuy_off')
    keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    keyboard.adjust(1)
    return keyboard.as_markup()


async def user_set_up_keyboard(user_id):
    user_session_start_stop = user_start_stop
    
    user_data = await user_session_start_stop.get_session_data(user_id)
    btc_status = next((currency.get("BTCUSDC") for currency in user_data if "BTCUSDC" in currency), False)
    kaspa_status = next((currency.get("KASUSDT") for currency in user_data if "KASUSDT" in currency), False)
    sui_status = next((currency.get("SUIUSDT") for currency in user_data if "SUIUSDT" in currency), False)
    pyth_status = next((currency.get("PYTHUSDT") for currency in user_data if "PYTHUSDT" in currency), False)
    dot_status = next((currency.get("DOTUSDT") for currency in user_data if "DOTUSDT" in currency), False)
    tao_status = next((currency.get("TAOUSDT") for currency in user_data if "TAOUSDT" in currency), False)
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"BTC/USDC {'✅' if btc_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_BTCUSDC").pack()
    )
    builder.button(
        text=f"KAS/USDT {'✅' if kaspa_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_KASUSDT").pack()
    )
    builder.button(
        text=f"SUI/USDT {'✅' if sui_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_SUIUSDT").pack()
    )
    builder.button(
        text=f"TAO/USDT {'✅' if tao_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_TAOUSDT").pack()
    )
    builder.button(
        text=f"PYTH/USDT {'✅' if pyth_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_PYTHUSDT").pack()
    )
    
    builder.button(
        text=f"DOT/USDT {'✅' if dot_status else '⬛️'}",
        callback_data=UserSymbolsConfig(level=1, action="symbol_DOTUSDT").pack()
    )
    
    builder.button(
        text=f"ПОДТВЕРДИТЬ",
        callback_data=StartTrade(level=1, action="start_trade").pack()
    )
    builder.button(
        text=f"ВЫХОД",
        callback_data=UserSymbolsConfig(level=1, action="exit").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


async def trading_set():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Управление торговлей",
        callback_data=UserSymbolsConfig(level=1, action="trading_set").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


async def back_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'🔙', callback_data='cancel_to_parametrs')
    return keyboard.as_markup()


async def yes_no_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Да', callback_data='yes_callback')
    keyboard.button(text=f'Нет', callback_data='cancel_to_parametrs')
    return keyboard.as_markup()


async def user_commission_choices():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Mейкер: 0.050% | Tейкер: 0.050% ', callback_data='set_user_commission_1')
    keyboard.button(text=f'Mейкер: 0.040% | Tейкер: 0.040% ', callback_data='set_user_commission_2')
    keyboard.button(text=f'Mейкер: 0.025% | Tейкер: 0.025%', callback_data='set_user_commission_3')
    keyboard.button(text=f'Посмотреть на сайте', url='https://www.mexc.com/fee')
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


def trial_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f'Тестовый период 7 дней', callback_data='set_trial_promo')
    keyboard.adjust(1)
    return keyboard.as_markup()


def create_pair_selection_keyboard():
    """
    Создает клавиатуру для выбора пары на основе словаря PAIR_TABLE_MAP.
    """
    keyboard = InlineKeyboardBuilder()
    for pair, table in PAIR_TABLE_MAP.items():
        keyboard.button(
            text=format_symbol_for_keyboards(pair),
            callback_data=PairCallback(pair=pair).pack()
        )
    keyboard.adjust(1)
    return keyboard.as_markup()


def create_pagination_keyboard(current_page: int, total_pages: int, pair: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if current_page > 1:
        builder.button(text="<<", callback_data=f"page:1:{pair}")
    else:
        builder.button(text="<<", callback_data="disabled", disabled=True)
    
    if current_page > 1:
        builder.button(text="<", callback_data=f"page:{current_page - 1}:{pair}")
    else:
        builder.button(text="<", callback_data="disabled", disabled=True)
    
    builder.button(text=f"({current_page}/{total_pages})", callback_data="disabled", disabled=True)
    
    if current_page < total_pages:
        builder.button(text=">", callback_data=f"page:{current_page + 1}:{pair}")
    else:
        builder.button(text=">", callback_data="disabled", disabled=True)
    
    if current_page < total_pages:
        builder.button(text=">>", callback_data=f"page:{total_pages}:{pair}")
    else:
        builder.button(text=">>", callback_data="disabled", disabled=True)
    
    builder.adjust(5)
    
    return builder.as_markup()
