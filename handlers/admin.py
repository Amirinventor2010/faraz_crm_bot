from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.base import AsyncSessionLocal
from db import crud
from utils.constants import ROLE_STAFF, ROLE_ADMIN, STATUS_ACTIVE
from keyboards.admin import admin_main_kb, admin_setup_kb
from keyboards.common import back_reply_kb, confirm_inline_kb, BACK_TEXT

router = Router()

# ----- ناوبری پنل مدیر -----
@router.callback_query(F.data == "admin_menu")
async def admin_menu(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("پنل مدیر:", reply_markup=admin_main_kb())

# ----- راه‌اندازی اولیه -----
@router.callback_query(F.data == "admin_setup")
async def admin_setup_menu(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text("راه‌اندازی اولیه – یکی از گزینه‌ها را انتخاب کنید:", reply_markup=admin_setup_kb())

@router.callback_query(F.data == "admin_back_main")
async def admin_back_main(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text("پنل مدیر:", reply_markup=admin_main_kb())

# ===== ثبت نیرو (با پیش‌نمایش/تأیید) =====
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
    # از اینجا به بعد ورودی متنی می‌گیریم؛ پیام جدید ارسال می‌شود
    await cb.message.answer("نقش کاربر را مشخص کنید (مدیر/نیرو):", reply_markup=back_reply_kb())

@router.message(AddStaff.waiting_role)
async def add_staff_role(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
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
    await msg.answer("Telegram ID کاربر (فقط عدد):", reply_markup=back_reply_kb())

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
        await msg.answer("Telegram ID کاربر (فقط عدد):", reply_markup=back_reply_kb())
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
    data = await state.get_data()
    data["status"] = status

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
    await msg.answer(preview, reply_markup=confirm_inline_kb("staff_confirm", "staff_cancel"))

@router.callback_query(AddStaff.waiting_confirm, F.data.in_({"staff_confirm", "staff_cancel"}))
async def add_staff_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "staff_cancel":
        await state.clear()
        await cb.message.edit_text("راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
        return

    data = await state.get_data()
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
    await cb.message.edit_text("✅ نیروی جدید ثبت شد.\nراه‌اندازی اولیه:", reply_markup=admin_setup_kb())

# ===== ثبت مشتری مثل قبل (منوها با edit_text برمی‌گردند) =====
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
    waiting_confirm = State()

@router.callback_query(F.data == "admin_add_client")
async def add_client_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddClient.business_name)
    await cb.message.answer("نام کسب‌وکار:", reply_markup=back_reply_kb())

@router.message(AddClient.business_name)
async def client_business_name(msg: types.Message, state: FSMContext):
    if msg.text == BACK_TEXT:
        await state.clear()
        await msg.answer("راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
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
    data = await state.get_data()
    data["status"] = status

    platforms_h = ", ".join(data.get("platforms", {}).get("list", [])) if data.get("platforms") else "-"
    contact_h = ", ".join([f"{k}={v}" for k, v in (data.get("contact_info") or {}).items()]) or "-"
    preview = (
        "لطفاً اطلاعات مشتری را بررسی کنید:\n\n"
        f"کسب‌وکار: {data['business_name']}\n"
        f"صنعت: {data.get('industry') or '-'}\n"
        f"تاریخ قرارداد: {data.get('contract_date') or '-'}\n"
        f"پلتفرم‌ها: {platforms_h}\n"
        f"شهر: {data.get('city') or '-'}\n"
        f"منبع داده فروش: {data.get('sales_source') or '-'}\n"
        f"کانال بازخورد: {data.get('feedback_channel') or '-'}\n"
        f"اطلاعات تماس: {contact_h}\n"
        f"یادداشت: {data.get('notes') or '-'}\n"
        f"وضعیت: {status}\n\n"
        "آیا تأیید می‌کنید؟"
    )
    await state.set_state(AddClient.waiting_confirm)
    await msg.answer(preview, reply_markup=confirm_inline_kb("client_confirm", "client_cancel"))

@router.callback_query(AddClient.waiting_confirm, F.data.in_({"client_confirm", "client_cancel"}))
async def add_client_confirm_or_cancel(cb: types.CallbackQuery, state: FSMContext):
    if cb.data == "client_cancel":
        await state.clear()
        await cb.message.edit_text("راه‌اندازی اولیه:", reply_markup=admin_setup_kb())
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
        )
        await crud.log_action(session, action="CREATE", entity="Client", entity_id=client.id, diff_json=data)

    await state.clear()
    await cb.message.edit_text("✅ مشتری جدید ثبت شد.\nراه‌اندازی اولیه:", reply_markup=admin_setup_kb())
