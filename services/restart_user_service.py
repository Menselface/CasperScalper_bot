import asyncio

from aiogram import Bot
from loguru import logger

from db_pack.repositories import GetUsersRepo
from services.admins.admins_message import AdminsMessageService


class RestartUserService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def restart_all_active_users(self, notify_admin_id: bool = False):
        logger.info("🔄 Рестарт всех активных пользователей")
        get_users_repo = GetUsersRepo()
        users = await get_users_repo.all_active_id_from_symbols_for_trade()
        # users = [653500570]

        tasks = []
        for user in users:
            try:
                res = await get_users_repo.first_user_message_obj(user)
                task = asyncio.create_task(self.restart_user_from_admin(res))
                tasks.append(task)
            except Exception as e:
                logger.warning(
                    f"⚠️ Не удалось подготовить рестарт для user_id={user}: {e}"
                )
                continue

        if notify_admin_id:
            msg = f"Все пользователи запущены! Всего {len(users)}"
            await AdminsMessageService.send_to_all_admins_message_text(msg, self.bot)
        await asyncio.gather(*tasks)

    async def restart_user_from_admin(self, user_data):
        from trading.start_trade import user_restart_from_admin_panel

        try:
            await user_restart_from_admin_panel(user_data, self.bot)
            logger.info(f"✅ Пользователь {user_data.from_user.id} успешно рестартован")
        except Exception as e:
            logger.error(f"❌ Ошибка рестарта пользователя {e}")
