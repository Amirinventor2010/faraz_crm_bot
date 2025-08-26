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
        [InlineKeyboardButton(text="💰 ثبت فروش جدید", callback_data="admin_add_sale")],  # ✅ جدید
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
        [InlineKeyboardButton(text="🗓 گزارش هفتگی کلی", callback_data="admin_reports_weekly")],
        [InlineKeyboardButton(text="📄 گزارش مشتری‌ها (انتخابی)", callback_data="admin_reports_clients")],
        [InlineKeyboardButton(text="👥 گزارش نیروها (انتخابی)", callback_data="admin_reports_staff")],
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
        # --- جدید ---
        [InlineKeyboardButton(text="📈 KPI مارکتینگ", callback_data="admin_mkt_kpi_menu")],
        [InlineKeyboardButton(text="📄 گزارش KPI مارکتینگ", callback_data="admin_mkt_kpi_report")],
        # -----------
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
    rows = []
    for c in clients:
        title = f"{getattr(c, 'business_name', 'بدون‌نام')} (#{c.id})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"assign_pick_client:{c.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assign_staff_kb(staff_tuples, include_auto: bool = True) -> InlineKeyboardMarkup:
    rows = []
    if include_auto:
        rows.append([InlineKeyboardButton(text="🤖 تخصیص خودکار", callback_data="assign_auto")])

    for s, cur, cap in staff_tuples:
        cap_human = "∞" if (int(cap or 0) == 0) else f"{cur}/{cap}"
        title = f"{getattr(s, 'name', 'بدون‌نام')} (ID={s.id}) | ظرفیت: {cap_human}"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"assign_pick_staff:{s.id}")])

    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_setup")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------
# Reports: انتخاب مشتری/نیرو + برگشت
# ---------------------------
def report_clients_kb(clients) -> InlineKeyboardMarkup:
    rows = []
    for c in clients:
        title = f"{getattr(c, 'business_name', 'بدون‌نام')} (#{c.id})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"report_client:{c.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_reports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def report_staff_kb(staff_list) -> InlineKeyboardMarkup:
    rows = []
    for s in staff_list:
        title = f"{getattr(s, 'name', 'بدون‌نام')} (ID={s.id})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"report_staff:{s.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_reports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_clients_reports_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⬅️ بازگشت به فهرست مشتری‌ها", callback_data="admin_reports_clients")],
        [InlineKeyboardButton(text="🔙 بازگشت به گزارش‌ها", callback_data="admin_reports_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_staff_reports_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⬅️ بازگشت به فهرست نیروها", callback_data="admin_reports_staff")],
        [InlineKeyboardButton(text="🔙 بازگشت به گزارش‌ها", callback_data="admin_reports_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------
# Sales: انتخاب مشتری برای ثبت فروش (جدید)
# ---------------------------
def sales_clients_kb(clients) -> InlineKeyboardMarkup:
    rows = []
    for c in clients:
        title = f"{getattr(c, 'business_name', 'بدون‌نام')} (#{c.id})"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"sale_pick_client:{c.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ انصراف", callback_data="admin_back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ============================================================
# 📈 KPI مارکتینگ: منوها (هفتگی/ماهانه + متریک‌ها + گزارش)
# ============================================================
def admin_mkt_kpi_root_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="KPI هفتگی", callback_data="mkt_kpi_scope:weekly"),
            InlineKeyboardButton(text="KPI ماهانه", callback_data="mkt_kpi_scope:monthly"),
        ],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_kpi_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_mkt_kpi_metrics_kb(scope: str) -> InlineKeyboardMarkup:
    weekly = [
        ("رشد فالوور", "ig_followers_growth"),
        ("تعداد لید اینستاگرام", "ig_leads"),
        ("تعداد کمپین اجرا", "campaigns_count"),
        ("تعداد فروش اینستا", "ig_sales"),
        ("تعداد فروش حضوری", "offline_sales"),
        ("ریچ پیج", "ig_reach"),
        ("تعداد لید واتساپ", "wa_leads"),
        ("تعداد فروش واتساپ", "wa_sales"),
        ("تعداد لید دیوار", "divar_leads"),
        ("تعداد فروش دیوار", "divar_sales"),
        ("تعداد لید ترب", "torob_leads"),
        ("تعداد فروش ترب", "torob_sales"),
    ]
    monthly = [
        ("نرخ تعامل", "engagement_rate"),
        ("رشد فالوور", "ig_followers_growth"),
        ("تعداد کمپین اجرا شده", "campaigns_count"),
        ("تعداد فروش اینستا", "ig_sales"),
        ("تعداد فروش حضوری", "offline_sales"),
        ("ریچ پیج", "ig_reach"),
        ("تعداد لید واتساپ", "wa_leads"),
        ("تعداد فروش واتساپ", "wa_sales"),
        ("تعداد لید دیوار", "divar_leads"),
        ("تعداد فروش دیوار", "divar_sales"),
        ("تعداد لید ترب", "torob_leads"),
        ("تعداد فروش ترب", "torob_sales"),
    ]
    items = weekly if scope == "weekly" else monthly
    rows = [[InlineKeyboardButton(text=fa, callback_data=f"mkt_kpi_metric:{scope}:{slug}")]
            for fa, slug in items]
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_mkt_kpi_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mkt_kpi_report_scope_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="گزارش هفتگی", callback_data="mkt_kpi_report_scope:weekly"),
            InlineKeyboardButton(text="گزارش ماهانه", callback_data="mkt_kpi_report_scope:monthly"),
        ],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_kpi_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_mkt_kpi_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="↩️ بازگشت به KPI مارکتینگ", callback_data="admin_mkt_kpi_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
