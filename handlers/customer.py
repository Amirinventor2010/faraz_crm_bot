from __future__ import annotations

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from keyboards.customer import customer_main_kb, customer_back_kb
from keyboards.common import confirm_inline_kb, BACK_TEXT
from db.base import AsyncSessionLocal
from db import crud

router = Router()

class AddFeedback(StatesGroup):
    pick_score = State()
    pick_comment = State()
    confirm = State()

@router.callback_query(F.data == "customer_add_feedback")
async def customer_add_feedback_start(cb: types.CallbackQuery, state: FSMContext):
    user_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        client = await crud.get_client_by_telegram_id(session, user_tg)
    if not client:
        await cb.message.answer("⚠️ شما به عنوان مشتری ثبت نشده‌اید.")
        return

    await state.update_data(client_id=client.id)
    await state.set_state(AddFeedback.pick_score)
    await cb.message.answer("امتیاز ۱ تا ۵ را وارد کنید:", reply_markup=customer_back_kb())

@router.message(AddFeedback.pick_score)
async def customer_pick_score(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("لغو شد.", reply_markup=customer_main_kb())
        return
    if not msg.text.isdigit():
        await msg.answer("❌ لطفاً عدد ۱ تا ۵ وارد کنید.")
        return
    score = int(msg.text)
    if score < 1 or score > 5:
        await msg.answer("❌ امتیاز معتبر ۱ تا ۵ است.")
        return
    await state.update_data(score=score)
    await state.set_state(AddFeedback.pick_comment)
    await msg.answer("توضیح اختیاری؟ (برای عبور، -)", reply_markup=customer_back_kb())

@router.message(AddFeedback.pick_comment)
async def customer_pick_comment(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddFeedback.pick_score)
        await msg.answer("امتیاز ۱ تا ۵ را وارد کنید:", reply_markup=customer_back_kb())
        return
    comment = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(comment=comment)

    data = await state.get_data()
    preview = (
        "📌 پیش‌نمایش بازخورد\n\n"
        f"امتیاز: {data['score']}\n"
        f"توضیح: {data.get('comment') or '-'}\n\n"
        "ارسال شود؟"
    )
    await state.set_state(AddFeedback.confirm)

    # 1) جمع کردن کیبورد Reply با پیام غیرخالی
    await msg.answer("لطفاً پیش‌نمایش را بررسی کنید.", reply_markup=types.ReplyKeyboardRemove())
    # 2) ارسال پیش‌نمایش همراه کیبورد اینلاین تأیید/لغو
    await msg.answer(preview, reply_markup=confirm_inline_kb("fb_ok", "fb_cancel"))

@router.callback_query(AddFeedback.confirm, F.data.in_({"fb_ok", "fb_cancel"}))
async def customer_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "fb_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=customer_main_kb())
        return

    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        await crud.create_feedback(
            session,
            client_id=data["client_id"],
            score=data["score"],
            comment=data.get("comment"),
        )
    await state.clear()
    await cb.message.answer("✅ بازخورد شما ثبت شد. ممنون از همکاری شما!", reply_markup=customer_main_kb())
