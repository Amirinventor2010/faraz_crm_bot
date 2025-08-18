from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from keyboards.staff import staff_main_kb, clients_inline_kb
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT
from utils.constants import ACTIVITY_TYPES

router = Router()

@router.callback_query(F.data == "staff_menu")
async def staff_menu(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("پنل نیروی مارکتینگ:", reply_markup=staff_main_kb())

class AddActivity(StatesGroup):
    choose_client = State()
    activity_type = State()
    platform = State()
    ts = State()
    goal = State()
    evidence_link = State()
    initial_result = State()
    confirm = State()

@router.callback_query(F.data == "staff_add_activity")
async def staff_add_activity_start(cb: types.CallbackQuery, state: FSMContext):
    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        staff = await crud.get_user_by_telegram_id(session, staff_tg)
        clients = await crud.list_clients_for_staff(session, staff.id) if staff else []
    if not clients:
        await cb.message.answer("⚠️ هنوز مشتری‌ای به شما تخصیص داده نشده.")
        return
    await state.set_state(AddActivity.choose_client)
    await cb.message.answer("لطفاً مشتری را انتخاب کنید:", reply_markup=clients_inline_kb(clients))

@router.callback_query(AddActivity.choose_client, F.data.startswith("staff_pick_client:"))
async def staff_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await state.set_state(AddActivity.activity_type)
    types_text = "، ".join(ACTIVITY_TYPES)
    await cb.message.answer(
        f"نوع فعالیت؟ (یکی از موارد: {types_text})",
        reply_markup=back_reply_kb()
    )

@router.message(AddActivity.activity_type)
async def staff_activity_type(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        async with AsyncSessionLocal() as session:
            me = await crud.get_user_by_telegram_id(session, msg.from_user.id)
            clients = await crud.list_clients_for_staff(session, me.id) if me else []
        await state.set_state(AddActivity.choose_client)
        await msg.answer("لطفاً مشتری را انتخاب کنید:", reply_markup=clients_inline_kb(clients))
        return
    raw = (msg.text or "").strip()
    if raw not in ACTIVITY_TYPES:
        await msg.answer("❌ نوع فعالیت معتبر نیست.")
        return
    await state.update_data(activity_type=raw)
    await state.set_state(AddActivity.platform)
    await msg.answer("پلتفرم هدف؟ (مثلاً Instagram / Telegram / Website … یا -)", reply_markup=back_reply_kb())

@router.message(AddActivity.platform)
async def staff_platform(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.activity_type)
        await msg.answer("نوع فعالیت؟", reply_markup=back_reply_kb())
        return
    platform = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(platform=platform)
    await state.set_state(AddActivity.ts)
    await msg.answer("تاریخ و ساعت فعالیت؟ (YYYY-MM-DD HH:MM یا - برای اکنون)", reply_markup=back_reply_kb())

@router.message(AddActivity.ts)
async def staff_ts(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.platform)
        await msg.answer("پلتفرم هدف؟", reply_markup=back_reply_kb())
        return
    ts = msg.text.strip()
    ts_value = None if ts == '-' else ts
    await state.update_data(ts=ts_value)
    await state.set_state(AddActivity.goal)
    await msg.answer("هدف فعالیت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())

@router.message(AddActivity.goal)
async def staff_goal(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.ts)
        await msg.answer("تاریخ و ساعت فعالیت؟ (YYYY-MM-DD HH:MM یا - برای اکنون)", reply_markup=back_reply_kb())
        return
    goal = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(goal=goal)
    await state.set_state(AddActivity.evidence_link)
    await msg.answer("لینک یا مدرک (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())

@router.message(AddActivity.evidence_link)
async def staff_evidence(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.goal)
        await msg.answer("هدف فعالیت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    link = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(evidence_link=link)
    await state.set_state(AddActivity.initial_result)
    await msg.answer("نتیجه اولیه (عدد یا توضیح کوتاه – اختیاری، برای عبور -):", reply_markup=back_reply_kb())

@router.message(AddActivity.initial_result)
async def staff_initial_result(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddActivity.evidence_link)
        await msg.answer("لینک یا مدرک (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    res = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(initial_result=res)

    data = await state.get_data()
    platforms_h = data.get("platform") or "-"
    ts_h = data.get("ts") or "اکنون"
    goal_h = data.get("goal") or "-"
    link_h = data.get("evidence_link") or "-"
    res_h = data.get("initial_result") or "-"

    preview = (
        "📌 پیش‌نمایش فعالیت\n\n"
        f"- مشتری ID: {data.get('client_id')}\n"
        f"- نوع فعالیت: {data.get('activity_type')}\n"
        f"- پلتفرم: {platforms_h}\n"
        f"- تاریخ/ساعت: {ts_h}\n"
        f"- هدف: {goal_h}\n"
        f"- مدرک: {link_h}\n"
        f"- نتیجه اولیه: {res_h}\n\n"
        "ثبت شود؟"
    )
    await state.set_state(AddActivity.confirm)
    await msg.answer(preview)
    await msg.answer("لطفاً یکی را انتخاب کنید:", reply_markup=confirm_inline_kb("act_confirm", "act_cancel"))

@router.callback_query(AddActivity.confirm, F.data.in_({"act_confirm", "act_cancel"}))
async def staff_act_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "act_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=staff_main_kb())
        return

    data = await state.get_data()
    staff_tg = cb.from_user.id

    async with AsyncSessionLocal() as session:
        staff = await crud.get_user_by_telegram_id(session, staff_tg)
        if not staff:
            await state.clear()
            await cb.message.answer("⚠️ شما به‌عنوان نیرو ثبت نشده‌اید.", reply_markup=staff_main_kb())
            return

        payload = {
            "client_id": data.get("client_id"),
            "staff_id": staff.id,
            "activity_type": data.get("activity_type"),
            "platform": data.get("platform"),
            "goal": data.get("goal"),
            "evidence_link": data.get("evidence_link"),
            "initial_result": data.get("initial_result"),
        }
        if data.get("ts") not in (None, "-"):
            payload["ts"] = data.get("ts")

        if not payload["client_id"] or not payload["activity_type"]:
            await state.clear()
            await cb.message.answer("❌ داده‌های ضروری ناقص است.", reply_markup=staff_main_kb())
            return

        await crud.create_activity(session, **payload)

    await state.clear()
    await cb.message.answer("✅ فعالیت ثبت شد.", reply_markup=staff_main_kb())
