from __future__ import annotations

import io
import csv
from datetime import datetime, timedelta

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import (
    ROLE_STAFF, ROLE_ADMIN,
    STATUS_ACTIVE,
    KPI_YELLOW_RATIO, KPI_RED_RATIO,
    INACTIVITY_WARN_DAYS, FEEDBACK_WARN_SCORE,
)
from keyboards.admin import (
    admin_main_kb, admin_setup_kb,
    admin_reports_kb, admin_export_kb,
    admin_kpi_kb, clients_inline_kb_for_kpi,
    assign_clients_kb, assign_staff_kb,
    report_clients_kb, report_staff_kb,
    back_to_clients_reports_kb, back_to_staff_reports_kb,
    sales_clients_kb,  # ✅ برای ثبت فروش
)
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT
from utils.ui import edit_or_send
from config import SALES_WARN_THRESHOLD  # ✅ آستانه هشدار فروش

router = Router()


# -------------------------
# ناوبری پنل مدیر
# -------------------------
@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send(cb, "پنل مدیر:", admin_main_kb())


@router.callback_query(F.data == "admin_setup")
async def admin_setup_menu(cb: types.CallbackQuery, state: FSMContext):
    await edit_or_send(cb, "راه‌اندازی اولیه – یکی از گزینه‌ها:", admin_setup_kb())


@router.callback_query(F.data == "admin_reports_menu")
async def admin_reports_menu(cb: types.CallbackQuery, state: FSMContext):
    await edit_or_send(cb, "📊 گزارش‌ها:", admin_reports_kb())


@router.callback_query(F.data == "admin_export_menu")
async def admin_export_menu(cb: types.CallbackQuery, state: FSMContext):
    await edit_or_send(cb, "📤 خروجی و دانلود:", admin_export_kb())


@router.callback_query(F.data == "admin_kpi_menu")
async def admin_kpi_menu(cb: types.CallbackQuery, state: FSMContext):
    await edit_or_send(cb, "🎯 KPI / SLA:", admin_kpi_kb())


# -----------------------------
# ثبت نیروی مارکتینگ
# -----------------------------
class AddStaff(StatesGroup):
    waiting_role = State()
    waiting_name = State()
    waiting_tg_id = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_skills = State()
    waiting_capacity = State()
    waiting_status = State()
    waiting_confirm = State()


@router.callback_query(F.data == "admin_add_staff")
async def add_staff_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddStaff.waiting_role)
    await edit_or_send(cb, "نقش کاربر را مشخص کنید (مدیر/نیرو):", back_reply_kb())


