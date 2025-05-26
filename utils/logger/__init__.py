import os
import sys
from loguru import logger
from .logger_config import *
from .trading_logs import TradingLogs

logger.remove()
logger.level("BOOT", no=35, color="<cyan>", icon="🚀")

# =========== Консоль ============
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level=CONSOLE_LEVEL,
    colorize=True,
    enqueue=True,
)

# =========== Общий лог-файл ============
if not os.path.exists(BASE_LOGS_DIR):
    os.makedirs(BASE_LOGS_DIR)

logger.add(
    COMMON_LOG_FILE,
    format=FILE_FORMAT,
    level=FILE_LEVEL,
    rotation=ROTATION,
    retention=RETENTION,
    compression=COMPRESSION,
    enqueue=True,
)

# =========== Динамическое добавление файлов для пользователей ===========

# Словарь вида {user_id: handler_id}
_user_loggers = {}

def add_user_logger(user_id: int, symbol: str):

    if not os.path.exists(USER_LOGS_DIR):
        os.makedirs(USER_LOGS_DIR)

    file_key = f"{user_id}_{symbol}"
    log_file = os.path.join(USER_LOGS_DIR, f"{file_key}.log")

    if file_key in _user_loggers:
        return

    handler_id = logger.add(
        log_file,
        format=FILE_FORMAT,
        level=FILE_LEVEL,
        rotation=ROTATION,
        retention=RETENTION,
        compression=COMPRESSION,
        enqueue=True,
        filter=lambda record: (
                record["extra"].get("user_id") == user_id and
                record["extra"].get("symbol") == symbol
        )
    )

    _user_loggers[file_key] = handler_id

def get_user_logger(user_id: int, symbol: str):
    """
    Возвращает логгер, привязанный к конкретному пользователю.
    """
    add_user_logger(user_id, symbol)
    return logger.bind(user_id=user_id, symbol=symbol)

