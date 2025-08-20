from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ---------------------------
# اصلی/ناوبری
# ---------------------------
def admin_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⚙️ راه‌اندازی اولیه", callback_data="admin_setup")],
        [InlineKeyboardButton(text="📊 گزارش‌ها", callback_data="admin_reports_menu")],
        [InlineKeyboardButton(text="📤 خروجی و دانلود", callback_data="admin_export_menu")],
        [InlineKeyboardButton(text="🎯 KPI / SLA", callback_data="admin_kpi_menu")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_setup_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ ثبت نیروی مارکتینگ", callback_data="admin_add_staff")],
        [InlineKeyboardButton(text="➕ ثبت مشتری", callback_data="admin_add_client")],
        [InlineKeyboardButton(text="🔁 تخصیص مشتری به نیرو", callback_data="admin_assign")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_reports_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🗓 گزارش هفتگی", callback_data="admin_reports_weekly")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_export_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⬇️ CSV هفتگی (7 روز)", callback_data="admin_export_week_csv")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_kpi_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎯 تنظیم KPI مشتری", callback_data="admin_kpi_set_client")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------
# KPI: انتخاب مشتری
# ---------------------------
def clients_inline_kb_for_kpi(clients) -> InlineKeyboardMarkup:
    btns = []
    for c in clients:
        title = f"{getattr(c, 'business_name', 'بدون‌نام')} (#{c.id})"
        btns.append([InlineKeyboardButton(text=title, callback_data=f"kpi_pick_client:{c.id}")])
    btns.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_kpi_menu")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


# ---------------------------
# Assign: انتخاب مشتری و نیرو
# ---------------------------
def assign_clients_kb(clients) -> InlineKeyboardMarkup:
    """
    لیست مشتری‌ها برای تخصیص:
    هر دکمه: «نام کسب‌وکار (#id)» → assign_pick_client:{client_id}
    """
    rows = []
    for c in clients:
        title = f"{getattr(c, 'business_name', 'بدون‌نام')} (#{c.id})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"assign_pick_client:{c.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assign_staff_kb(staff_tuples, include_auto: bool = True) -> InlineKeyboardMarkup:
    """
    staff_tuples: list of (User, current_count, max_capacity)
    نمایش ظرفیت به شکل cur/cap یا ∞
    """
    rows = []
    if include_auto:
        rows.append([InlineKeyboardButton(text="🤖 تخصیص خودکار", callback_data="assign_auto")])

    for s, cur, cap in staff_tuples:
        cap_human = "∞" if (int(cap or 0) == 0) else f"{cur}/{cap}"
        title = f"{getattr(s, 'name', 'بدون‌نام')} (ID={s.id}) | ظرفیت: {cap_human}"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"assign_pick_staff:{s.id}")])

    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
