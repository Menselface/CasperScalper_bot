import asyncio

from aiogram import Bot
from aiogram.types import Message

from services.mexc_api.all_mexc_methods.AccountMexc import AccountMexcMethods
from infrastructure.db_pack.db import (
    get_access_key,
    get_secret_key,
    delete_order_by_user_and_order_id,
    update_orderafter_sale_by_order_id,
    get_all_open_sell_orders_autobuy,
    get_orders_from_data,
    get_info_commission_percent,
)
from services.orders_checker import CountOrderCommission
from services.trading.trading_utils import TradeUtils
from trading.buy_sell_methods.buy_sell import BuySellOrders, get_symbol_price
from trading.db_querys.db_symbols_for_trade_methods import (
    get_user_symbol_data,
    update_user_symbol_data,
)
from trading.session_manager import manager_kaspa
from utils.additional_methods import create_time, safe_format
from utils.logger import TradingLogs, get_user_logger
from utils.user_buy_total import get_user_buy_sum
from utils.validate_user_statsus import validate_user_status


async def kaspa_trader(message: Message, bot: Bot, result: dict = None):
    user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    symbol_name = "KASUSDT"
    logs = TradingLogs(user_id=user_id, symbol=symbol_name)
    user_logger = get_user_logger(user_id=user_id, symbol=symbol_name)
    user_logger.info(f"Начал торговлю по {symbol_name}")
    trade_util = TradeUtils(symbol_name)
    is_user_expired = await validate_user_status(
        message, user_id, symbol=symbol_name, manager=manager_kaspa, bot=bot
    )
    user_get_limit_or_balance_message_status = (
        await trade_util.check_message_status_limit_or_balance_for_user(user_id)
    )
    if is_user_expired:
        return

    """Есть команда  СТОП?"""
    while True:
        if (
            result
            and result["avg_price"]
            and not user_get_limit_or_balance_message_status
        ):
            avg_price = result["avg_price"]
            actual_order_id = result["actual_order"]
            manager_kaspa.set_active(user_id)
            logs.user_automatically_reset(actual_order_id)
        else:
            if await trade_util.if_not_start_stop_at_symbols_for_trade(
                user_id, manager_kaspa, logs
            ):
                return
            is_user_expired = await validate_user_status(
                message, user_id, symbol=symbol_name, manager=manager_kaspa, bot=bot
            )
            if is_user_expired:
                logs.user_expired_and_stop()
                return
            manager_kaspa.set_active(user_id)
            order_limit_by_user = await get_user_symbol_data(
                user_id, symbol_name, "order_limit_by"
            )
            buy_sell = BuySellOrders(
                user_id=user_id,
                user_secret_key=user_secret_key,
                user_api_keys=user_api_keys,
                order_limit_by_user=order_limit_by_user,
            )
            logs.set_counter_to_zero()
            user_balance = AccountMexcMethods(user_api_keys, user_secret_key)
            await user_balance.get_account_info_()
            kaspa_limit = await get_user_symbol_data(
                user_id, symbol_name, "trade_limit"
            )
            logs.order_limits_by_and_trade_limit_user(order_limit_by_user, kaspa_limit)
            user_buy_stats = await get_user_buy_sum(user_id, symbol_name)
            if user_buy_stats + order_limit_by_user >= kaspa_limit:
                user_get_limit_message = await get_user_symbol_data(
                    user_id, symbol_name, "limit_message"
                )
                if user_get_limit_message:
                    logs.limit_message(minute=True)
                    await asyncio.sleep(60)
                    continue
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"Установленный вами лимит по KAS/USDT достиг {kaspa_limit} USDT\n Вы можете изменить его в /parameters",
                    )
                    logs.limit_message(first=True)
                    await update_user_symbol_data(user_id, symbol_name, limit_message=1)

                    continue

            if user_balance.total_free_usdt <= order_limit_by_user:
                user_get_message = await get_user_symbol_data(
                    user_id, symbol_name, "info_no_usdt"
                )
                if user_get_message:
                    logs.balance_message(minute=True)
                    await asyncio.sleep(60)
                    continue
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text="Недостаточно USDT для совершения покупки KAS.\nНастраивается в /parameters.",
                    )
                    await update_user_symbol_data(user_id, symbol_name, info_no_usdt=1)
                    logs.balance_message(first=True)
                    continue

            """Покупка по Рынку"""

            await trade_util.reset_user_info_usdt_and_limit_message(user_id)
            logs.all_limits_messages_reset_to_zero()
            logs.open_new_order()
            order_buy_id, qnty_for_sell, price_to_sell = (
                await buy_sell.open_kaspa_market_order_buy(bot=bot)
            )
            dict_data = {
                "order_id": order_buy_id,
                "qnty_to_sell": qnty_for_sell,
                "price": price_to_sell,
            }
            logs.return_open_orders_dict_data(dict_data)
            if await trade_util.check_error_for_sleep_and_restart(
                user_id, price_to_sell
            ):
                await asyncio.sleep(10)
                continue
            if price_to_sell == "critical_error":
                await update_user_symbol_data(user_id, symbol_name, start_stop=False)
                manager_kaspa.delete_user(user_id)
                logs.critical_error_after_buying(limit=True)
                return
            result = await buy_sell.open_kaspa_limit_order_sell(
                user_id, order_buy_id, qnty_for_sell, price_to_sell, bot
            )
            logs.open_limit_order_result(result)
            if result["critical_error"]:
                manager_kaspa.delete_user(user_id)
                await update_user_symbol_data(user_id, symbol_name, start_stop=False)
                logs.critical_error_after_buying()
                return
            avg_price = result["avg_price"]
            actual_order_id = result["actual_order"]

        while True:
            is_user_expired = await validate_user_status(
                message, user_id, symbol=symbol_name, manager=manager_kaspa, bot=bot
            )
            if is_user_expired:
                return
            kaspa_price = await get_symbol_price(symbol_name)
            auto_buy_down_perc = await get_user_symbol_data(
                user_id, symbol_name, "auto_buy_down_perc"
            )
            percent_profit = await get_user_symbol_data(
                user_id, symbol_name, "percent_profit"
            )
            sold_price = avg_price * (1 + percent_profit / 100)
            threshold_price = avg_price * (1 - auto_buy_down_perc / 100)
            await asyncio.sleep(3)
            manager_kaspa.set_active(user_id)
            start_or_stop = await get_user_symbol_data(
                user_id, symbol_name, "start_stop"
            )
            trading_data = {
                "symbol_name": symbol_name,
                "sui_price": kaspa_price,
                "auto_buy_down_perc": auto_buy_down_perc,
                "percent_profit": percent_profit,
                "avg_price": avg_price,
                "sold_price": sold_price,
                "threshold_price": threshold_price,
                "start_stop": start_or_stop,
            }
            logs.get_all_data_in_while_trading_module(trading_data)

            if await trade_util.if_not_start_stop_at_symbols_for_trade(
                user_id, manager_kaspa, logs
            ):
                return

            is_autobuy_was_closed = await orders_checker(
                message, bot, current_order_id=actual_order_id
            )
            if is_autobuy_was_closed.get("autobuy_is_closed"):
                logs.autobuy_was_closed(actual_order_id)
                result = None
                break
            if kaspa_price >= sold_price:
                await orders_checker(message, bot, current_order_id=actual_order_id)
                logs.autobuy_was_closed(actual_order_id, overprice=True)
                result = None
                break

            if float(kaspa_price) <= float(threshold_price):
                await message.answer(
                    f"🔻 <b>УВЕДОМЛЕНИЕ</b> 🔻 цена\n️KAS упала до {round(threshold_price, 6)} (на {round(auto_buy_down_perc, 2)} % от {round(avg_price, 6)})"
                ).as_(bot)
                result = None
                logs.price_is_above_threshold(threshold_price)
                break
            await asyncio.sleep(1)


