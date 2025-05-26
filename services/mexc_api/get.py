import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx

from config import BASE_URL
from services.mexc_api.base import BaseMexcAPI
from utils.decorators import mexc_request_safe_call


class GetMexcAPI(BaseMexcAPI):
    def __init__(self, user_id: int, api_key: str, secret_key: str, recvwindow: int = 50000):
        super().__init__(user_id, api_key, secret_key)
        self.params = {
            'symbol': "",
            'recvWindow': recvwindow,
            'timestamp': int(time.time() * 1000)
        }

    def _generate_signature(self, params: dict) -> str:
        query_string = urlencode(params)
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _get_headers(self) -> dict:
        return {'X-MEXC-APIKEY': self.api_key}

    def return_params(self):
        self.params['signature'] = self._generate_signature(self.params)

    @mexc_request_safe_call(default_return=[])
    async def order_commission(self, symbol: str, order_id: str):
        self.params.update(
                                {
                                'symbol': symbol,
                                'orderId': order_id
                                }
                            )
        self.return_params()

        async with httpx.AsyncClient() as client:
            response = await client.get(f'{BASE_URL}/myTrades', headers=self._get_headers(), params=self.params)
            response.raise_for_status()
            return response.json()
