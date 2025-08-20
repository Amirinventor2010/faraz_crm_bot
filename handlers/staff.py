from __future__ import annotations

from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import (
    ACTIVITY_TYPES, STATUS_ACTIVE, KPI_YELLOW_RATIO,
    INACTIVITY_WARN_DAYS, FEEDBACK_WARN_SCORE
)
from keyboards.staff import (
    staff_main_kb,
    clients_inline_kb,
    activity_types_inline_kb,
    sales_clients_inline_kb,
)
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT
from utils.ui import edit_or_send
from utils.notify import notify_activity

router = Router()

# ---------- ناوبری پنل نیرو ----------
@router.callback_query(F.data == "staff_menu")
async def staff_menu(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send(cb, "پنل نیروی مارکتینگ:", staff_main_kb())

# ===================================================================
#                         ثبت فعالیت جدید
# ===================================================================
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
    val = cb.data.split(":", 1)[1]
    if val == "other":
        await state.set_state(AddActivity.pick_type)
        await cb.message.answer("نوع فعالیت را تایپ کنید:", reply_markup=back_reply_kb())
        return

    await state.update_data(activity_type=val)
    await state.set_state(AddActivity.platform)
    await cb.message.answer("پلتفرم هدف؟ (مثال: اینستاگرام، تلگرام، سایت… یا -)", reply_markup=back_reply_kb())

@router.message(AddActivity.pick_type)
async def add_activity_type_text(msg: types.Message, state: FSMContext):
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
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("act_confirm", "act_cancel"))

@router.callback_query(AddActivity.confirm, F.data.in_({"act_confirm", "act_cancel"}))
async def add_activity_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "act_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد.", staff_main_kb())
        return

    data = await state.get_data()
    required = ("client_id", "activity_type", "ts")
    if any(k not in data or data[k] in (None, "") for k in required):
        await state.clear()
        await edit_or_send(cb, "⚠️ اطلاعات فرم ناقص است. لطفاً مجدداً تلاش کنید.", staff_main_kb())
        return

    staff_tg = cb.from_user.id
    async with AsyncSessionLocal() as session:
        user = await crud.get_user_by_telegram_id(session, staff_tg)
        if not user:
            await state.clear()
            await edit_or_send(cb, "⚠️ کاربر یافت نشد.", staff_main_kb())
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

    try:
        await notify_activity(
            cb.message.bot,
            client_name=data.get("client_name"),
            staff_name=(user.name if user else "-"),
            activity_type=data.get("activity_type"),
            platform=data.get("platform"),
            ts_str=data.get("ts"),
            goal=data.get("goal"),
            evidence=data.get("evidence"),
            result=data.get("initial_result"),
        )
    except Exception:
        pass

    await state.clear()
    await edit_or_send(cb, "✅ فعالیت ثبت شد.", staff_main_kb())

# ===================================================================
#                         ثبت فروش توسط نیرو
# ===================================================================
class StaffAddSale(StatesGroup):
    pick_client = State()
    ts = State()
    amount = State()
    source = State()
    note = State()
    confirm = State()

@router.callback_query(F.data == "staff_add_sale")
async def staff_add_sale_start(cb: types.CallbackQuery, state: FSMContext):
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

    await state.set_state(StaffAddSale.pick_client)
    await cb.message.answer("مشتری را برای ثبت فروش انتخاب کنید:", reply_markup=sales_clients_inline_kb(clients))

@router.callback_query(StaffAddSale.pick_client, F.data.startswith("staff_sale_pick_client:"))
async def staff_add_sale_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        client = await crud.get_client_by_id(session, client_id)
    if not client:
        await cb.message.answer("❌ مشتری یافت نشد. دوباره انتخاب کنید.")
        return

    await state.update_data(client_id=client_id, client_name=client.business_name)
    await state.set_state(StaffAddSale.ts)
    await cb.message.answer("تاریخ/ساعت فروش؟ (YYYY-MM-DD HH:MM یا «-» برای اکنون)", reply_markup=back_reply_kb())

