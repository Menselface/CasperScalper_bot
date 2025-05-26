from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

help_router = Router(name=__name__)


@help_router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "<b>Infinity Bot Pro v.2.250 12-05-2025</b>\n\n"
        "1. Алгоритм работы Бота ➡️ <a href='https://telegra.ph/Princip-raboty-Kaspa-Scalping-Bot-Pro-10-27'>[ЗДЕСЬ]</a>\n\n"
        "2. Частые вопросы ➡️ <a href='https://telegra.ph/CHastye-voprosy-FAQ-Kaspa-Scalping-Bot-10-24'>[FAQ]</a>\n\n"
        "3. Подробнее о Боте в Телеграм ➡️ <a href='https://t.me/KnyazeffCrypto/123'>[КАНАЛ]</a>\n\n"
        "4. ЧАТ➡️ <a href='https://t.me/+TyAYDj2suaJkNWY6'>Чат Infinity Crypto</a>\n\n"
        "5. Поддержка: <a href='https://t.me/Infinty_Support'>@Support_Infinity_Bot</a>"
    )

    await message.reply(help_text, parse_mode="HTML", disable_web_page_preview=True)
