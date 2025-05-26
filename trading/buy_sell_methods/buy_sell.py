import asyncio
import traceback

import httpx
from loguru import logger
from mexc_api.common.enums import Side, OrderType

from services.mexc_api.all_mexc_methods.mexc_methods import CreateSpotConn
from db_pack.db import update_all_not_autobuy, set_order_buy_in_db, \
    update_order_by_order_id, get_buy_price, spend_in_usdt_for_buy_order
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data
from utils.additional_methods import create_time, notify_admin, safe_format


async def get_symbol_price(symbol: str):
    url = f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}"
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=url, timeout=10)
                response.raise_for_status()
                kaspa_price_data = response.json()
                return float(kaspa_price_data['price'])
    
        except httpx.HTTPStatusError as http_err:
            logger.warning(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
            continue
        except httpx.RequestError as req_err:
            logger.warning(f"Request Error: {req_err}")
            continue
        except httpx.TimeoutException:
            logger.warning("Request timed out.")
            continue


class BuySellOrders:
    
    def __init__(
                 self,
                 user_id,
                 user_api_keys,
                 user_secret_key,
                 order_limit_by_user,
                 symbol = 'KASUSDT'
                 ):
        self.user_id = user_id
        self.user_api_keys = user_api_keys
        self.user_secret_key = user_secret_key
        self.order_limit_by_user = order_limit_by_user
        self.symbol = symbol
        self.http_mexc = CreateSpotConn(self.user_api_keys, self.user_secret_key, symbol=symbol)
    
    async def open_kaspa_market_order_buy(self, bot, buy_market:bool = False):
        percent_profit = await get_user_symbol_data(self.user_id, "KASUSDT", "percent_profit")
        try:
            if not buy_market:
                await update_all_not_autobuy(self.user_id, 1)
            new_order_buy = await asyncio.to_thread(self.http_mexc.open_new_order, side=Side.BUY,
                                                    quote_order_quantity=str(self.order_limit_by_user))
            await asyncio.sleep(1)
            """                 Order buy details                 """
            order_buy_id = new_order_buy.get('orderId')
            logger.info(f"Пользователь {self.user_id}: Открытие нового ордера {order_buy_id}")
            order_buy_details = await asyncio.to_thread(self.http_mexc.order_details, order_buy_id)
            time_of_order_buy = await create_time(order_buy_details.get('updateTime'))
            avg_price = await self.http_mexc.get_average_price_of_order(order_buy_id)
            spend_in_usdt_for_buy = order_buy_details.get('cummulativeQuoteQty')
            """                 Create price to sell here"""
            price_to_sell = avg_price * (1 + percent_profit / 100)
            qnty_for_sell = order_buy_details.get('executedQty')
            """                 Send order into database table 'orders'     """
            if float(qnty_for_sell) <= 0:
                while float(qnty_for_sell) <= 0:
                    qnty_for_sell = order_buy_details.get('executedQty')
                    price_to_sell = avg_price * (1 + percent_profit / 100)
            if buy_market:
                autobuy = 9
            else:
                autobuy = 1
            await set_order_buy_in_db(int(self.user_id),
                                      str(order_buy_id),
                                      time_of_order_buy,
                                      float(qnty_for_sell),
                                      float(avg_price),
                                      float(spend_in_usdt_for_buy),
                                      autobuy=autobuy,
                                      side='BUY'
                                      )
            """                 Send sell order in database and send message to user + update order by id  """
            return order_buy_id, qnty_for_sell, price_to_sell
            
           
        except Exception as e:
            if "Insufficient position" in str(e):
                await bot.send_message(
                                        chat_id=self.user_id,
                                        text=f'Недостаточно {self.symbol} для совершения покупки.\nНастраивается в /parameters.',
                                        parse_mode='HTML')
                logger.info(
                    f"Пользователь {self.user_id}:Недостаточно {self.symbol} для совершения покупки")
                return None, None, 'not_money'
            elif "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(
                    f"Too Many Requests для пользователя {self.symbol} {self.user_id}")
                await asyncio.sleep(2)
                return None, None, "Error 429"
            else:
                logger.critical(f"Ошибка у пользователя {self.symbol} {self.user_id}: {str(e)}")
                logger.critical("Подробности ошибки:\n" + traceback.format_exc())
                logger.opt(exception=True).critical("Детальный стек вызовов")
                await notify_admin(user_id=self.user_id, symbol=self.symbol, error_msg=str(e), bot=bot)
                return None, None, "critical_error"
                
    async def open_kaspa_limit_order_sell(self, user_id, order_buy_id, qnty_for_sell, price_to_sell, bot, buy_market=False):
        while True:
            try:
                new_order_sell = await asyncio.to_thread(
                    self.http_mexc.open_new_order, Side.SELL, OrderType.LIMIT, quantity=qnty_for_sell, price=price_to_sell)
                
                await asyncio.sleep(1)
                order_sell_id = new_order_sell.get('orderId')
                logger.info(f"Пользователь {self.user_id}: Открытие нового ордера продажа {order_sell_id}")
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
                
                await update_order_by_order_id(int(user_id), str(order_buy_id), time_of_order_sell,
                                               float(qnty_for_sell),
                                               float(price_to_sell),
                                               None, str(order_sell_id), autobuy=autobuy)
                avg_price = await get_buy_price(user_id, order_sell_id)
                spend_in_usdt_for_buy = await spend_in_usdt_for_buy_order(user_id, order_sell_id)
                message_order_buy = f"<b>КУПЛЕНО:</b>\n" \
                                    f"{safe_format(qnty_for_sell, 2)} KAS по {safe_format(avg_price, 6)} USDT\n" \
                                    f"Потраченно - {safe_format(spend_in_usdt_for_buy, 2)} USDT\n" \
                                    f"<b>ВЫСТАВЛЕННО:</b>\n" \
                                    f"{safe_format(qnty_for_sell, 2)} KAS по {safe_format(price_to_sell, 6)} USDT\n"
                await asyncio.sleep(1)
                
                while not order_sell_id and avg_price:
                    order_sell_id = new_order_sell.get('orderId')
                
                if order_sell_id and order_buy_id:
                    await bot.send_message(user_id, message_order_buy)
                    logger.info(
                        f"Пользователь {user_id}: получил сообщение о покупке Функция вернула коретные данные  Продажа - {order_sell_id}, Покупка - {order_buy_id}, цена - {avg_price}")
                    return {"actual_order": order_sell_id, "avg_price": avg_price, 'Error 429': False, "critical_error": False}
                
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    logger.warning(
                        f"Too Many Requests для пользователя {self.user_id}")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.critical(f"Ошибка у пользователя {self.user_id}: {str(e)}")
                    await notify_admin(user_id=self.user_id, symbol=self.symbol, error_msg=str(e), bot=bot)
                    return {"actual_order": None, "avg_price": None, 'Error 429': False, "critical_error": True}