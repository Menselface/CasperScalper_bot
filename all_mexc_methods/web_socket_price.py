import asyncio

from pymexc import spot

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
