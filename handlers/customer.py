from aiogram import Router, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from db.base import AsyncSessionLocal
from db import crud

router = Router()

class FeedbackFlow(StatesGroup):
    score = State()
    comment = State()

@router.callback_query(lambda c: c.data == "cust_feedback")
async def feedback_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(FeedbackFlow.score)
    await cb.message.answer("امتیاز 1 تا 5:")

@router.message(FeedbackFlow.score)
async def feedback_score(msg: types.Message, state: FSMContext):
    try:
        s = int(msg.text)
        assert 1 <= s <= 5
    except:
        await msg.answer("❌ لطفاً عددی بین 1 تا 5 وارد کنید.")
        return
    await state.update_data(score=s)
    await state.set_state(FeedbackFlow.comment)
    await msg.answer("توضیح (اختیاری) – برای عبور، خط تیره بفرستید:")

@router.message(FeedbackFlow.comment)
async def feedback_comment(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    comment = None if msg.text.strip() == "-" else msg.text.strip()
    # MVP: client_id را موقتاً از کاربر بپرسید یا به پروفایل مشتری وصل کنید
    await msg.answer("شناسه مشتری را وارد کنید:")
    await state.clear()
    # در نسخه بعدی: این مرحله را به صورت امن‌تر و لینک شده به کاربر کلاینت انجام می‌دهیم