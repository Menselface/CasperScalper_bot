import asyncio
import time
import hmac
import hashlib

import requests
from urllib.parse import urlencode
import httpx

from config import BASE_URL


class AccountMexcMethods:
    def __init__(self, api_key: str, secret_key: str, symbol: str = 'KASUSDT', recv_window: int = 5000):
        self.api_key = api_key
        self.secret_key = secret_key
        self.symbol = symbol
        self.recv_window = recv_window
    
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
        
        # Генерация подписи
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
            # Обработка случая, если не удается получить корректный JSON
            return None
    
    async def get_open_orders(self):
        params = {
            'symbol': self.symbol,
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
                    print('0')
                    return '0'
            else:
                return None
        except ValueError:
            return None
    
    async def get_order_status(self, order_id: str = None, orig_client_order_id: str = None):
        params = {
            'symbol': self.symbol,
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
            else:
                print('Order not found or an error occurred.')
                return None
        except ValueError:
            print('Failed to decode JSON response.')
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
                
                # Получение средней цены актива
                market_price = await self.get_avg_price()
                
                # Получение баланса USDT и расчет total_after_sale
                self.total_free_usdt = float(account.get('balances')[0]['free'])
                self.total_after_sale = (
                        float(account.get('balances')[0]['free']) +
                        float(account.get('balances')[0]['locked'])
                )
                
                # Если есть больше одного актива в балансе, считаем total_after_sale_Kass
                if len(account.get('balances')) > 1:
                    self.total_after_sale_Kass = float(account.get('balances')[1]['free'])
                    self.total_after_sale += (
                                                     float(account.get('balances')[1]['free']) +
                                                     float(account.get('balances')[1]['locked'])
                                             ) * float(market_price['price'])
                    self.locked = float(account.get('balances')[1]['locked'])
                    self.usdt_locked = float(account.get('balances')[0]['locked'])
                
                return account
            except (httpx.HTTPError, ValueError, IndexError):
                return None


class CreateSpotConn_(AccountMexcMethods):
    def __init__(self, api_key, secret_key, symbol="KASUSDT"):
        super().__init__(api_key, secret_key, symbol)
        self.total_after_sale = None
        self.total_after_sale_Kass = None
        self.total_free_usdt = None
    
    def get_avg_price(self):
        """Получение средней цены актива через API mexc."""
        url = f'{BASE_URL}/avgPrice'
        params = {
            'symbol': self.symbol,
            'timestamp': int(time.time() * 1000)
        }
        headers = self._get_headers()
        res = requests.get(url, headers=headers, params=params)
        try:
            return res.json()
        except ValueError:
            return None
    
    def get_account_info_(self):
        """Получение информации о балансе пользователя и расчет total_after_sale."""
        url = f'{BASE_URL}/account'
        params = {
            'recvWindow': self.recv_window,
            'timestamp': int(time.time() * 1000)
        }
        params['signature'] = self._generate_signature(params)
        headers = self._get_headers()
        
        res = requests.get(url, headers=headers, params=params)
        msg = res.content
        if "Api key info invalid" in str(msg):
            return "Api key info invalid"
        try:
            acount = res.json()
            market_price = self.get_avg_price()
            
            # Получение баланса USDT и расчет total_after_sale
            self.total_free_usdt = float(acount.get('balances')[0]['free'])
            self.total_after_sale = (
                    float(acount.get('balances')[0]['free']) +
                    float(acount.get('balances')[0]['locked'])
            )
            
            if len(acount.get('balances')) > 1:
                self.total_after_sale_Kass = float(acount.get('balances')[1]['free'])
                self.total_after_sale += (
                                                 float(acount.get('balances')[1]['free']) +
                                                 float(acount.get('balances')[1]['locked'])
                                         ) * float(market_price['price'])
            
            return acount
        except (ValueError, IndexError):
            return None
