import asyncio
import traceback

from loguru import logger
from mexc_api.common.enums import Side, OrderType

from all_mexc_methods.mexc_methods import CreateSpotConn
from db import get_info_percent_profit, get_info_commission_percent
from trading.buy_sell_methods.buy_sell import get_symbol_price
from trading.db_querys.db_for_btc_table import update_all_not_autobuy, set_order_buy_in_db, \
    update_order_by_order_id, get_buy_price, spend_in_usdt_for_buy_order
from trading.db_querys.db_methods_for_sui import update_all_not_autobuy_any_table, set_order_buy_any_table, \
    update_order_by_order_id_any_table, get_buy_price_any_table, spend_in_usdt_for_buy_order_any_table
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data
from utils.additional_methods import create_time, notify_admin, safe_format, user_message_returner, \
    user_buy_message_returner


class BuySellOrders:
    
    def __init__(
            self,
            user_id,
            user_api_keys,
            user_secret_key,
            order_limit_by_user,
            symbol='BTCUSDC'
    ):
        self.user_id = user_id
        self.user_api_keys = user_api_keys
        self.user_secret_key = user_secret_key
        self.order_limit_by_user = order_limit_by_user
        self.symbol = symbol
        self.http_mexc = CreateSpotConn(self.user_api_keys, self.user_secret_key, self.symbol)
    
    async def open_market_order_buy(self, bot, buy_market: bool = False):
        percent_profit = await get_user_symbol_data(self.user_id, self.symbol, "percent_profit")
        user_commission = await get_info_commission_percent(self.user_id)
        
        try:
            if not buy_market:
                await update_all_not_autobuy_any_table(self.user_id,  1, self.symbol)
                
            new_order_buy = await asyncio.to_thread(self.http_mexc.open_new_order,
                                                    side=Side.BUY,
                                                    quote_order_quantity=str(self.order_limit_by_user)
                                                    )
            
            await asyncio.sleep(1)
            """                 Order buy details                 """
            order_buy_id = new_order_buy.get('orderId')
            logger.info(f"Пользователь {self.user_id}: Открытие нового ордера для {self.symbol} {order_buy_id}")
            order_buy_details = await asyncio.to_thread(self.http_mexc.order_details, order_buy_id)
            time_of_order_buy = await create_time(order_buy_details.get('updateTime'))
            avg_price = await self.http_mexc.get_average_price_of_order(order_buy_id)
            spend_in_usdt_for_buy = order_buy_details.get('cummulativeQuoteQty')
            sui_price = await get_symbol_price(self.symbol)
            """                 Create price to sell here"""
            price_to_sell = sui_price * (1 + percent_profit / 100)
            qnty_for_sell = order_buy_details.get('executedQty')
            """                 Send order into database table 'orders'     """
            if float(qnty_for_sell) <= 0:
                while float(qnty_for_sell) <= 0:
                    qnty_for_sell = order_buy_details.get('executedQty')
                    price_to_sell = avg_price * (1 + (percent_profit + user_commission) / 100)
            if buy_market:
                autobuy = 9
            else:
                autobuy = 1
            await set_order_buy_any_table(self.symbol,
                                          int(self.user_id),
                                          str(order_buy_id),
                                          time_of_order_buy,
                                          float(qnty_for_sell),
                                          float(avg_price),
                                          float(spend_in_usdt_for_buy),
                                          autobay=autobuy,
                                          side='BUY'
                                          )
            """                 Send sell order in database and send message to user + update order by id  """
            return order_buy_id, qnty_for_sell, price_to_sell
        
        
        except Exception as e:
            if "Insufficient position" in str(e):
                await bot.send_message(
                    chat_id=self.user_id,
                    text='Недостаточно USDT для совершения покупки.\nНастраивается в /parameters.',
                    parse_mode='HTML')
                logger.info(
                    f"Пользователь {self.user_id}:Недостаточно USDT для совершения покупки")
                return None, None, 'not_money'
            elif "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(
                    f"Too Many Requests для пользователя {self.user_id}")
                await asyncio.sleep(2)
                return None, None, "Error 429"
            else:
                logger.critical(f"Ошибка у пользователя {self.user_id}: {str(e)}")
                logger.critical(f"Ошибка у пользователя {self.user_id}: {str(e)}")
                logger.critical("Подробности ошибки:\n" + traceback.format_exc())
                logger.opt(exception=True).critical("Детальный стек вызовов")
                await notify_admin(self.user_id, str(e), bot)
                return None, None, "critical_error"
    
    async def open_limit_order_sell(self, user_id, order_buy_id, qnty_for_sell, price_to_sell, bot,
                                          buy_market=False):
        while True:
            try:
                new_order_sell = await asyncio.to_thread(
                    self.http_mexc.open_new_order, Side.SELL, OrderType.LIMIT, quantity=qnty_for_sell,
                    price=price_to_sell)
                
                await asyncio.sleep(1)
                order_sell_id = new_order_sell.get('orderId')
                logger.info(f"Пользователь {self.user_id}: Открытие нового ордера {self.symbol} продажа {order_sell_id}")
                order_sell_details = self.http_mexc.order_details(order_sell_id)
                time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
                while not all([order_sell_id, order_sell_details, time_of_order_sell]):
                    logger.info(f"Пользователь {self.user_id}: ждет ответа от биржи")
                    order_sell_id = new_order_sell.get('orderId')
                    order_sell_details = self.http_mexc.order_details(order_sell_id)
                    time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
                if buy_market:
                    autobuy = 9
                else:
                    autobuy = 1
                
                await update_order_by_order_id_any_table(self.symbol, int(user_id), str(order_buy_id), time_of_order_sell,
                                               float(qnty_for_sell),
                                               float(price_to_sell),
                                               None, str(order_sell_id), autobuy=autobuy)
                avg_price = await get_buy_price_any_table(self.symbol, user_id, order_sell_id)
                spend_in_usdt_for_buy = await spend_in_usdt_for_buy_order_any_table(self.symbol, user_id, order_sell_id)
                message_order_buy = user_buy_message_returner(qnty_for_sell, avg_price, spend_in_usdt_for_buy, price_to_sell, self.symbol)
                
                await asyncio.sleep(1)
                
                while not order_sell_id and avg_price:
                    order_sell_id = new_order_sell.get('orderId')
                
                if order_sell_id and order_buy_id:
                    await bot.send_message(user_id, message_order_buy)
                    logger.info(
                        f"Пользователь {user_id}: получил сообщение о покупке Функция вернула коретные данные  Продажа - {order_sell_id}, Покупка - {order_buy_id}, цена - {avg_price}")
                    
                    return {"actual_order": order_sell_id, "avg_price": avg_price, 'Error 429': False,
                            "critical_error": False}
            
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    logger.warning(
                        f"Too Many Requests для пользователя {self.user_id}")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.critical(f"Ошибка у пользователя {self.user_id}: {str(e)}")
                    await notify_admin(self.user_id, str(e), bot)
                    return {"actual_order": None, "avg_price": None, 'Error 429': False, "critical_error": True}
