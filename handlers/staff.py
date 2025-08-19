from __future__ import annotations

from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import ACTIVITY_TYPES, STATUS_ACTIVE
from keyboards.staff import (
    staff_main_kb,
    clients_inline_kb,
    activity_types_inline_kb,
)
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT

router = Router()

# ---------- ناوبری پنل نیرو ----------
@router.callback_query(F.data == "staff_menu")
async def staff_menu(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("پنل نیروی مارکتینگ:", reply_markup=staff_main_kb())

# ---------- ثبت فعالیت جدید ----------
class AddActivity(StatesGroup):
    pick_client = State()
    pick_type = State()
    platform = State()
    ts = State()
    goal = State()
    evidence = State()
    initial_result = State()
    confirm = State()

@router.callback_query(F.data == "staff_add_activity")
async def add_activity_start(cb: types.CallbackQuery, state: FSMContext):
    """شروع فرم ثبت فعالیت: انتخاب مشتریِ تحت پوشش نیرو"""
    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        user = await crud.get_user_by_telegram_id(session, staff_tg)
        if not user or user.status != STATUS_ACTIVE:
            await cb.message.answer("⚠️ دسترسی شما به عنوان نیروی فعال تأیید نشد.")
            return
        clients = await crud.list_clients_for_staff(session, user.id)

    if not clients:
        await cb.message.answer("هیچ مشتری فعالی برای شما تعریف نشده است.")
        return

    await state.set_state(AddActivity.pick_client)
    await cb.message.answer("مشتری را انتخاب کنید:", reply_markup=clients_inline_kb(clients))

@router.callback_query(AddActivity.pick_client, F.data.startswith("staff_pick_client:"))
async def add_activity_pick_client(cb: types.CallbackQuery, state: FSMContext):
    """پس از انتخاب مشتری، رفتن به انتخاب نوع فعالیت (دکمه‌ای/تایپی)"""
    client_id = int(cb.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        client = await crud.get_client_by_id(session, client_id)
    if not client:
        await cb.message.answer("❌ مشتری یافت نشد. دوباره انتخاب کنید.")
        return

    await state.update_data(client_id=client_id, client_name=client.business_name)
    await state.set_state(AddActivity.pick_type)
    await cb.message.answer(
        "نوع فعالیت را انتخاب کنید یا «سایر» را بزنید:",
        reply_markup=activity_types_inline_kb(ACTIVITY_TYPES or [])
    )

@router.callback_query(AddActivity.pick_type, F.data.startswith("act_type:"))
async def add_activity_pick_type(cb: types.CallbackQuery, state: FSMContext):
    """اگر نوع فعالیت با دکمه انتخاب شد"""
    val = cb.data.split(":", 1)[1]
    if val == "other":
        # ورود تایپی در پیام بعد
        await state.set_state(AddActivity.pick_type)
        await cb.message.answer("نوع فعالیت را تایپ کنید:", reply_markup=back_reply_kb())
        return

    await state.update_data(activity_type=val)
    await state.set_state(AddActivity.platform)
    await cb.message.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، سایت… یا -)", reply_markup=back_reply_kb())

@router.message(AddActivity.pick_type)
async def add_activity_type_text(msg: types.Message, state: FSMContext):
    """اگر «سایر (تایپی)» انتخاب شد، اینجا نوع فعالیت را دریافت می‌کنیم"""
    if msg.text == BACK_TEXT:
        await msg.answer(
            "نوع فعالیت را انتخاب کنید:",
            reply_markup=activity_types_inline_kb(ACTIVITY_TYPES or [])
        )
        return
    raw = (msg.text or "").strip()
    if not raw:
        await msg.answer("❌ نوع فعالیت نمی‌تواند خالی باشد.")
        return

    await state.update_data(activity_type=raw)
    await state.set_state(AddActivity.platform)
    await msg.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، سایت… یا -)", reply_markup=back_reply_kb())

@router.message(AddActivity.platform)
async def add_activity_platform(msg: types.Message, state: FSMContext):
    """پلتفرم هدف (اختیاری)"""
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_type)
        await msg.answer(
            "نوع فعالیت را انتخاب کنید:",
            reply_markup=activity_types_inline_kb(ACTIVITY_TYPES or [])
        )
        return

    platform = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(platform=platform)
    await state.set_state(AddActivity.ts)
    await msg.answer("تاریخ/ساعت فعالیت؟ (فرمت: YYYY-MM-DD HH:MM یا «-» برای اکنون)", reply_markup=back_reply_kb())

