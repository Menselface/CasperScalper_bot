import asyncio

from aiogram import Bot
from loguru import logger

from services import RestartUserService


async def on_startup(bot: Bot):
    restart_service = RestartUserService(bot)

    async def safe_restart():
        try:
            await restart_service.restart_all_active_users(notify_admin_id=True)
        except Exception as e:
            logger.error(f"Ошибка при рестарте пользователей: {e}")

    asyncio.create_task(safe_restart())
