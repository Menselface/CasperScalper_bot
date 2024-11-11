from pymexc import spot
from queue import Queue


class WebSocketLCientOrders:
    def __init__(self, api_key, api_secret):
        self.client = spot.WebSocket(api_key=api_key, api_secret=api_secret)
        self.order_updates = Queue()
        self.last_order_id = None
        self.status = None
        self.avg_price = None
        self.type = None
        self.message = None
        self.websocket_working = False

    def handle_order_update(self, message):
        # Обработка обновлений ордеров
        # print("Received order update:", message)
        if 'd' in message and 'i' in message['d']:
            self.last_order_id = message['d']['i']
            self.status = message['d'].get('s', 'UNKNOWN')
            self.avg_price = message['d'].get('p', 0)
            self.type = message['d'].get('S', 0)  # 'trade' or 'sell'
            self.message = message
            # print(f"Order ID: {self.last_order_id}, Status: {self.status}")

    def start(self):
        self.websocket_working = True
        try:
            self.client.account_orders(self.handle_order_update)
        except Exception:
            self.websocket_working = False

    def last_order(self):
        return self.last_order_id, self.status, self.type

    def is_working(self):
        return self.websocket_working