@router.message(AddActivity.ts)
async def add_activity_ts(msg: types.Message, state: FSMContext):
    """زمان فعالیت: یا «-» برای اکنون، یا فرمت مشخص"""
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.platform)
        await msg.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، سایت… یا -)", reply_markup=back_reply_kb())
        return

    val = (msg.text or "").strip()
    if val == "-":
        ts = datetime.utcnow()
    else:
        try:
            ts = datetime.strptime(val, "%Y-%m-%d %H:%M")
        except ValueError:
            await msg.answer("❌ فرمت نادرست است. نمونه صحیح: 2025-08-18 14:30 یا «-»")
            return

    await state.update_data(ts=ts.isoformat())
    await state.set_state(AddActivity.goal)
    await msg.answer("هدف فعالیت؟ (کوتاه یا «-»)", reply_markup=back_reply_kb())

@router.message(AddActivity.goal)
async def add_activity_goal(msg: types.Message, state: FSMContext):
    """هدف فعالیت (اختیاری)"""
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.ts)
        await msg.answer("تاریخ/ساعت فعالیت؟ (YYYY-MM-DD HH:MM یا «-»)", reply_markup=back_reply_kb())
        return

    goal = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(goal=goal)
    await state.set_state(AddActivity.evidence)
    await msg.answer("لینک/مدرک؟ (URL یا «-»)", reply_markup=back_reply_kb())

@router.message(AddActivity.evidence)
async def add_activity_evidence(msg: types.Message, state: FSMContext):
    """مدرک/لینک (اختیاری)"""
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.goal)
        await msg.answer("هدف فعالیت؟ (کوتاه یا «-»)", reply_markup=back_reply_kb())
        return

    ev = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(evidence=ev)
    await state.set_state(AddActivity.initial_result)
    await msg.answer("نتیجه اولیه (عدد/توضیح کوتاه یا «-»):", reply_markup=back_reply_kb())

@router.message(AddActivity.initial_result)
async def add_activity_initial_result(msg: types.Message, state: FSMContext):
    """نتیجه اولیه (اختیاری) + پیش‌نمایش"""
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.evidence)
        await msg.answer("لینک/مدرک؟ (URL یا «-»)", reply_markup=back_reply_kb())
        return

    init_res = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(initial_result=init_res)

    data = await state.get_data()
    client_name = data.get("client_name") or f"#{data.get('client_id')}"
    ts_h = data.get("ts") or "-"

    preview = (
        "📌 پیش‌نمایش فعالیت\n\n"
        f"- مشتری: {client_name}\n"
        f"- نوع فعالیت: {data.get('activity_type')}\n"
        f"- پلتفرم: {data.get('platform') or '-'}\n"
        f"- تاریخ/ساعت: {ts_h}\n"
        f"- هدف: {data.get('goal') or '-'}\n"
        f"- مدرک: {data.get('evidence') or '-'}\n"
        f"- نتیجه اولیه: {data.get('initial_result') or '-'}\n\n"
        "آیا ثبت شود؟"
    )
    await state.set_state(AddActivity.confirm)
    await msg.answer(preview)
    # همیشه یک متن غیرفارغ قبل از کیبورد بده تا خطای text must be non-empty نگیریم
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("act_confirm", "act_cancel"))

@router.callback_query(AddActivity.confirm, F.data.in_({"act_confirm", "act_cancel"}))
async def add_activity_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    """تأیید/لغو ثبت فعالیت"""
    if cb.data == "act_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=staff_main_kb())
        return

    data = await state.get_data()

    # حداقل‌های لازم را چک کنیم تا اگر state ناقص شد، ارور نده
    required = ("client_id", "activity_type", "ts")
    if any(k not in data or data[k] in (None, "") for k in required):
        await state.clear()
        await cb.message.answer("⚠️ اطلاعات فرم ناقص است. لطفاً مجدداً تلاش کنید.", reply_markup=staff_main_kb())
        return

    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        user = await crud.get_user_by_telegram_id(session, staff_tg)
        if not user:
            await state.clear()
            await cb.message.answer("⚠️ کاربر یافت نشد.", reply_markup=staff_main_kb())
            return

        act = await crud.create_activity(
            session,
            client_id=data["client_id"],
            staff_id=user.id,
            activity_type=data["activity_type"],
            platform=data.get("platform"),
            ts=datetime.fromisoformat(data["ts"]),
            goal=data.get("goal"),
            evidence_link=data.get("evidence"),
            initial_result=data.get("initial_result"),
        )
        await crud.log_action(
            session,
            action="CREATE",
            entity="Activity",
            entity_id=act.id,
            diff_json=data
        )

    await state.clear()
    await cb.message.answer("✅ فعالیت ثبت شد.", reply_markup=staff_main_kb())
