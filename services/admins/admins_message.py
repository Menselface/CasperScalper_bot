import os
import shutil

from aiogram import Bot
from aiogram.types import FSInputFile

from db_pack.repositories import GetUsersRepo
from utils.decorators import send_message_safe_call


class AdminsMessageService:
    user_repo = GetUsersRepo()
    temp_log_main_file = f'logs/loggers_сopy.log'
    temp_log_user_file = f'logs/users'

    @classmethod
    async def get_all_admins_from_db(cls):
        return await cls.user_repo.get_all_admins()
        # return [653500570]

    @classmethod
    @send_message_safe_call(default_return=[])
    async def get_main_logger_file(cls):
        log_file = f'logs/project.log'
        shutil.copy(log_file, cls.temp_log_main_file)
        return  FSInputFile('logs/loggers_сopy.log', filename='loggers_сopy.log')

    @classmethod
    @send_message_safe_call(default_return=[])
    async def get_user_logger_file(cls, user_id: int, symbol: str):
        user_log_file = f'logs/users/{user_id}_{symbol}.log'
        file_name = f"{user_id}_{symbol}.log"
        cls.temp_log_user_file = f"{user_log_file}_copy.log"
        shutil.copy(user_log_file, cls.temp_log_user_file)
        return FSInputFile(cls.temp_log_user_file, filename=file_name)

    @classmethod
    @send_message_safe_call(default_return=[])
    async def remove_copy_main_logger_file(cls):
        os.remove(cls.temp_log_main_file)

    @classmethod
    @send_message_safe_call(default_return=[])
    async def remove_copy_user_logger_file(cls):
        os.remove(cls.temp_log_user_file)

    @classmethod
    @send_message_safe_call(default_return=[])
    async def send_to_all_admins_message_text(cls, message_text: str, bot: Bot):
        all_admins = await cls.get_all_admins_from_db()
        for admin in all_admins:
            await bot.send_message(
                chat_id=admin,
                text=message_text
        )

    @classmethod
    @send_message_safe_call(default_return=[])
    async def send_admin_main_logger_file(cls, bot: Bot, msg: str = None, admin_id: int = None):
        file = await cls.get_main_logger_file()
        if file:
            if not admin_id:
                for admin in await cls.get_all_admins_from_db():
                    await bot.send_document(
                        chat_id=admin,
                        document=file,
                        caption=msg if msg else "."
                    )
                await cls.remove_copy_main_logger_file()
            else:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file,
                    caption=msg if msg else "."
                )

        else:
            await cls.send_to_all_admins_message_text(msg, bot)

    @classmethod
    @send_message_safe_call(default_return=[])
    async def send_admin_user_logger_file(cls, user_id: int, symbol: str, bot: Bot, msg: str = None):
        file = await cls.get_user_logger_file(user_id, symbol)
        if file:
            for admin in await cls.get_all_admins_from_db():
                await bot.send_document(
                    chat_id=admin,
                    document=file,
                    caption=msg if msg else "."
                )
            await cls.remove_copy_user_logger_file()
        else:
            await cls.send_admin_main_logger_file(bot, msg)