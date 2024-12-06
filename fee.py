from aiogram import Bot, F, types, Router
from aiogram.fsm.context import FSMContext

from db import set_commission_percent, user_get_any
from keyboards import user_commission_choices
from parameters import delete_message

fee_router = Router()

async def get_user_commission_keybs(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    message_id_callback = data.get("message_id_callback")
    commission_dict = {
        0.010: 'Mейкер: 0.050% | Tейкер: 0.050% % ✅',
        0.080: 'Mейкер: 0.040% | Tейкер: 0.040% % ✅',
        0.050: 'Mейкер: 0.025% | Tейкер: 0.025% % ✅'}
    
    await delete_message(user_id, message_id_callback, bot)
    user_commission = await user_get_any(user_id, commission_percent='commission_percent')
    final_text = f"Сейчас у вас установленна комиссия:\n {commission_dict.get(round(user_commission, 3))}"
    sent_message = await bot.send_message(user_id, f"{final_text}\n\n<b>Выберите комиссию:</b>",
                                          reply_markup=await user_commission_choices())
    await state.update_data(message_id=sent_message.message_id)



@fee_router.callback_query(F.data.startswith('set_user_commission_'))
async def set_user_commission(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    data = await state.get_data()
    message_id_callback = data.get("message_id")

    if callback_data == 'set_user_commission_1':
        await set_commission_percent(user_id, 0.010)
        await callback_query.answer("Вы выбрали Mейкер: 0.050% | Tейкер: 0.050% % ✅", show_alert=True)
    elif callback_data == 'set_user_commission_2':
        await set_commission_percent(user_id, 0.080)
        await callback_query.answer("Вы выбрали Mейкер: 0.040% | Tейкер: 0.040% % ✅", show_alert=True)
    elif callback_data == 'set_user_commission_3':
        await set_commission_percent(user_id, 0.050)
        await callback_query.answer("Вы выбрали Mейкер: 0.025% | Tейкер: 0.025% % ✅", show_alert=True)
    await delete_message(user_id, message_id_callback, bot)
    