from functools import wraps

import httpx
from aiogram.exceptions import TelegramBadRequest
from loguru import logger


def db_safe_call(default_return=None, log_result=False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                if log_result:
                    logger.debug(f"[DB RESULT] {func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.warning(f"[DB ERROR] in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


def parameters_safe_call(default_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[Parameters ERROR] in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

def mexc_request_safe_call(default_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except httpx.RequestError as exc:
                logger.warning(f"[HTTPX] Request error: {exc}")
            except httpx.HTTPStatusError as exc:
                logger.warning(f"[HTTPX] Status error: {exc.response.status_code}")
            except ValueError:
                logger.warning("[HTTPX] Failed to decode JSON response")
            return default_return
        return wrapper
    return decorator


def handle_commission_errors(default_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[OCU ERROR] {func.__name__}:{e}")
                return default_return
        return wrapper
    return decorator



def send_message_safe_call(default_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except TelegramBadRequest as e:
                logger.info(f"[TG MSG ERROR] {func.__name__}: {e}")
                return default_return
            except FileNotFoundError as e:
                logger.info(f"[OS FILE ERROR] {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.warning(f"[TG MSG ERROR] {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator
