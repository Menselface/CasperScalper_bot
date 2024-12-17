import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx
import requests
from loguru import logger

from config import BASE_URL


class AccountMexcMethods:
    def __init__(self, api_key: str, secret_key: str, symbol: str = 'KASUSDT', recv_window: int = 50000):
        self.api_key = api_key
        self.secret_key = secret_key
        self.symbol = symbol
        self.recv_window = recv_window
        
        self.free_kas = 0
        self.total_after_sale = 0
        self.total_after_sale_Kass = 0
        
        self.total_free_usdt = 0
        self.usdt_locked = 0
        self.locked = 0
        
        self.total_free_usdc = 0
        self.total_after_sale_usdc = 0
        self.usdc_locked = 0
        
        self.free_btc = 0
        self.total_after_sale_btc = 0
        self.locked_btc = 0
        
        self.free_sui = 0
        self.total_after_sale_sui = 0
        self.locked_sui = 0
        
        self.free_pyth = 0
        self.locked_pyth = 0
        self.total_after_sale_pyth = 0
        
        self.free_dot = 0
        self.locked_dot = 0
        self.total_after_sale_dot = 0
    
    def _generate_signature(self, params: dict) -> str:
        query_string = urlencode(params)
        return hmac.new(self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def _get_headers(self) -> dict:
        return {'X-MEXC-APIKEY': self.api_key}
    
    def check_user_own_commission(self):
        params = {
            'symbol': self.symbol,
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000)
        }
        
        params['signature'] = self._generate_signature(params)
        
        headers = self._get_headers()
        res = requests.get(f'{BASE_URL}/tradeFee', headers=headers, params=params)
        
        try:
            result = res.json()
            if 'data' in result and result['data']:
                return result['data']
            else:
                return None
        except ValueError:
            logger.warning("не удается получить корректный JSON")
            return None
    
    async def get_open_orders(self, symbol: str = "KASUSDT"):
        params = {
            'symbol': symbol,
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000)
        }
        
        params['signature'] = self._generate_signature(params)
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            res = await client.get(f'{BASE_URL}/openOrders', headers=headers, params=params)
        
        try:
            result = res.json()
            if isinstance(result, list):
                if len(result) >= 1:
                    return result
                else:
                    return '0'
            else:
                return None
        except ValueError:
            return None
    
    async def get_order_status(self, order_id: str = None, orig_client_order_id: str = None, symbol: str = "KASUSDT"):
        params = {
            'symbol': symbol,
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000)
        }
        
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        params['signature'] = self._generate_signature(params)
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            res = await client.get(f'{BASE_URL}/order', headers=headers, params=params)
        
        try:
            result = res.json()
            if 'orderId' in result:
                return result
            elif "must be sent, but both were empty/null!" in result['msg']:
                return "Order lost in the echo"
            
            else:
                return None
        
        except ValueError:
            logger.info('Failed to decode JSON response.')
            return None
    
    async def get_avg_price(self):
        """Асинхронное получение средней цены актива через API mexc."""
        url = f'{BASE_URL}/avgPrice'
        params = {
            'symbol': self.symbol,
            'timestamp': int(time.time() * 1000)
        }
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, headers=headers, params=params)
                return res.json()
            except (httpx.HTTPError, ValueError):
                return None
    
    async def get_account_info_(self):
        """Асинхронное получение информации о балансе пользователя и расчет total_after_sale."""
        url = f'{BASE_URL}/account'
        params = {
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000)
        }
        params['signature'] = self._generate_signature(params)
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, headers=headers, params=params)
                account = res.json()
                market_price = await self.get_avg_price()
                for balance in account.get('balances', []):
                    asset = balance.get('asset')
                    
                    if asset == 'USDT':
                        self.total_free_usdt = float(balance.get('free', 0))
                        self.total_after_sale += (
                                float(balance.get('free', 0)) +
                                float(balance.get('locked', 0))
                        )
                        
                        self.usdt_locked = float(balance.get('locked'))
                    elif asset == "USDC":
                        self.total_free_usdc = float(balance.get('free', 0))
                        self.total_after_sale_usdc += (
                                float(balance.get('free', 0)) +
                                float(balance.get('locked', 0))
                        )
                        
                        self.usdc_locked = float(balance.get('locked'))
                    
                    
                    elif asset == 'KAS':
                        self.free_kas = float(balance.get('free', 0))
                        self.locked = float(balance.get('locked', 0))
                        self.total_after_sale += (self.free_kas + self.locked) * float(market_price['price'])
                    
                    
                    elif asset == 'SUI':
                        self.free_sui = float(balance.get('free', 0))
                        self.locked_sui = float(balance.get('locked', 0))
                        self.total_after_sale_sui += (self.free_sui + self.locked_sui) * float(market_price['price'])
                    
                    elif asset == 'BTC':
                        self.free_btc = float(balance.get('free', 0))
                        self.locked_btc = float(balance.get('locked'))
                        self.total_after_sale_btc += (self.free_btc + self.locked_btc) * float(market_price['price'])
                    
                    elif asset == 'PYTH':
                        self.free_pyth = float(balance.get('free', 0))
                        self.locked_pyth = float(balance.get('locked'))
                        self.total_after_sale_pyth += (self.free_pyth + self.locked_pyth) * float(market_price['price'])
                    
                    elif asset == 'DOT':
                        self.free_dot = float(balance.get('free', 0))
                        self.locked_dot = float(balance.get('locked'))
                        self.total_after_sale_dot += (self.free_dot + self.locked_dot) * float(market_price['price'])
                
                return account
            except (httpx.HTTPError, ValueError, IndexError):
                return None
    
    async def get_all_orders(self, start_time: int = None, end_time: int = None, limit: int = 500):
        
        params = {
            'symbol': self.symbol,
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000),
            'limit': min(limit, 1000)
        }
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        params['signature'] = self._generate_signature(params)
        
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f'{BASE_URL}/allOrders', headers=headers, params=params)
                response.raise_for_status()
                return response.json()  # Возвращаем JSON с результатом
            except httpx.RequestError as exc:
                logger.warning(f"HTTP запрос завершился ошибкой: {exc}")
            except httpx.HTTPStatusError as exc:
                logger.warning(f"Ошибка статуса HTTP: {exc.response.status_code}")
            except ValueError:
                logger.warning("Ошибка преобразования ответа в JSON")
            return None
