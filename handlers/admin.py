from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import ROLE_STAFF, ROLE_ADMIN, STATUS_ACTIVE, STATUS_INACTIVE
from keyboards.admin import admin_main_kb, admin_setup_kb
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT
from keyboards.staff import assign_clients_inline_kb, assign_staff_inline_kb

router = Router()

# ---------- ناوبری ----------
@router.callback_query(F.data == "admin_setup")
async def admin_setup_menu(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer("راه‌اندازی اولیه – یکی را انتخاب کنید:", reply_markup=admin_setup_kb())

@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.answer("پنل مدیر:", reply_markup=admin_main_kb())

# ---------- ثبت نیروی مارکتینگ/مدیر ----------
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
    await cb.message.answer("نقش کاربر؟ (مدیر / نیرو)", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_role)
async def add_staff_role(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("بازگشت:", reply_markup=admin_setup_kb())
        return
    raw = (msg.text or "").strip()
    if raw not in ("مدیر", "نیرو"):
        await msg.answer("❌ لطفاً «مدیر» یا «نیرو» وارد کنید.")
        return
    await state.update_data(role=ROLE_ADMIN if raw == "مدیر" else ROLE_STAFF)
    await state.set_state(AddStaff.waiting_name)
    await msg.answer("نام و نام‌خانوادگی:", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_name)
async def add_staff_name(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_role)
        await msg.answer("نقش کاربر؟ (مدیر / نیرو)", reply_markup=back_reply_kb())
        return
    name = (msg.text or "").strip()
    if not name:
        await msg.answer("❌ نام نمی‌تواند خالی باشد.")
        return
    await state.update_data(name=name)
    await state.set_state(AddStaff.waiting_tg_id)
    await msg.answer("Telegram ID عددی کاربر:", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_tg_id)
async def add_staff_tg(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_name)
        await msg.answer("نام و نام‌خانوادگی:", reply_markup=back_reply_kb())
        return
    if not msg.text.isdigit():
        await msg.answer("❌ لطفاً عدد معتبر وارد کنید.")
        return
    await state.update_data(telegram_id=int(msg.text.strip()))
    await state.set_state(AddStaff.waiting_phone)
    await msg.answer("شماره تلفن؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_phone)
async def add_staff_phone(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_tg_id)
        await msg.answer("Telegram ID عددی کاربر:", reply_markup=back_reply_kb())
        return
    phone = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(phone=phone)
    await state.set_state(AddStaff.waiting_email)
    await msg.answer("ایمیل؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_email)
async def add_staff_email(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_phone)
        await msg.answer("شماره تلفن؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())
        return
    email = None if msg.text.strip() == '-' else msg.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddStaff.waiting_skills)
    await msg.answer("مهارت‌ها؟ (لیست با کاما، یا -)", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_skills)
async def add_staff_skills(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_email)
        await msg.answer("ایمیل؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())
        return
    raw = None if msg.text.strip() == '-' else msg.text.strip()
    skills = None if raw is None else {"list": [s.strip() for s in raw.split(',') if s.strip()]}
    await state.update_data(skills=skills)
    await state.set_state(AddStaff.waiting_capacity)
    await msg.answer("حداکثر ظرفیت مشتری؟ (عدد – اگر نامحدود، 0)", reply_markup=back_reply_kb())

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
    await msg.answer("وضعیت کاربر؟ (ACTIVE/INACTIVE)", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_status)
async def add_staff_status(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddStaff.waiting_capacity)
        await msg.answer("حداکثر ظرفیت مشتری؟ (عدد – اگر نامحدود، 0)", reply_markup=back_reply_kb())
        return
    status = (msg.text or "").strip().upper()
    if status not in (STATUS_ACTIVE, STATUS_INACTIVE):
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
        f"وضعیت: {data['status']}\n\n"
        "ثبت شود؟"
    )
    await state.set_state(AddStaff.waiting_confirm)
    await msg.answer(preview)
    await msg.answer("لطفاً یکی را انتخاب کنید:", reply_markup=confirm_inline_kb("staff_confirm", "staff_cancel"))

@router.callback_query(AddStaff.waiting_confirm, F.data.in_({"staff_confirm", "staff_cancel"}))
async def add_staff_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "staff_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=admin_setup_kb())
        return

    data = await state.get_data()
    status = data.get("status", STATUS_ACTIVE)

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
            status=status,
        )
        await crud.log_action(session, action="CREATE", entity="User", entity_id=user.id, diff_json=data)

    await state.clear()
    await cb.message.answer("✅ نیروی جدید ثبت شد.", reply_markup=admin_setup_kb())

# ---------- ثبت مشتری (با مرحله Telegram ID) ----------
class AddClient(StatesGroup):
    business_name = State()
    telegram_id = State()       # 👈 مرحله جدید برای دریافت آی‌دی مشتری
    industry = State()
    contract_date = State()
    platforms = State()
    city = State()
    sales_source = State()
    feedback_channel = State()
    contact_info = State()
    notes = State()
    status = State()
    waiting_confirm = State()

@router.callback_query(F.data == "admin_add_client")
async def add_client_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddClient.business_name)
    await cb.message.answer("نام کسب‌وکار:", reply_markup=back_reply_kb())

@router.message(AddClient.business_name)
async def client_business_name(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("بازگشت:", reply_markup=admin_setup_kb())
        return
    name = (msg.text or "").strip()
    if not name:
        await msg.answer("❌ نام کسب‌وکار نمی‌تواند خالی باشد.")
        return
    await state.update_data(business_name=name)
    await state.set_state(AddClient.telegram_id)
    await msg.answer("Telegram ID عددی مشتری؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())

@router.message(AddClient.telegram_id)
async def client_telegram_id(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.business_name)
        await msg.answer("نام کسب‌وکار:", reply_markup=back_reply_kb())
        return
    val = (msg.text or "").strip()
    if val == "-":
        tg_id = None
    else:
        if not val.isdigit():
            await msg.answer("❌ لطفاً عدد معتبر یا - وارد کنید.")
            return
        tg_id = int(val)
    await state.update_data(telegram_id=tg_id)
    await state.set_state(AddClient.industry)
    await msg.answer("صنعت (اختیاری – برای عبور، -):", reply_markup=back_reply_kb())

@router.message(AddClient.industry)
async def client_industry(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.set_state(AddClient.telegram_id)
        await msg.answer("Telegram ID عددی مشتری؟ (اختیاری – برای عبور، -)", reply_markup=back_reply_kb())
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
    status = (msg.text or "").strip().upper()
    if status not in (STATUS_ACTIVE, STATUS_INACTIVE):
        await msg.answer("❌ مقدار معتبر: ACTIVE یا INACTIVE")
        return
    await state.update_data(status=status)

    data = await state.get_data()
    platforms_h = ", ".join(data.get("platforms", {}).get("list", [])) if data.get("platforms") else "-"
    contact_h = ", ".join([f"{k}={v}" for k, v in (data.get("contact_info") or {}).items()]) or "-"
    tg_h = data.get("telegram_id") or "-"
    preview = (
        "لطفاً اطلاعات مشتری را بررسی کنید:\n\n"
        f"کسب‌وکار: {data['business_name']}\n"
        f"Telegram ID: {tg_h}\n"
        f"صنعت: {data.get('industry') or '-'}\n"
        f"تاریخ قرارداد: {data.get('contract_date') or '-'}\n"
        f"پلتفرم‌ها: {platforms_h}\n"
        f"شهر: {data.get('city') or '-'}\n"
        f"منبع داده فروش: {data.get('sales_source') or '-'}\n"
        f"کانال بازخورد: {data.get('feedback_channel') or '-'}\n"
        f"اطلاعات تماس: {contact_h}\n"
        f"یادداشت: {data.get('notes') or '-'}\n"
        f"وضعیت: {data['status']}\n\n"
        "ثبت شود؟"
    )
    await state.set_state(AddClient.waiting_confirm)
    await msg.answer(preview)
    await msg.answer("لطفاً یکی را انتخاب کنید:", reply_markup=confirm_inline_kb("client_confirm", "client_cancel"))

@router.callback_query(AddClient.waiting_confirm, F.data.in_({"client_confirm", "client_cancel"}))
async def add_client_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "client_cancel":
        await state.clear()
        await cb.message.answer("لغو شد.", reply_markup=admin_setup_kb())
        return

    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        client = await crud.create_client(
            session,
            telegram_id=data.get("telegram_id"),
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
        )
        await crud.log_action(session, action="CREATE", entity="Client", entity_id=client.id, diff_json=data)

    await state.clear()
    await cb.message.answer("✅ مشتری جدید ثبت شد.", reply_markup=admin_setup_kb())

# ---------- تخصیص مشتری ----------
class AssignFlow(StatesGroup):
    pick_client = State()
    pick_staff = State()

@router.callback_query(F.data == "admin_assign")
async def assign_start(cb: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        clients = await crud.list_clients_active(session)
    if not clients:
        await cb.message.answer("هیچ مشتری فعالی یافت نشد.", reply_markup=admin_setup_kb())
        return
    await state.set_state(AssignFlow.pick_client)
    await cb.message.answer("مشتری را انتخاب کنید:", reply_markup=assign_clients_inline_kb(clients))

@router.callback_query(AssignFlow.pick_client, F.data.startswith("assign_pick_client:"))
async def assign_pick_client(cb: types.CallbackQuery, state: FSMContext):
    client_id = int(cb.data.split(":")[1])
    await state.update_data(client_id=client_id)

    async with AsyncSessionLocal() as session:
        staff_list = await crud.list_staff_active(session)
    if not staff_list:
        await state.clear()
        await cb.message.answer("نیروی فعال موجود نیست.", reply_markup=admin_setup_kb())
        return
    await state.set_state(AssignFlow.pick_staff)
    await cb.message.answer("نیرو را انتخاب کنید یا تخصیص خودکار:", reply_markup=assign_staff_inline_kb(staff_list))

@router.callback_query(AssignFlow.pick_staff, F.data == "assign_auto")
async def assign_auto(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    async with AsyncSessionLocal() as session:
        staff = await crud.pick_staff_by_capacity(session)
        if not staff:
            await state.clear()
            await cb.message.answer("❌ نیروی فعال با ظرفیت آزاد پیدا نشد.", reply_markup=admin_setup_kb())
            return
        await crud.assign_client_to_staff(session, client_id=client_id, staff_id=staff.id)
        await crud.log_action(session, action="ASSIGN", entity="Client", entity_id=client_id, diff_json={"staff_id": staff.id, "mode": "auto"})
    await state.clear()
    await cb.message.answer(f"✅ مشتری {client_id} به‌صورت خودکار به نیروی {staff.name} (ID={staff.id}) تخصیص یافت.", reply_markup=admin_setup_kb())

@router.callback_query(AssignFlow.pick_staff, F.data.startswith("assign_pick_staff:"))
async def assign_pick_staff(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    staff_id = int(cb.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        staff = await crud.get_user_by_id(session, staff_id)
        if not staff:
            await cb.message.answer("❌ نیروی موردنظر یافت نشد.", reply_markup=admin_setup_kb())
            return
        await crud.assign_client_to_staff(session, client_id=client_id, staff_id=staff_id)
        await crud.log_action(session, action="ASSIGN", entity="Client", entity_id=client_id, diff_json={"staff_id": staff_id, "mode": "manual"})
    await state.clear()
    await cb.message.answer(f"✅ مشتری {client_id} به نیروی {staff.name} تخصیص داده شد.", reply_markup=admin_setup_kb())
