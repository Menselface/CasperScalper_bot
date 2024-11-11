import hashlib
import hmac
import requests
import time
from urllib.parse import urlencode

from config import BASE_URL

def check_user_own_commission(api_key, api_secret):
    symbol = "KASUSDT"
    params = {
        'symbol': symbol,
        'recvWindow': 5000,
        'timestamp': int(time.time() * 1000)
    }
    
    query_string = urlencode(params)
    
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    params['signature'] = signature
    headers = {
        'X-MEXC-APIKEY': api_key
    }
    res = requests.get(f'{BASE_URL}/tradeFee', headers=headers, params=params)
    result = res.json()
    if result['data']:
        return result['data']
    else:
        return False
