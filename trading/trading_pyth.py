import asyncio

from aiogram import Bot
from aiogram.types import Message
from loguru import logger

from all_mexc_methods.AccountMexc import AccountMexcMethods
from db import get_access_key, get_secret_key, get_await_time, get_orders_from_data, \
    get_info_commission_percent, get_all_open_sell_orders_autobuy_from_any_table
from trading.buy_sell_methods.buy_sell import get_symbol_price
from trading.buy_sell_methods.buy_sell_sui import BuySellOrders
from trading.db_querys.db_methods_for_sui import delete_order_by_user_and_order_id_from_any_table_by_symbol, \
    update_order_by_order_id_any_table
from trading.db_querys.db_symbols_for_trade_methods import update_start_stop, get_user_symbol_data, \
    update_user_symbol_data
from trading.session_manager import manager_pyth
from utils.additional_methods import create_time, user_message_returner
from utils.user_api_keys_checker import validation_user_keys
from utils.user_buy_total import get_user_buy_sum


async def pyth_trader(message: Message, bot: Bot, result: dict = None):
    user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    """Есть команда  СТОП?"""
    while True:
        if result:
            avg_price = result["avg_price"]
            actual_order_id = result["actual_order"]
            manager_pyth.set_active(user_id)
        else:
            manager_pyth.set_active(user_id)
            order_limit_by_user = await get_user_symbol_data(user_id, "PYTHUSDT", "order_limit_by")
            buy_sell = BuySellOrders(user_id=user_id,
                                     user_secret_key=user_secret_key,
                                     user_api_keys=user_api_keys,
                                     order_limit_by_user=order_limit_by_user,
                                     symbol="PYTHUSDT")
            
            user_balance = AccountMexcMethods(user_api_keys, user_secret_key)
            await user_balance.get_account_info_()
            pyth_limit = await get_user_symbol_data(user_id, "PYTHUSDT", "trade_limit")
            user_buy_stats = await get_user_buy_sum(user_id, "PYTHUSDT")
            if user_buy_stats + order_limit_by_user >= pyth_limit:
                user_get_limit_message = await get_user_symbol_data(user_id, "PYTHUSDT", "limit_message")
                if user_get_limit_message:
                    await asyncio.sleep(60)
                    continue
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"Установленный вами лимит по PYTH/USDT достиг {pyth_limit} USDT\n Вы можете изменить его в /parameters"
                    )
                    await update_user_symbol_data(user_id, "PYTHUSDT", limit_message=1)
                    continue
            
            if user_balance.total_free_usdt <= order_limit_by_user:
                user_get_message = await get_user_symbol_data(user_id, "PYTHUSDT", "info_no_usdt")
                if user_get_message:
                    await asyncio.sleep(60)
                    continue
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text="Недостаточно USDT для совершения покупки PYTH.\nНастраивается в /parameters."
                    )
                    await update_user_symbol_data(user_id, "PYTHUSDT", info_no_usdt=1)
                    continue
            
            """Покупка по Рынку"""
            await update_user_symbol_data(user_id, "PYTHUSDT", info_no_usdt=0)
            await update_user_symbol_data(user_id, "PYTHUSDT", limit_message=0)
            order_buy_id, qnty_for_sell, price_to_sell = await buy_sell.open_market_order_buy(bot=bot)
            if price_to_sell == "Error 429":
                continue
            if price_to_sell == "critical_error":
                await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=False)
                manager_pyth.delete_user(user_id)
                return
            result = await buy_sell.open_limit_order_sell(user_id, order_buy_id, qnty_for_sell, price_to_sell,
                                                          bot)
            if result["critical_error"]:
                manager_pyth.delete_user(user_id)
                await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=False)
                return
            avg_price = result["avg_price"]
            actual_order_id = result["actual_order"]
        
        while True:
            sui_price = await get_symbol_price('PYTHUSDT')
            auto_buy_down_perc = await get_user_symbol_data(user_id, "PYTHUSDT", "auto_buy_down_perc")
            percent_profit = await get_user_symbol_data(user_id, "PYTHUSDT", "percent_profit")
            sold_price = avg_price * (1 + percent_profit / 100)
            threshold_price = avg_price * (1 - auto_buy_down_perc / 100)
            await asyncio.sleep(3)
            start_or_stop = await get_user_symbol_data(user_id, "PYTHUSDT", "start_stop")
            manager_pyth.set_active(user_id)
            
            if not start_or_stop:
                await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=False)
                await update_start_stop(user_id, "PYTHUSDT", info_no_usdt=0)
                await update_user_symbol_data(user_id, "PYTHUSDT", limit_message=0)
                manager_pyth.delete_user(user_id)
                logger.info(f"Модуль PYTH/USDT остановлен пользователем {user_id}!")
                return
            
            is_autobuy_was_closed = await orders_checker(message, bot, current_order_id=actual_order_id)
            if is_autobuy_was_closed.get('autobuy_is_closed'):
                logger.info(f"Пользователь {user_id}: автобай PYTH/USDT был закрыт, номер - {actual_order_id}")
                delay_time = await get_await_time(user_id)
                result = None
                await asyncio.sleep(delay_time)
                break
            
            if sui_price >= sold_price:
                result = None
                break
            
            if float(sui_price) <= float(threshold_price):
                await message.answer(
                    f'🔻 <b>УВЕДОМЛЕНИЕ</b> 🔻 цена\nPYTH упала до {round(threshold_price, 4)} (на {round(auto_buy_down_perc, 2)} % от {round(avg_price, 4)})').as_(
                    bot)
                result = None
                break
            await asyncio.sleep(1)