async def orders_checker(
    message: Message, bot, user_id: int = None, current_order_id: str = None
):
    if not user_id:
        user_id = message.from_user.id
    symbol = "KASUSDT"
    user_logger = get_user_logger(user_id, symbol)
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    user_commission = await get_info_commission_percent(user_id)
    not_founds = []
    result = {
        "autobuy_is_closed": False,
        "autobuy_was_cancelled": False,
        "400": not_founds,
    }

    user_orders_from_table = await get_all_open_sell_orders_autobuy(user_id, 1)
    closed_orders = set()
    for record in user_orders_from_table:
        try:
            order = await http_mexc.get_order_status(
                order_id=record["order_id_limit"], symbol=symbol
            )
            status = order.get("status")
            user_logger.info(status)
            if status == "FILLED":
                user_logger.info(f"Данные о закрытом ордере {order}")

                totalamountonpurchace = record["totalamountonpurchace"]
                order_buy_id = order.get("orderId")
                user_logger.info(f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
                if current_order_id == order_buy_id:
                    result.update({"autobuy_is_closed": True})
                    user_logger.info(f"Пользователь {user_id}: закрыт ордер autobuy")

                time_of_order_sell = await create_time(order.get("updateTime"))
                qnty_for_sell = order.get("executedQty")
                price_to_sell = order.get("price")
                total_after_sale = order.get("origQuoteOrderQty")
                account_info = await http_mexc.get_account_info_()
                fee = await CountOrderCommission(
                    user_id, order_buy_id, symbol
                ).return_commission_total_result()

                fee_limit_order = (
                    float(qnty_for_sell) * float(price_to_sell)
                    - float(totalamountonpurchace)
                    - fee
                )
                total_balance_usdt = http_mexc.total_after_sale or 0
                total_open_trades = len(await http_mexc.get_open_orders()) or 0
                kaspa_in_orders = http_mexc.total_after_sale_Kass or 0
                total_free_usdt = http_mexc.total_free_usdt or 0

                await update_orderafter_sale_by_order_id(
                    int(user_id),
                    str(order_buy_id),
                    time_of_order_sell,
                    float(qnty_for_sell),
                    float(price_to_sell),
                    order_id_limit=record["order_id_limit"],
                    autobuy=2,
                    total_amount_after_sale=total_after_sale,
                    feelimit=fee_limit_order,
                    balance_total=total_balance_usdt,
                    orders_in_progress=total_open_trades,
                    kaspa_in_orders=kaspa_in_orders,
                    currency_for_trading=total_free_usdt,
                )
                closed_orders.add(order_buy_id)
            if status == "CANCELED":
                await delete_order_by_user_and_order_id(user_id, current_order_id)
                user_logger.info(f"User {user_id} canceled order with status 1 {order}")
                result.update({"autobuy_was_cancelled": True})

        except Exception as e:
            user_logger.info(f"Ордер попал в исключение - {e}")
            continue
        else:
            pass
    await send_messages_to_user(message, closed_orders, bot, user_logger)
    return result


async def send_messages_to_user(message: Message, orders, bot, user_logger):
    user_id = message.from_user.id
    for i in orders:
        try:
            res = await get_orders_from_data(user_id, i)
            order_buy_id = res["order_id"]
            qnty_for_sell = res["qtytosell"]
            price_to_sell = res["priceordersell"]
            total_after_sale = res["totalamountaftersale"]
            fee_limit_order = res["feelimitorder"]
            user_message = (
                f"<b>ПРОДАНО:</b>\n"
                f"{safe_format(qnty_for_sell, 2)} KAS по {safe_format(price_to_sell, 6)} USDT\n"
                f"<b>Получено:</b> {safe_format(total_after_sale, 2)} USDT\n"
                f"<b>ПРИБЫЛЬ:</b> {safe_format(fee_limit_order, 4)} USDT\n"
            )
            await message.answer(user_message, parse_mode="HTML").as_(bot)
            user_logger.info(f"Отправили сообщение {order_buy_id}")
        except Exception as e:
            user_logger.info(f"Ошибка при отправке сообшения {e}")
