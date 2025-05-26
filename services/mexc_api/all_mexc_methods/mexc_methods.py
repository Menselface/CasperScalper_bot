import asyncio

from loguru import logger
from mexc_api.common.enums import OrderType
from mexc_api.spot import Spot


class CreateSpotConn:
    def __init__(self, api_key, api_secret, symbol: str = "KASUSDT"):
        self.spot_client = Spot(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.total_after_sale = None
        self.total_after_sale_Kass = None
        self.total_free_usdt = None
    
    def get_avg_price(self):
        """Получение средней цены актива."""
        return self.spot_client.market.avg_price(self.symbol)
    
    def get_account_info_(self):
        acount = self.spot_client.account.get_account_info()
        market_price = self.get_avg_price()
        self.total_free_usdt = float(acount.get('balances')[0]['free'])
        self.total_after_sale = (
                float(acount.get('balances')[0]['free']) +
                float(acount.get('balances')[0]['locked'])
        )
        
        # Если второй элемент существует, добавить его к total_after_sale
        if len(acount.get('balances')) > 1:
            self.total_after_sale_Kass = acount.get('balances')[1]['free']
            self.total_after_sale += (
                                             float(acount.get('balances')[1]['free']) +
                                             float(acount.get('balances')[1]['locked'])
                                     ) * float(market_price['price'])
        
        return acount
    
    def open_orders(self):
        """Получение текущих открытых ордеров."""
        return self.spot_client.account.get_open_orders(self.symbol)
    
    
    def open_new_order(self, side, order_type: OrderType = OrderType.MARKET, quantity: str = None,
                       quote_order_quantity: str = '5', price: str = None, client_order_id: str | None = None):
        """Открытие нового ордера."""
        return self.spot_client.account.new_order(symbol=self.symbol, side=side, order_type=order_type,
                                                  quote_order_quantity=quote_order_quantity, quantity=quantity,
                                                  price=price, client_order_id=client_order_id)
    
    def order_details(self, order_id):
        """Получение деталей ордера."""
        return self.spot_client.account.get_order(symbol=self.symbol, order_id=order_id)
    
    async def get_average_price_of_order(self, order_id):
        while True:
            order_status = self.order_details(order_id)
            executed_qty = float(order_status['executedQty'])
            cummulative_quote_qty = float(order_status['cummulativeQuoteQty'])
            avg_price = 0
            
            # Если есть частичное исполнение, пересчитываем среднюю цену
            if executed_qty > 0:
                avg_price = cummulative_quote_qty / executed_qty
            
            # Если ордер полностью исполнен, завершаем цикл
            if order_status['status'] == 'FILLED':
                logger.info(f"Средняя цена заполнения ордера {avg_price}")
                return avg_price
            
            await asyncio.sleep(2)
    
    def get_last_trade(self):
        response = self.spot_client.account.get_trades(self.symbol)
        return response[0] if response else None
    
    def get_last_trades(self, limit: int = 100):
        """
        Return all KAS orders with limit 100
        :param order_id: str
        :param limit: int
        :return: list
        """
        return self.spot_client.account.get_orders(symbol=self.symbol, limit=limit)
    
    async def current_open_orders_loop(self):
        while True:
            orders = self.open_orders()
            # print(f"Открытые ордера: {orders}")
            await asyncio.sleep(5)
#
#
# api_key = "mx0vgl2RfS79ubslmx"
# api_secret = "23879388919a4c8fa83d800c6700bc2b"
#
#
# async def main():
#     http_mexc = CreateSpotConn(api_key, api_secret)
#     s = http_mexc.get_last_trades()
#     pprint(s)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
