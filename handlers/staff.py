from __future__ import annotations

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from typing import Optional

from keyboards.staff import staff_main_kb, staff_back_kb, clients_inline_kb
from keyboards.common import confirm_inline_kb, BACK_TEXT
from db.base import AsyncSessionLocal
from db import crud

router = Router()

# ---------------------- ابزار کمکی ----------------------
def _parse_dt_or_now(raw: Optional[str]) -> datetime:
    """
    اگر raw == "-" یا خالی → الان
    اگر فرمت "YYYY-MM-DD HH:MM" یا "YYYY/MM/DD HH:MM" بود → همان زمان
    در غیر این صورت → الان
    """
    if not raw or raw.strip() == "-":
        return datetime.utcnow()
    raw = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return datetime.utcnow()

# ---------------------- وضعیت‌ها ----------------------
class AddActivity(StatesGroup):
    pick_client = State()
    pick_type = State()
    pick_platform = State()
    pick_ts = State()
    pick_goal = State()
    pick_evidence = State()
    pick_result = State()
    confirm = State()

# ---------------------- ثبت فعالیت ----------------------
@router.callback_query(F.data == "staff_add_activity")
async def staff_add_activity_start(cb: types.CallbackQuery, state: FSMContext):
    user_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        me = await crud.get_user_by_telegram_id(session, user_tg)
        clients = await crud.list_clients_for_staff(session, me.id) if me else []
    if not me:
        await cb.message.answer("⚠️ حساب نیروی مارکتینگ شما یافت نشد.")
        return
    if not clients:
        await cb.message.answer("هیچ مشتریِ تخصیص‌یافته‌ای برای شما یافت نشد.", reply_markup=staff_main_kb())
        return

    await state.set_state(AddActivity.pick_client)
    await cb.message.answer("مشتری را انتخاب کنید:", reply_markup=clients_inline_kb(clients))

@router.callback_query(AddActivity.pick_client, F.data.startswith("staff_pick_client:"))
async def staff_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await state.set_state(AddActivity.pick_type)
    await cb.message.answer("نوع فعالیت؟ (مثال: پست، استوری، کمپین، DM، ...)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_type)
async def staff_type(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("لغو شد.", reply_markup=staff_main_kb())
        return
    t = (msg.text or "").strip()
    if not t:
        await msg.answer("❌ نوع فعالیت خالی است.")
        return
    await state.update_data(activity_type=t)
    await state.set_state(AddActivity.pick_platform)
    await msg.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، دیوار، ... یا -)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_platform)
async def staff_platform(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_type)
        await msg.answer("نوع فعالیت؟", reply_markup=staff_back_kb())
        return
    platform = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(platform=platform)
    await state.set_state(AddActivity.pick_ts)
    await msg.answer("تاریخ/ساعت فعالیت؟ (مثال: 2025-08-18 18:00 یا - برای اکنون)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_ts)
async def staff_ts(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_platform)
        await msg.answer("پلتفرم هدف؟", reply_markup=staff_back_kb())
        return
    ts_dt = _parse_dt_or_now(msg.text)
    await state.update_data(ts=ts_dt)
    await state.set_state(AddActivity.pick_goal)
    await msg.answer("هدف فعالیت؟ (جمله کوتاه یا -)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_goal)
async def staff_goal(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_ts)
        await msg.answer("تاریخ/ساعت فعالیت؟", reply_markup=staff_back_kb())
        return
    goal = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(goal=goal)
    await state.set_state(AddActivity.pick_evidence)
    await msg.answer("لینک/مدرک؟ (URL یا -)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_evidence)
async def staff_evidence(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_goal)
        await msg.answer("هدف فعالیت؟", reply_markup=staff_back_kb())
        return
    evidence = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(evidence_link=evidence)
    await state.set_state(AddActivity.pick_result)
    await msg.answer("نتیجه اولیه؟ (عدد یا توضیح کوتاه یا -)", reply_markup=staff_back_kb())

@router.message(AddActivity.pick_result)
async def staff_result(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_evidence)
        await msg.answer("لینک/مدرک؟", reply_markup=staff_back_kb())
        return
    result = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(initial_result=result)

    data = await state.get_data()
    ts_show = data.get("ts")
    if isinstance(ts_show, datetime):
        ts_show = ts_show.strftime("%Y-%m-%d %H:%M UTC")

    preview = (
        "📌 پیش‌نمایش فعالیت\n\n"
        f"مشتری: #{data['client_id']}\n"
        f"نوع: {data['activity_type']}\n"
        f"پلتفرم: {data.get('platform') or '-'}\n"
        f"زمان: {ts_show}\n"
        f"هدف: {data.get('goal') or '-'}\n"
        f"مدرک: {data.get('evidence_link') or '-'}\n"
        f"نتیجه اولیه: {data.get('initial_result') or '-'}\n\n"
        "ثبت شود؟"
    )
    await state.set_state(AddActivity.confirm)

    # 1) جمع کردن کیبورد Reply با پیام غیرخالی
    await msg.answer("لطفاً پیش‌نمایش را بررسی کنید.", reply_markup=types.ReplyKeyboardRemove())
    # 2) ارسال پیش‌نمایش همراه با کیبورد اینلاین تأیید/لغو
    await msg.answer(preview, reply_markup=confirm_inline_kb("act_ok", "act_cancel"))

@router.callback_query(AddActivity.confirm, F.data.in_({"act_ok", "act_cancel"}))
async def staff_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "act_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=staff_main_kb())
        return

    user_tg = cb.from_user.id
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        me = await crud.get_user_by_telegram_id(session, user_tg)
        await crud.create_activity(
            session,
            client_id=data["client_id"],
            staff_id=me.id,
            activity_type=data["activity_type"],
            platform=data.get("platform"),
            ts=data.get("ts"),  # datetime
            goal=data.get("goal"),
            evidence_link=data.get("evidence_link"),
            initial_result=data.get("initial_result"),
        )

    await state.clear()
    await cb.message.answer("✅ فعالیت ثبت شد.", reply_markup=staff_main_kb())
