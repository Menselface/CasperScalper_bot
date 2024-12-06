import asyncio

from pymexc import spot
import time
import threading

api_key = "mx0vglp2mmtTvV1atO"
api_secret = "d10007277f4e462bb43bd9f59472d02e"


class WebSocketPrice:
    def __init__(self, api_key, api_secret):
        self.client = spot.WebSocket(api_key=api_key, api_secret=api_secret)
        self.last_price = None
        self.symbol = 'KASUSDT'
        self.websocket_working = False
        self.price_event = asyncio.Event()

    def handle_message(self, message):
        if 'd' in message and 'deals' in message['d'] and len(message['d']['deals']) > 0:
            self.last_price = message['d']['deals'][0]['p']
            self.price_event.set()

    def start(self):
        self.websocket_working = True
        try:
            self.client.deals_stream(self.handle_message, self.symbol)
        except Exception as e:
            print(f"Ошибка подключения WebSocket: {e}")
            self.websocket_working = False

    async def get_price(self):
        await self.price_event.wait()
        self.price_event.clear()
        return self.last_price




# async def main():
#     ws_connection = WebSocketPrice(api_key, api_secret)
#
#
#     threading.Thread(target=ws_connection.start, daemon=True).start()
#
#
#     while True:
#         current_price = await ws_connection.get_price()
#         print(f"Последняя цена: {current_price}")
#
#
# asyncio.run(main())


# old
#----------------------------------------------------------
# from pymexc import spot
# import time
# import threading
#
# api_key = "mx0vglp2mmtTvV1atO"
# api_secret = "d10007277f4e462bb43bd9f59472d02e"
#
#
# class WebSocketPrice:
#     def __init__(self, api_key, api_secret):
#         self.client = spot.WebSocket(api_key=api_key, api_secret=api_secret)
#         self.last_price = None
#         self.symbol = 'KASUSDT'
#         self.websocket_working = False
#
#     def handle_message(self, message):
#         # print("Received message:", message)
#         if 'd' in message and 'deals' in message['d'] and len(message['d']['deals']) > 0:
#             self.last_price = message['d']['deals'][0]['p']
#
#     def start(self):
#         self.websocket_working = True
#         try:
#             self.client.deals_stream(self.handle_message, self.symbol)
#         except Exception:
#             self.websocket_working = False
#
#     def is_working(self):
#         return self.websocket_working
#
#     def get_price(self):
#         # Метод для получения последней цены
#         return self.last_price

# ws_con = WebSocketPrice(api_key, api_secret)
# threading.Thread(target=ws_con.start).start()
# while True:
#     time.sleep(1)
#     current_price = ws_con.get_price()
#     print(type(current_price))
# ws_connection = WebSocketPrice(api_key, api_secret)
#
# ws_connection.start()
#
# while True:
#     time.sleep(1)
#     current_price = ws_connection.get_price()
#     print(type(current_price))