@router.message(AddStaff.waiting_role)
async def add_staff_role(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("بازگشت به راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
        return
    raw = (msg.text or "").strip()
    if raw not in ("مدیر", "نیرو"):
        await msg.answer("❌ لطفاً یکی از این دو را بنویسید: مدیر  یا  نیرو")
        return
    role = ROLE_ADMIN if raw == "مدیر" else ROLE_STAFF
    await state.update_data(role=role)
    await state.set_state(AddStaff.waiting_name)
    await msg.answer("نام و نام‌خانوادگی:", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_name)
async def add_staff_name(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_role)
        await msg.answer("نقش کاربر را مشخص کنید (مدیر/نیرو):", reply_markup=back_reply_kb())
        return
    if not msg.text or not msg.text.strip():
        await msg.answer("❌ نام نمی‌تواند خالی باشد.")
        return
    await state.update_data(name=msg.text.strip())
    await state.set_state(AddStaff.waiting_tg_id)
    await msg.answer("Telegram ID کاربر را وارد کنید (فقط عدد):", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_tg_id)
async def add_staff_tg(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_name)
        await msg.answer("نام و نام‌خانوادگی:", reply_markup=back_reply_kb())
        return
    if not msg.text.isdigit():
        await msg.answer("❌ لطفاً عدد معتبر وارد کنید.")
        return
    await state.update_data(telegram_id=int(msg.text))
    await state.set_state(AddStaff.waiting_phone)
    await msg.answer("شماره تلفن؟ (اختیاری – برای عبور، - بفرست)", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_phone)
async def add_staff_phone(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_tg_id)
        await msg.answer("Telegram ID کاربر را وارد کنید (فقط عدد):", reply_markup=back_reply_kb())
        return
    phone = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(phone=phone)
    await state.set_state(AddStaff.waiting_email)
    await msg.answer("ایمیل؟ (اختیاری – برای عبور، - بفرست)", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_email)
async def add_staff_email(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_phone)
        await msg.answer("شماره تلفن؟ (اختیاری – برای عبور، - بفرست)", reply_markup=back_reply_kb())
        return
    email = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddStaff.waiting_skills)
    await msg.answer("مهارت‌ها؟ (لیست با کاما، یا -)", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_skills)
async def add_staff_skills(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_email)
        await msg.answer("ایمیل؟ (اختیاری – برای عبور، - بفرست)", reply_markup=back_reply_kb())
        return
    raw = None if msg.text.strip() == '-' else msg.text.strip()
    skills = None if raw is None else {"list": [s.strip() for s in raw.split(',') if s.strip()]}
    await state.update_data(skills=skills)
    await state.set_state(AddStaff.waiting_capacity)
    await msg.answer("حداکثر ظرفیت مشتری؟ (عدد – اگر نامحدود است، 0)", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_capacity)
async def add_staff_capacity(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_skills)
        await msg.answer("مهارت‌ها؟ (لیست با کاما، یا -)", reply_markup=back_reply_kb())
        return
    try:
        capacity = int(msg.text)
        if capacity < 0:
            raise ValueError()
    except:
        await msg.answer("❌ لطفاً عدد معتبر (≥0) وارد کنید.")
        return
    await state.update_data(max_capacity=capacity)
    await state.set_state(AddStaff.waiting_status)
    await msg.answer("وضعیت کاربر؟ (ACTIVE/INACTIVE):", reply_markup=back_reply_kb())


@router.message(AddStaff.waiting_status)
async def add_staff_status(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_capacity)
        await msg.answer("حداکثر ظرفیت مشتری؟ (عدد – اگر نامحدود است، 0)", reply_markup=back_reply_kb())
        return
    status = (msg.text or "").strip().upper()
    if status not in ("ACTIVE", "INACTIVE"):
        await msg.answer("❌ مقدار معتبر: ACTIVE یا INACTIVE")
        return

    await state.update_data(status=status)

    data = await state.get_data()
    role_h = "مدیر" if data["role"] == ROLE_ADMIN else "نیروی مارکتینگ"
    skills_h = ", ".join(data.get("skills", {}).get("list", [])) if data.get("skills") else "-"
    preview = (
        "لطفاً اطلاعات را بررسی کنید:\n\n"
        f"نام: {data['name']}\n"
        f"نقش: {role_h}\n"
        f"Telegram ID: {data['telegram_id']}\n"
        f"تلفن: {data.get('phone') or '-'}\n"
        f"ایمیل: {data.get('email') or '-'}\n"
        f"مهارت‌ها: {skills_h}\n"
        f"حداکثر ظرفیت: {data.get('max_capacity')}\n"
        f"وضعیت: {status}\n\n"
        "آیا تأیید می‌کنید؟"
    )
    await state.set_state(AddStaff.waiting_confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("staff_confirm", "staff_cancel"))


@router.callback_query(AddStaff.waiting_confirm, F.data.in_({"staff_confirm", "staff_cancel"}))
async def add_staff_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "staff_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد. بازگشت به راه‌اندازی اولیه.", admin_setup_kb())
        return

    data = await state.get_data()
    required = ("role", "name", "telegram_id", "status")
    missing = [k for k in required if not data.get(k)]
    if missing:
        await state.clear()
        await edit_or_send(
            cb,
            f"⚠️ اطلاعات فرم ناقص است (کمبود: {', '.join(missing)}). لطفاً مجدداً ثبت نیرو را انجام دهید.",
            admin_setup_kb()
        )
        return

    async with AsyncSessionLocal() as session:
        user = await crud.create_user(
            session,
            telegram_id=data["telegram_id"],
            role=data["role"],
            name=data["name"],
            phone=data.get("phone"),
            email=data.get("email"),
            skills=data.get("skills"),
            max_capacity=data.get("max_capacity"),
            status=data["status"],
        )
        await crud.log_action(session, action="CREATE", entity="User", entity_id=user.id, diff_json=data)

    await state.clear()
    await edit_or_send(cb, "✅ نیروی جدید با موفقیت ثبت شد.\nبازگشت به راه‌اندازی اولیه:", admin_setup_kb())


# -----------------------------
# ثبت مشتری
# -----------------------------
class AddClient(StatesGroup):
    business_name = State()
    industry = State()
    contract_date = State()
    platforms = State()
    city = State()
    sales_source = State()
    feedback_channel = State()
    contact_info = State()
    notes = State()
    status = State()
    telegram_id = State()
    waiting_confirm = State()


@router.callback_query(F.data == "admin_add_client")
async def add_client_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddClient.business_name)
    await edit_or_send(cb, "نام کسب‌وکار:", back_reply_kb())


