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
    await cb.message.edit_text("پنل نیروی مارکتینگ:", reply_markup=staff_main_kb())

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
    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        user = await crud.get_user_by_telegram_id(session, staff_tg)
        if not user or user.status != STATUS_ACTIVE:
            await cb.message.edit_text("⚠️ دسترسی شما به عنوان نیروی فعال تأیید نشد.", reply_markup=staff_main_kb())
            return
        clients = await crud.list_clients_for_staff(session, user.id)

    if not clients:
        await cb.message.edit_text("هیچ مشتری فعالی برای شما تعریف نشده است.", reply_markup=staff_main_kb())
        return

    await state.set_state(AddActivity.pick_client)
    # منوی انتخاب مشتری جایگزین منوی قبلی شود
    await cb.message.edit_text("مشتری را انتخاب کنید:", reply_markup=clients_inline_kb(clients))

@router.callback_query(AddActivity.pick_client, F.data.startswith("staff_pick_client:"))
async def add_activity_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await state.set_state(AddActivity.pick_type)
    await cb.message.edit_text("نوع فعالیت را انتخاب کنید یا «سایر» را بزنید:", reply_markup=activity_types_inline_kb(ACTIVITY_TYPES))

@router.callback_query(AddActivity.pick_type, F.data.startswith("act_type:"))
async def add_activity_pick_type(cb: types.CallbackQuery, state: FSMContext):
    val = cb.data.split(":", 1)[1]
    if val == "other":
        await state.set_state(AddActivity.pick_type)
        await cb.message.edit_text("نوع فعالیت را تایپ کنید:", reply_markup=None)
        return
    await state.update_data(activity_type=val)
    await state.set_state(AddActivity.platform)
    await cb.message.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، سایت… یا -)", reply_markup=back_reply_kb())

@router.message(AddActivity.pick_type)
async def add_activity_type_text(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await msg.answer("نوع فعالیت را انتخاب کنید:", reply_markup=activity_types_inline_kb(ACTIVITY_TYPES))
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
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.pick_type)
        await msg.answer("نوع فعالیت را انتخاب کنید:", reply_markup=activity_types_inline_kb(ACTIVITY_TYPES))
        return
    platform = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(platform=platform)
    await state.set_state(AddActivity.ts)
    await msg.answer("تاریخ/ساعت فعالیت؟ (فرمت: YYYY-MM-DD HH:MM یا «-» برای اکنون)", reply_markup=back_reply_kb())

@router.message(AddActivity.ts)
async def add_activity_ts(msg: types.Message, state: FSMContext):
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
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.evidence)
        await msg.answer("لینک/مدرک؟ (URL یا «-»)", reply_markup=back_reply_kb())
        return
    init_res = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(initial_result=init_res)

    data = await state.get_data()
    ts_h = data.get("ts")
    preview = (
        "📌 پیش‌نمایش فعالیت\n\n"
        f"- مشتری: {data.get('client_id')}\n"
        f"- نوع فعالیت: {data.get('activity_type')}\n"
        f"- پلتفرم: {data.get('platform') or '-'}\n"
        f"- تاریخ/ساعت: {ts_h}\n"
        f"- هدف: {data.get('goal') or '-'}\n"
        f"- مدرک: {data.get('evidence') or '-'}\n"
        f"- نتیجه اولیه: {data.get('initial_result') or '-'}\n\n"
        "آیا ثبت شود؟"
    )
    await state.set_state(AddActivity.confirm)
    await msg.answer(preview, reply_markup=confirm_inline_kb("act_confirm", "act_cancel"))

@router.callback_query(AddActivity.confirm, F.data.in_({"act_confirm", "act_cancel"}))
async def add_activity_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "act_cancel":
        await state.clear()
        await cb.message.edit_text("پنل نیروی مارکتینگ:", reply_markup=staff_main_kb())
        return

    data = await state.get_data()
    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        user = await crud.get_user_by_telegram_id(session, staff_tg)
        if not user:
            await state.clear()
            await cb.message.edit_text("⚠️ کاربر یافت نشد.", reply_markup=staff_main_kb())
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
        await crud.log_action(session, action="CREATE", entity="Activity", entity_id=act.id, diff_json=data)

    await state.clear()
    await cb.message.edit_text("✅ فعالیت ثبت شد.\nپنل نیروی مارکتینگ:", reply_markup=staff_main_kb())