@router.message(StaffAddSale.ts)
async def staff_add_sale_ts(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        staff_tg = msg.from_user.id
        async with AsyncSessionLocal() as session:
            user = await crud.get_user_by_telegram_id(session, staff_tg)
            clients = await crud.list_clients_for_staff(session, user.id) if user else []
        await state.set_state(StaffAddSale.pick_client)
        await msg.answer("مشتری را انتخاب کنید:", reply_markup=sales_clients_inline_kb(clients or []))
        return

    val = (msg.text or "").strip()
    if val == "-":
        ts = datetime.utcnow()
    else:
        try:
            ts = datetime.strptime(val, "%Y-%m-%d %H:%M")
        except ValueError:
            await msg.answer("❌ فرمت نادرست است. مثال صحیح: 2025-08-18 14:30 یا «-»")
            return

    await state.update_data(ts=ts.isoformat())
    await state.set_state(StaffAddSale.amount)
    await msg.answer("مبلغ فروش؟ (عدد ≥ 0)", reply_markup=back_reply_kb())

@router.message(StaffAddSale.amount)
async def staff_add_sale_amount(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(StaffAddSale.ts)
        await msg.answer("تاریخ/ساعت فروش؟ (YYYY-MM-DD HH:MM یا «-»)", reply_markup=back_reply_kb())
        return

    try:
        amount = float((msg.text or "").strip())
        if amount < 0:
            raise ValueError()
    except Exception:
        await msg.answer("❌ مبلغ نامعتبر است. یک عدد ≥ 0 وارد کنید.")
        return

    await state.update_data(amount=amount)
    await state.set_state(StaffAddSale.source)
    await msg.answer("منبع/کانال فروش؟ (اختیاری، یا «-»)", reply_markup=back_reply_kb())

@router.message(StaffAddSale.source)
async def staff_add_sale_source(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(StaffAddSale.amount)
        await msg.answer("مبلغ فروش؟ (عدد ≥ 0)", reply_markup=back_reply_kb())
        return

    source = None if (msg.text or "").strip() == "-" else (msg.text or "").strip()
    await state.update_data(source=source)
    await state.set_state(StaffAddSale.note)
    await msg.answer("یادداشت (اختیاری، یا «-»):", reply_markup=back_reply_kb())

@router.message(StaffAddSale.note)
async def staff_add_sale_note(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(StaffAddSale.source)
        await msg.answer("منبع/کانال فروش؟ (اختیاری، یا «-»)", reply_markup=back_reply_kb())
        return

    note = None if (msg.text or "").strip() == "-" else (msg.text or "").strip()
    await state.update_data(note=note)

    data = await state.get_data()
    preview = (
        "📌 پیش‌نمایش فروش\n\n"
        f"- مشتری: {data.get('client_name')} (#{data.get('client_id')})\n"
        f"- زمان: {data.get('ts')}\n"
        f"- مبلغ: {data.get('amount')}\n"
        f"- منبع: {data.get('source') or '-'}\n"
        f"- یادداشت: {data.get('note') or '-'}\n\n"
        "آیا ثبت شود؟"
    )
    await state.set_state(StaffAddSale.confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("staff_sale_confirm", "staff_sale_cancel"))

@router.callback_query(StaffAddSale.confirm, F.data.in_({"staff_sale_confirm", "staff_sale_cancel"}))
async def staff_add_sale_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "staff_sale_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد.", staff_main_kb())
        return

    data = await state.get_data()
    required = ("client_id", "ts", "amount")
    if any(k not in data or data[k] in (None, "") for k in required):
        await state.clear()
        await edit_or_send(cb, "⚠️ اطلاعات فرم ناقص است.", staff_main_kb())
        return

    async with AsyncSessionLocal() as session:
        s = await crud.create_sale(
            session,
            client_id=int(data["client_id"]),
            ts=datetime.fromisoformat(data["ts"]),
            amount=float(data["amount"]),
            source=data.get("source"),
            note=data.get("note"),
        )
        await crud.log_action(session, action="CREATE", entity="Sale", entity_id=s.id, diff_json=data)

    await state.clear()
    await edit_or_send(cb, "✅ فروش ثبت شد.", staff_main_kb())

# ===================================================================
#                    گزارش عملکرد «منِ نیرو» (۷ روز)
# ===================================================================
@router.callback_query(F.data == "staff_my_report")
async def staff_my_report(cb: types.CallbackQuery, state: FSMContext):
    staff_tg = cb.from_user.id
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        me = await crud.get_user_by_telegram_id(session, staff_tg)
        if not me or me.status != STATUS_ACTIVE:
            await edit_or_send(cb, "⚠️ شما نیروی فعال نیستید.", staff_main_kb())
            return

        acts_cnt = await crud.count_activities_in_range_by_staff(session, me.id, start_dt, end_dt)
        clients = await crud.list_clients_for_staff(session, me.id)
        fb_avg = await crud.avg_feedback_for_staff_clients(session, me.id)
        last_ts = await crud.last_activity_ts_for_staff(session, me.id)
        recent_acts = await crud.list_recent_activities_for_staff(session, me.id, limit=10)

    clients_h = ", ".join([c.business_name for c in clients]) if clients else "-"
    fb_h = f"{fb_avg:.2f}" if fb_avg is not None else "-"
    last_h = last_ts.strftime("%Y-%m-%d %H:%M") if last_ts else "-"

    lines = [
        f"📈 گزارش عملکرد شما (۷ روز اخیر)",
        f"- نام: {me.name or 'بدون‌نام'} (ID={me.id})",
        f"- تعداد فعالیت: {acts_cnt}",
        f"- مشتریان تحت پوشش: {clients_h}",
        f"- میانگین رضایت مشتریان: {fb_h}",
        f"- آخرین فعالیت: {last_h}",
    ]

    # هشدارهای SLA پایه (اختیاری برای نمایش)
    if fb_avg is not None and fb_avg < FEEDBACK_WARN_SCORE:
        lines.append(f"\n⚠️ هشدار SLA: میانگین رضایت ({fb_h}) کمتر از آستانه {FEEDBACK_WARN_SCORE}")
    if last_ts is None or (end_dt - last_ts).days > INACTIVITY_WARN_DAYS:
        inactive_days = (end_dt - last_ts).days if last_ts else "∞"
        lines.append(f"⚠️ هشدار SLA: عدم فعالیت بیش از {INACTIVITY_WARN_DAYS} روز (فعلی: {inactive_days} روز)")

    if recent_acts:
        lines.append("\n📝 فعالیت‌های اخیر شما (۱۰ مورد آخر):")
        for a in recent_acts:
            ts = getattr(a, "ts", getattr(a, "created_at", None))
            ts_h = ts.strftime("%Y-%m-%d %H:%M") if ts else "-"
            typ = getattr(a, "activity_type", "-")
            plat = getattr(a, "platform", "-")
            goal = getattr(a, "goal", None)
            res = getattr(a, "initial_result", None)
            evd = getattr(a, "evidence_link", None)
            client_id = getattr(a, "client_id", None)
            extra = []
            if goal: extra.append(f"هدف: {goal}")
            if res: extra.append(f"نتیجه: {res}")
            if evd: extra.append(f"مدرک: {evd}")
            extra_h = " | ".join(extra) if extra else "-"
            lines.append(f"• {ts_h} — {typ} در {plat} (#{client_id}) — {extra_h}")

    await edit_or_send(cb, "\n".join(lines), staff_main_kb())

# ===================================================================
#         گزارش هفتگی مشتریانِ من (KPI رنگی + SLA پایه)
# ===================================================================
@router.callback_query(F.data == "staff_clients_week")
async def staff_clients_week(cb: types.CallbackQuery, state: FSMContext):
    staff_tg = cb.from_user.id
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        me = await crud.get_user_by_telegram_id(session, staff_tg)
        if not me or me.status != STATUS_ACTIVE:
            await edit_or_send(cb, "⚠️ شما نیروی فعال نیستید.", staff_main_kb())
            return
        clients = await crud.list_clients_for_staff(session, me.id)

        if not clients:
            await edit_or_send(cb, "هیچ مشتری فعالی برای شما وجود ندارد.", staff_main_kb())
            return

        lines = [f"🗓 گزارش هفتگی مشتریان شما ({me.name or me.id})"]
        for c in clients:
            kpi = await crud.get_client_kpi(session, c.id)
            target = (kpi.target_per_week if kpi else 0)
            acts = await crud.count_activities_in_range(session, c.id, start_dt, end_dt)
            last_ts = await crud.last_activity_ts(session, c.id)
            fb_avg = await crud.avg_feedback_for_client(session, c.id)

            status_emoji = "⚪️"
            if target > 0:
                ratio = acts / max(target, 1)
                if ratio >= 1.0:
                    status_emoji = "🟢"
                elif ratio >= KPI_YELLOW_RATIO:
                    status_emoji = "🟡"
                else:
                    status_emoji = "🔴"

            fb_h = f"{fb_avg:.2f}" if fb_avg is not None else "-"
            last_h = last_ts.strftime("%Y-%m-%d") if last_ts else "-"

            line = (
                f"\n• {c.business_name} (#{c.id})\n"
                f"  وضعیت KPI: {status_emoji}  {acts} / {target}\n"
                f"  میانگین رضایت: {fb_h}\n"
                f"  آخرین فعالیت: {last_h}"
            )

            # SLA پایه: هشدارهای هر مشتری
            warn = []
            if fb_avg is not None and fb_avg < FEEDBACK_WARN_SCORE:
                warn.append(f"رضایت < {FEEDBACK_WARN_SCORE}")
            if last_ts is None or (end_dt - last_ts).days > INACTIVITY_WARN_DAYS:
                days = (end_dt - last_ts).days if last_ts else "∞"
                warn.append(f"عدم فعالیت > {INACTIVITY_WARN_DAYS} روز (فعلی: {days})")
            if warn:
                line += "\n  ⚠️ " + " | ".join(warn)

            lines.append(line)

    await edit_or_send(cb, "\n".join(lines), staff_main_kb())
