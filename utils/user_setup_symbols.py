from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import PAIR_TABLE_MAP
from keyboards import user_set_up_keyboard, UserSymbolsConfig
from parameters import delete_message
from trading.db_querys.db_symbols_for_trade_methods import user_get_any_symbols, get_user_exist_with_symbol, user_update_symbols, \
    user_update_by_symbol, add_user, user_get_any_by_symbol
from trading.sesison_manager_start_stop import UserSessionManagerStartStop, user_start_stop

user_setup_router = Router()


async def user_set_up(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    await user_start_stop.remove_user(user_id)
    text = ("<b>Управление торговлей:</b>\n"
        "Зелёная галочка ✅ — бот торгует этой монетой.\n"
        "1. ✅ Отметь галочкой пару, которой хочешь торговать.\n"
        "2. ❌ Сними галочку с пары, с которой НЕ хочешь торговать.\n"
        "3. Нажми <b>[Подтвердить]</b>.")

    mes = await bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=await user_set_up_keyboard(user_id)
    )
    await state.update_data(message_id=mes.message_id)


@user_setup_router.callback_query(UserSymbolsConfig.filter())
async def user_set_up_callbacks(callback: CallbackQuery, callback_data: UserSymbolsConfig, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    action = callback_data.action
    data = await state.get_data()
    message_id = data.get("message_id")
    symbol_name = action.split("_")[-1]
    for symbol in PAIR_TABLE_MAP.keys():
        user_exist = await get_user_exist_with_symbol(user_id, symbol)
        if not user_exist:
            await add_user(user_id, symbol=symbol, start_stop=False)
        
    
    user_session_start_stop = user_start_stop
    
    if user_id not in user_session_start_stop.sessions:
        await user_session_start_stop.fill_info_from_db(user_id)
    
    if action.startswith("symbol_"):
        user_session_start_stop.change_status(user_id, symbol_name)
    
    new_keyboard = await user_set_up_keyboard(user_id)
    
    if action == "exit":
        await delete_message(user_id, message_id, bot)
        return
    
    await bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=message_id,
        reply_markup=new_keyboard
    )
    
    
            