async def orders_checker(message: Message, bot, user_id: int = None, current_order_id: str = None):
    if not user_id:
        user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    user_commission = await get_info_commission_percent(user_id)
    not_founds = []
    result = {
        'autobuy_is_closed': False,
        'autobuy_was_cancelled': False,
        '400': not_founds
    }
    
    user_orders_from_table = await get_all_open_sell_orders_autobuy_from_any_table(user_id, "PYTHUSDT", 1)
    closed_orders = set()
    logger.info(
        f"Пользователь {user_id}: Проверка закрытых ордеров, текуший автобай = {current_order_id}")
    for record in user_orders_from_table:
        try:
            order = await http_mexc.get_order_status(order_id=record['order_id_limit'], symbol="PYTHUSDT")
            status = order.get('status')
            logger.info(status)
            if status == 'FILLED':
                logger.info(f"Данные о закрытом ордере {order}")
                
                totalamountonpurchace = record['totalamountonpurchace']
                order_buy_id = order.get('orderId')
                logger.info(
                    f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
                if current_order_id == order_buy_id:
                    result.update({'autobuy_is_closed': True})
                    logger.info(
                        f"Пользователь {user_id}: закрыт ордер autobuy")
                
                time_of_order_sell = await create_time(order.get('updateTime'))
                qnty_for_sell = order.get('executedQty')
                price_to_sell = order.get('price')
                total_after_sale = order.get('origQuoteOrderQty')
                account_info = await http_mexc.get_account_info_()
                fee_limit_order = (float(total_after_sale) - float(totalamountonpurchace)) * (
                        1 - float(user_commission) / 100)
                total_balance_usdt = http_mexc.total_after_sale or 0
                total_open_trades = len(await http_mexc.get_open_orders()) or 0
                kaspa_in_orders = http_mexc.total_after_sale_sui or 0
                total_free_usdt = http_mexc.total_free_usdt or 0
                
                await update_order_by_order_id_any_table("PYTHUSDT",
                                                         int(user_id),
                                                         str(order_buy_id),
                                                         time_of_order_sell,
                                                         float(qnty_for_sell),
                                                         float(price_to_sell),
                                                         order_id_limit=record['order_id_limit'],
                                                         autobuy=2,
                                                         total_amount_after_sale=total_after_sale,
                                                         feelimit=fee_limit_order,
                                                         balance_total=total_balance_usdt,
                                                         orders_in_progress=total_open_trades,
                                                         kaspa_in_orders=kaspa_in_orders,
                                                         currency_for_trading=total_free_usdt
                                                         )
                closed_orders.add(order_buy_id)
            if status == 'CANCELED':
                await delete_order_by_user_and_order_id_from_any_table_by_symbol("PYTHUSDT", user_id, current_order_id)
                logger.info(f"User {user_id} canceled order with status 1 {order}")
                result.update({'autobuy_was_cancelled': True})
        
        except Exception as e:
            logger.info(f"Ордер попал в исключение - {e}")
            continue
        else:
            pass
    await send_messages_to_user(message, closed_orders, bot)
    logger.info(f"Пользователю: {user_id} возвращаем {result}")
    return result


async def send_messages_to_user(message: Message, orders, bot):
    user_id = message.from_user.id
    for i in orders:
        try:
            res = await get_orders_from_data(user_id, i)
            order_buy_id = res['order_id']
            qnty_for_sell = res['qtytosell']
            price_to_sell = res['priceordersell']
            total_after_sale = res['totalamountaftersale']
            fee_limit_order = res['feelimitorder']
            user_message = user_message_returner(qnty_for_sell, price_to_sell, total_after_sale, fee_limit_order,
                                                 "PYTHUSDT")
            await message.answer(user_message, parse_mode="HTML").as_(bot)
            logger.info(f"Отправили сообщение {order_buy_id}")
        
        except Exception as e:
            logger.info(f"Ошибка при отправке сообшения {e}")