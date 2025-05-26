import os

BASE_LOGS_DIR = "logs"
USER_LOGS_DIR = os.path.join(BASE_LOGS_DIR, "users")
COMMON_LOG_FILE = os.path.join(BASE_LOGS_DIR, "project.log")


FILE_FORMAT = (
    "<white>{time:YYYY-MM-DD HH:mm:ss}</white>"
    " | <level>{level: <8}</level>"
    " | <cyan>{module}:{line}</cyan>"
    " | <white><b>{message}</b></white>"
)
LOG_FORMAT = (
    "<white>{time:YYYY-MM-DD HH:mm:ss}</white> | "
    "<level>{level.icon} {level: <8}</level> | "
    "<cyan>{module}:{line}</cyan> | "
    "<m><b>{message}</b></m>"
)

CONSOLE_LEVEL = "WARNING"
FILE_LEVEL = "INFO"

ROTATION = "50 MB"
RETENTION = "5 days"
COMPRESSION = "gz"