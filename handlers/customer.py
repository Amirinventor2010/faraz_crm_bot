from __future__ import annotations

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime

from db.base import AsyncSessionLocal
from db import crud
from keyboards.customer import customer_main_kb, feedback_score_kb
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT
from utils.ui import edit_or_send
from utils.notify import notify_client_feedback  # 🔔 ارسال نوتیفیکیشن بازخورد به گروه/تاپیک

router = Router()

# ---------- ناوبری ----------
@router.callback_query(F.data == "customer_menu")
async def customer_menu(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send(cb, "پنل مشتری:", customer_main_kb())

# ---------- فرم ثبت بازخورد ----------
class AddFeedback(StatesGroup):
    waiting_score = State()
    waiting_comment = State()
    waiting_confirm = State()

@router.callback_query(F.data == "customer_add_feedback")
async def customer_add_feedback_start(cb: types.CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    async with AsyncSessionLocal() as session:
        client = await crud.get_client_by_telegram_id(session, tg_id)
    if not client:
        await edit_or_send(cb, "⚠️ شما به عنوان مشتری ثبت نشده‌اید.", customer_main_kb())
        return

    await state.update_data(client_id=client.id, client_name=client.business_name)
    await state.set_state(AddFeedback.waiting_score)
    await cb.message.answer("لطفاً امتیاز خود را انتخاب کنید (۱ تا ۵):", reply_markup=feedback_score_kb())

@router.callback_query(AddFeedback.waiting_score, F.data.startswith("fb_score:"))
async def customer_feedback_pick_score(cb: types.CallbackQuery, state: FSMContext):
    score = int(cb.data.split(":")[1])
    if score < 1 or score > 5:
        await cb.message.answer("❌ امتیاز نامعتبر است.")
        return
    await state.update_data(score=score)
    await state.set_state(AddFeedback.waiting_comment)
    await cb.message.answer("توضیح اختیاری خود را بنویسید (یا «-» برای عبور):", reply_markup=back_reply_kb())

@router.message(AddFeedback.waiting_comment)
async def customer_feedback_comment(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddFeedback.waiting_score)
        await msg.answer("لطفاً امتیاز خود را انتخاب کنید (۱ تا ۵):", reply_markup=feedback_score_kb())
        return

    comment = None if (msg.text or "").strip() == "-" else (msg.text or "").strip()
    await state.update_data(comment=comment)

    data = await state.get_data()
    preview = (
        "📌 پیش‌نمایش بازخورد\n\n"
        f"- مشتری: {data.get('client_name')}\n"
        f"- امتیاز: {data.get('score')}\n"
        f"- توضیح: {data.get('comment') or '-'}\n\n"
        "آیا ارسال شود؟"
    )
    await state.set_state(AddFeedback.waiting_confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("fb_confirm", "fb_cancel"))

@router.callback_query(AddFeedback.waiting_confirm, F.data.in_({"fb_confirm", "fb_cancel"}))
async def customer_feedback_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "fb_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد.", customer_main_kb())
        return

    data = await state.get_data()
    if "client_id" not in data or "score" not in data:
        await state.clear()
        await edit_or_send(cb, "⚠️ اطلاعات ناقص است. لطفاً دوباره تلاش کنید.", customer_main_kb())
        return

    # ذخیره بازخورد + لاگ و سپس ارسال به گروه/تاپیک (در صورت تنظیم در .env)
    async with AsyncSessionLocal() as session:
        fb = await crud.create_feedback(
            session,
            client_id=data["client_id"],
            score=int(data["score"]),
            comment=data.get("comment"),
        )
        await crud.log_action(
            session,
            action="CREATE",
            entity="Feedback",
            entity_id=fb.id,
            diff_json=data
        )
        client = await crud.get_client_by_id(session, data["client_id"])

    # 🔔 نوتیفای گروه/تاپیک «گزارش مشتری‌ها»
    try:
        await notify_client_feedback(cb.message.bot, fb, client=client)
    except Exception:
        # خطای ارسال گروه نباید روند کاربر را خراب کند
        pass

    await state.clear()
    await edit_or_send(cb, "✅ بازخورد شما ثبت شد. ممنون از همکاری شما!", customer_main_kb())

# ---------- گزارش خلاصه مشتری ----------
@router.callback_query(F.data == "customer_summary")
async def customer_summary(cb: types.CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    async with AsyncSessionLocal() as session:
        client = await crud.get_client_by_telegram_id(session, tg_id)
        if not client:
            await cb.message.answer("⚠️ شما به عنوان مشتری ثبت نشده‌اید.")
            return

        act_cnt = await crud.count_activities_for_client(session, client.id)
        fb_avg = await crud.avg_feedback_for_client(session, client.id)

    fb_avg_h = f"{fb_avg:.2f}" if fb_avg is not None else "-"
    txt = (
        "📌 عملکرد تیم مارکتینگ\n\n"
        f"- نام کسب‌وکار: {client.business_name}\n"
        f"- تعداد فعالیت‌ها: {act_cnt}\n"
        f"- KPI پیشرفت: - / - (به‌زودی)\n"
        f"- بازخورد میانگین: {fb_avg_h}\n"
        f"- وضعیت مشتری: - (🟢/🟡/🔴 به‌زودی)\n"
    )
    await cb.message.answer(txt, reply_markup=customer_main_kb())