@router.message(AddClient.business_name)
async def client_business_name(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("بازگشت به راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
        return
    name = (msg.text or "").strip()
    if not name:
        await msg.answer("❌ نام کسب‌وکار نمی‌تواند خالی باشد.")
        return
    await state.update_data(business_name=name)
    await state.set_state(AddClient.industry)
    await msg.answer("صنعت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())


@router.message(AddClient.industry)
async def client_industry(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.business_name)
        await msg.answer("نام کسب‌وکار:", reply_markup=back_reply_kb())
        return
    industry = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(industry=industry)
    await state.set_state(AddClient.contract_date)
    await msg.answer("تاریخ قرارداد (YYYY-MM-DD یا -):", reply_markup=back_reply_kb())


@router.message(AddClient.contract_date)
async def client_contract_date(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.industry)
        await msg.answer("صنعت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    contract_date = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(contract_date=contract_date)
    await state.set_state(AddClient.platforms)
    await msg.answer("پلتفرم‌ها (لیست با کاما، یا -):", reply_markup=back_reply_kb())


@router.message(AddClient.platforms)
async def client_platforms(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.contract_date)
        await msg.answer("تاریخ قرارداد (YYYY-MM-DD یا -):", reply_markup=back_reply_kb())
        return
    raw = None if msg.text.strip() == '-' else msg.text.strip()
    platforms = None if raw is None else {"list": [p.strip() for p in raw.split(',') if p.strip()]}
    await state.update_data(platforms=platforms)
    await state.set_state(AddClient.city)
    await msg.answer("شهر (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())


@router.message(AddClient.city)
async def client_city(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.platforms)
        await msg.answer("پلتفرم‌ها (لیست با کاما، یا -):", reply_markup=back_reply_kb())
        return
    city = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(city=city)
    await state.set_state(AddClient.sales_source)
    await msg.answer("منبع داده فروش (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())


@router.message(AddClient.sales_source)
async def client_sales_source(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.city)
        await msg.answer("شهر (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    sales_source = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(sales_source=sales_source)
    await state.set_state(AddClient.feedback_channel)
    await msg.answer("کانال بازخورد (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())


@router.message(AddClient.feedback_channel)
async def client_feedback_channel(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.sales_source)
        await msg.answer("منبع داده فروش (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    feedback_channel = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(feedback_channel=feedback_channel)
    await state.set_state(AddClient.contact_info)
    await msg.answer("اطلاعات تماس (مثال: phone=..., email=... یا -):", reply_markup=back_reply_kb())


@router.message(AddClient.contact_info)
async def client_contact_info(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.feedback_channel)
        await msg.answer("کانال بازخورد (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    contact_info = None
    if msg.text.strip() != '-':
        parts = [p.strip() for p in msg.text.split(',') if p.strip()]
        kv = {}
        for p in parts:
            if '=' in p:
                k, v = p.split('=', 1)
                kv[k.strip()] = v.strip()
        contact_info = kv or None
    await state.update_data(contact_info=contact_info)
    await state.set_state(AddClient.notes)
    await msg.answer("یادداشت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())


@router.message(AddClient.notes)
async def client_notes(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.contact_info)
        await msg.answer("اطلاعات تماس (مثال: phone=..., email=... یا -):", reply_markup=back_reply_kb())
        return
    notes = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(notes=notes)
    await state.set_state(AddClient.status)
    await msg.answer("وضعیت مشتری (ACTIVE/INACTIVE):", reply_markup=back_reply_kb())


@router.message(AddClient.status)
async def client_status(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.notes)
        await msg.answer("یادداشت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())
        return
    status = msg.text.strip().upper()
    if status not in ("ACTIVE", "INACTIVE"):
        await msg.answer("❌ مقدار معتبر: ACTIVE یا INACTIVE")
        return
    await state.update_data(status=status)
    await state.set_state(AddClient.telegram_id)
    await msg.answer("Telegram ID مشتری؟ (فقط عدد – برای ورود پنل مشتری الزامی)", reply_markup=back_reply_kb())


@router.message(AddClient.telegram_id)
async def client_telegram_id(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.status)
        await msg.answer("وضعیت مشتری (ACTIVE/INACTIVE):", reply_markup=back_reply_kb())
        return
    if not msg.text.isdigit():
        await msg.answer("❌ لطفاً عدد معتبر وارد کنید.")
        return
    await state.update_data(telegram_id=int(msg.text))

    data = await state.get_data()
    platforms_h = ", ".join(data.get("platforms", {}).get("list", [])) if data.get("platforms") else "-"
    contact_h = ", ".join([f"{k}={v}" for k, v in (data.get("contact_info") or {}).items()]) or "-"
    preview = (
        "📌 پیش‌نمایش مشتری\n\n"
        f"کسب‌وکار: {data['business_name']}\n"
        f"صنعت: {data.get('industry') or '-'}\n"
        f"تاریخ قرارداد: {data.get('contract_date') or '-'}\n"
        f"پلتفرم‌ها: {platforms_h}\n"
        f"شهر: {data.get('city') or '-'}\n"
        f"منبع داده فروش: {data.get('sales_source') or '-'}\n"
        f"کانال بازخورد: {data.get('feedback_channel') or '-'}\n"
        f"اطلاعات تماس: {contact_h}\n"
        f"یادداشت: {data.get('notes') or '-'}\n"
        f"وضعیت: {data['status']}\n"
        f"Telegram ID مشتری: {data['telegram_id']}\n\n"
        "آیا تأیید می‌کنید؟"
    )
    await state.set_state(AddClient.waiting_confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("client_confirm", "client_cancel"))


@router.callback_query(AddClient.waiting_confirm, F.data.in_({"client_confirm", "client_cancel"}))
async def add_client_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "client_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد. بازگشت به راه‌اندازی اولیه.", admin_setup_kb())
        return

    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        client = await crud.create_client(
            session,
            business_name=data["business_name"],
            industry=data.get("industry"),
            contract_date=data.get("contract_date"),
            platforms=data.get("platforms"),
            city=data.get("city"),
            sales_source=data.get("sales_source"),
            feedback_channel=data.get("feedback_channel"),
            contact_info=data.get("contact_info"),
            notes=data.get("notes"),
            status=data["status"],
            telegram_id=data["telegram_id"],
        )
        await crud.log_action(session, action="CREATE", entity="Client", entity_id=client.id, diff_json=data)

    await state.clear()
    await edit_or_send(cb, "✅ مشتری جدید ثبت شد.\nبازگشت به راه‌اندازی اولیه:", admin_setup_kb())


# -----------------------------
# تخصیص مشتری به نیرو (دکمه‌ای)
# -----------------------------
class AssignClient(StatesGroup):
    pick_client = State()
    pick_staff = State()


@router.callback_query(F.data == "admin_assign")
async def assign_start(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)
    if not clients:
        await edit_or_send(cb, "هیچ مشتری‌ای ثبت نشده است.", admin_setup_kb())
        return

    await state.set_state(AssignClient.pick_client)
    await edit_or_send(cb, "یک مشتری را انتخاب کنید:", assign_clients_kb(clients))


@router.callback_query(AssignClient.pick_client, F.data.startswith("assign_pick_client:"))
async def assign_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)

    async with AsyncSessionLocal() as session:
        staff_tuples = await crud.list_staff_with_capacity(session)
        if not staff_tuples:
            staff_all = await crud.list_staff_active(session)
            tuples = []
            for s in staff_all:
                cur = await crud.count_clients_for_staff(session, s.id)
                cap = int(s.max_capacity or 0)
                tuples.append((s, cur, cap))
            staff_tuples = tuples

    await state.set_state(AssignClient.pick_staff)
    await edit_or_send(
        cb,
        "حالا یک نیرو را انتخاب کنید (یا روی «🤖 تخصیص خودکار» بزنید):",
        assign_staff_kb(staff_tuples, include_auto=True)
    )


@router.callback_query(AssignClient.pick_staff, F.data == "assign_auto")
async def assign_auto(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    if not client_id:
        await state.clear()
        await edit_or_send(cb, "⚠️ مشتری انتخاب نشده. دوباره تلاش کنید.", admin_setup_kb())
        return

    async with AsyncSessionLocal() as session:
        staff = await crud.pick_staff_by_capacity(session)
        if not staff:
            await state.clear()
            await edit_or_send(cb, "❌ نیروی فعال با ظرفیت آزاد پیدا نشد.", admin_setup_kb())
            return

        await crud.assign_client_to_staff(session, client_id=client_id, staff_id=staff.id)
        await crud.log_action(
            session, action="ASSIGN", entity="Client", entity_id=client_id,
            diff_json={"staff_id": staff.id, "mode": "auto"}
        )

    await state.clear()
    await edit_or_send(cb, f"✅ مشتری #{client_id} به‌صورت خودکار به «{staff.name or 'بدون‌نام'}» (ID={staff.id}) تخصیص یافت.", admin_setup_kb())


@router.callback_query(AssignClient.pick_staff, F.data.startswith("assign_pick_staff:"))
async def assign_pick_staff(cb: types.CallbackQuery, state: FSMContext):
    staff_id = int(cb.data.split(":")[1])
    data = await state.get_data()
    client_id = data.get("client_id")
    if not client_id:
        await state.clear()
        await edit_or_send(cb, "⚠️ مشتری انتخاب نشده. دوباره تلاش کنید.", admin_setup_kb())
        return

    async with AsyncSessionLocal() as session:
        staff = await crud.get_user_by_id(session, staff_id)
        if not staff:
            await edit_or_send(cb, "❌ نیروی موردنظر یافت نشد.", admin_setup_kb())
            return

        await crud.assign_client_to_staff(session, client_id=client_id, staff_id=staff_id)
        await crud.log_action(
            session, action="ASSIGN", entity="Client", entity_id=client_id,
            diff_json={"staff_id": staff_id, "mode": "manual"}
        )

    await state.clear()
    await edit_or_send(cb, f"✅ مشتری #{client_id} به «{staff.name or 'بدون‌نام'}» (ID={staff_id}) تخصیص داده شد.", admin_setup_kb())


# -----------------------------
# 🎯 KPI / SLA — تنظیم هدف هفتگی
# -----------------------------
class KPISet(StatesGroup):
    pick_client = State()
    set_target = State()
    confirm = State()


@router.callback_query(F.data == "admin_kpi_set_client")
async def kpi_pick_client_menu(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)
    if not clients:
        await edit_or_send(cb, "هیچ مشتری‌ای ثبت نشده است.", admin_kpi_kb())
        return
    await state.set_state(KPISet.pick_client)
    await edit_or_send(cb, "مشتری را برای تنظیم KPI انتخاب کنید:", clients_inline_kb_for_kpi(clients))


@router.callback_query(KPISet.pick_client, F.data.startswith("kpi_pick_client:"))
async def kpi_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await state.set_state(KPISet.set_target)
    await cb.message.answer("هدف هفتگی تعداد فعالیت را وارد کنید (عدد ≥ 0):", reply_markup=back_reply_kb())


@router.message(KPISet.set_target)
async def kpi_set_target(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("بازگشت به KPI / SLA:", reply_markup=admin_kpi_kb())
        return
    try:
        target = int(msg.text)
        if target < 0:
            raise ValueError()
    except:
        await msg.answer("❌ لطفاً یک عدد معتبر (≥0) وارد کنید.")
        return
    data = await state.get_data()
    await state.update_data(target=target)
    preview = f"🎯 KPI هفتگی مشتری {data['client_id']} → هدف تعداد فعالیت: {target}\nآیا تأیید می‌کنید؟"
    await state.set_state(KPISet.confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("kpi_confirm", "kpi_cancel"))


@router.callback_query(KPISet.confirm, F.data.in_({"kpi_confirm", "kpi_cancel"}))
async def kpi_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "kpi_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد.", admin_kpi_kb())
        return
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        k = await crud.upsert_client_kpi(session, data["client_id"], data["target"])
        await crud.log_action(session, action="UPSERT", entity="ClientKPI", entity_id=k.id, diff_json=data)
    await state.clear()
    await edit_or_send(cb, "✅ KPI هفتگی ذخیره شد.", admin_kpi_kb())


# =============================
# 💰 ثبت فروش جدید (فقط مدیر)
# =============================
class AddSale(StatesGroup):
    pick_client = State()
    ts = State()
    amount = State()
    source = State()
    note = State()
    confirm = State()

@router.callback_query(F.data == "admin_add_sale")
async def admin_add_sale_start(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)
    if not clients:
        await edit_or_send(cb, "هیچ مشتری‌ای ثبت نشده است.", admin_main_kb())
        return
    await state.set_state(AddSale.pick_client)
    await edit_or_send(cb, "برای ثبت فروش، مشتری را انتخاب کنید:", sales_clients_kb(clients))

@router.callback_query(AddSale.pick_client, F.data.startswith("sale_pick_client:"))
async def admin_add_sale_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        c = await crud.get_client_by_id(session, client_id)
    if not c:
        await edit_or_send(cb, "❌ مشتری یافت نشد.", admin_main_kb())
        return
    await state.update_data(client_id=client_id, client_name=c.business_name)
    await state.set_state(AddSale.ts)
    await cb.message.answer("تاریخ/ساعت فروش؟ (YYYY-MM-DD HH:MM یا «-» برای اکنون)", reply_markup=back_reply_kb())

@router.message(AddSale.ts)
async def admin_add_sale_ts(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("لغو شد.", reply_markup=admin_main_kb())
        return
    val = (msg.text or "").strip()
    if val == "-":
        ts = datetime.utcnow()
    else:
        try:
            ts = datetime.strptime(val, "%Y-%m-%d %H:%M")
        except ValueError:
            await msg.answer("❌ فرمت نادرست است. مثال: 2025-08-18 14:30 یا «-»")
            return
    await state.update_data(ts=ts.isoformat())
    await state.set_state(AddSale.amount)
    await msg.answer("مبلغ فروش؟ (عدد ≥ 0)", reply_markup=back_reply_kb())

@router.message(AddSale.amount)
async def admin_add_sale_amount(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddSale.ts)
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
    await state.set_state(AddSale.source)
    await msg.answer("منبع/کانال فروش؟ (اختیاری، یا «-»)", reply_markup=back_reply_kb())

@router.message(AddSale.source)
async def admin_add_sale_source(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddSale.amount)
        await msg.answer("مبلغ فروش؟ (عدد ≥ 0)", reply_markup=back_reply_kb())
        return
    source = None if msg.text.strip() == "-" else msg.text.strip()
    await state.update_data(source=source)
    await state.set_state(AddSale.note)
    await msg.answer("یادداشت (اختیاری، یا «-»):", reply_markup=back_reply_kb())

@router.message(AddSale.note)
async def admin_add_sale_note(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddSale.source)
        await msg.answer("منبع/کانال فروش؟ (اختیاری، یا «-»)", reply_markup=back_reply_kb())
        return
    note = None if msg.text.strip() == "-" else msg.text.strip()
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
    await state.set_state(AddSale.confirm)
    await msg.answer(preview)
    await msg.answer("انتخاب کنید:", reply_markup=confirm_inline_kb("sale_confirm", "sale_cancel"))

@router.callback_query(AddSale.confirm, F.data.in_({"sale_confirm", "sale_cancel"}))
async def admin_add_sale_confirm(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "sale_cancel":
        await state.clear()
        await edit_or_send(cb, "لغو شد.", admin_main_kb())
        return

    data = await state.get_data()
    required = ("client_id", "ts", "amount")
    if any(k not in data or data[k] in (None, "") for k in required):
        await state.clear()
        await edit_or_send(cb, "⚠️ اطلاعات فرم ناقص است.", admin_main_kb())
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
    await edit_or_send(cb, "✅ فروش ثبت شد.", admin_main_kb())


# -----------------------------
# 📊 گزارش‌ها
# -----------------------------
@router.callback_query(F.data == "admin_reports_weekly")
async def admin_report_weekly(cb: types.CallbackQuery, state: FSMContext):
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)
        if not clients:
            await edit_or_send(cb, "هیچ مشتری‌ای ثبت نشده است.", admin_reports_kb())
            return

        lines = ["📊 گزارش هفتگی مشتریان\n"]
        warn_lines = []

        for c in clients:
            kpi = await crud.get_client_kpi(session, c.id)
            target = (kpi.target_per_week if kpi else 0)

            acts = await crud.count_activities_in_range(session, c.id, start_dt, end_dt)
            fb_avg = await crud.avg_feedback_for_client(session, c.id)
            last_ts = await crud.last_activity_ts(session, c.id)
            sales_sum = await crud.sum_sales_in_range(session, c.id, start_dt, end_dt)  # ✅ جمع فروش ۷روز

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
            sales_h = f"{sales_sum:,.0f}"

            lines.append(
                f"\n1️⃣ مشتری: {c.business_name}\n"
                f"- وضعیت: {status_emoji}\n"
                f"- KPI فعلی (۷روز): {acts} / {target}\n"
                f"- فروش (۷روز): {sales_h}\n"
                f"- بازخورد: {fb_h}\n"
                f"- آخرین فعالیت: {last_h}"
            )

            # هشدارها
            if fb_avg is not None and fb_avg < FEEDBACK_WARN_SCORE:
                warn_lines.append(f"• رضایت پایین‌تر از آستانه ({c.business_name}): {fb_h}")
            if last_ts is None or (end_dt - last_ts).days > INACTIVITY_WARN_DAYS:
                days = (end_dt - last_ts).days if last_ts else "∞"
                warn_lines.append(f"• عدم فعالیت نیرو > {INACTIVITY_WARN_DAYS} روز ({c.business_name}): {days} روز")
            if SALES_WARN_THRESHOLD > 0 and sales_sum < SALES_WARN_THRESHOLD:
                warn_lines.append(f"• فروش هفتگی پایین‌تر از آستانه ({c.business_name}): {sales_h} < {SALES_WARN_THRESHOLD:,.0f}")

        if warn_lines:
            lines.append("\n⚠️ هشدارها:")
            lines.extend([f"- {w}" for w in warn_lines])

        await edit_or_send(cb, "\n".join(lines), admin_reports_kb())


@router.callback_query(F.data == "admin_reports_clients")
async def admin_reports_clients(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)
    if not clients:
        await edit_or_send(cb, "هیچ مشتری‌ای ثبت نشده است.", admin_reports_kb())
        return
    await edit_or_send(cb, "یک مشتری را انتخاب کنید:", report_clients_kb(clients))


@router.callback_query(F.data.startswith("report_client:"))
async def admin_report_one_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        c = await crud.get_client_by_id(session, client_id)
        if not c:
            await edit_or_send(cb, "❌ مشتری یافت نشد.", admin_reports_kb())
            return
        kpi = await crud.get_client_kpi(session, client_id)
        target = (kpi.target_per_week if kpi else 0)
        acts_7d = await crud.count_activities_in_range(session, client_id, start_dt, end_dt)
        fb_avg = await crud.avg_feedback_for_client(session, client_id)
        last_ts = await crud.last_activity_ts(session, client_id)
        sales_7d = await crud.sum_sales_in_range(session, client_id, start_dt, end_dt)  # ✅ فروش ۷روز
        staff = await crud.get_user_by_id(session, c.assigned_staff_id) if c.assigned_staff_id else None
        recent_acts = await crud.list_recent_activities_for_client(session, client_id, limit=10)
        recent_fb = await crud.list_recent_feedback_for_client(session, client_id, limit=10)
        recent_sales = await crud.list_recent_sales_for_client(session, client_id, limit=10)  # ✅ فروش‌های اخیر

    status_emoji = "⚪️"
    if target > 0:
        ratio = acts_7d / max(target, 1)
        if ratio >= 1.0:
            status_emoji = "🟢"
        elif ratio >= KPI_YELLOW_RATIO:
            status_emoji = "🟡"
        else:
            status_emoji = "🔴"

    fb_h = f"{fb_avg:.2f}" if fb_avg is not None else "-"
    last_h = last_ts.strftime("%Y-%m-%d %H:%M") if last_ts else "-"
    staff_h = f"{staff.name} (ID={staff.id})" if staff else "-"
    sales_h = f"{sales_7d:,.0f}"

    lines = [
        f"📄 گزارش مشتری: {c.business_name} (#{c.id})",
        f"- وضعیت KPI (۷روز): {status_emoji}  {acts_7d} / {target}",
        f"- فروش (۷روز): {sales_h}",
        f"- میانگین رضایت: {fb_h}",
        f"- آخرین فعالیت: {last_h}",
        f"- نیروی تخصیص‌یافته: {staff_h}",
    ]

    # ریز فعالیت‌های اخیر
    if recent_acts:
        lines.append("\n📝 فعالیت‌های اخیر (۱۰ مورد آخر):")
        for a in recent_acts:
            ts = getattr(a, "ts", getattr(a, "created_at", None))
            ts_h = ts.strftime("%Y-%m-%d %H:%M") if ts else "-"
            typ = getattr(a, "activity_type", "-")
            plat = getattr(a, "platform", "-")
            goal = getattr(a, "goal", None)
            res = getattr(a, "initial_result", None)
            evd = getattr(a, "evidence_link", None)
            extra = []
            if goal: extra.append(f"هدف: {goal}")
            if res: extra.append(f"نتیجه: {res}")
            if evd: extra.append(f"مدرک: {evd}")
            extra_h = " | ".join(extra) if extra else "-"
            lines.append(f"• {ts_h} — {typ} در {plat} — {extra_h}")

    # فروش‌های اخیر
    if recent_sales:
        lines.append("\n💰 فروش‌های اخیر (۱۰ مورد آخر):")
        for s in recent_sales:
            ts_h = s.ts.strftime("%Y-%m-%d %H:%M")
            amt = f"{(s.amount or 0):,.0f}"
            src = s.source or "-"
            note = s.note or "-"
            lines.append(f"• {ts_h} — مبلغ: {amt} — منبع: {src} — یادداشت: {note}")

    # بازخوردهای اخیر
    if recent_fb:
        lines.append("\n💬 بازخوردهای اخیر (۱۰ مورد آخر):")
        for f in recent_fb:
            ts_h = f.created_at.strftime("%Y-%m-%d %H:%M")
            score = int(getattr(f, "score", 0) or 0)
            stars = "⭐" * max(1, min(5, score))
            comment = getattr(f, "comment", None) or "-"
            lines.append(f"• {ts_h} — {stars} ({score}/5) — {comment}")

    await edit_or_send(cb, "\n".join(lines), back_to_clients_reports_kb())


@router.callback_query(F.data == "admin_reports_staff")
async def admin_reports_staff(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        staff = await crud.list_staff_active(session)
    if not staff:
        await edit_or_send(cb, "هیچ نیروی فعالی ثبت نشده است.", admin_reports_kb())
        return
    await edit_or_send(cb, "یک نیرو را انتخاب کنید:", report_staff_kb(staff))


@router.callback_query(F.data.startswith("report_staff:"))
async def admin_report_one_staff(cb: types.CallbackQuery, state: FSMContext):
    staff_id = int(cb.data.split(":")[1])
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        s = await crud.get_user_by_id(session, staff_id)
        if not s:
            await edit_or_send(cb, "❌ نیرو یافت نشد.", admin_reports_kb())
            return
        acts_7d = await crud.count_activities_in_range_by_staff(session, staff_id, start_dt, end_dt)
        clients = await crud.list_clients_for_staff(session, staff_id)
        fb_avg = await crud.avg_feedback_for_staff_clients(session, staff_id)
        last_ts = await crud.last_activity_ts_for_staff(session, staff_id)
        recent_acts = await crud.list_recent_activities_for_staff(session, staff_id, limit=10)
        sales_sum = await crud.sum_sales_in_range_for_staff(session, staff_id, start_dt, end_dt)  # ✅ فروش ۷روز

    clients_h = ", ".join([c.business_name for c in clients]) if clients else "-"
    fb_h = f"{fb_avg:.2f}" if fb_avg is not None else "-"
    last_h = last_ts.strftime("%Y-%m-%d %H:%M") if last_ts else "-"
    sales_h = f"{sales_sum:,.0f}"

    lines = [
        f"👤 گزارش نیرو: {s.name or 'بدون‌نام'} (ID={s.id})",
        f"- فعالیت‌ها (۷ روز اخیر): {acts_7d}",
        f"- فروش مشتریان تحت‌پوشش (۷روز): {sales_h}",
        f"- مشتریان تحت پوشش: {clients_h}",
        f"- میانگین رضایت مشتریان: {fb_h}",
        f"- آخرین فعالیت: {last_h}",
    ]

    if recent_acts:
        lines.append("\n📝 فعالیت‌های اخیر (۱۰ مورد آخر):")
        for a in recent_acts:
            ts = getattr(a, "ts", getattr(a, "created_at", None))
            ts_h = ts.strftime("%Y-%m-%d %H:%M") if ts else "-"
            typ = getattr(a, "activity_type", "-")
            plat = getattr(a, "platform", "-")
            goal = getattr(a, "goal", None)
            res = getattr(a, "initial_result", None)
            evd = getattr(a, "evidence_link", None)
            client_id = getattr(a, "client_id", None)
            client_part = f"(#{client_id})" if client_id else ""
            extra = []
            if goal: extra.append(f"هدف: {goal}")
            if res: extra.append(f"نتیجه: {res}")
            if evd: extra.append(f"مدرک: {evd}")
            extra_h = " | ".join(extra) if extra else "-"
            lines.append(f"• {ts_h} — {typ} در {plat} {client_part} — {extra_h}")

    await edit_or_send(cb, "\n".join(lines), back_to_staff_reports_kb())


# -----------------------------
# 📤 خروجی هفتگی CSV (به‌روزشده: شامل فروش)
# -----------------------------
@router.callback_query(F.data == "admin_export_week_csv")
async def admin_export_week_csv(cb: types.CallbackQuery, state: FSMContext):
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        clients = await crud.list_all_clients(session)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["client_id", "business_name", "kpi_target", "acts_7d", "sales_7d", "avg_feedback", "last_activity_utc"])

        for c in clients:
            kpi = await crud.get_client_kpi(session, c.id)
            target = (kpi.target_per_week if kpi else 0)
            acts = await crud.count_activities_in_range(session, c.id, start_dt, end_dt)
            sales_sum = await crud.sum_sales_in_range(session, c.id, start_dt, end_dt)  # ✅
            fb_avg = await crud.avg_feedback_for_client(session, c.id)
            last_ts = await crud.last_activity_ts(session, c.id)
            writer.writerow([
                c.id,
                c.business_name,
                target,
                acts,
                f"{sales_sum:.2f}",
                f"{fb_avg:.2f}" if fb_avg is not None else "",
                last_ts.isoformat() if last_ts else ""
            ])

    data = buf.getvalue().encode("utf-8-sig")
    await cb.message.answer_document(
        types.BufferedInputFile(data, filename="weekly_summary.csv"),
        caption="📤 خروجی هفتگی (7 روز اخیر) — KPI/فعالیت/فروش/بازخورد"
    )
    await cb.message.answer("گزینه‌های دیگر:", reply_markup=admin_export_kb())
