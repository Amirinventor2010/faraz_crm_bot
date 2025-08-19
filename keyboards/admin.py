from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# پنل اصلی مدیر
def admin_main_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🧰 راه‌اندازی اولیه", callback_data="admin_setup")],
        [InlineKeyboardButton(text="📊 گزارش‌ها", callback_data="admin_reports_menu")],
        [InlineKeyboardButton(text="📤 خروجی و دانلود", callback_data="admin_export_menu")],
        [InlineKeyboardButton(text="🎯 KPI / SLA", callback_data="admin_kpi_menu")],
        [InlineKeyboardButton(text="⬅️ بازگشت به منوی ورود", callback_data="back_to_entry")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# زیرمنوی راه‌اندازی اولیه (قبلی)
def admin_setup_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ ثبت نیرو", callback_data="admin_add_staff")],
        [InlineKeyboardButton(text="➕ ثبت مشتری", callback_data="admin_add_client")],
        [InlineKeyboardButton(text="🔁 تخصیص مشتری به نیرو", callback_data="admin_assign")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# منوی گزارش‌ها
def admin_reports_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📅 گزارش هفتگی مشتریان", callback_data="admin_reports_weekly")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# منوی خروجی
def admin_export_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⬇️ دانلود CSV هفتگی (فعالیت/بازخورد)", callback_data="admin_export_week_csv")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# منوی KPI
def admin_kpi_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎯 تنظیم KPI مشتری", callback_data="admin_kpi_set_client")],
        [InlineKeyboardButton(text="⬅️ بازگشت به پنل مدیر", callback_data="admin_back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# لیست مشتری برای انتخاب (KPI)
def clients_inline_kb_for_kpi(clients: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.business_name, callback_data=f"kpi_pick_client:{c.id}")]
        for c in clients[:50]
    ]
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_kpi_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
